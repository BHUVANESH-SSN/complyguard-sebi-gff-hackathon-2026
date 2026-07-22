# LangGraph Compliance Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the user's pasted LangGraph pipeline code (models, state, build_graph,
routes_review) actually work end to end: fix the 6 integration bugs it introduced,
implement all 9 node functions, and align the rest of the scaffold (gap engine, qdrant
client, tests, dependencies) with the real schema.

**Architecture:** `app/graph/nodes.py` gets built up across four tasks (pure nodes,
Groq-calling extractor, Qdrant-calling differ, then the five DB-writing/interrupt nodes
that share a `task` dict contract and an audit-hash helper). `build_graph.py` is fixed to
use a lazy, correctly-scoped Postgres checkpointer and the dynamic `interrupt()`
mechanism instead of the conflicting `interrupt_before` + `Command(resume=...)` mix.
`routes_review.py` becomes import-safe (lazy graph singleton) and gets wired into
`app/api/main.py`. `gap_engine.py` is rewritten for the real `Task`-level schema. A new
`app/services/supersession.py` handles the batch-level "obligation dropped from a newer
circular" concern, kept separate from per-clause gap tracking.

**Tech Stack:** LangGraph 1.2.9 + `langgraph-checkpoint-postgres` 3.1.0, Groq
(`llama-3.3-70b-versatile`), Qdrant (already wired, Task 11 of the prior plan),
SQLAlchemy + Postgres, pytest with mocks for Groq/Qdrant/Postgres, in-memory SQLite for
real ORM-level tests.

## Global Constraints

- `ComplianceState.diff_status` gains a `"unchanged"` literal value (clause re-ingested,
  no change) alongside the existing `"new"`, `"amended"`, `"superseded"`, `None`.
- `app/db/models.py` must import `Base` from `app.db.database` — one shared declarative
  base for the whole app, not two.
- `PostgresSaver.from_conn_string(conn_string)` returns `Iterator[PostgresSaver]`
  (verified against the installed 3.1.0) — it is a context manager. Never assign its
  return value directly to a variable and use it as a saver.
- The graph's Postgres connection string comes from `DATABASE_URL` (env var, same
  pattern as `app/db/database.py`), never a hardcoded string — and never `regops_db`,
  which doesn't match `docker-compose.yml`'s `regops` database name.
- Human-review resume value is always `Command(resume={"decision": ..., "actor": ...})`
  — a dict, not a bare string — so `human_review_node`'s `interrupt()` call can recover
  both who decided and what they decided.
- `routes_review.py` must not call `build_graph()` at module import time — lazy,
  cached, built on first request only (same import-safety principle as every other
  module in this codebase).
- `qdrant_client.search()`'s return shape gains a `"payload"` key (full raw Qdrant
  payload) alongside the existing `"text"`/`"score"` keys — additive, backward
  compatible.
- Test runner is pytest; mock Groq/Qdrant/the Postgres checkpointer in unit tests
  (matching the established style from the prior restructure); use in-memory SQLite via
  the shared `Base` for tests that need real ORM behavior (queries, joins, commits).
- Design reference: `docs/superpowers/specs/2026-07-22-langgraph-pipeline-design.md`.

---

### Task 1: Unify the declarative Base and extend `ComplianceState`

**Files:**
- Modify: `app/db/models.py`
- Modify: `app/graph/state.py`
- Test: `tests/db/test_models.py`
- Test: `tests/graph/test_state.py`

