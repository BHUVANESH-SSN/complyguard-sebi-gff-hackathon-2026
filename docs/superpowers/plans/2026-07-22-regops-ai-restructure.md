# RegOps AI Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the ComplyGuard hackathon prototype onto a LangGraph + PostgreSQL + Qdrant layout, rebrand it to RegOps AI, and leave a stable, importable scaffold ready for the user to paste in their own LangGraph/DB-model/review-route/synthetic-data code.

**Architecture:** Move the existing React frontend into `frontend/`, delete the old FastAPI/SQLite/Chroma backend, and scaffold a new `app/` Python package (`ingestion`, `embeddings`, `graph`, `db`, `services`, `api`) plus `scripts/`. Files the user already has code for become import-safe placeholder stubs (`NotImplementedError` on call, never on import); everything else gets a real, working, unit-tested implementation ported from the old backend's logic. Repo root is renamed to `regops-ai/` as the final step.

**Tech Stack:** FastAPI, SQLAlchemy + psycopg2 (Postgres), qdrant-client, sentence-transformers (`BAAI/bge-base-en-v1.5`), Groq (`llama-3.3-70b-versatile`), langgraph/langchain-core, pytest, Docker Compose, React 19 + Vite (frontend, unchanged apart from rebrand).

## Global Constraints

- Repo root directory is renamed from `complyguard-prototype/` to `regops-ai/` — local disk rename only, does not touch git history or any GitHub remote name. Done as the **last** task so no mid-plan task depends on the new path.
- Display name in UI/README copy: **"RegOps AI"**. Technical identifiers use lowercase-hyphenated `regops-ai` (package.json name, docker-compose project name) or `regops` (Postgres DB name/user/password).
- LLM: Groq `llama-3.3-70b-versatile`, read from `GROQ_API_KEY` / `GROQ_MODEL` env vars.
- Embeddings: `BAAI/bge-base-en-v1.5` via `sentence-transformers`, local, no API key.
- Stub contract: every placeholder file must import cleanly with zero side effects. Only calling its function(s) or instantiating its class(es) raises `NotImplementedError` with a message naming the real thing to paste in.
- No fabricated synthetic data or real SEBI PDFs — `data/raw_pdfs/` and `data/synthetic/` stay empty (`.gitkeep` only); the user populates them once their generator/PDFs are in place.
- Test runner is pytest (`pytest.ini` sets `pythonpath = .` so `app.*` / `scripts.*` imports resolve without installing the package).
- Design reference: `docs/superpowers/specs/2026-07-22-regops-ai-restructure-design.md`.

---

### Task 1: Move the frontend into `frontend/`

**Files:**
- Move: `src/` → `frontend/src/`
- Move: `public/` → `frontend/public/`
- Move: `index.html` → `frontend/index.html`
- Move: `package.json` → `frontend/package.json`
- Move: `package-lock.json` → `frontend/package-lock.json`
- Move: `vite.config.js` → `frontend/vite.config.js`
- Move: `.oxlintrc.json` → `frontend/.oxlintrc.json`
- Move (untracked, plain `mv`): `node_modules/` → `frontend/node_modules/`, `dist/` → `frontend/dist/`
- Modify: `frontend/vite.config.js`

**Interfaces:** None — pure relocation, no code behavior changes.

- [ ] **Step 1: Create the frontend directory and git-mv tracked files**

```bash
cd /home/bhuvi/Downloads/sebi-hackathon/complyguard-prototype
mkdir -p frontend
git mv src frontend/src
git mv public frontend/public
git mv index.html frontend/index.html
git mv package.json frontend/package.json
git mv package-lock.json frontend/package-lock.json
git mv vite.config.js frontend/vite.config.js
git mv .oxlintrc.json frontend/.oxlintrc.json
```

- [ ] **Step 2: Move the untracked directories alongside**

```bash
mv node_modules frontend/node_modules
mv dist frontend/dist 2>/dev/null || true
```

- [ ] **Step 3: Drop the now-pointless backend watch-ignore from vite.config.js**

Edit `frontend/vite.config.js` to:

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

- [ ] **Step 4: Verify the moved frontend still builds**

```bash
cd frontend && npm run build
```

Expected: build completes successfully, `frontend/dist/` is (re)populated, no path-resolution errors.

- [ ] **Step 5: Commit**

```bash
cd /home/bhuvi/Downloads/sebi-hackathon/complyguard-prototype
git add -A frontend vite.config.js src public index.html package.json package-lock.json .oxlintrc.json
git commit -m "Move frontend into frontend/ subdirectory"
```

---

### Task 2: Rebrand the frontend from ComplyGuard to RegOps AI

**Files:**
- Modify: `frontend/package.json:2`
- Modify: `frontend/index.html:7`
- Modify: `frontend/src/components/layout/Nav.jsx:22,26`
- Modify: `frontend/src/components/views/Hero.jsx:30`
- Modify: `frontend/src/App.jsx:107`

**Interfaces:** None — text-only changes, no prop/function signatures touched.

- [ ] **Step 1: Rename the package**

In `frontend/package.json`, change:

```json
  "name": "complyguard-prototype",
```

to:

```json
  "name": "regops-ai",
```

- [ ] **Step 2: Rebrand the page title**

In `frontend/index.html`, change:

```html
    <title>ComplyGuard — SEBI Agentic Compliance</title>
```

to:

```html
    <title>RegOps AI — SEBI Agentic Compliance</title>
```

- [ ] **Step 3: Rebrand the nav bar**

In `frontend/src/components/layout/Nav.jsx`, change line 22 from:

```jsx
              ComplyGuard
```

to:

```jsx
              RegOps AI
```

and change line 26 from:

```jsx
            <span>SEBI x ComplyGuard</span>
```

to:

```jsx
            <span>SEBI x RegOps AI</span>
```

- [ ] **Step 4: Rebrand the hero copy**

In `frontend/src/components/views/Hero.jsx`, change line 30 from:

```jsx
            Upload a SEBI circular. ComplyGuard reads it, extracts every
```

to:

```jsx
            Upload a SEBI circular. RegOps AI reads it, extracts every
```

- [ ] **Step 5: Rebrand the footer text in App.jsx**

In `frontend/src/App.jsx`, change line 107 from:

