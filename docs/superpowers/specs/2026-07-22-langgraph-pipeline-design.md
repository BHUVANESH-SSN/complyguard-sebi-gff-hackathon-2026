# LangGraph compliance pipeline — design

## Goal

Make the LangGraph-based compliance-obligation pipeline (state schema, graph, DB models,
review API — pasted in by the user into the previously-stubbed files) actually work,
end to end, at a production-appropriate quality bar: fix the integration bugs the pasted
code introduced, implement the nine missing node functions, and align the rest of the
scaffold (gap engine, tests, dependencies) with the real schema.

## Context

Following the earlier `regops-ai` restructure (see
`docs/superpowers/specs/2026-07-22-regops-ai-restructure-design.md` and
`docs/superpowers/plans/2026-07-22-regops-ai-restructure.md`), the user pasted their own
code into four previously-empty stub files: `app/db/models.py`, `app/graph/state.py`,
`app/graph/build_graph.py`, `app/api/routes_review.py`. Running the existing test suite
against these pastes surfaced several real bugs (missing dependency, broken checkpointer
usage, stale references to the old placeholder class names). `app/graph/nodes.py` was
never pasted — it remains the original empty stub — and `build_graph()` requires nine
functions from it that don't exist yet.

## Scope

**In scope:**
- Fix the 6 integration bugs identified in the pasted files (checkpointer lifecycle,
  interrupt mechanism, eager graph construction, duplicate declarative Base, DB name
  mismatch, stale `run_diff.py` invoke shape).
- Extend `ComplianceState.diff_status` with an `"unchanged"` value.
- Implement all 9 node functions in `app/graph/nodes.py`.
- Rewrite `app/services/gap_engine.py` for the real `Obligation`/`Task`/`EvidenceLog`
  schema (evidence and due dates now live on `Task`, not directly on `Obligation`).
- Extend `app/embeddings/qdrant_client.py`'s `search()` to return the full payload
  (backward compatible — existing `text`/`score` keys unchanged, plus a new `payload` key).
- Add `mark_superseded_obligations(circular_id)` as a separate batch-level helper (not a
  graph node) for detecting obligations dropped from a newer circular version.
- Update `tests/test_stubs.py` (drop stale assertions about now-real modules) and
  `scripts/run_diff.py` (match the real `ComplianceState` field names).
- Add `langgraph-checkpoint-postgres==3.1.0` to `requirements.txt`.
- Unit tests for every new/changed piece of pure logic; integration points that need a
  live Postgres/Qdrant/Groq are exercised via mocks, matching the pattern already
  established in the earlier restructure (Tasks 7–13).

