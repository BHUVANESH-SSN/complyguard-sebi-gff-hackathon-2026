from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import Obligation
from app.services.supersession import mark_superseded_obligations


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_marks_unmatched_active_obligations_as_superseded():
    db = _make_session()
    db.add(Obligation(id="obl-1", clause_id="c1", requirement="A", frequency="annual",
                       evidence_type="policy", deadline_rule="annual", status="active"))
    db.add(Obligation(id="obl-2", clause_id="c2", requirement="B", frequency="annual",
                       evidence_type="policy", deadline_rule="annual", status="active"))
    db.commit()

    result = mark_superseded_obligations(db, "circular-2", matched_obligation_ids={"obl-1"})

    assert result == ["obl-2"]
    assert db.query(Obligation).filter(Obligation.id == "obl-2").one().status == "superseded"
    assert db.query(Obligation).filter(Obligation.id == "obl-1").one().status == "active"


def test_does_not_touch_already_inactive_obligations():
    db = _make_session()
    db.add(Obligation(id="obl-3", clause_id="c3", requirement="C", frequency="annual",
                       evidence_type="policy", deadline_rule="annual", status="superseded"))
    db.commit()

    result = mark_superseded_obligations(db, "circular-2", matched_obligation_ids=set())

    assert result == []
    assert db.query(Obligation).filter(Obligation.id == "obl-3").one().status == "superseded"