**Interfaces:**
- Produces: `Obligation`, `Task`, `EvidenceLog`, `AuditTrail` (SQLAlchemy models,
  sharing `app.db.database.Base`'s metadata) — consumed by Tasks 3, 7, 8, 9, 11, 12.
- Produces: `ComplianceState` with `diff_status` allowing `"unchanged"` — consumed by
  Tasks 4–9.

- [ ] **Step 1: Write the failing tests**

Create `tests/db/test_models.py`:

```python
from sqlalchemy import create_engine, inspect

from app.db.database import Base as DatabaseBase
from app.db.models import AuditTrail, EvidenceLog, Obligation, Task


def test_models_share_the_database_base():
    assert Obligation.metadata is DatabaseBase.metadata


def test_all_tables_registered_on_shared_metadata():
    table_names = set(DatabaseBase.metadata.tables.keys())
    assert {"obligations", "tasks", "evidence_log", "audit_trail"} <= table_names


def test_create_all_tables_against_sqlite():
    engine = create_engine("sqlite:///:memory:")
    DatabaseBase.metadata.create_all(engine)
    with engine.connect() as conn:
        inspector = inspect(conn)
        assert set(inspector.get_table_names()) >= {
            "obligations", "tasks", "evidence_log", "audit_trail",
        }
```

Create `tests/graph/__init__.py` (empty) and `tests/graph/test_state.py`:

```python
from typing import get_args, get_type_hints

from app.graph.state import ComplianceState


def test_diff_status_allows_unchanged():
    hints = get_type_hints(ComplianceState, include_extras=True)
    diff_status_args = get_args(hints["diff_status"])
    assert set(diff_status_args) == {"new", "amended", "superseded", "unchanged", None}
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
mkdir -p tests/graph && touch tests/graph/__init__.py
source venv/bin/activate
pytest tests/db/test_models.py tests/graph/test_state.py -v
```

Expected: `test_models_share_the_database_base` FAILS (`Obligation.metadata` is a
different object from `DatabaseBase.metadata` — two separate `declarative_base()`
calls). `test_diff_status_allows_unchanged` FAILS (`"unchanged"` not in the current
Literal's args).

- [ ] **Step 3: Fix `app/db/models.py`**

Replace the file's current `Base = declarative_base()` line and the `declarative_base`
import with an import of the shared `Base`:

```python
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
import datetime

from app.db.database import Base

class Obligation(Base):
    __tablename__ = "obligations"
    id = Column(String, primary_key=True)
    clause_id = Column(String)
    requirement = Column(Text)
    frequency = Column(String)
    evidence_type = Column(String)
    deadline_rule = Column(String)
    status = Column(String, default="active")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True)
    obligation_id = Column(String, ForeignKey("obligations.id"))
    owner = Column(String)
    due_date = Column(DateTime)
    status = Column(String, default="open")

class EvidenceLog(Base):
    __tablename__ = "evidence_log"
    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey("tasks.id"))
    file_ref = Column(String)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

class AuditTrail(Base):
    __tablename__ = "audit_trail"
    id = Column(String, primary_key=True)
    thread_id = Column(String)
    node_name = Column(String)
    action = Column(JSON)
    actor = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    prev_hash = Column(String)
    hash = Column(String)
```

- [ ] **Step 4: Fix `app/graph/state.py`**

```python
from typing import TypedDict, Literal, Optional, List

class ComplianceState(TypedDict):
    circular_id: str
    clause_id: str
    raw_clause: str
    heading: str
    embedding: Optional[List[float]]
    extracted_obligation: Optional[dict]
    similarity_match: Optional[dict]
    diff_status: Literal["new", "amended", "superseded", "unchanged", None]
    task: Optional[dict]
    evidence_status: Literal["present", "missing", "invalid", None]
    human_decision: Optional[str]
    audit_log: List[dict]
```

- [ ] **Step 5: Run the tests again to verify they pass**

```bash
pytest tests/db/test_models.py tests/graph/test_state.py -v
```

Expected: PASS — all 4 tests green.

- [ ] **Step 6: Commit**

```bash
git add app/db/models.py app/graph/state.py tests/db/test_models.py tests/graph
git commit -m "Unify declarative Base and add unchanged to diff_status"
```

---

### Task 2: Extend `qdrant_client.search()` to return the full payload

**Files:**
- Modify: `app/embeddings/qdrant_client.py`
- Modify: `tests/embeddings/test_qdrant_client.py`

**Interfaces:**
- Produces: `search(...)` results now include a `"payload"` key — consumed by Task 6
  (`differ_node`, via `similarity_match["payload"]["obligation_id"]`).

- [ ] **Step 1: Update the existing test**

In `tests/embeddings/test_qdrant_client.py`, replace the
`test_search_maps_results_to_text_and_score` test with:

```python
def test_search_maps_results_to_text_and_score():
    client = MagicMock()
    hit = MagicMock(payload={"text": "clause one", "obligation_id": "obl-1"}, score=0.9)
    client.query_points.return_value = MagicMock(points=[hit])

    results = search(client, query_vector=[0.1, 0.2])

    assert results == [
        {
            "text": "clause one",
            "score": 0.9,
            "payload": {"text": "clause one", "obligation_id": "obl-1"},
        }
    ]
    client.query_points.assert_called_once_with(
        collection_name=DEFAULT_COLLECTION, query=[0.1, 0.2], limit=3
    )
```

Leave the other three tests in that file (`test_ensure_collection_creates_when_missing`,
`test_ensure_collection_skips_when_present`,
`test_upsert_chunks_sends_one_point_per_chunk`) untouched.

- [ ] **Step 2: Run the test to verify it fails**

```bash
pytest tests/embeddings/test_qdrant_client.py::test_search_maps_results_to_text_and_score -v
```

Expected: FAIL — actual result dict has only `text`/`score` keys, missing `payload`.

- [ ] **Step 3: Update `search()` in `app/embeddings/qdrant_client.py`**

Replace the function body's return statement:

```python
def search(
    client: QdrantClient,
    query_vector: list[float],
    limit: int = 3,
    collection_name: str = DEFAULT_COLLECTION,
) -> list[dict]:
    response = client.query_points(
        collection_name=collection_name, query=query_vector, limit=limit
    )
    return [
        {"text": p.payload.get("text"), "score": p.score, "payload": p.payload}
        for p in response.points
    ]
```

- [ ] **Step 4: Run the full qdrant_client test file to verify everything passes**

```bash
pytest tests/embeddings/test_qdrant_client.py -v
```

Expected: PASS — all 4 tests green.

- [ ] **Step 5: Commit**

```bash
git add app/embeddings/qdrant_client.py tests/embeddings/test_qdrant_client.py
git commit -m "Extend qdrant_client.search() to return the full payload"
```

---

### Task 3: Rewrite `gap_engine.py` for the Task-level schema

**Files:**
- Modify: `app/services/gap_engine.py`
- Modify: `tests/services/test_gap_engine.py`

**Interfaces:**
- Consumes: `app.db.models.Task`, `app.db.models.EvidenceLog`, `app.db.models.Obligation`
  (Task 1).
- Produces: `compute_status(...)` (unchanged signature/behavior), `update_all_task_statuses(db)`,
  `get_gaps(db) -> list[Task]` — `get_gaps` consumed by `app/api/main.py` (unchanged
  caller, already imports `get_gaps` by that name).

- [ ] **Step 1: Write the new/updated tests**

Replace `tests/services/test_gap_engine.py` with (the 5 existing pure `compute_status`
tests are kept verbatim; three new DB-facing tests are added):

```python
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
```

- [ ] **Step 2: Run the tests to verify the DB-facing ones fail**

```bash
pytest tests/services/test_gap_engine.py -v
```

Expected: the 5 pure tests PASS unchanged; the 3 new DB-facing tests FAIL (`ImportError`
or `AttributeError` — `update_all_task_statuses`/current `get_gaps` still reference the
old `ObligationDB`/`EvidenceDB` names that no longer exist).

- [ ] **Step 3: Rewrite `app/services/gap_engine.py`**

```python
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
```

- [ ] **Step 4: Run the tests again to verify they pass**

```bash
pytest tests/services/test_gap_engine.py -v
```

Expected: PASS — all 8 tests green.

- [ ] **Step 5: Commit**

```bash
git add app/services/gap_engine.py tests/services/test_gap_engine.py
git commit -m "Rewrite gap_engine for the Task-level schema"
```

---

### Task 4: `app/graph/nodes.py` — pure/simple nodes and helpers

**Files:**
- Create: `app/graph/nodes.py`
- Test: `tests/graph/test_nodes.py`

**Interfaces:**
- Consumes: `app.embeddings.embedder.embed_texts` (existing).
- Produces: `chunker_node`, `embedder_node`, `resolve_due_date(deadline_rule, today) -> date | None`,
  `compute_audit_hash(prev_hash, action, timestamp) -> str` — `resolve_due_date` and
  `compute_audit_hash` consumed by Task 7's DB-writing nodes.

- [ ] **Step 1: Write the failing tests**

Create `tests/graph/test_nodes.py`:

```python
from datetime import date, datetime
from unittest.mock import patch

from app.graph.nodes import (
    chunker_node,
    compute_audit_hash,
    embedder_node,
    resolve_due_date,
)


def test_chunker_node_strips_whitespace_and_derives_heading():
    state = {"raw_clause": "  1. Appoint a compliance officer.\nDetails here.  "}
    result = chunker_node(state)
    assert result["raw_clause"] == "1. Appoint a compliance officer.\nDetails here."
    assert result["heading"] == "1. Appoint a compliance officer."


def test_chunker_node_keeps_existing_heading():
    state = {"raw_clause": "1. Do X.", "heading": "Custom Heading"}
    result = chunker_node(state)
    assert result["heading"] == "Custom Heading"


def test_embedder_node_calls_embed_texts_with_raw_clause():
    with patch("app.graph.nodes.embed_texts", return_value=[[0.1, 0.2]]) as mock_embed:
        result = embedder_node({"raw_clause": "1. Do X."})
    mock_embed.assert_called_once_with(["1. Do X."])
    assert result == {"embedding": [0.1, 0.2]}


def test_resolve_due_date_parses_iso_date():
    assert resolve_due_date("2026-12-31", date(2026, 1, 1)) == date(2026, 12, 31)


def test_resolve_due_date_maps_quarterly_keyword():
    assert resolve_due_date("quarterly", date(2026, 1, 1)) == date(2026, 4, 1)


def test_resolve_due_date_maps_annual_keyword():
    assert resolve_due_date("annual", date(2026, 1, 1)) == date(2027, 1, 1)


def test_resolve_due_date_returns_none_for_unrecognized_or_missing():
    assert resolve_due_date(None, date(2026, 1, 1)) is None
    assert resolve_due_date("", date(2026, 1, 1)) is None
    assert resolve_due_date("whenever", date(2026, 1, 1)) is None


def test_compute_audit_hash_is_deterministic_and_chains_on_prev_hash():
    ts = datetime(2026, 1, 1, 12, 0, 0)
    action = {"obligation_id": "obl-1"}
    h1 = compute_audit_hash("", action, ts)
    h2 = compute_audit_hash("", action, ts)
    h3 = compute_audit_hash("some-prev-hash", action, ts)
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pytest tests/graph/test_nodes.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.graph.nodes'` (this
replaces the empty placeholder stub from the prior restructure).

- [ ] **Step 3: Create `app/graph/nodes.py`**

```python
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
```

- [ ] **Step 4: Run the test again to verify it passes**

```bash
pytest tests/graph/test_nodes.py -v
```

Expected: PASS — all 8 tests green.

- [ ] **Step 5: Commit**

```bash
git add app/graph/nodes.py tests/graph/test_nodes.py
git commit -m "Add pure chunker/embedder nodes and due-date/audit-hash helpers"
```

---

### Task 5: `app/graph/nodes.py` — `extractor_node` (Groq)

**Files:**
- Modify: `app/graph/nodes.py`
- Create: `tests/graph/test_nodes_extractor.py`

**Interfaces:**
- Produces: `extractor_node` — consumed by `build_graph()` (Task 8).

- [ ] **Step 1: Write the failing tests**

Create `tests/graph/test_nodes_extractor.py`:

```python
from unittest.mock import MagicMock, patch

import pytest

from app.graph.nodes import extractor_node


def _make_fake_groq_response(content: str):
    message = MagicMock(content=content)
    choice = MagicMock(message=message)
    return MagicMock(choices=[choice])


def test_extractor_node_parses_json_response(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    fake_response = _make_fake_groq_response(
        '{"requirement": "Appoint a compliance officer", "frequency": "one-time", '
        '"evidence_type": "board resolution", "deadline_rule": "2026-06-30"}'
    )
    with patch("app.graph.nodes.Groq") as mock_groq_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = fake_response
        mock_groq_cls.return_value = mock_client

        result = extractor_node({"raw_clause": "1. Appoint a compliance officer by 2026-06-30."})

    assert result == {
        "extracted_obligation": {
            "requirement": "Appoint a compliance officer",
            "frequency": "one-time",
            "evidence_type": "board resolution",
            "deadline_rule": "2026-06-30",
        }
    }


def test_extractor_node_strips_markdown_code_fences(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    fake_response = _make_fake_groq_response(
        '```json\n{"requirement": "Do X", "frequency": "annual", '
        '"evidence_type": "policy doc", "deadline_rule": "annual"}\n```'
    )
    with patch("app.graph.nodes.Groq") as mock_groq_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = fake_response
        mock_groq_cls.return_value = mock_client

        result = extractor_node({"raw_clause": "2. Do X annually."})

    assert result["extracted_obligation"]["requirement"] == "Do X"


def test_extractor_node_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        extractor_node({"raw_clause": "1. Do X."})
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pytest tests/graph/test_nodes_extractor.py -v
```

Expected: FAIL — `ImportError: cannot import name 'extractor_node' from 'app.graph.nodes'`.

- [ ] **Step 3: Add imports and `extractor_node` to `app/graph/nodes.py`**

Add these imports to the top of the existing import block (after the existing
`import hashlib`/`import json`/`from datetime import ...` lines):

```python
import os
import time

from groq import APIConnectionError, Groq
```

Append to the end of the file:

```python
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
```

- [ ] **Step 4: Run the test again to verify it passes**

```bash
pytest tests/graph/test_nodes_extractor.py -v
```

Expected: PASS — all 3 tests green.

- [ ] **Step 5: Run the full nodes test suite to confirm no regression**

```bash
pytest tests/graph/ -v
```

Expected: all tests from Task 4 and this task pass together.

- [ ] **Step 6: Commit**

```bash
git add app/graph/nodes.py tests/graph/test_nodes_extractor.py
git commit -m "Add Groq-based extractor_node"
```

---

### Task 6: `app/graph/nodes.py` — `differ_node` (Qdrant similarity search)

**Files:**
- Modify: `app/graph/nodes.py`
- Create: `tests/graph/test_nodes_differ.py`

**Interfaces:**
- Consumes: `app.embeddings.qdrant_client.{get_client,ensure_collection,search}` (Task 2
  extended `search()`'s return shape).
- Produces: `differ_node` — consumed by `build_graph()` (Task 8).

- [ ] **Step 1: Write the failing tests**

Create `tests/graph/test_nodes_differ.py`:

```python
from unittest.mock import patch

from app.graph.nodes import differ_node


def test_differ_node_returns_new_when_no_match():
    with (
        patch("app.graph.nodes.get_client", return_value="fake-client"),
        patch("app.graph.nodes.ensure_collection") as mock_ensure,
        patch("app.graph.nodes.search", return_value=[]) as mock_search,
    ):
        result = differ_node({"raw_clause": "1. Do X.", "embedding": [0.1] * 768})

    assert result == {"diff_status": "new", "similarity_match": None}
    mock_ensure.assert_called_once_with("fake-client", vector_size=768)
    mock_search.assert_called_once()


def test_differ_node_returns_unchanged_when_match_is_identical_text():
    hit = {"text": "1. Do X.", "score": 0.99, "payload": {"obligation_id": "obl-1"}}
    with (
        patch("app.graph.nodes.get_client", return_value="fake-client"),
        patch("app.graph.nodes.ensure_collection"),
        patch("app.graph.nodes.search", return_value=[hit]),
    ):
        result = differ_node({"raw_clause": "1.  Do X.  ", "embedding": [0.1] * 768})

    assert result == {"diff_status": "unchanged", "similarity_match": hit}


def test_differ_node_returns_amended_when_match_has_different_text():
    hit = {"text": "1. Do X annually.", "score": 0.9, "payload": {"obligation_id": "obl-1"}}
    with (
        patch("app.graph.nodes.get_client", return_value="fake-client"),
        patch("app.graph.nodes.ensure_collection"),
        patch("app.graph.nodes.search", return_value=[hit]),
    ):
        result = differ_node({"raw_clause": "1. Do X quarterly.", "embedding": [0.1] * 768})

    assert result == {"diff_status": "amended", "similarity_match": hit}


def test_differ_node_returns_new_when_score_below_threshold():
    hit = {"text": "unrelated clause", "score": 0.5, "payload": {}}
    with (
        patch("app.graph.nodes.get_client", return_value="fake-client"),
        patch("app.graph.nodes.ensure_collection"),
        patch("app.graph.nodes.search", return_value=[hit]),
    ):
        result = differ_node({"raw_clause": "1. Do X.", "embedding": [0.1] * 768})

    assert result == {"diff_status": "new", "similarity_match": None}
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pytest tests/graph/test_nodes_differ.py -v
```

Expected: FAIL — `ImportError: cannot import name 'differ_node' from 'app.graph.nodes'`.

- [ ] **Step 3: Add imports and `differ_node` to `app/graph/nodes.py`**

Add to the top import block:

```python
from app.embeddings.qdrant_client import ensure_collection, get_client, search
```

Append to the end of the file:

```python
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
```

- [ ] **Step 4: Run the test again to verify it passes**

```bash
pytest tests/graph/test_nodes_differ.py -v
```

Expected: PASS — all 4 tests green.

- [ ] **Step 5: Run the full nodes test suite to confirm no regression**

```bash
pytest tests/graph/ -v
```

- [ ] **Step 6: Commit**

```bash
git add app/graph/nodes.py tests/graph/test_nodes_differ.py
git commit -m "Add Qdrant-similarity-based differ_node"
```

---

### Task 7: `app/graph/nodes.py` — DB-writing nodes and the audit-trail helper

**Files:**
- Modify: `app/graph/nodes.py`
- Create: `tests/graph/test_nodes_db.py`

**Interfaces:**
- Consumes: `app.db.database.SessionLocal`, `app.db.models.{Obligation,Task,EvidenceLog,AuditTrail}`
  (Task 1), `app.embeddings.qdrant_client.upsert_chunks` (existing), `resolve_due_date`/
  `compute_audit_hash` (Task 4).
- Produces: `mapper_node`, `evidence_node`, `gap_engine_node`, `human_review_node`,
  `finalize_node` — all consumed by `build_graph()` (Task 8). `mapper_node`'s returned
  `task` dict shape (`{"id", "obligation_id", "due_date"}`) is relied on by
  `evidence_node`/`gap_engine_node` (`task_info["id"]`).

These five nodes and the shared `_write_audit_entry` helper are grouped into one task
because they share the same DB-session pattern and the `task` dict contract — a
reviewer needs to see them together to judge whether that contract actually holds.

- [ ] **Step 1: Write the failing tests**

Create `tests/graph/test_nodes_db.py`:

```python
import json
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import AuditTrail, EvidenceLog, Obligation, Task
from app.graph.nodes import (
    evidence_node,
    finalize_node,
    gap_engine_node,
    human_review_node,
    mapper_node,
)


@pytest.fixture()
def db_session(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)
    monkeypatch.setattr("app.graph.nodes.SessionLocal", TestSessionLocal)
    session = TestSessionLocal()
    yield session
    session.close()


def test_mapper_node_creates_new_obligation_and_task(db_session):
    state = {
        "circular_id": "circular-1",
        "clause_id": "clause-1",
        "raw_clause": "1. Appoint a compliance officer.",
        "embedding": [0.1, 0.2],
        "diff_status": "new",
        "similarity_match": None,
        "extracted_obligation": {
            "requirement": "Appoint a compliance officer",
            "frequency": "one-time",
            "evidence_type": "board resolution",
            "deadline_rule": "2026-06-30",
        },
    }

    with patch("app.graph.nodes.get_client", return_value="fake-client"), \
         patch("app.graph.nodes.upsert_chunks") as mock_upsert:
        result = mapper_node(state)

    obligation = db_session.query(Obligation).one()
    assert obligation.requirement == "Appoint a compliance officer"
    task = db_session.query(Task).one()
    assert task.obligation_id == obligation.id
    assert task.due_date == datetime(2026, 6, 30)
    assert result["task"]["id"] == task.id
    assert result["task"]["obligation_id"] == obligation.id
    mock_upsert.assert_called_once()
    _, kwargs = mock_upsert.call_args
    assert kwargs["metadatas"][0]["obligation_id"] == obligation.id


def test_mapper_node_updates_existing_obligation_when_amended(db_session):
    db_session.add(Obligation(id="obl-1", clause_id="clause-0", requirement="Old text",
                               frequency="annual", evidence_type="policy",
                               deadline_rule="annual"))
    db_session.commit()

    state = {
        "circular_id": "circular-1",
        "clause_id": "clause-1",
        "raw_clause": "1. Do X quarterly.",
        "embedding": [0.1, 0.2],
        "diff_status": "amended",
        "similarity_match": {"payload": {"obligation_id": "obl-1"}},
        "extracted_obligation": {
            "requirement": "Do X",
            "frequency": "quarterly",
            "evidence_type": "policy doc",
            "deadline_rule": "quarterly",
        },
    }

    with patch("app.graph.nodes.get_client", return_value="fake-client"), \
         patch("app.graph.nodes.upsert_chunks"):
        mapper_node(state)

    assert db_session.query(Obligation).count() == 1
    obligation = db_session.query(Obligation).one()
    assert obligation.id == "obl-1"
    assert obligation.requirement == "Do X"


def test_mapper_node_skips_when_rejected(db_session):
    state = {"human_decision": "reject", "diff_status": "amended"}
    result = mapper_node(state)
    assert result == {}
    assert db_session.query(Obligation).count() == 0


def test_mapper_node_skips_when_unchanged(db_session):
    state = {"diff_status": "unchanged"}
    result = mapper_node(state)
    assert result == {}
    assert db_session.query(Task).count() == 0


def test_evidence_node_reports_present_when_evidence_exists(db_session):
    db_session.add(Obligation(id="obl-1", clause_id="c1", requirement="X",
                               frequency="annual", evidence_type="policy",
                               deadline_rule="annual"))
    db_session.add(Task(id="task-1", obligation_id="obl-1", owner="compliance"))
    db_session.add(EvidenceLog(id="ev-1", task_id="task-1", file_ref="doc.pdf"))
    db_session.commit()

    result = evidence_node({"task": {"id": "task-1"}})

    assert result == {"evidence_status": "present"}


def test_evidence_node_reports_missing_when_no_evidence(db_session):
    db_session.add(Obligation(id="obl-2", clause_id="c2", requirement="Y",
                               frequency="annual", evidence_type="policy",
                               deadline_rule="annual"))
    db_session.add(Task(id="task-2", obligation_id="obl-2", owner="compliance"))
    db_session.commit()

    result = evidence_node({"task": {"id": "task-2"}})

    assert result == {"evidence_status": "missing"}


def test_evidence_node_reports_missing_when_no_task_in_state():
    assert evidence_node({}) == {"evidence_status": "missing"}


def test_gap_engine_node_marks_overdue_task(db_session):
    db_session.add(Obligation(id="obl-3", clause_id="c3", requirement="Z",
                               frequency="annual", evidence_type="policy",
                               deadline_rule="annual"))
    db_session.add(Task(id="task-3", obligation_id="obl-3", owner="compliance",
                         due_date=datetime(2020, 1, 1), status="open"))
    db_session.commit()

    result = gap_engine_node({"task": {"id": "task-3"}})

    assert result["task"]["status"] == "overdue"
    task = db_session.query(Task).filter(Task.id == "task-3").one()
    assert task.status == "overdue"


def test_gap_engine_node_noop_without_task():
    assert gap_engine_node({}) == {}


def test_human_review_node_approve_writes_audit_entry(db_session):
    with patch("app.graph.nodes.interrupt", return_value={"decision": "approve", "actor": "alice"}):
        result = human_review_node({
            "circular_id": "circular-1",
            "clause_id": "clause-1",
            "extracted_obligation": {"requirement": "Do X"},
            "diff_status": "amended",
            "similarity_match": None,
        })

    assert result["human_decision"] == "approve"
    assert result["extracted_obligation"] == {"requirement": "Do X"}
    entry = db_session.query(AuditTrail).one()
    assert entry.actor == "alice"
    assert entry.node_name == "human_review"
    assert json.loads(entry.action) if isinstance(entry.action, str) else entry.action


def test_human_review_node_amend_merges_correction(db_session):
    with patch("app.graph.nodes.interrupt", return_value={
        "decision": 'amend:{"requirement": "Corrected text"}', "actor": "bob",
    }):
        result = human_review_node({
            "circular_id": "circular-1",
            "clause_id": "clause-1",
            "extracted_obligation": {"requirement": "Do X", "frequency": "annual"},
            "diff_status": "amended",
            "similarity_match": None,
        })

    assert result["human_decision"] == "amend"
    assert result["extracted_obligation"] == {
        "requirement": "Corrected text", "frequency": "annual",
    }


def test_finalize_node_writes_hash_chained_audit_entry(db_session):
    result_1 = finalize_node({
        "circular_id": "circular-1", "clause_id": "clause-1",
        "task": {"id": "task-1", "obligation_id": "obl-1"},
        "diff_status": "new", "human_decision": None,
    })
    result_2 = finalize_node({
        "circular_id": "circular-1", "clause_id": "clause-2",
        "task": {"id": "task-2", "obligation_id": "obl-2"},
        "diff_status": "new", "human_decision": None,
    })

    assert result_1 == {}
    assert result_2 == {}
    entries = db_session.query(AuditTrail).order_by(AuditTrail.timestamp).all()
    assert len(entries) == 2
    assert entries[0].prev_hash == ""
    assert entries[1].prev_hash == entries[0].hash
    assert entries[0].actor == "system"
```

- [ ] **Step 2: Run it to verify it fails**

```bash
mkdir -p tests/graph
pytest tests/graph/test_nodes_db.py -v
```

Expected: FAIL — `ImportError` (`mapper_node`, `evidence_node`, `gap_engine_node`,
`human_review_node`, `finalize_node` don't exist yet).

- [ ] **Step 3: Add imports and the five nodes to `app/graph/nodes.py`**

Add to the top import block:

```python
import uuid
from datetime import datetime as dt_datetime

from langgraph.types import interrupt

from app.db.database import SessionLocal
from app.db.models import AuditTrail, EvidenceLog, Obligation, Task
from app.embeddings.qdrant_client import upsert_chunks
```

Append to the end of the file:

```python
def mapper_node(state: ComplianceState) -> dict:
    if state.get("human_decision") == "reject" or state.get("diff_status") == "unchanged":
        return {}

    obligation_data = state["extracted_obligation"]
    db = SessionLocal()
    try:
        obligation = None
        if state.get("diff_status") == "amended" and state.get("similarity_match"):
            obligation_id = state["similarity_match"]["payload"].get("obligation_id")
            if obligation_id:
                obligation = (
                    db.query(Obligation).filter(Obligation.id == obligation_id).one_or_none()
                )

        if obligation is None:
            obligation = Obligation(id=str(uuid.uuid4()), clause_id=state["clause_id"])
            db.add(obligation)

        obligation.requirement = obligation_data["requirement"]
        obligation.frequency = obligation_data["frequency"]
        obligation.evidence_type = obligation_data["evidence_type"]
        obligation.deadline_rule = obligation_data["deadline_rule"]
        db.flush()

        due_date_value = resolve_due_date(obligation_data.get("deadline_rule"), date.today())
        task_due_date = (
            dt_datetime.combine(due_date_value, dt_datetime.min.time())
            if due_date_value else None
        )
        task = Task(
            id=str(uuid.uuid4()),
            obligation_id=obligation.id,
            owner="compliance",
            due_date=task_due_date,
        )
        db.add(task)
        db.commit()

        obligation_id, task_id = obligation.id, task.id
    finally:
        db.close()

    client = get_client()
    upsert_chunks(
        client,
        chunks=[state["raw_clause"]],
        vectors=[state["embedding"]],
        metadatas=[{
            "circular_id": state["circular_id"],
            "clause_id": state["clause_id"],
            "obligation_id": obligation_id,
        }],
    )

    return {
        "task": {
            "id": task_id,
            "obligation_id": obligation_id,
            "due_date": str(due_date_value) if due_date_value else None,
        }
    }


def evidence_node(state: ComplianceState) -> dict:
    task_info = state.get("task")
    if not task_info:
        return {"evidence_status": "missing"}

    db = SessionLocal()
    try:
        has_evidence = (
            db.query(EvidenceLog).filter(EvidenceLog.task_id == task_info["id"]).first()
            is not None
        )
    finally:
        db.close()

    return {"evidence_status": "present" if has_evidence else "missing"}


def gap_engine_node(state: ComplianceState) -> dict:
    task_info = state.get("task")
    if not task_info:
        return {}

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_info["id"]).one_or_none()
        if task is None:
            return {}
        deadline = task.due_date.date().isoformat() if task.due_date else None
        from app.services.gap_engine import compute_status
        task.status = compute_status(has_evidence=False, deadline=deadline, today=date.today())
        db.commit()
        new_status = task.status
    finally:
        db.close()

    return {"task": {**task_info, "status": new_status}}


def _write_audit_entry(thread_id: str, node_name: str, action: dict, actor: str) -> None:
    db = SessionLocal()
    try:
        last = db.query(AuditTrail).order_by(AuditTrail.timestamp.desc()).first()
        prev_hash = last.hash if last else ""
        timestamp = dt_datetime.utcnow()
        entry_hash = compute_audit_hash(prev_hash, action, timestamp)
        db.add(AuditTrail(
            id=str(uuid.uuid4()),
            thread_id=thread_id,
            node_name=node_name,
            action=action,
            actor=actor,
            timestamp=timestamp,
            prev_hash=prev_hash,
            hash=entry_hash,
        ))
        db.commit()
    finally:
        db.close()


def human_review_node(state: ComplianceState) -> dict:
    resume = interrupt({
        "clause_id": state["clause_id"],
        "extracted_obligation": state.get("extracted_obligation"),
        "diff_status": state.get("diff_status"),
        "similarity_match": state.get("similarity_match"),
    })
    decision = resume["decision"]
    actor = resume.get("actor", "unknown")

    extracted_obligation = state.get("extracted_obligation")
    human_decision = decision
    if decision.startswith("amend:"):
        amendment = json.loads(decision[len("amend:"):])
        extracted_obligation = {**(extracted_obligation or {}), **amendment}
        human_decision = "amend"

    _write_audit_entry(
        thread_id=f"{state['circular_id']}:{state['clause_id']}",
        node_name="human_review",
        action={"decision": human_decision},
        actor=actor,
    )

    return {
        "extracted_obligation": extracted_obligation,
        "human_decision": human_decision,
    }


def finalize_node(state: ComplianceState) -> dict:
    _write_audit_entry(
        thread_id=f"{state['circular_id']}:{state['clause_id']}",
        node_name="finalize",
        action={
            "obligation_id": (state.get("task") or {}).get("obligation_id"),
            "task_id": (state.get("task") or {}).get("id"),
            "diff_status": state.get("diff_status"),
            "human_decision": state.get("human_decision"),
        },
        actor="system",
    )
    return {}
```

- [ ] **Step 4: Run the test again to verify it passes**

```bash
pytest tests/graph/test_nodes_db.py -v
```

Expected: PASS — all 13 tests green.

- [ ] **Step 5: Run the full nodes test suite to confirm no regression**

```bash
pytest tests/graph/ -v
```

Expected: every test from Tasks 4, 5, 6, and this task passes together.

- [ ] **Step 6: Commit**

```bash
git add app/graph/nodes.py tests/graph/test_nodes_db.py
git commit -m "Add mapper/evidence/gap_engine/human_review/finalize nodes and audit-hash chaining"
```

---

### Task 8: Fix `app/graph/build_graph.py`

**Files:**
- Modify: `app/graph/build_graph.py`
- Create: `tests/graph/test_build_graph.py`

**Interfaces:**
- Consumes: all 9 node functions (Tasks 4–7).
- Produces: `build_graph(checkpointer=None)`, `route_after_diff`, `route_after_evidence`
  — consumed by Task 9 (`routes_review.py`) and Task 10 (`run_diff.py`).

- [ ] **Step 1: Write the failing tests**

Create `tests/graph/test_build_graph.py`:

```python
from langgraph.checkpoint.memory import MemorySaver

from app.graph.build_graph import build_graph, route_after_diff, route_after_evidence


def test_build_graph_compiles_with_injected_checkpointer():
    graph = build_graph(checkpointer=MemorySaver())
    node_names = set(graph.get_graph().nodes.keys())
    assert {
        "chunker", "embedder", "extractor", "differ", "human_review",
        "mapper", "evidence_check", "gap_engine", "finalize",
    } <= node_names


def test_route_after_diff_sends_amended_and_superseded_to_human_review():
    assert route_after_diff({"diff_status": "amended"}) == "human_review"
    assert route_after_diff({"diff_status": "superseded"}) == "human_review"


def test_route_after_diff_sends_unchanged_to_finalize():
    assert route_after_diff({"diff_status": "unchanged"}) == "finalize"


def test_route_after_diff_sends_new_to_mapper():
    assert route_after_diff({"diff_status": "new"}) == "mapper"


def test_route_after_evidence_routing():
    assert route_after_evidence({"evidence_status": "missing"}) == "gap_engine"
    assert route_after_evidence({"evidence_status": "invalid"}) == "human_review"
    assert route_after_evidence({"evidence_status": "present"}) == "finalize"
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pytest tests/graph/test_build_graph.py -v
```

Expected: FAIL — `test_build_graph_compiles_with_injected_checkpointer` fails because
`build_graph()` doesn't accept a `checkpointer` argument yet and internally calls
`PostgresSaver.from_conn_string(PG_CONN)` incorrectly; `test_route_after_diff_sends_unchanged_to_finalize`
fails because the current `route_after_diff` doesn't handle `"unchanged"`.

- [ ] **Step 3: Rewrite `app/graph/build_graph.py`**

```python
import os
from contextlib import ExitStack

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, StateGraph

from . import nodes
from .state import ComplianceState

_exit_stack = ExitStack()
_checkpointer = None


def _get_checkpointer():
    global _checkpointer
    if _checkpointer is None:
        conn_string = os.environ.get(
            "DATABASE_URL", "postgresql://regops:regops@localhost:5432/regops"
        )
        _checkpointer = _exit_stack.enter_context(
            PostgresSaver.from_conn_string(conn_string)
        )
        _checkpointer.setup()
    return _checkpointer


def route_after_diff(state: ComplianceState) -> str:
    if state["diff_status"] in ("amended", "superseded"):
        return "human_review"
    if state["diff_status"] == "unchanged":
        return "finalize"
    return "mapper"


def route_after_evidence(state: ComplianceState) -> str:
    if state["evidence_status"] == "missing":
        return "gap_engine"
    if state["evidence_status"] == "invalid":
        return "human_review"
    return "finalize"


def build_graph(checkpointer=None):
    g = StateGraph(ComplianceState)
    g.add_node("chunker", nodes.chunker_node)
    g.add_node("embedder", nodes.embedder_node)
    g.add_node("extractor", nodes.extractor_node)
    g.add_node("differ", nodes.differ_node)
    g.add_node("human_review", nodes.human_review_node)
    g.add_node("mapper", nodes.mapper_node)
    g.add_node("evidence_check", nodes.evidence_node)
    g.add_node("gap_engine", nodes.gap_engine_node)
    g.add_node("finalize", nodes.finalize_node)

    g.set_entry_point("chunker")
    g.add_edge("chunker", "embedder")
    g.add_edge("embedder", "extractor")
    g.add_edge("extractor", "differ")
    g.add_conditional_edges("differ", route_after_diff,
        {"human_review": "human_review", "mapper": "mapper", "finalize": "finalize"})
    g.add_edge("human_review", "mapper")
    g.add_edge("mapper", "evidence_check")
    g.add_conditional_edges("evidence_check", route_after_evidence,
        {"gap_engine": "gap_engine", "human_review": "human_review", "finalize": "finalize"})
    g.add_edge("gap_engine", "finalize")
    g.add_edge("finalize", END)

    return g.compile(checkpointer=checkpointer or _get_checkpointer())
```

- [ ] **Step 4: Run the test again to verify it passes**

```bash
pytest tests/graph/test_build_graph.py -v
```

Expected: PASS — all 6 tests green (compiling with `MemorySaver()` never touches
Postgres, since `checkpointer` is passed explicitly and `_get_checkpointer()` is never
called).

- [ ] **Step 5: Run the full nodes+graph test suite to confirm no regression**

```bash
pytest tests/graph/ -v
```

- [ ] **Step 6: Commit**

```bash
git add app/graph/build_graph.py tests/graph/test_build_graph.py
git commit -m "Fix build_graph checkpointer lifecycle and unchanged routing"
```

---

### Task 9: Fix `app/api/routes_review.py` and wire it into `app/api/main.py`

**Files:**
- Modify: `app/api/routes_review.py`
- Modify: `app/api/main.py`
- Create: `tests/api/test_routes_review.py`

**Interfaces:**
- Consumes: `app.graph.build_graph.build_graph` (Task 8).
- Produces: `router` (now with a real, working `/review/{thread_id}/decision` route),
  wired into the main FastAPI app.

- [ ] **Step 1: Write the failing tests**

Create `tests/api/test_routes_review.py`:

```python
import subprocess
import sys
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_importing_routes_review_module_does_not_build_the_graph():
    result = subprocess.run(
        [sys.executable, "-c", (
            "from unittest.mock import patch\n"
            "with patch('app.graph.build_graph.build_graph') as m:\n"
            "    import app.api.routes_review\n"
            "    assert not m.called, 'build_graph was called at import time'\n"
            "print('OK')"
        )],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


def test_submit_decision_builds_graph_lazily_and_resumes_with_command():
    import app.api.routes_review as routes_review_module

    routes_review_module._graph = None
    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {"diff_status": "amended"}

    try:
        with patch("app.api.routes_review.build_graph", return_value=fake_graph) as mock_build:
            app = FastAPI()
            app.include_router(routes_review_module.router)
            client = TestClient(app)

            response = client.post(
                "/review/circular-1:clause-1/decision",
                params={"decision": "approve", "actor": "alice"},
            )

        assert response.status_code == 200
        assert response.json() == {"status": "resumed", "state": {"diff_status": "amended"}}
        mock_build.assert_called_once()

        from langgraph.types import Command

        call_args = fake_graph.invoke.call_args
        command_arg = call_args.args[0]
        assert isinstance(command_arg, Command)
        assert command_arg.resume == {"decision": "approve", "actor": "alice"}
        assert call_args.kwargs["config"] == {
            "configurable": {"thread_id": "circular-1:clause-1"}
        }
    finally:
        routes_review_module._graph = None


def test_submit_decision_reuses_cached_graph_across_calls():
    import app.api.routes_review as routes_review_module

    routes_review_module._graph = None
    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {}

    try:
        with patch("app.api.routes_review.build_graph", return_value=fake_graph) as mock_build:
            app = FastAPI()
            app.include_router(routes_review_module.router)
            client = TestClient(app)

            client.post("/review/t1/decision", params={"decision": "approve"})
            client.post("/review/t1/decision", params={"decision": "reject"})

        mock_build.assert_called_once()
    finally:
        routes_review_module._graph = None
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pytest tests/api/test_routes_review.py -v
```

Expected: the import-safety test FAILS (current code builds the graph eagerly at
import); the other two fail with connection errors (real `build_graph()` tries to
reach Postgres).

- [ ] **Step 3: Fix `app/api/routes_review.py`**

```python
"""Human-review API routes: resume a paused compliance-pipeline run with a decision."""
from fastapi import APIRouter
from langgraph.types import Command

from app.graph.build_graph import build_graph

router = APIRouter()

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


@router.post("/review/{thread_id}/decision")
def submit_decision(thread_id: str, decision: str, actor: str = "reviewer"):
    graph = _get_graph()
    result = graph.invoke(
        Command(resume={"decision": decision, "actor": actor}),
        config={"configurable": {"thread_id": thread_id}},
    )
    return {"status": "resumed", "state": result}
```

- [ ] **Step 4: Wire the router into `app/api/main.py`**

Add this import near the existing `from app.services.gap_engine import get_gaps` line:

```python
from app.api.routes_review import router as review_router
```

Add this line immediately after `app = FastAPI(title="RegOps AI API")` and its
`add_middleware(...)` block:

```python
app.include_router(review_router)
```

- [ ] **Step 5: Run the test again to verify it passes**

```bash
pytest tests/api/test_routes_review.py -v
```

Expected: PASS — all 3 tests green.

- [ ] **Step 6: Run the existing main.py test suite to confirm no regression**

```bash
pytest tests/api/ -v
```

Expected: all `tests/api/test_main.py` tests still pass alongside the new
`test_routes_review.py` tests.

- [ ] **Step 7: Commit**

```bash
git add app/api/routes_review.py app/api/main.py tests/api/test_routes_review.py
git commit -m "Make routes_review import-safe and wire it into the API"
```

---

### Task 10: Fix `scripts/run_diff.py`

**Files:**
- Modify: `scripts/run_diff.py`
- Modify: `tests/scripts/test_run_diff.py`

**Interfaces:**
- Consumes: `app.graph.build_graph.build_graph` (Task 8).
- Produces: `run_diff(circular_id, clause_id, raw_clause, heading=None) -> dict`.

- [ ] **Step 1: Replace `tests/scripts/test_run_diff.py`**

```python
from unittest.mock import MagicMock, patch

from scripts.run_diff import run_diff


def test_run_diff_invokes_graph_with_real_state_shape_and_thread_id():
    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {"diff_status": "new"}

    with patch("scripts.run_diff.build_graph", return_value=fake_graph) as mock_build:
        result = run_diff("circular-1", "clause-1", "1. Appoint a compliance officer.")

    mock_build.assert_called_once()
    fake_graph.invoke.assert_called_once_with(
        {
            "circular_id": "circular-1",
            "clause_id": "clause-1",
            "raw_clause": "1. Appoint a compliance officer.",
            "heading": None,
        },
        config={"configurable": {"thread_id": "circular-1:clause-1"}},
    )
    assert result == {"diff_status": "new"}
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pytest tests/scripts/test_run_diff.py -v
```

Expected: FAIL — current `run_diff(clause_text)` takes one argument, this test calls it
with three.

- [ ] **Step 3: Rewrite `scripts/run_diff.py`**

```python
"""CLI: run the LangGraph extraction/diff pipeline over a single clause.
Usage: python -m scripts.run_diff <circular_id> <clause_id> '<raw clause text>'
"""
import sys

from app.graph.build_graph import build_graph


def run_diff(circular_id: str, clause_id: str, raw_clause: str, heading: str | None = None) -> dict:
    graph = build_graph()
    return graph.invoke(
        {
            "circular_id": circular_id,
            "clause_id": clause_id,
            "raw_clause": raw_clause,
            "heading": heading,
        },
        config={"configurable": {"thread_id": f"{circular_id}:{clause_id}"}},
    )


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python -m scripts.run_diff <circular_id> <clause_id> '<raw clause text>'")
        sys.exit(1)
    result = run_diff(sys.argv[1], sys.argv[2], sys.argv[3])
    print(result)
```

- [ ] **Step 4: Run the test again to verify it passes**

```bash
pytest tests/scripts/test_run_diff.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/run_diff.py tests/scripts/test_run_diff.py
git commit -m "Fix run_diff to match the real ComplianceState shape and thread_id"
```

---

### Task 11: Add `app/services/supersession.py`

**Files:**
- Create: `app/services/supersession.py`
- Create: `tests/services/test_supersession.py`

**Interfaces:**
- Consumes: `app.db.models.Obligation` (Task 1).
- Produces: `mark_superseded_obligations(db, circular_id, matched_obligation_ids) -> list[str]`
  — not consumed elsewhere in this plan (a driver script wiring the full
  ingest-a-circular-version-and-detect-drops workflow is out of scope, per the design
  spec).

- [ ] **Step 1: Write the failing tests**

Create `tests/services/test_supersession.py`:

```python
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
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pytest tests/services/test_supersession.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.supersession'`.

- [ ] **Step 3: Create `app/services/supersession.py`**

```python
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
```

- [ ] **Step 4: Run the test again to verify it passes**

```bash
pytest tests/services/test_supersession.py -v
```

Expected: PASS — both tests green.

- [ ] **Step 5: Commit**

```bash
git add app/services/supersession.py tests/services/test_supersession.py
git commit -m "Add batch-level obligation supersession detection"
```

---

### Task 12: Update `test_stubs.py`, pin the new dependency, and verify the whole suite

**Files:**
- Modify: `tests/test_stubs.py`
- Modify: `requirements.txt`
- Modify: `app/api/main.py`

**Interfaces:** None new — this task is final integration and cleanup.

- [ ] **Step 1: Replace `tests/test_stubs.py`**

```python
"""Import-safety checks for modules still awaiting user-provided implementation,
plus a sanity check that the now-real graph/model/route modules import cleanly."""
import pytest

from app.api.routes_review import router
from app.db.models import AuditTrail, EvidenceLog, Obligation, Task
from app.db.seed_synthetic import seed
from app.graph.build_graph import build_graph
from app.graph.state import ComplianceState
from app.ingestion.pdf_cleaner import clean_pdf
from scripts.generate_synthetic_data import generate


def test_remaining_stub_functions_raise_not_implemented_when_called():
    with pytest.raises(NotImplementedError):
        clean_pdf("whatever.pdf")
    with pytest.raises(NotImplementedError):
        seed()
    with pytest.raises(NotImplementedError):
        generate()


def test_real_graph_db_and_route_modules_import_cleanly():
    assert callable(build_graph)
    assert {"circular_id", "clause_id", "raw_clause", "diff_status"} <= set(
        ComplianceState.__annotations__
    )
    assert Obligation.__tablename__ == "obligations"
    assert Task.__tablename__ == "tasks"
    assert EvidenceLog.__tablename__ == "evidence_log"
    assert AuditTrail.__tablename__ == "audit_trail"
    assert router is not None
```

- [ ] **Step 2: Run it to verify it fails first (confirms it exercises real behavior)**

```bash
pytest tests/test_stubs.py -v
```

Expected: FAILS at this point only because `app/api/main.py` doesn't yet import
`app.db.models`/`app.graph.nodes` in a way that fully registers everything — actually
expected to PASS already since all imports are real by now from prior tasks; if it
fails, read the traceback carefully before changing anything (don't paper over a real
import error).

- [ ] **Step 3: Pin the new dependency in `requirements.txt`**

Add this line (keep alphabetical-ish grouping consistent with the existing file; add it
near the other `langgraph` line):

```
langgraph-checkpoint-postgres==3.1.0
```

- [ ] **Step 4: Ensure Postgres tables get created at API startup**

In `app/api/main.py`, add this import near the existing `from app.db.database import get_db`
line:

```python
from app.db.database import Base, engine
import app.db.models  # noqa: F401 — registers all tables on Base.metadata before create_all
```

Add this line immediately after those imports, before `app = FastAPI(...)`:

```python
Base.metadata.create_all(bind=engine)
```

- [ ] **Step 5: Run the full test suite**

```bash
source venv/bin/activate
pytest -v
```

Expected: every test across every task in this plan (and every test from the prior
restructure plan) passes. Note the total count in your report.

- [ ] **Step 6: Commit**

```bash
git add tests/test_stubs.py requirements.txt app/api/main.py
git commit -m "Update test_stubs for the real modules, pin langgraph-checkpoint-postgres, create tables at startup"
```

---

## After this plan

The compliance pipeline is now real end to end: ingest a clause → embed → extract via
Groq → diff against Qdrant → (optionally pause for human review) → map into
Obligation/Task rows → check evidence → flag gaps → write a hash-chained audit entry.
Still stubbed, by design, awaiting the user's own code: `app/ingestion/pdf_cleaner.py`,
`app/db/seed_synthetic.py`, `scripts/generate_synthetic_data.py`. A live end-to-end run
(`docker compose up -d`, then `python -m scripts.run_diff <circular_id> <clause_id>
'<clause text>'` against a real Postgres+Qdrant+Groq) remains a manual smoke test, same
as the Qdrant smoke test in the prior plan.

**Known remaining gap, explicitly out of scope for this plan:** `app/api/main.py`'s
`/upload` endpoint still invokes `build_graph()` with `{"file_path": ..., "filename":
...}`, which doesn't match `ComplianceState` — the same class of bug just fixed in
`scripts/run_diff.py`. It's harmless today (the endpoint's existing broad `except
Exception` → `501` catches whatever error results), but wiring `/upload` into the real
per-clause pipeline (PDF → `pdf_cleaner` → `clause_splitter` → loop over clauses →
`build_graph().invoke(...)` per clause → `mark_superseded_obligations`) is a genuine
product decision — does upload block until every clause finishes, or enqueue
background work? — not a small fix, and deserves its own design pass once
`pdf_cleaner.py` is no longer a stub.
