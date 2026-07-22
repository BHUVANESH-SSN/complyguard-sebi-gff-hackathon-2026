# RegOps AI restructure — design

## Goal

Restructure the ComplyGuard hackathon prototype onto a LangGraph + PostgreSQL + Qdrant
stack, matching a target `regops-ai/` project layout, rebranding the product from
ComplyGuard to **RegOps AI**, and aligning the existing React frontend and the new
backend under one stable, coherent repo — without yet implementing the LangGraph
agent logic itself (that code will be pasted in separately by the user).

## Scope

**In scope:**
- Physical repo restructure: rename root dir, move frontend under `frontend/`,
  delete the old FastAPI/SQLite/Chroma backend, scaffold the new `app/` package.
- New infra: `docker-compose.yml` (Postgres + Qdrant), `requirements.txt`, `.env.example`.
- Full rebrand: ComplyGuard → RegOps AI in UI text, README, package.json, DB name,
  docker-compose project/container names.
- Real, working implementations for the modules NOT covered by code the user is
  pasting in separately (the "build" files below).
- Placeholder stub files for the modules the user will paste real code into (the
  "stub" files below), so the tree is complete and nothing import-crashes.

**Out of scope (explicitly not building now):**
- The actual LangGraph agent graph, state schema, DB ORM models, human-review API
  routes, and synthetic-data generator — the user has this code and will paste it
  into the stub files themselves, in another IDE.
- Any real synthetic data content (`data/synthetic/*.json|csv`) — generated later
  by the user's `generate_synthetic_data.py` once pasted in.
- Fetching/committing real SEBI circular PDFs into `data/raw_pdfs/` — left empty
  for the user to populate.

## Final directory layout

```
regops-ai/
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── docs/
│   └── plan.md                        # untouched, historical
├── data/
│   ├── raw_pdfs/.gitkeep
│   ├── synthetic/.gitkeep
│   └── processed/clauses/             # generated, gitignored
├── app/
│   ├── __init__.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── pdf_cleaner.py             # STUB
│   │   └── clause_splitter.py         # BUILD
│   ├── embeddings/
│   │   ├── __init__.py
│   │   ├── embedder.py                # BUILD — BAAI/bge-base-en-v1.5
│   │   └── qdrant_client.py           # BUILD
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py                   # STUB
│   │   ├── nodes.py                   # BUILD (thin, replaced once user pastes real graph)
│   │   └── build_graph.py             # STUB
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py                # BUILD — Postgres engine/session
│   │   ├── models.py                  # STUB
│   │   └── seed_synthetic.py          # STUB
│   ├── services/
│   │   ├── __init__.py
│   │   └── gap_engine.py              # BUILD
│   └── api/
│       ├── __init__.py
│       ├── main.py                    # BUILD
│       └── routes_review.py           # STUB
├── frontend/                          # moved from repo root, unchanged otherwise
│   ├── src/...
│   ├── package.json                   # name -> "regops-ai"
│   ├── vite.config.js
│   ├── index.html                     # title -> "RegOps AI — SEBI Agentic Compliance"
│   ├── .oxlintrc.json
│   └── public/
├── scripts/
│   ├── generate_synthetic_data.py     # STUB
│   ├── run_ingest.py                  # BUILD — CLI: pdf -> clauses -> embeddings -> qdrant
│   └── run_diff.py                    # BUILD — CLI: invokes build_graph() over a clause
└── tests/.gitkeep
```

`STUB` = docstring + safe no-op signatures matching what other modules import;
no import-time side effects, so the app boots before real code is pasted in.
`BUILD` = real, working implementation written now.

## Rebrand (ComplyGuard → RegOps AI)

| File | Change |
|---|---|
| Repo root dir | `complyguard-prototype/` → `regops-ai/` |
| `frontend/package.json` | `"name": "complyguard-prototype"` → `"name": "regops-ai"` |
| `frontend/index.html` | `<title>ComplyGuard — SEBI Agentic Compliance</title>` → `<title>RegOps AI — SEBI Agentic Compliance</title>` |
| `frontend/src/components/layout/Nav.jsx` | "ComplyGuard" → "RegOps AI"; "SEBI x ComplyGuard" → "SEBI x RegOps AI" |
| `frontend/src/components/views/Hero.jsx` | "ComplyGuard reads it…" → "RegOps AI reads it…" |
| `frontend/src/App.jsx` | "ComplyGuard — Connects to Python FastAPI Backend." → "RegOps AI — Connects to Python FastAPI Backend." |
| `README.md` | Title/headline rebranded; architecture section rewritten to describe the LangGraph/Postgres/Qdrant stack instead of the stale "no backend, all mocked" note |
| `docs/plan.md` | Left untouched — historical record of the original build plan |
| Postgres DB name | `regops` |
| docker-compose project/container names | `regops-ai-postgres`, `regops-ai-qdrant` |

