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
from app.services.gap_engine import get_gaps


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

    try:
        # KNOWN GAP: build_graph() is real now (the LangGraph pipeline is fully
        # wired — see app/graph/), but this endpoint still invokes it with a
        # whole-document {"file_path", "filename"} shape left over from before
        # ComplianceState existed. The graph expects one clause at a time
        # (circular_id/clause_id/raw_clause/heading — see scripts/run_diff.py
        # for the correct shape), so this call always fails with a KeyError,
        # caught below and reported as 501. Wiring /upload into the real
        # per-clause pipeline (clean -> split -> loop -> invoke ->
        # mark_superseded_obligations) is a deliberate, separate design
        # decision (streaming vs. background job) — not done here.
        # NOTE: build_graph() also opens a real Postgres checkpointer
        # connection as a side effect of being called, even though this
        # request still ends in 501 — so this endpoint is not free to call
        # today without Postgres reachable.
        from app.graph.build_graph import build_graph

        graph = build_graph()
        graph.invoke({"file_path": file_path, "filename": file.filename})
    except Exception as exc:
        raise HTTPException(
            status_code=501, detail=f"Ingestion pipeline not wired up yet: {exc}"
        ) from exc

    return {"status": "success", "filename": file.filename}


@app.get("/gaps")
def list_gaps(db: Session = Depends(get_db)):
    try:
        return get_gaps(db)
    except Exception as exc:
        # Same note as above — narrow once app.db.models is real.
        raise HTTPException(status_code=501, detail=str(exc)) from exc
