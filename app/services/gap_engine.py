"""Obligation status computation: pure logic plus a thin DB-facing wrapper."""
from datetime import date


def compute_status(has_evidence: bool, deadline: str | None, today: date) -> str:
    if has_evidence:
        return "met"
    if deadline and date.fromisoformat(deadline) < today:
        return "overdue"
    return "pending"


def update_all_statuses(db) -> None:
    """Recompute status for every obligation.

    Requires app.db.models to provide real ObligationDB (.id, .deadline,
    .status) and EvidenceDB (.obligation_id) classes — currently stubs.
    """
    from app.db.models import EvidenceDB, ObligationDB

    today = date.today()
    for obligation in db.query(ObligationDB).all():
        if obligation.status == "met":
            continue
        has_evidence = (
            db.query(EvidenceDB)
            .filter(EvidenceDB.obligation_id == obligation.id)
            .first()
            is not None
        )
        obligation.status = compute_status(has_evidence, obligation.deadline, today)
    db.commit()


def get_gaps(db) -> list:
    from app.db.models import ObligationDB

    update_all_statuses(db)
    return (
        db.query(ObligationDB)
        .filter(ObligationDB.status.in_(["pending", "overdue"]))
        .all()
    )
