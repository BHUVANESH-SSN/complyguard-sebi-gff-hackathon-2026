from datetime import date

from app.services.gap_engine import compute_status


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
