# ComplyGuard — Working Prototype Plan
### SEBI Agentic Compliance: From Regulatory Text to Operational Action
*A build-it-yourself plan that teaches AI/ML, backend coding, and web development as you go.*

---

## 0. What You're Building (one paragraph)

A web app where a compliance officer uploads a SEBI circular (PDF), and the system automatically reads it, extracts the specific obligations it imposes on stockbrokers, turns each into a trackable checklist item, lets the officer attach evidence of compliance, and shows a live dashboard flagging which obligations are unmet or overdue. Text goes in → actionable, auditable compliance comes out.

**Scope discipline (read this twice):** ONE circular. ONE intermediary category (stockbrokers). 5–8 obligations. A working end-to-end slice beats a broken broad system every single time. You can always widen later.

---

## 1. The Learning Map — What Each Part Teaches You

This project is deliberately structured so every module teaches one skill from your goals. Don't skip the "why" — that's where the learning lives.

| You'll build | You'll learn | Why it matters for your career |
|---|---|---|
| PDF → text → chunks → embeddings → vector store | **RAG (Retrieval-Augmented Generation)** | The #1 in-demand LLM engineering skill right now |
| LLM call that returns validated JSON | **Structured extraction + Pydantic** | Separates real LLM systems from toy chatbots |
| FastAPI endpoints | **Backend web development** | Every full-stack/SDE role needs this |
| SQLite tables + queries | **Databases + SQL + data modeling** | Universal, non-negotiable skill |
| Gap-detection logic | **Business logic / algorithms** | The "thinking" part of software |
| React dashboard | **Frontend web development** | Makes your work visible and demoable |
| Connecting UI ↔ API ↔ DB | **Full-stack data flow** | The thing that finally makes web dev "click" |

---

## 2. Architecture (simple on purpose — you should understand every box)

```
┌──────────────────┐        ┌─────────────────────────────────────┐        ┌──────────────┐
│   React Frontend │  HTTP  │          FastAPI Backend            │  SQL   │  SQLite DB   │
│                  │───────▶│                                     │───────▶│              │
│ • Upload circular│        │  ┌─────────────────────────────┐   │        │ obligations  │
│ • Obligation list│        │  │ 1. Ingest  (PDF → text)     │   │        │ evidence     │
│ • Evidence upload│        │  │ 2. Chunk + Embed → Vector DB│   │        │ audit_log    │
│ • Gap dashboard  │◀───────│  │ 3. Extract obligations (LLM)│   │◀───────│              │
│                  │        │  │ 4. Gap check + status       │   │        │              │
└──────────────────┘        │  └─────────────────────────────┘   │        └──────────────┘
                            └──────────────┬──────────────────────┘
                                           │
                              ┌────────────▼─────────────┐
                              │  Claude API + ChromaDB   │
                              │  (embeddings + retrieval)│
                              └──────────────────────────┘
```

Four backend steps. One database with three tables. One frontend. That's the whole system.

---

## 3. Tech Stack (with reasons, so you're not cargo-culting)

| Layer | Tool | Why this one |
|---|---|---|
| Language | **Python 3.11+** | Best AI/ML ecosystem; you'll learn it deeply here |
| Backend framework | **FastAPI** | Modern, auto-generates API docs, teaches you async + typing |
| Data validation | **Pydantic** | Forces clean data structures — core skill for LLM extraction |
| PDF reading | **pypdf** | Simple, pure-Python, no system dependencies |
| Embeddings | **sentence-transformers** (`all-MiniLM-L6-v2`) | Free, runs locally, teaches you what embeddings *are* |
| Vector store | **ChromaDB** | Easiest vector DB to start with; zero config |
| LLM | **Claude API** | Best structured-extraction reliability |
| Database | **SQLite** | Zero setup, one file, real SQL — perfect for learning |
| Frontend | **React (Vite)** | Industry standard; Vite makes setup painless |
| HTTP from frontend | **fetch** (built-in) | Learn the fundamentals before reaching for libraries |

**Deliberately NOT using** (yet): PostgreSQL, Docker, auth, cloud deploy. Add these *after* the core works. Adding them now is how beginners stall.

