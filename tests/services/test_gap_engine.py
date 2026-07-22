from datetime import date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import EvidenceLog, Obligation, Task
from app.services.gap_engine import compute_status, get_gaps, update_all_task_statuses


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_met_when_evidence_present_even_past_deadline():
    assert compute_status(True, "2020-01-01", date(2026, 1, 1)) == "met"


def test_overdue_when_no_evidence_and_deadline_passed():
    assert compute_status(False, "2020-01-01", date(2026, 1, 1)) == "overdue"


def test_pending_when_no_evidence_and_deadline_in_future():
    assert compute_status(False, "2030-01-01", date(2026, 1, 1)) == "pending"


def test_pending_when_no_evidence_and_no_deadline():
    assert compute_status(False, None, date(2026, 1, 1)) == "pending"


def test_pending_when_deadline_is_today():
    assert compute_status(False, "2026-01-01", date(2026, 1, 1)) == "pending"


def test_update_all_task_statuses_marks_overdue_task_without_evidence():
    db = _make_session()
    db.add(Obligation(id="obl-1", clause_id="c1", requirement="Do X",
                       frequency="annual", evidence_type="policy",
                       deadline_rule="annual"))
    db.add(Task(id="task-1", obligation_id="obl-1", owner="compliance",
                due_date=datetime(2020, 1, 1), status="open"))
    db.commit()

    update_all_task_statuses(db)

    task = db.query(Task).filter(Task.id == "task-1").one()
    assert task.status == "overdue"


def test_update_all_task_statuses_marks_met_task_with_evidence():
    db = _make_session()
    db.add(Obligation(id="obl-2", clause_id="c2", requirement="Do Y",
                       frequency="annual", evidence_type="policy",
                       deadline_rule="annual"))
    db.add(Task(id="task-2", obligation_id="obl-2", owner="compliance",
                due_date=datetime(2020, 1, 1), status="open"))
    db.add(EvidenceLog(id="ev-1", task_id="task-2", file_ref="doc.pdf"))
    db.commit()

    update_all_task_statuses(db)

    task = db.query(Task).filter(Task.id == "task-2").one()
    assert task.status == "met"


def test_get_gaps_returns_only_pending_and_overdue_tasks():
    db = _make_session()
    db.add(Obligation(id="obl-3", clause_id="c3", requirement="Do Z",
                       frequency="annual", evidence_type="policy",
                       deadline_rule="annual"))
    db.add(Task(id="task-3", obligation_id="obl-3", owner="compliance",
                due_date=datetime(2020, 1, 1), status="open"))
    db.add(Obligation(id="obl-4", clause_id="c4", requirement="Do W",
                       frequency="annual", evidence_type="policy",
                       deadline_rule="annual"))
    db.add(Task(id="task-4", obligation_id="obl-4", owner="compliance",
                due_date=datetime(2020, 1, 1), status="open"))
    db.add(EvidenceLog(id="ev-2", task_id="task-4", file_ref="doc2.pdf"))
    db.commit()

    gaps = get_gaps(db)

    assert {t.id for t in gaps} == {"task-3"}
