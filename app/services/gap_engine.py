"""Obligation/Task status computation: pure logic plus thin DB-facing wrappers."""
from datetime import date


def compute_status(has_evidence: bool, deadline: str | None, today: date) -> str:
    if has_evidence:
        return "met"
    if deadline and date.fromisoformat(deadline) < today:
        return "overdue"
    return "pending"


def update_all_task_statuses(db) -> None:
    """Recompute status for every Task, based on its EvidenceLog rows and due_date."""
    from app.db.models import EvidenceLog, Task

    today = date.today()
    for task in db.query(Task).all():
        if task.status == "met":
            continue
        has_evidence = (
            db.query(EvidenceLog).filter(EvidenceLog.task_id == task.id).first()
            is not None
        )
        deadline = task.due_date.date().isoformat() if task.due_date else None
        task.status = compute_status(has_evidence, deadline, today)
    db.commit()


def get_gaps(db) -> list:
    from app.db.models import Task

    update_all_task_statuses(db)
    return db.query(Task).filter(Task.status.in_(["pending", "overdue"])).all()