---

## 4. Repository Structure

```
complyguard/
├── README.md
├── backend/
│   ├── main.py                 # FastAPI app + routes
│   ├── ingest.py               # Step 1-2: PDF → text → chunks → embeddings
│   ├── extract.py              # Step 3: LLM structured extraction
│   ├── gaps.py                 # Step 4: gap-detection logic
│   ├── database.py             # SQLite setup + queries
│   ├── models.py               # Pydantic schemas
│   ├── requirements.txt
│   └── data/
│       └── circulars/          # SEBI PDFs go here
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── UploadCircular.jsx
│   │   │   ├── ObligationList.jsx
│   │   │   └── GapDashboard.jsx
│   │   └── api.js              # all fetch calls to backend
│   └── package.json
└── docs/
    └── demo-script.md
```

---

## 5. The Data Model (learn this before coding — it's the backbone)

Three tables. Understand *why* each column exists.

**`obligations`** — one row per extracted requirement
| Column | Type | Meaning |
|---|---|---|
| id | INTEGER PK | unique id |
| circular_name | TEXT | which circular it came from |
| obligation_text | TEXT | the requirement in plain language |
| intermediary | TEXT | who it applies to (e.g. "stockbroker") |
| deadline | TEXT | when it must be met (nullable) |
| evidence_type | TEXT | what proof is needed (e.g. "policy document") |
| source_chunk | TEXT | the exact circular text it was extracted from (for auditability) |
| status | TEXT | "pending" / "met" / "overdue" |

**`evidence`** — proof attached by the compliance officer
| Column | Type | Meaning |
|---|---|---|
| id | INTEGER PK | unique id |
| obligation_id | INTEGER FK | links to obligations.id |
| description | TEXT | what evidence was provided |
| submitted_at | TEXT | timestamp |

**`audit_log`** — immutable trail (this is what makes it "auditable")
| Column | Type | Meaning |
|---|---|---|
| id | INTEGER PK | unique id |
| action | TEXT | what happened (e.g. "obligation extracted", "evidence added") |
| detail | TEXT | specifics |
| timestamp | TEXT | when |

The `source_chunk` column is your killer feature — it means every extracted obligation can be traced back to the exact regulatory text it came from. Judges love traceability.

---

## 6. Build Order = Your Learning Curriculum

Follow this order strictly. Each step works before you move on. Don't build the whole thing then debug — build one working slice at a time.

### PHASE A — Backend + AI Core (learn Python, RAG, extraction)

**Step 1 — FastAPI hello world**
Goal: understand what a web server is.
- One endpoint `GET /health` that returns `{"status": "ok"}`
- Run it, hit it in browser, see FastAPI's auto-docs at `/docs`
- **Learning checkpoint:** you now understand routes, servers, and JSON responses.

**Step 2 — PDF to text**
Goal: file handling.
- Endpoint `POST /upload` that takes a PDF, extracts text with `pypdf`
- **Learning checkpoint:** file I/O, how PDFs are just structured text.

**Step 3 — Chunk + embed + store (THE RAG STEP)**
Goal: understand retrieval.
- Split text into ~500-word overlapping chunks
- Embed each chunk with `sentence-transformers`
- Store in ChromaDB
- Add a test query: "what must brokers report?" → retrieve top 3 relevant chunks
- **Learning checkpoint:** you now understand embeddings, vector similarity, and RAG — the foundation of modern AI apps. Spend real time here.

**Step 4 — Extract obligations (STRUCTURED EXTRACTION STEP)**
Goal: reliable LLM output.
- Define a Pydantic `Obligation` model matching your data schema
- Prompt Claude with retrieved chunks: "Extract every obligation for stockbrokers as JSON matching this schema"
- Parse and validate the response with Pydantic
- **Learning checkpoint:** you now know how to make LLMs return clean, usable data — the single most valuable LLM-engineering skill.

### PHASE B — Database + Logic (learn SQL, data modeling)

**Step 5 — SQLite storage**
- Create the three tables from §5
- Save extracted obligations
- **Learning checkpoint:** SQL, schemas, primary/foreign keys.

