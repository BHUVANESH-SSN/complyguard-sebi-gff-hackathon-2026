from sqlalchemy.orm import Session
from datetime import datetime
from models import ObligationDB, EvidenceDB

def update_obligation_statuses(db: Session):
    obligations = db.query(ObligationDB).all()
    now_date_str = datetime.utcnow().strftime("%Y-%m-%d")
    
    for ob in obligations:
        if ob.status == "met":
            continue
            
        # Check if any evidence exists
        evidence = db.query(EvidenceDB).filter(EvidenceDB.obligation_id == ob.id).first()
        
        if evidence:
            ob.status = "met"
        elif ob.deadline and ob.deadline < now_date_str:
            ob.status = "overdue"
        else:
            ob.status = "pending"
            
        db.commit()

def get_gaps(db: Session):
    update_obligation_statuses(db)
    return db.query(ObligationDB).filter(ObligationDB.status.in_(["pending", "overdue"])).all()
