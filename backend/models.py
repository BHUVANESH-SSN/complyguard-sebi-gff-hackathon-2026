from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- SQLAlchemy Models (Database Tables) ---

class ObligationDB(Base):
    __tablename__ = "obligations"

    id = Column(Integer, primary_key=True, index=True)
    circular_name = Column(String, index=True)
    obligation_text = Column(String)
    intermediary = Column(String)
    deadline = Column(String, nullable=True)
    evidence_type = Column(String)
    source_chunk = Column(String)
    status = Column(String, default="pending")  # pending, met, overdue

    evidence = relationship("EvidenceDB", back_populates="obligation")

class EvidenceDB(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    obligation_id = Column(Integer, ForeignKey("obligations.id"))
    description = Column(String)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    obligation = relationship("ObligationDB", back_populates="evidence")

class AuditLogDB(Base):
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    detail = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

# --- Pydantic Schemas (API Validation) ---

class ObligationBase(BaseModel):
    circular_name: str
    obligation_text: str
    intermediary: str
    deadline: Optional[str] = None
    evidence_type: str
    source_chunk: str

class ObligationCreate(ObligationBase):
    pass

class Obligation(ObligationBase):
    id: int
    status: str

    class Config:
        from_attributes = True

class EvidenceCreate(BaseModel):
    obligation_id: int
    description: str

class Evidence(EvidenceCreate):
    id: int
    submitted_at: datetime

    class Config:
        from_attributes = True

class AuditLog(BaseModel):
    id: int
    action: str
    detail: str
    timestamp: datetime

    class Config:
        from_attributes = True
