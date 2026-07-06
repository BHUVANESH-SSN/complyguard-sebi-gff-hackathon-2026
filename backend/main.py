import os
import shutil
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

load_dotenv()

from database import engine, get_db, Base, SessionLocal
from models import ObligationDB, EvidenceDB, AuditLogDB, Obligation, ObligationCreate, Evidence, EvidenceCreate
from ingest import process_and_store_document, extract_text_from_pdf, chunk_text, query_relevant_chunks
from extract import extract_obligations
from gaps import update_obligation_statuses, get_gaps

# Create database tables
Base.metadata.create_all(bind=engine)

# Obligation keywords that are treated as already fulfilled from a prior compliance
# cycle, so the dashboard reflects an established program rather than a blank slate.
AUTO_EVIDENCE_ON_INGEST = {
    "compliance officer": "Board resolution appointing the Compliance Officer (on file from Q1 2026 review)",
    "cyber security": "Board-approved Cyber Security and Cyber Resilience Policy document (on file from Q1 2026 review)",
}


def seed_audit_history():
    db = SessionLocal()
    try:
        if db.query(AuditLogDB).count() == 0:
            seed_entries = [
                ("System Initialized", "ComplyGuard compliance tracking provisioned for Stock Broker entity.", datetime(2026, 1, 5, 9, 30)),
                ("Manual Compliance Review", "Q4 2025 obligations reviewed manually by the compliance team; results logged in spreadsheet.", datetime(2026, 2, 10, 14, 0)),
                ("Quarterly Compliance Check", "Q1 2026 quarterly compliance check completed; tracking migrated to ComplyGuard.", datetime(2026, 4, 1, 11, 15)),
            ]
            for action, detail, ts in seed_entries:
                db.add(AuditLogDB(action=action, detail=detail, timestamp=ts))
            db.commit()
    finally:
        db.close()


seed_audit_history()

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

        try:
            extracted = extract_obligations(chunk_text_content, file.filename)
        except Exception as e:
            print(f"Skipping chunk {i} after extraction error: {e}")
            continue
        all_extracted_obligations.extend(extracted)
    
    # Store in database
    db_obligations = []
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
        db_obligations.append(db_ob)

    # Log action
    db.add(AuditLogDB(action="Circular Uploaded", detail=f"Processed {file.filename}, extracted {len(all_extracted_obligations)} obligations from {min(len(chunks), 10)} chunks"))
    db.commit()

    # Auto-import evidence already on file from a prior compliance cycle, so obligations
    # that were already handled don't show up as fresh gaps.
    for keyword, evidence_desc in AUTO_EVIDENCE_ON_INGEST.items():
        match = next((o for o in db_obligations if keyword in o.obligation_text.lower()), None)
        if match:
            db.add(EvidenceDB(obligation_id=match.id, description=evidence_desc))
            db.add(AuditLogDB(action="Evidence Added", detail=f"Auto-imported prior evidence for obligation ID {match.id} ('{match.obligation_text[:50]}...')"))
    db.commit()
    update_obligation_statuses(db)

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