```jsx
        ComplyGuard — Connects to Python FastAPI Backend.
```

to:

```jsx
        RegOps AI — Connects to Python FastAPI Backend.
```

- [ ] **Step 6: Regenerate the lockfile and verify the build**

```bash
cd frontend
npm install
npm run build
```

Expected: `npm install` completes with only `package-lock.json`'s `name` field changing; build succeeds.

- [ ] **Step 7: Grep-verify no ComplyGuard references remain in frontend source**

```bash
grep -rn "ComplyGuard" frontend/src frontend/index.html frontend/package.json
```

Expected: no output.

- [ ] **Step 8: Commit**

```bash
cd /home/bhuvi/Downloads/sebi-hackathon/complyguard-prototype
git add frontend/package.json frontend/package-lock.json frontend/index.html \
  frontend/src/components/layout/Nav.jsx frontend/src/components/views/Hero.jsx frontend/src/App.jsx
git commit -m "Rebrand frontend from ComplyGuard to RegOps AI"
```

---

### Task 3: Update `.gitignore` for the new Python layout

**Files:**
- Modify: `.gitignore`

**Interfaces:** None.

- [ ] **Step 1: Append Python-specific ignore rules**

Append to `.gitignore`:

```

# Python
__pycache__/
*.pyc
venv/

# Generated data
data/processed/
```

- [ ] **Step 2: Verify**

```bash
cat .gitignore | tail -8
```

