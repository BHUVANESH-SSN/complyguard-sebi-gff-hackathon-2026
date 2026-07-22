from typing import get_args, get_type_hints

from app.graph.state import ComplianceState


def test_diff_status_allows_unchanged():
    hints = get_type_hints(ComplianceState, include_extras=True)
    diff_status_args = get_args(hints["diff_status"])
    assert set(diff_status_args) == {"new", "amended", "superseded", "unchanged", None}
