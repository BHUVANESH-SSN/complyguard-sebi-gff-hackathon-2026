"""FastAPI application wiring for RegOps AI."""
import os
import shutil

from dotenv import load_dotenv

load_dotenv()  # must run before importing app.db.database, which reads
                # DATABASE_URL at import time

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.routes_review import router as review_router
from app.db.database import get_db
from app.services.gap_engine import get_gaps

app = FastAPI(title="RegOps AI API")

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
        from app.graph.build_graph import build_graph

        graph = build_graph()
        graph.invoke({"file_path": file_path, "filename": file.filename})
    except Exception as exc:
        # NOTE: broad on purpose while app.graph.build_graph is still a stub.
        # Narrow this once the real graph is pasted in, so genuine runtime
        # bugs don't get silently reported as "not wired up yet".
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