Expected: shows the new block exactly as above.

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "Add Python and generated-data entries to .gitignore"
```

---

### Task 4: Delete the old backend

**Files:**
- Delete: `backend/` (entire tracked tree: `main.py`, `database.py`, `models.py`, `ingest.py`, `extract.py`, `gaps.py`, `requirements.txt`, `data/circulars/*.pdf`, `chroma_db/*`, `complyguard.db`, `__pycache__/*.pyc`)
- Delete (untracked): `backend/venv/`, `backend/.env`

**Interfaces:** None — full removal, nothing downstream references `backend/` after Task 1's vite.config.js cleanup.

- [ ] **Step 1: Remove the tracked backend tree**

```bash
git rm -r backend
```

Expected: git reports removal of all 23 tracked files under `backend/` (including the incidentally-committed `__pycache__`, `chroma_db`, and `complyguard.db`).

- [ ] **Step 2: Remove any leftover untracked backend files**

```bash
rm -rf backend
```

Expected: `backend/` no longer exists on disk at all (catches `venv/` and `.env`, which git never tracked).

- [ ] **Step 3: Verify**

```bash
git status --short
ls backend 2>&1
```

Expected: `git status` shows only the staged deletions from Step 1; `ls backend` reports "No such file or directory".

- [ ] **Step 4: Commit**

```bash
git commit -m "Remove old FastAPI/SQLite/Chroma backend"
```

---

### Task 5: Add new backend infra files

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `docker-compose.yml`
- Create: `pytest.ini`

**Interfaces:** None yet — these are configuration, no Python modules depend on them for import.

- [ ] **Step 1: Create `requirements.txt`**

```
fastapi
uvicorn
python-multipart
pydantic
sqlalchemy
psycopg2-binary
pypdf
sentence-transformers
qdrant-client
groq
python-dotenv
langgraph
langchain-core
pytest>=7.0
httpx
```

- [ ] **Step 2: Create `.env.example`**

```
DATABASE_URL=postgresql://regops:regops@localhost:5432/regops
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama-3.3-70b-versatile
QDRANT_URL=http://localhost:6333
```

- [ ] **Step 3: Create `docker-compose.yml`**

```yaml
name: regops-ai

services:
  postgres:
    image: postgres:16
    container_name: regops-ai-postgres
    environment:
      POSTGRES_USER: regops
      POSTGRES_PASSWORD: regops
      POSTGRES_DB: regops
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U regops -d regops"]
      interval: 5s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    container_name: regops-ai-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  qdrant_data:
```

- [ ] **Step 4: Create `pytest.ini`**

```ini
[pytest]
pythonpath = .
```

- [ ] **Step 5: Validate the compose file**

```bash
docker compose config
```

Expected: prints the fully-resolved compose config with no errors (works even without the Docker daemon running — it only parses the file). If the `docker` CLI isn't installed in this environment, note that and skip to Step 6.

- [ ] **Step 6: Create and populate the root virtualenv**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Expected: all packages install without error (`sentence-transformers` pulls in `torch`, so this step can take a few minutes).

- [ ] **Step 7: Commit**

```bash
git add requirements.txt .env.example docker-compose.yml pytest.ini
git commit -m "Add Postgres/Qdrant docker-compose, requirements, and pytest config"
```

---

### Task 6: Scaffold the `app/` package and stub files

**Files:**
- Create: `app/__init__.py`, `app/ingestion/__init__.py`, `app/embeddings/__init__.py`, `app/graph/__init__.py`, `app/db/__init__.py`, `app/services/__init__.py`, `app/api/__init__.py`
- Create: `app/ingestion/pdf_cleaner.py` (STUB)
- Create: `app/graph/state.py` (STUB)
- Create: `app/graph/build_graph.py` (STUB)
- Create: `app/db/models.py` (STUB)
- Create: `app/db/seed_synthetic.py` (STUB)
- Create: `app/api/routes_review.py` (STUB)
- Create: `scripts/__init__.py`
- Create: `scripts/generate_synthetic_data.py` (STUB)
- Create: `data/raw_pdfs/.gitkeep`, `data/synthetic/.gitkeep`, `data/processed/clauses/.gitkeep`
- Create: `tests/__init__.py`, `tests/test_stubs.py`

**Interfaces:**
- Produces: `ObligationDB`, `EvidenceDB`, `AuditLogDB` (classes in `app.db.models`, raise `NotImplementedError` on instantiation)
- Produces: `GraphState` (class in `app.graph.state`, plain placeholder)
- Produces: `build_graph() -> None` (function in `app.graph.build_graph`, raises `NotImplementedError` on call)
- Produces: `clean_pdf(pdf_path: str) -> str` (function in `app.ingestion.pdf_cleaner`, raises `NotImplementedError` on call)
- Produces: `seed() -> None` (function in `app.db.seed_synthetic`, raises `NotImplementedError` on call)
- Produces: `generate() -> None` (function in `scripts.generate_synthetic_data`, raises `NotImplementedError` on call)
- Produces: `router` (`fastapi.APIRouter` instance in `app.api.routes_review`, empty, no routes yet)

- [ ] **Step 1: Write the failing test**

Create `tests/test_stubs.py`:

```python
import pytest

from app.ingestion.pdf_cleaner import clean_pdf
from app.graph.build_graph import build_graph
from app.graph.state import GraphState
from app.db.models import ObligationDB, EvidenceDB, AuditLogDB
from app.db.seed_synthetic import seed
from app.api.routes_review import router
from scripts.generate_synthetic_data import generate


def test_stub_functions_raise_not_implemented_when_called():
    with pytest.raises(NotImplementedError):
        clean_pdf("whatever.pdf")
    with pytest.raises(NotImplementedError):
        build_graph()
    with pytest.raises(NotImplementedError):
        seed()
    with pytest.raises(NotImplementedError):
        generate()


def test_stub_model_classes_raise_not_implemented_when_instantiated():
    with pytest.raises(NotImplementedError):
        ObligationDB()
    with pytest.raises(NotImplementedError):
        EvidenceDB()
    with pytest.raises(NotImplementedError):
        AuditLogDB()


def test_stub_state_and_router_are_importable_placeholders():
    assert issubclass(GraphState, dict)
    assert router is not None
```

- [ ] **Step 2: Run it to verify it fails on import**

```bash
source venv/bin/activate
pytest tests/test_stubs.py -v
```

Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'app'` (none of the modules exist yet).

- [ ] **Step 3: Create the package `__init__.py` files**

```bash
mkdir -p app/ingestion app/embeddings app/graph app/db app/services app/api scripts \
  data/raw_pdfs data/synthetic data/processed/clauses tests
touch app/__init__.py app/ingestion/__init__.py app/embeddings/__init__.py \
  app/graph/__init__.py app/db/__init__.py app/services/__init__.py app/api/__init__.py \
  scripts/__init__.py tests/__init__.py \
  data/raw_pdfs/.gitkeep data/synthetic/.gitkeep data/processed/clauses/.gitkeep
```

- [ ] **Step 4: Write the stub modules**

Create `app/ingestion/pdf_cleaner.py`:

```python
"""Placeholder for PDF text cleaning (strips headers/footers/page numbers).

Real implementation is pasted in separately. Once ready, running
`python -m app.ingestion.pdf_cleaner <pdf_path>` should print a spot-check
of cleaned paragraphs.
"""


def clean_pdf(pdf_path: str) -> str:
    raise NotImplementedError(
        "app.ingestion.pdf_cleaner.clean_pdf is a placeholder — paste the "
        "real PDF cleaning implementation here."
    )
```

Create `app/graph/state.py`:

```python
"""Placeholder for the LangGraph pipeline's shared state schema.

Real implementation (a TypedDict or Pydantic model describing graph
state) is pasted in separately.
"""


class GraphState(dict):
    """Placeholder state type — replace with the real schema."""
```

Create `app/graph/build_graph.py`:

```python
"""Placeholder for the LangGraph pipeline (extraction, diffing, human-review interrupts).

Real implementation is pasted in separately.
"""


def build_graph():
    raise NotImplementedError(
        "app.graph.build_graph.build_graph is a placeholder — paste the "
        "real LangGraph graph-construction code here."
    )
```

Create `app/db/models.py`:

```python
"""Placeholder ORM + schema definitions.

Real content (Obligation, Evidence, AuditLog, Task, Grievance, OrgRole
models — SQLAlchemy tables + Pydantic schemas) is pasted in separately.
Importing this module must never fail; using these placeholder classes
for real queries raises NotImplementedError.
"""


class _Unbuilt:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            f"{type(self).__name__} is a placeholder — paste the real "
            "SQLAlchemy/Pydantic model here."
        )


class ObligationDB(_Unbuilt):
    pass


class EvidenceDB(_Unbuilt):
    pass


class AuditLogDB(_Unbuilt):
    pass
```

Create `app/db/seed_synthetic.py`:

```python
"""Placeholder for seeding Postgres with synthetic compliance data
(6 obligations, 143 tasks, 129 evidence rows, 25 grievances, org roles).

Real implementation is pasted in separately. Once ready, run:
    python -m app.db.seed_synthetic
"""


def seed() -> None:
    raise NotImplementedError(
        "app.db.seed_synthetic.seed is a placeholder — paste the real "
        "synthetic-data seeding implementation here."
    )


if __name__ == "__main__":
    seed()
```

Create `app/api/routes_review.py`:

```python
"""Placeholder for human-review API routes (approve/reject extracted obligations).

Real implementation is pasted in separately. Once ready, wire its router
into app.api.main with `app.include_router(router)`.
"""
from fastapi import APIRouter

router = APIRouter()
```

Create `scripts/generate_synthetic_data.py`:

```python
"""Placeholder for generating synthetic compliance data fixtures
(data/synthetic/obligations_seed.json, tasks.csv, evidence_log.csv,
grievance_records.csv, org_roles.json).

Real implementation is pasted in separately. Once ready, run:
    python -m scripts.generate_synthetic_data
"""


def generate() -> None:
    raise NotImplementedError(
        "scripts.generate_synthetic_data.generate is a placeholder — "
        "paste the real synthetic-data generator here."
    )


if __name__ == "__main__":
    generate()
```

- [ ] **Step 5: Run the test again to verify it passes**

```bash
pytest tests/test_stubs.py -v
```

Expected: PASS — all 3 tests green.

- [ ] **Step 6: Commit**

```bash
git add app scripts/__init__.py scripts/generate_synthetic_data.py tests/__init__.py tests/test_stubs.py \
  data/raw_pdfs/.gitkeep data/synthetic/.gitkeep data/processed/clauses/.gitkeep
git commit -m "Scaffold app/ package with import-safe placeholder stubs"
```

---

### Task 7: Build `app/db/database.py` (Postgres engine/session)

**Files:**
- Create: `app/db/database.py`
- Test: `tests/db/test_database.py`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `make_engine(database_url: str | None = None) -> sqlalchemy.Engine`, `Base` (declarative base), `SessionLocal` (sessionmaker), `get_db()` (generator yielding a `Session`) — all imported by Task 12 (`app/api/main.py`).

- [ ] **Step 1: Write the failing test**

Create `tests/db/__init__.py` (empty) and `tests/db/test_database.py`:

```python
import os

from app.db.database import make_engine


def test_make_engine_uses_provided_url():
    engine = make_engine("sqlite:///:memory:")
    assert str(engine.url) == "sqlite:///:memory:"


def test_make_engine_defaults_to_env_var(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test_default.db")
    engine = make_engine()
    assert "test_default.db" in str(engine.url)
```

- [ ] **Step 2: Run it to verify it fails**

```bash
mkdir -p tests/db && touch tests/db/__init__.py
pytest tests/db/test_database.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.db.database'`.

- [ ] **Step 3: Implement `app/db/database.py`**

```python
"""SQLAlchemy engine/session factory for the RegOps AI Postgres database."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

DEFAULT_DATABASE_URL = "postgresql://regops:regops@localhost:5432/regops"


def make_engine(database_url: str | None = None):
    url = database_url or os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    return create_engine(url)


engine = make_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: Run the test again to verify it passes**

```bash
pytest tests/db/test_database.py -v
```

Expected: PASS — both tests green. (Note: this only constructs the `Engine` object, it never connects, so no Postgres instance needs to be running.)

- [ ] **Step 5: Commit**

```bash
git add app/db/database.py tests/db
git commit -m "Add Postgres engine/session factory"
```

---

### Task 8: Build `app/ingestion/clause_splitter.py`

**Files:**
- Create: `app/ingestion/clause_splitter.py`
- Test: `tests/ingestion/test_clause_splitter.py`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `split_into_clauses(text: str) -> list[str]`, consumed by Task 13 (`scripts/run_ingest.py`).

- [ ] **Step 1: Write the failing test**

Create `tests/ingestion/__init__.py` (empty) and `tests/ingestion/test_clause_splitter.py`:

```python
from app.ingestion.clause_splitter import split_into_clauses


def test_splits_top_level_numbered_clauses():
    text = "1. Appoint a compliance officer.\n\n2. File a cyber security policy."
    assert split_into_clauses(text) == [
        "1. Appoint a compliance officer.",
        "2. File a cyber security policy.",
    ]


def test_keeps_sub_clauses_separate_when_separately_numbered():
    text = "1. Do X.\n1.1 Sub-requirement A.\n1.2 Sub-requirement B.\n2. Do Y."
    assert split_into_clauses(text) == [
        "1. Do X.",
        "1.1 Sub-requirement A.",
        "1.2 Sub-requirement B.",
        "2. Do Y.",
    ]


def test_falls_back_to_paragraph_split_when_no_numbering():
    text = "Intro paragraph with no numbers.\n\nSecond paragraph, still no numbers."
    assert split_into_clauses(text) == [
        "Intro paragraph with no numbers.",
        "Second paragraph, still no numbers.",
    ]


def test_empty_text_returns_empty_list():
    assert split_into_clauses("") == []
    assert split_into_clauses("   \n\n  ") == []
```

- [ ] **Step 2: Run it to verify it fails**

```bash
mkdir -p tests/ingestion && touch tests/ingestion/__init__.py
pytest tests/ingestion/test_clause_splitter.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.ingestion.clause_splitter'`.

- [ ] **Step 3: Implement `app/ingestion/clause_splitter.py`**

```python
"""Split cleaned circular text into individual numbered-clause chunks."""
import re

CLAUSE_PATTERN = re.compile(r"(?m)^(?=\d+(?:\.\d+)*\.?\s+\S)")


def split_into_clauses(text: str) -> list[str]:
    if not text or not text.strip():
        return []

    pieces = CLAUSE_PATTERN.split(text)
    clauses = [p.strip() for p in pieces if p.strip()]

    if len(clauses) <= 1:
        clauses = [p.strip() for p in text.split("\n\n") if p.strip()]

    return clauses
```

- [ ] **Step 4: Run the test again to verify it passes**

```bash
pytest tests/ingestion/test_clause_splitter.py -v
```

Expected: PASS — all 4 tests green.

- [ ] **Step 5: Commit**

```bash
git add app/ingestion/clause_splitter.py tests/ingestion
git commit -m "Add clause splitter for numbered circular clauses"
```

---

### Task 9: Build `app/services/gap_engine.py`

**Files:**
- Create: `app/services/gap_engine.py`
- Test: `tests/services/test_gap_engine.py`

**Interfaces:**
- Consumes: `app.db.models.ObligationDB`, `app.db.models.EvidenceDB` (currently stubs — only imported lazily inside `update_all_statuses`/`get_gaps`, not at module top, so this module always imports cleanly).
- Produces: `compute_status(has_evidence: bool, deadline: str | None, today: date) -> str`, `update_all_statuses(db) -> None`, `get_gaps(db) -> list` — consumed by Task 12 (`app/api/main.py`).

- [ ] **Step 1: Write the failing test**

Create `tests/services/__init__.py` (empty) and `tests/services/test_gap_engine.py`:

```python
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
```

- [ ] **Step 2: Run it to verify it fails**

```bash
mkdir -p tests/services && touch tests/services/__init__.py
pytest tests/services/test_gap_engine.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.gap_engine'`.

- [ ] **Step 3: Implement `app/services/gap_engine.py`**

```python
"""Obligation status computation: pure logic plus a thin DB-facing wrapper."""
from datetime import date


def compute_status(has_evidence: bool, deadline: str | None, today: date) -> str:
    if has_evidence:
        return "met"
    if deadline and date.fromisoformat(deadline) < today:
        return "overdue"
    return "pending"


def update_all_statuses(db) -> None:
    """Recompute status for every obligation.

    Requires app.db.models to provide real ObligationDB (.id, .deadline,
    .status) and EvidenceDB (.obligation_id) classes — currently stubs.
    """
    from app.db.models import EvidenceDB, ObligationDB

    today = date.today()
    for obligation in db.query(ObligationDB).all():
        if obligation.status == "met":
            continue
        has_evidence = (
            db.query(EvidenceDB)
            .filter(EvidenceDB.obligation_id == obligation.id)
            .first()
            is not None
        )
        obligation.status = compute_status(has_evidence, obligation.deadline, today)
    db.commit()


def get_gaps(db) -> list:
    from app.db.models import ObligationDB

    update_all_statuses(db)
    return (
        db.query(ObligationDB)
        .filter(ObligationDB.status.in_(["pending", "overdue"]))
        .all()
    )
```

- [ ] **Step 4: Run the test again to verify it passes**

```bash
pytest tests/services/test_gap_engine.py -v
```

Expected: PASS — all 5 tests green.

- [ ] **Step 5: Commit**

```bash
git add app/services/gap_engine.py tests/services
git commit -m "Add gap engine with pure status computation"
```

---

### Task 10: Build `app/embeddings/embedder.py`

**Files:**
- Create: `app/embeddings/embedder.py`
- Test: `tests/embeddings/test_embedder.py`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `embed_texts(texts: list[str], model_name: str = "BAAI/bge-base-en-v1.5") -> list[list[float]]`, `get_model(model_name: str) -> SentenceTransformer`, `DEFAULT_MODEL_NAME` — consumed by Task 13 (`scripts/run_ingest.py`).

- [ ] **Step 1: Write the failing test**

Create `tests/embeddings/__init__.py` (empty) and `tests/embeddings/test_embedder.py`:

```python
import numpy as np
import pytest
from unittest.mock import MagicMock

from app.embeddings.embedder import _model_cache, embed_texts


@pytest.fixture(autouse=True)
def clear_model_cache():
    yield
    _model_cache.clear()


def test_embed_texts_returns_empty_list_for_no_input():
    assert embed_texts([]) == []


def test_embed_texts_uses_model_encode_and_returns_lists():
    fake_model = MagicMock()
    fake_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
    _model_cache["fake-model"] = fake_model

    result = embed_texts(["a", "b"], model_name="fake-model")

    fake_model.encode.assert_called_once_with(["a", "b"])
    assert result == [[0.1, 0.2], [0.3, 0.4]]
```

- [ ] **Step 2: Run it to verify it fails**

```bash
mkdir -p tests/embeddings && touch tests/embeddings/__init__.py
pytest tests/embeddings/test_embedder.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.embeddings.embedder'`.

- [ ] **Step 3: Implement `app/embeddings/embedder.py`**

```python
"""Wraps a local sentence-transformers model for embedding text into vectors."""
from sentence_transformers import SentenceTransformer

DEFAULT_MODEL_NAME = "BAAI/bge-base-en-v1.5"

_model_cache: dict[str, SentenceTransformer] = {}


def get_model(model_name: str = DEFAULT_MODEL_NAME) -> SentenceTransformer:
    if model_name not in _model_cache:
        _model_cache[model_name] = SentenceTransformer(model_name)
    return _model_cache[model_name]


def embed_texts(
    texts: list[str], model_name: str = DEFAULT_MODEL_NAME
) -> list[list[float]]:
    if not texts:
        return []
    model = get_model(model_name)
    return model.encode(texts).tolist()
```

- [ ] **Step 4: Run the test again to verify it passes**

```bash
pytest tests/embeddings/test_embedder.py -v
```

Expected: PASS — both tests green, no real model download triggered (the fake model is injected directly into `_model_cache`).

- [ ] **Step 5: Commit**

```bash
git add app/embeddings/embedder.py tests/embeddings/__init__.py tests/embeddings/test_embedder.py
git commit -m "Add local sentence-transformers embedder"
```

---

### Task 11: Build `app/embeddings/qdrant_client.py`

**Files:**
- Create: `app/embeddings/qdrant_client.py`
- Test: `tests/embeddings/test_qdrant_client.py`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `get_client(url: str | None = None)`, `ensure_collection(client, collection_name=DEFAULT_COLLECTION, vector_size=768)`, `upsert_chunks(client, chunks, vectors, metadatas, collection_name=DEFAULT_COLLECTION) -> list[str]`, `search(client, query_vector, limit=3, collection_name=DEFAULT_COLLECTION) -> list[dict]`, `DEFAULT_COLLECTION` — consumed by Task 13 (`scripts/run_ingest.py`).

- [ ] **Step 1: Write the failing test**

Create `tests/embeddings/test_qdrant_client.py`:

```python
from unittest.mock import MagicMock

from app.embeddings.qdrant_client import (
    DEFAULT_COLLECTION,
    ensure_collection,
    search,
    upsert_chunks,
)


def test_ensure_collection_creates_when_missing():
    client = MagicMock()
    client.get_collections.return_value = MagicMock(collections=[])

    ensure_collection(client, vector_size=768)

    client.create_collection.assert_called_once()
    _, kwargs = client.create_collection.call_args
    assert kwargs["collection_name"] == DEFAULT_COLLECTION
    assert kwargs["vectors_config"].size == 768


def test_ensure_collection_skips_when_present():
    client = MagicMock()
    existing = MagicMock()
    existing.name = DEFAULT_COLLECTION
    client.get_collections.return_value = MagicMock(collections=[existing])

    ensure_collection(client)

    client.create_collection.assert_not_called()


def test_upsert_chunks_sends_one_point_per_chunk():
    client = MagicMock()
    ids = upsert_chunks(
        client,
        chunks=["clause one", "clause two"],
        vectors=[[0.1, 0.2], [0.3, 0.4]],
        metadatas=[{"source": "a.pdf"}, {"source": "a.pdf"}],
    )

    assert len(ids) == 2
    _, kwargs = client.upsert.call_args
    assert len(kwargs["points"]) == 2
    assert kwargs["points"][0].payload["text"] == "clause one"


def test_search_maps_results_to_text_and_score():
    client = MagicMock()
    hit = MagicMock(payload={"text": "clause one"}, score=0.9)
    client.search.return_value = [hit]

    results = search(client, query_vector=[0.1, 0.2])

    assert results == [{"text": "clause one", "score": 0.9}]
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pytest tests/embeddings/test_qdrant_client.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.embeddings.qdrant_client'`.

- [ ] **Step 3: Implement `app/embeddings/qdrant_client.py`**

```python
"""Thin wrapper around the Qdrant client for storing and querying circular chunks."""
import os
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

DEFAULT_COLLECTION = "circular_clauses"


def get_client(url: str | None = None) -> QdrantClient:
    return QdrantClient(url=url or os.environ.get("QDRANT_URL", "http://localhost:6333"))


def ensure_collection(
    client: QdrantClient,
    collection_name: str = DEFAULT_COLLECTION,
    vector_size: int = 768,
) -> None:
    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def upsert_chunks(
    client: QdrantClient,
    chunks: list[str],
    vectors: list[list[float]],
    metadatas: list[dict],
    collection_name: str = DEFAULT_COLLECTION,
) -> list[str]:
    ids = [str(uuid.uuid4()) for _ in chunks]
    points = [
        PointStruct(id=ids[i], vector=vectors[i], payload={**metadatas[i], "text": chunks[i]})
        for i in range(len(chunks))
    ]
    client.upsert(collection_name=collection_name, points=points)
    return ids


def search(
    client: QdrantClient,
    query_vector: list[float],
    limit: int = 3,
    collection_name: str = DEFAULT_COLLECTION,
) -> list[dict]:
    results = client.search(
        collection_name=collection_name, query_vector=query_vector, limit=limit
    )
    return [{"text": r.payload.get("text"), "score": r.score} for r in results]
```

- [ ] **Step 4: Run the test again to verify it passes**

```bash
pytest tests/embeddings/test_qdrant_client.py -v
```

Expected: PASS — all 4 tests green (no live Qdrant instance required, everything is mocked).

- [ ] **Step 5: Commit**

```bash
git add app/embeddings/qdrant_client.py tests/embeddings/test_qdrant_client.py
git commit -m "Add Qdrant client wrapper for clause storage and retrieval"
```

- [ ] **Step 6 (manual, optional): Smoke-test against real Qdrant**

Only if Docker is available:

```bash
docker compose up -d qdrant
python -c "
from app.embeddings.qdrant_client import get_client, ensure_collection, upsert_chunks, search
from app.embeddings.embedder import embed_texts
client = get_client()
ensure_collection(client, vector_size=768)
vectors = embed_texts(['Stockbrokers must appoint a compliance officer.'])
upsert_chunks(client, ['Stockbrokers must appoint a compliance officer.'], vectors, [{'source': 'demo'}])
print(search(client, vectors[0]))
"
```

Expected: prints a list with one result whose `text` matches the input sentence and a `score` near `1.0`.

---

### Task 12: Build `app/api/main.py`

**Files:**
- Create: `app/api/main.py`
- Test: `tests/api/test_main.py`

**Interfaces:**
- Consumes: `app.db.database.get_db` (Task 7), `app.services.gap_engine.get_gaps` (Task 9), `app.graph.build_graph.build_graph` (Task 6 stub, imported lazily).
- Produces: `app` (the FastAPI instance), served at `/health`, `/upload`, `/gaps`.

- [ ] **Step 1: Write the failing test**

Create `tests/api/__init__.py` (empty) and `tests/api/test_main.py`:

```python
import os

from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_gaps_returns_501_before_real_models_are_pasted_in():
    response = client.get("/gaps")
    assert response.status_code == 501


def test_upload_returns_501_before_graph_is_pasted_in():
    pdf_bytes = b"%PDF-1.4 minimal"
    response = client.post(
        "/upload",
        files={"file": ("test_upload_scaffold.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 501

    created = "data/raw_pdfs/test_upload_scaffold.pdf"
    if os.path.exists(created):
        os.remove(created)
```

- [ ] **Step 2: Run it to verify it fails**

```bash
mkdir -p tests/api && touch tests/api/__init__.py
pytest tests/api/test_main.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.api.main'`.

- [ ] **Step 3: Implement `app/api/main.py`**

```python
"""FastAPI application wiring for RegOps AI."""
import os
import shutil

from dotenv import load_dotenv

load_dotenv()  # must run before importing app.db.database, which reads
                # DATABASE_URL at import time

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.gap_engine import get_gaps

app = FastAPI(title="RegOps AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/upload")
async def upload_circular(file: UploadFile = File(...), db: Session = Depends(get_db)):
    os.makedirs("data/raw_pdfs", exist_ok=True)
    file_path = f"data/raw_pdfs/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        from app.graph.build_graph import build_graph

        graph = build_graph()
        graph.invoke({"file_path": file_path, "filename": file.filename})
    except Exception as exc:
        # NOTE: broad on purpose while app.graph.build_graph is still a stub.
        # Narrow this once the real graph is pasted in, so genuine runtime
        # bugs don't get silently reported as "not wired up yet".
        raise HTTPException(
            status_code=501, detail=f"Ingestion pipeline not wired up yet: {exc}"
        ) from exc

    return {"status": "success", "filename": file.filename}


@app.get("/gaps")
def list_gaps(db: Session = Depends(get_db)):
    try:
        return get_gaps(db)
    except Exception as exc:
        # Same note as above — narrow once app.db.models is real.
        raise HTTPException(status_code=501, detail=str(exc)) from exc
```

- [ ] **Step 4: Run the test again to verify it passes**

```bash
pytest tests/api/test_main.py -v
```

Expected: PASS — all 3 tests green.

- [ ] **Step 5: Commit**

```bash
git add app/api/main.py tests/api
git commit -m "Add FastAPI app wiring with placeholder-safe error handling"
```

---

### Task 13: Build `scripts/run_ingest.py` and `scripts/run_diff.py`

**Files:**
- Create: `scripts/run_ingest.py`
- Create: `scripts/run_diff.py`
- Test: `tests/scripts/test_run_ingest.py`
- Test: `tests/scripts/test_run_diff.py`

**Interfaces:**
- Consumes: `app.ingestion.pdf_cleaner.clean_pdf` (Task 6 stub), `app.ingestion.clause_splitter.split_into_clauses` (Task 8), `app.embeddings.embedder.embed_texts` (Task 10), `app.embeddings.qdrant_client.{get_client,ensure_collection,upsert_chunks}` (Task 11), `app.graph.build_graph.build_graph` (Task 6 stub).
- Produces: `run_ingest(pdf_path: str) -> list[str]`, `run_diff(clause_text: str) -> dict` — CLI entry points, nothing downstream consumes these as a library.

- [ ] **Step 1: Write the failing tests**

Create `tests/scripts/__init__.py` (empty) and `tests/scripts/test_run_ingest.py`:

```python
from unittest.mock import patch

from scripts.run_ingest import run_ingest


def test_run_ingest_orchestrates_pipeline_and_returns_ids():
    with (
        patch("scripts.run_ingest.clean_pdf", return_value="1. Do X.\n\n2. Do Y.") as mock_clean,
        patch("scripts.run_ingest.embed_texts", return_value=[[0.1], [0.2]]) as mock_embed,
        patch("scripts.run_ingest.get_client", return_value="fake-client"),
        patch("scripts.run_ingest.ensure_collection") as mock_ensure,
        patch("scripts.run_ingest.upsert_chunks", return_value=["id-1", "id-2"]) as mock_upsert,
    ):
        result = run_ingest("data/raw_pdfs/demo.pdf")

    mock_clean.assert_called_once_with("data/raw_pdfs/demo.pdf")
    mock_embed.assert_called_once_with(["1. Do X.", "2. Do Y."])
    mock_ensure.assert_called_once_with("fake-client", vector_size=1)
    mock_upsert.assert_called_once()
    assert result == ["id-1", "id-2"]


def test_run_ingest_returns_empty_list_when_no_clauses_found():
    with patch("scripts.run_ingest.clean_pdf", return_value="   "):
        assert run_ingest("data/raw_pdfs/empty.pdf") == []
```

Create `tests/scripts/test_run_diff.py`:

```python
import pytest

from scripts.run_diff import run_diff


def test_run_diff_propagates_not_implemented_until_graph_is_pasted_in():
    with pytest.raises(NotImplementedError):
        run_diff("1. Appoint a compliance officer.")
```

- [ ] **Step 2: Run them to verify they fail**

```bash
mkdir -p tests/scripts && touch tests/scripts/__init__.py
pytest tests/scripts/test_run_ingest.py tests/scripts/test_run_diff.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.run_ingest'` (and `run_diff`).

- [ ] **Step 3: Implement `scripts/run_ingest.py`**

```python
"""CLI: ingest a SEBI circular PDF into Qdrant. Usage: python -m scripts.run_ingest <pdf_path>"""
import sys

from app.embeddings.embedder import embed_texts
from app.embeddings.qdrant_client import ensure_collection, get_client, upsert_chunks
from app.ingestion.clause_splitter import split_into_clauses
from app.ingestion.pdf_cleaner import clean_pdf


def run_ingest(pdf_path: str) -> list[str]:
    cleaned_text = clean_pdf(pdf_path)
    clauses = split_into_clauses(cleaned_text)
    if not clauses:
        print(f"No clauses found in {pdf_path}")
        return []

    vectors = embed_texts(clauses)
    client = get_client()
    ensure_collection(client, vector_size=len(vectors[0]))
    ids = upsert_chunks(
        client,
        chunks=clauses,
        vectors=vectors,
        metadatas=[{"source": pdf_path, "clause_index": i} for i in range(len(clauses))],
    )
    print(f"Ingested {len(ids)} clauses from {pdf_path}")
    return ids


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.run_ingest <pdf_path>")
        sys.exit(1)
    run_ingest(sys.argv[1])
```

- [ ] **Step 4: Implement `scripts/run_diff.py`**

```python
"""CLI: run the LangGraph extraction/diff pipeline over a clause.
Usage: python -m scripts.run_diff '<clause text>'
"""
import sys

from app.graph.build_graph import build_graph


def run_diff(clause_text: str) -> dict:
    graph = build_graph()
    return graph.invoke({"clause_text": clause_text})


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.run_diff '<clause text>'")
        sys.exit(1)
    result = run_diff(sys.argv[1])
    print(result)
```

- [ ] **Step 5: Run the tests again to verify they pass**

```bash
pytest tests/scripts/test_run_ingest.py tests/scripts/test_run_diff.py -v
```

Expected: PASS — all 3 tests green.

- [ ] **Step 6: Run the full test suite to confirm nothing regressed**

```bash
pytest -v
```

Expected: every test across all tasks (`test_stubs.py`, `test_database.py`, `test_clause_splitter.py`, `test_gap_engine.py`, `test_embedder.py`, `test_qdrant_client.py`, `test_main.py`, `test_run_ingest.py`, `test_run_diff.py`) passes.

- [ ] **Step 7: Commit**

```bash
git add scripts/run_ingest.py scripts/run_diff.py tests/scripts
git commit -m "Add run_ingest and run_diff CLI entry points"
```

---

### Task 14: Rewrite README.md for RegOps AI

**Files:**
- Modify: `README.md`

**Interfaces:** None.

- [ ] **Step 1: Replace the full contents of `README.md`**

```markdown
# RegOps AI

**From regulatory text to operational action.**

RegOps AI is an agentic compliance copilot for SEBI-regulated intermediaries. Upload a regulatory circular and it reads it, extracts every obligation it imposes, and tracks what's met, pending, or overdue — automatically and auditably.

<p align="center">
  <img src="https://img.shields.io/badge/status-hackathon%20prototype-orange?style=for-the-badge" alt="status" />
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="license" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/LangGraph-agentic-1C3C3C?style=for-the-badge" alt="LangGraph" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Qdrant-vector%20store-DC244C?style=for-the-badge" alt="Qdrant" />
</p>

---

## Why

Compliance teams at brokers, RTAs, and other SEBI intermediaries manually read hundred-page circulars to figure out what they're now required to do, then track it in spreadsheets. Obligations get missed, deadlines slip, and there's no audit trail of who did what when. RegOps AI turns that unstructured regulatory text into a structured, trackable, auditable checklist.

## How it works

| Step | What happens |
|---|---|
| **1. Ingest** | A SEBI circular PDF is cleaned (headers/footers stripped) and split into numbered-clause chunks. |
| **2. Embed & store** | Clauses are embedded (`BAAI/bge-base-en-v1.5`) and stored in Qdrant so relevant text can be retrieved on demand. |
| **3. Extract & diff** | A LangGraph pipeline (Groq `llama-3.3-70b-versatile`) reads clauses, extracts structured obligations, diffs against prior circular versions, and pauses for human review on uncertain calls. |
| **4. Track** | Each obligation becomes a trackable item in Postgres. Missing evidence or a passed deadline is flagged as a gap automatically. |

## Features

- **Circular ingestion** — PDF cleaning, clause splitting, embedding, and vector storage
- **Obligation extraction & diffing** — structured obligations with deadline, required evidence type, and source clause, diffed across circular versions
- **Human-in-the-loop review** — LangGraph interrupts route uncertain extractions to a reviewer before they're trusted
- **Evidence tracking** — attach evidence to an obligation and watch its status flip to "met"
- **Gap dashboard** — at-a-glance view of overdue and pending obligations
- **Synthetic data** — a generator seeds realistic obligations, tasks, evidence, and grievance records for demoing without real customer data

> **Note:** This is a hackathon prototype under active restructuring. The LangGraph pipeline, ORM models, review routes, and synthetic-data generator are being wired in — see `docs/superpowers/specs/2026-07-22-regops-ai-restructure-design.md` for the current build status.

## Tech stack

| Layer | Technology |
|---|---|
| UI | [React 19](https://react.dev/) + [Vite](https://vite.dev/) + [Tailwind CSS 4](https://tailwindcss.com/) |
| API | [FastAPI](https://fastapi.tiangolo.com/) |
| Agent orchestration | [LangGraph](https://www.langchain.com/langgraph) |
| LLM | [Groq](https://groq.com/) (`llama-3.3-70b-versatile`) |
| Relational store | [PostgreSQL 16](https://www.postgresql.org/) |
| Vector store | [Qdrant](https://qdrant.tech/) |
| Embeddings | `BAAI/bge-base-en-v1.5` (sentence-transformers) |

## Getting started

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Docker + Docker Compose

### 1. Start infrastructure

```bash
docker compose up -d
docker ps
```

### 2. Install Python dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in GROQ_API_KEY
```

### 3. Seed synthetic data

```bash
python -m app.db.seed_synthetic
```

### 4. Ingest a circular

Drop a PDF into `data/raw_pdfs/`, then:

```bash
python -m app.ingestion.pdf_cleaner data/raw_pdfs/<your-circular>.pdf
python -m scripts.run_ingest data/raw_pdfs/<your-circular>.pdf
```

### 5. Run the extraction/diff pipeline

```bash
python -m scripts.run_diff "<clause text>"
```

### 6. Start the API

```bash
uvicorn app.api.main:app --reload --port 8080
```

### 7. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard is available at `http://localhost:5173` and talks to the API at `http://localhost:8080`.

## Project structure

```
regops-ai/
├── docker-compose.yml       # postgres + qdrant
├── requirements.txt
├── .env.example
├── pytest.ini
├── docs/plan.md             # original build plan this prototype follows
├── data/
│   ├── raw_pdfs/            # SEBI circular PDFs you provide
│   ├── synthetic/           # generated by scripts/generate_synthetic_data.py
│   └── processed/clauses/   # clause_splitter output
├── app/
│   ├── ingestion/           # pdf_cleaner, clause_splitter
│   ├── embeddings/          # embedder, qdrant_client
│   ├── graph/               # state, nodes, build_graph (LangGraph pipeline)
│   ├── db/                  # database, models, seed_synthetic
│   ├── services/            # gap_engine
│   └── api/                 # main, routes_review
├── frontend/                # React dashboard
├── scripts/                 # generate_synthetic_data, run_ingest, run_diff
└── tests/
```

## Roadmap

- [ ] Real LangGraph extraction/diffing/human-review pipeline (`app/graph/nodes.py`)
- [ ] Real ORM models for obligations, tasks, evidence, grievances, org roles (`app/db/models.py`)
- [ ] Synthetic data generator (`scripts/generate_synthetic_data.py`)
- [ ] Human review API routes (`app/api/routes_review.py`)
- [ ] Multi-circular / multi-intermediary support

## License

MIT
```

- [ ] **Step 2: Verify no ComplyGuard references remain anywhere in the repo**

```bash
grep -ril "complyguard" . --include="*.md" --include="*.json" --include="*.jsx" --include="*.js" --include="*.html" --include="*.py" | grep -v node_modules | grep -v dist
```

Expected: no output (except possibly `frontend/package-lock.json` history entries, which are fine — that file is regenerated, not hand-authored).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "Rewrite README for RegOps AI architecture"
```

---

### Task 15: Rename the repo root directory

**Files:** None (filesystem-level rename only).

**Interfaces:** None.

This is last on purpose: every earlier task uses paths relative to the current repo root, so none of them depend on this rename having happened yet. Do this only after Tasks 1–14 are committed and verified.

- [ ] **Step 1: Confirm a clean working tree before renaming**

```bash
cd /home/bhuvi/Downloads/sebi-hackathon/complyguard-prototype
git status --short
```

Expected: no output (everything from Tasks 1–14 is committed).

- [ ] **Step 2: Rename the directory**

```bash
cd /home/bhuvi/Downloads/sebi-hackathon
mv complyguard-prototype regops-ai
cd regops-ai
```

- [ ] **Step 3: Verify git still works from the new path**

```bash
git status --short
git log --oneline -5
```

Expected: clean tree, same commit history as before — renaming the containing directory doesn't touch `.git` internals or any GitHub remote.

- [ ] **Step 4: Re-point your editor/terminal**

If you have a terminal, IDE window, or running dev servers pointed at the old path (`/home/bhuvi/Downloads/sebi-hackathon/complyguard-prototype`), close and reopen them at the new path (`/home/bhuvi/Downloads/sebi-hackathon/regops-ai`) — the old path no longer exists.

No commit needed for this task — nothing inside the git repository changed, only its containing folder name.

---

## After this plan

Once these 15 tasks are done, you'll have a fully-scaffolded, test-covered `regops-ai/` repo where:
- `frontend/` builds and runs exactly as before, rebranded.
- `docker compose up -d` gives you Postgres + Qdrant.
- Every non-stub module (`clause_splitter`, `embedder`, `qdrant_client`, `database`, `gap_engine`, `api/main`, `run_ingest`, `run_diff`) is real, working, and unit-tested.
- Every stub module (`pdf_cleaner`, `state`, `build_graph`, `models`, `seed_synthetic`, `routes_review`, `generate_synthetic_data`) is ready for you to paste your existing code into — replacing the `NotImplementedError` bodies — with nothing else in the codebase needing to change to pick it up.
