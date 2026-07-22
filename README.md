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
