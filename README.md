# ComplyGuard

**From regulatory text to operational action.**

ComplyGuard is an agentic compliance copilot for SEBI-regulated intermediaries. Upload a regulatory circular and it reads it, extracts every obligation it imposes, and tracks what's met, pending, or overdue — automatically and auditably.

<p align="center">
  <img src="https://img.shields.io/badge/status-hackathon%20prototype-orange?style=for-the-badge" alt="status" />
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="license" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/Vite-8-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/JavaScript-ES2022-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript" />
  <img src="https://img.shields.io/badge/oxlint-1.71-EE7A16?style=for-the-badge&logo=eslint&logoColor=white" alt="oxlint" />
</p>

---

## Why

Compliance teams at brokers, RTAs, and other SEBI intermediaries manually read hundred-page circulars to figure out what they're now required to do, then track it in spreadsheets. Obligations get missed, deadlines slip, and there's no audit trail of who did what when. ComplyGuard turns that unstructured regulatory text into a structured, trackable, auditable checklist.

## How it works

| Step | What happens |
|---|---|
| **1. Ingest** | A SEBI circular PDF is parsed into text and split into overlapping chunks. |
| **2. Retrieve** | Chunks are embedded and stored in a vector database so relevant text can be retrieved on demand. |
| **3. Extract** | An LLM reads the retrieved chunks and returns validated, structured obligations — not free text. |
| **4. Track** | Each obligation becomes a trackable item. Missing evidence or a passed deadline is flagged as a gap automatically. |

## Features

- 📄 **Circular upload & parsing** — simulated ingestion pipeline for a SEBI master circular
- ✅ **Obligation extraction** — structured obligations with deadline, required evidence type, and the exact source clause
- 📎 **Evidence tracking** — attach evidence to an obligation and watch its status flip to "met"
- 📊 **Gap dashboard** — at-a-glance view of overdue and pending obligations
- 🕓 **Audit trail** — immutable log of every ingestion, extraction, and evidence event
- 🧭 **Guided navigation** — views unlock progressively as the pipeline "runs"

> **Note:** This is a frontend hackathon prototype. All data (circulars, obligations, evidence, audit log) is mocked in [`src/data/mockData.js`](src/data/mockData.js) — there is no backend, LLM, or vector store wired up yet.

## Tech stack

| Layer | Technology |
|---|---|
| UI | [React 19](https://react.dev/) |
| Build tool | [Vite 8](https://vite.dev/) |
| Styling | [Tailwind CSS 4](https://tailwindcss.com/) |
| Linting | [oxlint](https://oxc.rs/) |
| Language | JavaScript (ESM, JSX) |

## Getting started

### Prerequisites

- Node.js 18+
- npm

### Install & run

```bash
# clone the repo
git clone https://github.com/<your-username>/complyguard-prototype.git
cd complyguard-prototype

# install dependencies
npm install

# start the dev server
npm run dev
```

The app will be available at `http://localhost:5173`.

### Other scripts

```bash
npm run build     # production build to dist/
npm run preview   # preview the production build locally
npm run lint       # run oxlint
```

## Project structure

```
docs/
└── plan.md                 # original build plan this prototype follows
src/
├── assets/
│   └── sebi-logo.png
├── components/
│   ├── layout/
│   │   ├── Nav.jsx         # top navigation, view switching
│   │   └── Sidebar.jsx     # summary stats panel
│   ├── views/
│   │   ├── Hero.jsx            # landing hero section
│   │   ├── Landing.jsx         # "how it works" explainer
│   │   ├── UploadCircular.jsx  # circular upload / ingestion simulation
│   │   ├── ObligationList.jsx  # extracted obligations + evidence attachment
│   │   ├── GapDashboard.jsx    # overdue / pending obligation overview
│   │   └── AuditTrail.jsx      # audit log viewer
│   └── shared/
│       └── StatusBadge.jsx # met / pending / overdue badge
├── data/
│   └── mockData.js         # mock circular, obligations, evidence, audit log
├── App.jsx                 # view routing & state
└── main.jsx                # app entry point
```

## Roadmap

- [ ] Real PDF ingestion & chunking pipeline
- [ ] Vector store + embedding-based retrieval
- [ ] LLM-backed structured obligation extraction
- [ ] Persistent backend & auth
- [ ] Multi-circular / multi-intermediary support

## License

MIT
