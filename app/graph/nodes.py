"""LangGraph pipeline nodes for the RegOps AI compliance-obligation pipeline."""
import hashlib
import json
from datetime import date, datetime, timedelta

from app.embeddings.embedder import embed_texts

from .state import ComplianceState

FREQUENCY_DAYS = {
    "monthly": 30,
    "quarterly": 90,
    "annual": 365,
}


def chunker_node(state: ComplianceState) -> dict:
    raw_clause = state["raw_clause"].strip()
    heading = state.get("heading") or raw_clause.splitlines()[0][:80].strip()
    return {"raw_clause": raw_clause, "heading": heading}


def embedder_node(state: ComplianceState) -> dict:
    embedding = embed_texts([state["raw_clause"]])[0]
    return {"embedding": embedding}


def resolve_due_date(deadline_rule: str | None, today: date) -> date | None:
    if not deadline_rule:
        return None
    try:
        return date.fromisoformat(deadline_rule)
    except ValueError:
        pass
    days = FREQUENCY_DAYS.get(deadline_rule.strip().lower())
    if days is None:
        return None
    return today + timedelta(days=days)


def compute_audit_hash(prev_hash: str, action: dict, timestamp: datetime) -> str:
    payload = prev_hash + json.dumps(action, sort_keys=True) + timestamp.isoformat()
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
