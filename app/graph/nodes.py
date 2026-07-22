"""LangGraph pipeline nodes for the RegOps AI compliance-obligation pipeline."""
import hashlib
import json
from datetime import date, datetime, timedelta

import os
import time

from groq import APIConnectionError, Groq

from app.embeddings.embedder import embed_texts
from app.embeddings.qdrant_client import ensure_collection, get_client, search

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


GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_RETRIES = 3

EXTRACTION_PROMPT = """
You are a regulatory compliance AI. Read the SEBI circular clause below and extract
the single compliance obligation it imposes.

Return the result strictly as a JSON object matching this schema:
{{
    "requirement": "Clear description of what must be done",
    "frequency": "How often this recurs (e.g. one-time, monthly, quarterly, annual)",
    "evidence_type": "What proof is needed to show compliance",
    "deadline_rule": "An ISO date YYYY-MM-DD if the clause gives a specific calendar
        date, a recognized frequency keyword (monthly/quarterly/annual) if it recurs
        on a schedule with no fixed date, or null if open-ended with no deadline"
}}

Do not include any other text in your response, only the JSON object.

Clause to analyze:
{clause_text}
"""


def extractor_node(state: ComplianceState) -> dict:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable is not set")

    client = Groq(api_key=api_key)
    prompt = EXTRACTION_PROMPT.format(clause_text=state["raw_clause"])

    response = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=0,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
            )
            break
        except APIConnectionError:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(1.5 * (attempt + 1))

    content = response.choices[0].message.content
    content = content.replace("```json", "").replace("```", "").strip()
    start_idx = content.find("{")
    end_idx = content.rfind("}") + 1
    obligation = json.loads(content[start_idx:end_idx])
    return {"extracted_obligation": obligation}


SIMILARITY_THRESHOLD = 0.85


def _normalize(text: str) -> str:
    return " ".join(text.split()).strip().lower()


def differ_node(state: ComplianceState) -> dict:
    client = get_client()
    ensure_collection(client, vector_size=len(state["embedding"]))
    hits = search(client, state["embedding"], limit=1)

    if not hits or hits[0]["score"] < SIMILARITY_THRESHOLD:
        return {"diff_status": "new", "similarity_match": None}

    top = hits[0]
    if _normalize(top["text"]) == _normalize(state["raw_clause"]):
        return {"diff_status": "unchanged", "similarity_match": top}
    return {"diff_status": "amended", "similarity_match": top}