**Out of scope:**
- Building a UI for the human-review flow (routes_review.py's API is the extent of it).
- Multi-circular diffing orchestration beyond the single `mark_superseded_obligations`
  helper — no scheduling/automation of when to run it.
- Authentication/authorization on the new `/review/{thread_id}/decision` endpoint.
- Changing anything in `frontend/` — this is backend-only work.

## Bug fixes to the pasted files

1. **Checkpointer lifecycle.** `PostgresSaver.from_conn_string()` (verified against the
   installed `langgraph-checkpoint-postgres==3.1.0`) returns `Iterator[PostgresSaver]` —
   it's a context manager, not a plain constructor. `build_graph.py`'s
   `checkpointer = PostgresSaver.from_conn_string(PG_CONN)` is invalid. Fix: a
   module-level lazy singleton in `build_graph.py`, using `contextlib.ExitStack` entered
   once on first use (held for the process lifetime — acceptable for this app's
   single-process deployment model) and `.setup()` called once to create the checkpoint
   tables.
2. **Interrupt mechanism.** `Command(resume=decision)` (already used in
   `routes_review.py`) is LangGraph's mechanism for resuming a *dynamic* `interrupt()`
   call made *inside* a node — it does not pair with a static `interrupt_before=[...]`
   compile-time pause. `build_graph.py` currently sets both, which is inconsistent. Fix:
   remove `interrupt_before=["human_review"]` from `g.compile(...)`; `human_review_node`
   itself calls `langgraph.types.interrupt(payload)`, which is the mechanism
   `build_graph.py` already imports (`from langgraph.types import interrupt`) but never
   uses.
3. **Eager graph construction.** `routes_review.py` currently does
   `app_graph = build_graph()` at module level, executing graph/checkpointer
   construction as a side effect of importing the module — breaking the import-safety
   pattern the rest of the scaffold relies on. Fix: lazy singleton, built on first
   request via a module-level cache function (same pattern as `embedder.py`'s
   `_model_cache`).
4. **Duplicate declarative Base.** `app/db/models.py` defines its own
   `Base = declarative_base()`, separate from `app/db/database.py`'s `Base`. Fix:
   `models.py` imports `Base` from `app.db.database` instead of creating its own, so
   `Base.metadata.create_all()` sees all four tables.
5. **DB name mismatch.** `build_graph.py` hardcodes
   `postgresql://regops:regops@localhost:5432/regops_db` (note: `regops_db`, not
   `regops`) while `database.py`/`docker-compose.yml` use `regops`. Fix: read
   `DATABASE_URL` from the environment (via `os.environ.get`, same default pattern as
   `database.py`), removing the hardcoded, inconsistent connection string.
6. **Stale `run_diff.py` invoke shape.** `scripts/run_diff.py` currently calls
   `graph.invoke({"clause_text": clause_text})` — `clause_text` isn't a field of
   `ComplianceState` (the real fields are `circular_id`, `clause_id`, `raw_clause`,
   `heading`). Fix: update `run_diff(circular_id, clause_id, raw_clause, heading=None)`
   to build a state dict with the real field names, and to invoke the graph with
   `config={"configurable": {"thread_id": f"{circular_id}:{clause_id}"}}` — LangGraph's
   Postgres checkpointer keys a run's resumable state by `thread_id`, and this is the
   same `thread_id` `routes_review.py`'s `/review/{thread_id}/decision` endpoint must be
   given later to resume that exact clause's paused run.

## State schema change

`app/graph/state.py`'s `diff_status: Literal["new", "amended", "superseded", None]`
gains `"unchanged"`: the case where an ingested clause's embedding matches an existing
one in Qdrant with (near-)identical text — nothing changed, so no duplicate `Task`
should be created. `route_after_diff` sends `"unchanged"` straight to `"finalize"`
(bypassing `mapper`/`evidence_check` entirely, since there's nothing new to map or check
evidence for).

## Node design (`app/graph/nodes.py`)

All nodes are plain functions `(state: ComplianceState) -> dict`, returning only the
keys they update (LangGraph merges partial updates into state) — no node mutates
`state` in place.

- **`chunker_node`**: `raw_clause = state["raw_clause"].strip()`; `heading` derived from
  the first line of `raw_clause` (truncated) if not already set in the input state.
  Pure, no I/O.
- **`embedder_node`**: `embed_texts([state["raw_clause"]])[0]` → `embedding`. Calls the
  real Task 10 embedder (`BAAI/bge-base-en-v1.5`).
- **`extractor_node`**: Groq call (same client/retry pattern as the old, deleted
  `backend/extract.py`) with a JSON-extraction prompt tailored to the `Obligation`
  schema fields (`requirement`, `frequency`, `evidence_type`, `deadline_rule`) →
  `extracted_obligation` dict.
- **`differ_node`**: read-only. Calls `qdrant_client.search()` on `state["embedding"]`
  (threshold `SIMILARITY_THRESHOLD = 0.85`). No match above threshold → `"new"`.
  Match above threshold with near-identical text (case/whitespace-insensitive compare)
  → `"unchanged"`. Match above threshold with different text → `"amended"`, and
  `similarity_match` carries the full matched payload (via the `search()` extension
  below), including the prior `obligation_id` once that starts being stored (see
  `mapper_node`). Does not write to Qdrant — that's `mapper_node`'s job, once the real
  `obligation_id` is known.
- **`human_review_node`**: reached only for `"amended"`/`"superseded"`. Calls
  `interrupt({"clause_id": ..., "extracted_obligation": ..., "diff_status": ...,
  "similarity_match": ...})`, which pauses the graph. On resume, the value passed via
  `Command(resume={"decision": decision, "actor": actor})` becomes this call's return
  value — `routes_review.py`'s endpoint signature gains an `actor: str = "reviewer"`
  parameter (alongside the existing `decision: str`) specifically so this node can
  attribute the `AuditTrail` entry to who made the call, and resumes with that combined
  dict rather than the bare `decision` string. Parses `decision`: `"approve"` → no
  change to `extracted_obligation`; `"reject"` → sets `human_decision: "reject"` in
  state (checked by `mapper_node` to skip Task creation); `"amend:<json>"` → parses the
  JSON suffix and merges it into `extracted_obligation`. Writes one `AuditTrail` row
  recording the decision (`actor` from the resume payload, decision text, timestamp).
- **`mapper_node`**: skipped (returns state unchanged) if `human_decision == "reject"`
  or `diff_status == "unchanged"`. Otherwise: `"new"` → insert an `Obligation` row
  (`uuid4` id); `"amended"` → update the existing `Obligation` row found via
  `similarity_match["payload"]["obligation_id"]`. Creates a `Task` row (`uuid4` id,
  `due_date` resolved from `deadline_rule` — parsed as an ISO date if it looks like one,
  else mapped from a recognized frequency keyword (`"quarterly"`, `"annual"`,
  `"monthly"`) to the next occurrence from today, else `None` for open-ended). Then
  upserts this clause's embedding into Qdrant with `obligation_id` included in the
  payload, so future `differ_node` runs can resolve the match back to a concrete row.
- **`evidence_node`**: queries `EvidenceLog` for the `Task` created/updated by
  `mapper_node` → `evidence_status` (`"present"` if any row exists, else `"missing"`;
  `"invalid"` is reserved for a future validation rule and not set by this node yet —
  documented as a known gap, not silently implemented with fake logic).
- **`gap_engine_node`**: reached only when `evidence_status == "missing"`. Calls the
  rewritten `compute_status(has_evidence=False, due_date, today)` to set `Task.status`,
  and writes a gap note (no separate table — reuses `AuditTrail`).
- **`finalize_node`**: writes exactly one hash-chained `AuditTrail` row per graph run,
  with `actor="system"` (as opposed to `human_review_node`'s entries, which carry the
  real reviewer's `actor` from the resume payload): `prev_hash` = the `hash` of the most
  recent existing `AuditTrail` row (empty string if none exists yet),
  `hash = sha256(prev_hash + json.dumps(action, sort_keys=True) +
  timestamp.isoformat()).hexdigest()`. `action` summarizes the run's outcome
  (`obligation_id`, `task_id`, `diff_status`, `human_decision`).

## Gap engine rewrite (`app/services/gap_engine.py`)

`compute_status(has_evidence: bool, deadline: str | None, today: date) -> str` stays a
pure function with the same signature and behavior (already correct, already tested —
no change needed there). `update_all_statuses`/`get_gaps` are rewritten to query `Task`
(not the old `ObligationDB`) joined to `EvidenceLog` (`Task.due_date` instead of the old
flat `Obligation.deadline`; evidence existence checked via `EvidenceLog.task_id`).

## `qdrant_client.search()` extension

Additive, backward-compatible: each result dict gains a `"payload"` key with the full
raw Qdrant payload, alongside the existing `"text"`/`"score"` keys. Existing callers
(Task 13's `scripts/run_ingest.py`, existing tests) are unaffected since they only read
`"text"`/`"score"`.

## Superseded detection

`mark_superseded_obligations(circular_id: str) -> list[str]` (new function, not a graph
node): for a given newly-ingested circular, finds `Obligation` rows whose Qdrant-stored
clause embeddings have no match among the circular's newly-processed clauses, and marks
their `status` as `"superseded"`. Called by a driver script after all of a circular's
clauses have been run through the graph — not part of the per-clause graph itself, since
"no match anywhere in this document" is inherently a whole-document concern.

## Testing strategy

Following the pattern established in the earlier restructure: pure logic
(`compute_status`, the deadline-rule resolver, the hash-chaining function, `chunker_node`)
gets real unit tests with no mocking. Anything touching Groq, Qdrant, or Postgres gets
tested via mocks matching the already-established style (`embedder.py`'s `_model_cache`
injection, `qdrant_client.py`'s `MagicMock`-based tests). `build_graph()` itself is
tested by injecting an in-memory checkpointer (`langgraph.checkpoint.memory.MemorySaver`)
rather than requiring a live Postgres, confirming the graph compiles and its edges route
correctly — not a full live end-to-end run (that remains a manual/documented smoke-test
step, same as the earlier Qdrant smoke test).

`tests/test_stubs.py` is updated: the assertions about `ObligationDB`/`EvidenceDB`/
`AuditLogDB` raising `NotImplementedError` on instantiation, and `build_graph()` raising
`NotImplementedError` on call, are removed (those modules are real now, not stubs).
Real import-sanity checks replace them where still meaningful (e.g., `app.graph.nodes`
still has no functions of its own to test here since all its logic is covered by the
dedicated node tests).

## Dependencies

Add `langgraph-checkpoint-postgres==3.1.0` to `requirements.txt` (pinned, following the
same reasoning as the earlier `qdrant-client` pin — this package's API is exactly the
kind of thing that breaks across versions, and we've now verified 3.1.0's actual
contract by hand).