**Step 6 — Evidence endpoint**
- `POST /evidence` to attach evidence to an obligation
- Write to `audit_log` every time
- **Learning checkpoint:** CRUD operations, relational links.

**Step 7 — Gap detection**
- Logic: obligation is a "gap" if it has no evidence OR deadline is past
- `GET /gaps` returns all gaps
- **Learning checkpoint:** business logic, querying across tables.

### PHASE C — Frontend (learn React, web dev)

**Step 8 — React setup + upload**
- `npm create vite@latest` → React app
- Upload component that POSTs a PDF to your backend
- **Learning checkpoint:** components, state, fetch, frontend↔backend connection.

**Step 9 — Obligation list**
- Fetch obligations from API, render as a table with status badges
- **Learning checkpoint:** rendering lists, mapping data to UI.

**Step 10 — Gap dashboard**
- Red/green cards showing met vs. gap obligations
- Click an obligation → see its `source_chunk` (the traceability feature)
- **Learning checkpoint:** conditional rendering, the full data loop clicks into place.

### PHASE D — Polish + Demo

**Step 11 — Audit trail view** — simple table showing the log.
**Step 12 — Demo video** — see §8.

---

## 7. Milestone Checkpoints (so you know you're on track)

- [ ] **M1 (end of Phase A):** You can upload a real SEBI circular and see extracted obligations printed as JSON in your terminal. *The AI core works.*
- [ ] **M2 (end of Phase B):** Obligations persist in the database; you can add evidence and query gaps via API docs. *The backend works.*
- [ ] **M3 (end of Phase C):** The whole thing works in a browser — upload, see obligations, add evidence, see gaps. *It's a real app.*
- [ ] **M4 (end of Phase D):** 3-minute demo recorded. *It's submittable.*

If you hit M1, you've already built something most hackathon teams never finish. Everything after is making it presentable.

---

## 8. Demo Script (3 minutes — plan this early)

1. **(0:00–0:30)** The problem: SEBI circulars are dense text; compliance is manual and error-prone. Show a real circular PDF.
2. **(0:30–1:30)** Upload it. Watch obligations get extracted live into a checklist. Click one → show the exact source text it came from (traceability).
3. **(1:30–2:15)** Attach evidence to one obligation. Show the dashboard update from red to green.
4. **(2:15–3:00)** Show a gap being flagged (unmet/overdue obligation) and the audit trail. Close with the impact line: "regulatory text to operational action, automatically and auditably."

Record the *working narrow slice*. Never demo features that aren't solid.

---

## 9. Getting the SEBI Corpus

- Go to SEBI's official website → Legal → Master Circulars
- Download the **Master Circular for Stock Brokers** (publicly available, consolidates all obligations — exactly what SEBI suggested in the problem statement)
- Put it in `backend/data/circulars/`
- Start with just this one document. Prove the pipeline on it before adding more.

---

## 10. Honest Difficulty + Time Notes

- **Phase A is the hard/valuable part** — budget the most time here. RAG + structured extraction is where the real learning is, and where you'll get stuck-and-unstuck the most (which is how you actually learn).
- **Phase B is the easiest** — SQLite is forgiving.
- **Phase C feels hardest if you've never done React** — but connecting a working backend to a UI is the fastest way to finally understand web dev, because you can see your own data flowing.
- **Don't add auth, Docker, or cloud deploy until M3 is done.** They add zero demo value and lots of stall risk.

---

## 11. Stretch Features (ONLY after M3 — do not touch before)

- Multi-circular support (extract across several documents)
- "New circular arrives → auto-diff against existing obligations" (the *dynamic regulatory translation* half of the problem statement — very impressive if you get here)
- A second intermediary category (investment advisers)
- Deadline email/alert notifications

---

## 12. Your Very First Command

```bash
mkdir -p complyguard/backend/data/circulars
cd complyguard/backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pypdf sentence-transformers chromadb anthropic pydantic
```

Then we write `main.py` Step 1 together, line by line, so you learn what each piece does.

---

**Next action:** Tell me to start Step 1, and I'll write the minimal FastAPI backend with every line explained — you'll have a running web server in 10 minutes and understand exactly why it works.
