"""FastAPI application wiring for RegOps AI."""
import os
import shutil
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()  # must run before importing app.db.database, which reads
                # DATABASE_URL at import time

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.routes_review import router as review_router
from app.db.database import Base, engine, get_db
import app.db.models  # noqa: F401 — registers all tables on Base.metadata before create_all
from app.graph.build_graph import build_graph
from app.ingestion.clause_splitter import split_into_clauses
from app.ingestion.pdf_cleaner import extract_and_clean
from app.services.gap_engine import get_gaps
from app.services.supersession import mark_superseded_obligations


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="RegOps AI API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/upload")
async def upload_circular(file: UploadFile = File(...), db: Session = Depends(get_db)):
    os.makedirs("data/raw_pdfs", exist_ok=True)
    file_path = f"data/raw_pdfs/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    circular_id = os.path.splitext(file.filename)[0]

    try:
        cleaned_text = extract_and_clean(file_path)
    except Exception as exc:
        # Fail fast here, before build_graph() ever runs, so a bad/unreadable
        # PDF doesn't pay the cost of opening a real Postgres checkpointer
        # connection for a request that can't proceed anyway.
        raise HTTPException(
            status_code=422, detail=f"PDF cleaning failed: {exc}"
        ) from exc

    clauses = split_into_clauses(cleaned_text)
    if not clauses:
        return {
            "status": "success",
            "filename": file.filename,
            "circular_id": circular_id,
            "clauses_processed": 0,
            "results": [],
        }

    graph = build_graph()
    results = []
    matched_obligation_ids = set()

    for i, clause_text in enumerate(clauses):
        clause_id = f"clause-{i}"
        state = {
            "circular_id": circular_id,
            "clause_id": clause_id,
            "raw_clause": clause_text,
            "heading": None,
        }
        config = {"configurable": {"thread_id": f"{circular_id}:{clause_id}"}}

        try:
            result = graph.invoke(state, config=config)
        except Exception as exc:
            results.append({"clause_id": clause_id, "status": "error", "detail": str(exc)})
            continue

        if "__interrupt__" in result:
            # Paused for human review (amended/superseded clause). The old
            # obligation this clause matches is still active and awaiting a
            # decision — protect it from being wrongly marked superseded
            # below just because its review hasn't been submitted yet.
            interrupt_payload = result["__interrupt__"][0].value
            similarity_match = interrupt_payload.get("similarity_match") or {}
            obligation_id = (similarity_match.get("payload") or {}).get("obligation_id")
            if obligation_id:
                matched_obligation_ids.add(obligation_id)
            results.append({"clause_id": clause_id, "status": "pending_review"})
            continue

        task = result.get("task")
        if task:
            matched_obligation_ids.add(task["obligation_id"])
        results.append({
            "clause_id": clause_id,
            "status": "processed",
            "diff_status": result.get("diff_status"),
            "task": task,
        })

    # Only mark obligations superseded when every clause in this circular was
    # actually processed — a clause that errored out doesn't tell us whether
    # its obligation is still current, so treating a partial run as complete
    # coverage would risk wrongly superseding obligations that just failed to
    # re-match due to the error, not because they were genuinely dropped.
    had_errors = any(r["status"] == "error" for r in results)
    superseded = []
    if not had_errors:
        superseded = mark_superseded_obligations(db, circular_id, matched_obligation_ids)

    return {
        "status": "success",
        "filename": file.filename,
        "circular_id": circular_id,
        "clauses_processed": len(clauses),
        "results": results,
        "superseded_obligation_ids": superseded,
        "supersession_skipped_due_to_errors": had_errors,
    }


@app.get("/gaps")
def list_gaps(db: Session = Depends(get_db)):
    try:
        return get_gaps(db)
    except Exception as exc:
        # Same note as above — narrow once app.db.models is real.
        raise HTTPException(status_code=501, detail=str(exc)) from exc
