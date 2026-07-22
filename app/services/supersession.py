"""Detects obligations superseded by a newer circular version.

This is a batch-level concern ("does any active obligation have no match anywhere in
the new circular?"), not a per-clause one, so it's a plain function a driver script
calls after all of a circular's clauses have been run through the graph — not a
LangGraph node.
"""
from app.db.models import Obligation


def mark_superseded_obligations(
    db, circular_id: str, matched_obligation_ids: set[str]
) -> list[str]:
    superseded_ids = []
    for obligation in db.query(Obligation).filter(Obligation.status == "active").all():
        if obligation.id not in matched_obligation_ids:
            obligation.status = "superseded"
            superseded_ids.append(obligation.id)
    db.commit()
    return superseded_ids
