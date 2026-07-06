import os
import shutil
from fastapi import FastAPI, Depends, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from database import engine, get_db, Base
from models import ObligationDB, EvidenceDB, AuditLogDB, Obligation, ObligationCreate, Evidence, EvidenceCreate
from ingest import process_and_store_document, extract_text_from_pdf, chunk_text, query_relevant_chunks
from extract import extract_obligations
from gaps import update_obligation_statuses, get_gaps

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ComplyGuard API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/upload")
async def upload_circular(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save file locally
    os.makedirs("data/circulars", exist_ok=True)
    file_path = f"data/circulars/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Retrieve chunks
    chunks = process_and_store_document(file_path, file.filename)
    
    # Map-Reduce Extraction over all chunks
    all_extracted_obligations = []
    
    for i, chunk_text_content in enumerate(chunks):
        # We only process the first 10 chunks to avoid timeout for this demo
        # For a production system with async celery tasks, this would process all chunks.
        if i >= 10:
            break
            
        extracted = extract_obligations(chunk_text_content, file.filename)
        all_extracted_obligations.extend(extracted)
    
    # Store in database
    for ob in all_extracted_obligations:
        db_ob = ObligationDB(
            circular_name=ob.circular_name,
            obligation_text=ob.obligation_text,
            intermediary=ob.intermediary,
            deadline=ob.deadline,
            evidence_type=ob.evidence_type,
            source_chunk=ob.source_chunk
        )
        db.add(db_ob)
    
    # Log action
    db.add(AuditLogDB(action="Circular Uploaded", detail=f"Processed {file.filename}, extracted {len(all_extracted_obligations)} obligations from {min(len(chunks), 10)} chunks"))
    db.commit()
    
    return {"status": "success", "chunks_stored": len(chunks), "obligations_extracted": len(all_extracted_obligations)}

@app.get("/obligations", response_model=List[Obligation])
def list_obligations(db: Session = Depends(get_db)):
    update_obligation_statuses(db)
    return db.query(ObligationDB).all()

@app.post("/evidence", response_model=Evidence)
def add_evidence(evidence: EvidenceCreate, db: Session = Depends(get_db)):
    db_evidence = EvidenceDB(
        obligation_id=evidence.obligation_id,
        description=evidence.description
    )
    db.add(db_evidence)
    
    # Log action
    db.add(AuditLogDB(action="Evidence Added", detail=f"Added evidence for obligation ID {evidence.obligation_id}"))
    
    db.commit()
    db.refresh(db_evidence)
    
    update_obligation_statuses(db)
    return db_evidence

@app.get("/evidence", response_model=List[Evidence])
def list_evidence(db: Session = Depends(get_db)):
    return db.query(EvidenceDB).all()

@app.get("/gaps", response_model=List[Obligation])
def list_gaps(db: Session = Depends(get_db)):
    return get_gaps(db)

@app.get("/audit_log")
def get_audit_log(db: Session = Depends(get_db)):
    return db.query(AuditLogDB).order_by(AuditLogDB.timestamp.desc()).all()