Display text in UI/README uses "RegOps AI" (title case); technical identifiers
(package name, DB name, docker project) use lowercase-hyphenated `regops-ai`/`regops`.

## Mechanical steps

1. `git mv` current root frontend files (`src/`, `public/`, `index.html`,
   `package.json`, `package-lock.json`, `vite.config.js`, `.oxlintrc.json`) into
   `frontend/`. `node_modules/` and `dist/` (both gitignored, untracked) are moved
   with a plain `mv` alongside.
2. `git rm -r backend/` — removes the old FastAPI service and the incidentally
   committed junk in it (`__pycache__/*.pyc`, `chroma_db/*`, `complyguard.db`).
   `backend/venv/` and `backend/.env` are untracked; deleted with a plain `rm -rf`.
3. Scaffold `app/`, `data/`, `scripts/`, `tests/` per the tree above.
4. Rename the repo root directory `complyguard-prototype/` → `regops-ai/` (local
   disk rename only — does not touch git history or any GitHub remote name).
5. Update `.gitignore`: add `data/processed/`, `__pycache__/`, `venv/`, `*.pyc`.

## New infra files

- **`docker-compose.yml`**: `postgres:16` service (named volume, healthcheck, env
  from `.env`: `POSTGRES_DB=regops`) + `qdrant/qdrant` service (REST `6333`, gRPC
  `6334`, named volume). Project name `regops-ai`.
- **`.env.example`**: `DATABASE_URL`, `GROQ_API_KEY`, `GROQ_MODEL`, `QDRANT_URL`
  placeholders. Real `.env` stays gitignored (already covered by the existing
  `.gitignore` rule).
- **`requirements.txt`**: `fastapi`, `uvicorn`, `pypdf`, `sentence-transformers`,
  `qdrant-client`, `groq`, `python-dotenv`, `pydantic`, `sqlalchemy`,
  `psycopg2-binary`, `python-multipart`, `langgraph`, `langchain-core`.

## Models

- **LLM**: Groq, `llama-3.3-70b-versatile` (unchanged from the old backend, reuses
  existing `GROQ_API_KEY`).
- **Embeddings**: `BAAI/bge-base-en-v1.5` (768-dim, local, no API key), replacing
  `all-MiniLM-L6-v2`.

## What gets really built now (the `BUILD` files)

Since these aren't covered by code the user is pasting in, they get real,
working implementations, porting logic from the old `backend/`:

- `app/ingestion/clause_splitter.py` — splits cleaned circular text into
  numbered-clause chunks (adapting the old recursive chunking approach).
- `app/embeddings/embedder.py` — wraps `BAAI/bge-base-en-v1.5` for encoding text.
- `app/embeddings/qdrant_client.py` — Qdrant collection setup, upsert, and query
  helpers (replacing the old Chroma client).
- `app/db/database.py` — SQLAlchemy engine/session against Postgres
  (`DATABASE_URL` from `.env`), replacing the old SQLite `database.py`.
- `app/services/gap_engine.py` — obligation status/gap logic (ported from the old
  `gaps.py`: evidence-present → met, deadline-passed → overdue, else pending).
- `app/api/main.py` — FastAPI app wiring health/upload/obligations/evidence/gaps
  endpoints against the new modules (structurally similar to the old `main.py`,
  importing from `app.db.models` / `app.graph.build_graph` even though those are
  currently stubs — so the app boots, real behavior arrives once the user pastes
  the graph/model code in).
- `scripts/run_ingest.py` — CLI: PDF path → `pdf_cleaner` (stub-safe) →
  `clause_splitter` → `embedder` → `qdrant_client` upsert.
- `scripts/run_diff.py` — CLI: invokes `build_graph()` (stub-safe) over a clause
  pair.

## Stub file contract

Each `STUB` file gets a module docstring noting it's a placeholder, plus function/
class signatures (matching what `BUILD` files import from it) that raise
`NotImplementedError` when called — so importing the module never fails, only
calling into unbuilt logic does.

## Verification

- `cd frontend && npm run build` — confirms the moved frontend still builds after
  relocation.
- `python -c "import app.api.main"` — confirms the new package tree imports
  cleanly (stub files included) with no circular-import or path errors.
- `docker-compose config` — validates the compose file syntax without starting
  containers.
