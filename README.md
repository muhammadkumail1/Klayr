# The AI Scientist

> **Fulcrum Science × Hack-Nation Hackathon**  
> Transforms a natural language scientific hypothesis into a complete, operationally realistic experiment plan a real lab can execute — in under 60 seconds.

---

## What It Does

A researcher types:

> *"Does trehalose preserve HeLa cells better than DMSO during cryopreservation?"*

The AI Scientist returns a fully structured, publication-ready experiment plan including:

| Component | What you get |
|---|---|
| **Refined Hypothesis** | Falsifiable If/Then/Because form + sub-hypotheses |
| **Literature QC** | Top 3 relevant papers from PubMed + Semantic Scholar, deduplicated, LLM-summarized, gap analysis |
| **Protocol** | 8–20 detailed steps with exact concentrations, temperatures, equipment |
| **Materials List** | Real catalog numbers (Sigma-Aldrich, Thermo Fisher), quantities, costs |
| **Budget** | Line-item breakdown with NIH-standard 26% IDC overhead |
| **Timeline** | Phased Gantt-style plan with dependencies and milestones |
| **Statistical Validation** | Sample size, power analysis, appropriate statistical test, controls |
| **Biosafety Assessment** | BSL level, PPE requirements, waste disposal, regulatory flags |
| **Risk Register** | 4–10 risks with severity, likelihood, and specific mitigations |
| **Quality Score** | 0–100 completeness and rigor score |

---

## Architecture

```
src/
├── domain/          ← ZERO framework imports. Pure Python.
│   ├── entities/    ← Pydantic v2 models
│   ├── ports/       ← ABC interfaces (ILLMClient, ILitSearch, IExperimentRepo, ICache)
│   ├── prompts/     ← Pure prompt builder functions
│   ├── parsers/     ← Pure JSON → typed model converters
│   └── pipeline/    ← LangGraph StateGraph (8 nodes)
│
├── infrastructure/  ← Implements domain ports. Owns all I/O.
│   ├── llm/         ← Groq Llama 3.3 70B (llama-3.3-70b-versatile)
│   ├── search/      ← PubMed + Semantic Scholar + combined dedup
│   ├── db/          ← PostgreSQL via async SQLAlchemy 2.0
│   └── cache/       ← Redis
│
└── api/             ← FastAPI. Wires infrastructure into domain via Depends().
    ├── routes/      ← POST /api/run, GET /api/plan, POST /api/feedback
    └── dependencies.py  ← Composition root

public/             ← Frontend (vanilla JS + Bootstrap)
├── index.html       ← Interactive UI
└── app.js           ← Client-side logic
```

**The rule:** `domain/` never imports from `infrastructure/` or `api/`. Ever.

---

## Pipeline (LangGraph)

```
refine_hypothesis → literature_qc → generate_protocol → generate_materials
    → generate_budget → generate_timeline → generate_validation
    → assess_safety_and_risks [biosafety + risks run concurrently]
```

Each node = 1 prompt builder + 1 LLM call + 1 parser. Nothing else.

---

## Competitive Features

### 1. Feedback Loop (Few-Shot Learning)
`POST /api/feedback` stores scientist corrections. Future pipeline runs for the same domain automatically inject these as few-shot examples into the protocol prompt. The system gets smarter with every correction.

### 2. Real-Time Streaming (SSE)
`POST /api/run/stream` streams pipeline progress as Server-Sent Events. Your frontend can show a live progress bar as each of the 8 nodes completes.

### 3. Dual Literature Sources
Concurrent PubMed + Semantic Scholar search with DOI-based deduplication. PubMed has superior biomedical coverage; Semantic Scholar covers CS and chemistry. Combined, they cover the full experimental science space.

### 4. Biosafety Intelligence
Automatically determines BSL level, required PPE, waste disposal protocol, and regulatory flags (IBC, IRB, DEA). This is the feature every real lab scientist needs and no other AI tool provides.

### 6. Interactive Web Frontend
No registration required. One-click plan generation with tabbed results, real-time progress, and plan sharing.

---

## Quick Start

```bash
cd "C:\Users\Muhammad Kumail\Desktop\PROJECTS\MIT"

# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
copy .env.example .env
# Add your GROQ_API_KEY to .env

# 3. Start infrastructure (Docker required)
docker-compose up -d postgres redis

# 4. Initialize database
$env:PYTHONPATH = "src"
python -c "..."

# 5. Run the server
$env:PYTHONPATH = "src"
python -m uvicorn api.main:app --reload --port 8000
```

**Open browser:** http://localhost:8000

---

## Frontend

A modern, interactive web interface is included at `/public/`. It provides:

- **Hypothesis Input Form** — Submit your scientific question
- **Real-Time Progress Tracking** — Watch the AI pipeline execute in real-time via SSE streaming
- **Interactive Plan Viewer** — 8 tabbed sections for detailed plan inspection
- **Quality Score Display** — Numeric score + colored badge (Excellent/Good/Fair/Poor)
- **Plan History** — Browse and load previous experiments
- **Feedback System** — Provide corrections to improve future generations
- **Download & Share** — Export plans as text or share via URL

The frontend is **vanilla JS + Bootstrap 5** — no build step, pure browser-native.

---

## API Reference

### POST /api/run
```json
{
  "hypothesis": "Does trehalose preserve HeLa cells better than DMSO?",
  "domain": "cell_biology"
}
```

### POST /api/run/stream
Same body. Returns Server-Sent Events stream.

### GET /api/plan/{plan_id}
Returns full saved plan.

### GET /api/plans?limit=20&offset=0
Paginated list of all plans.

### POST /api/feedback
```json
{
  "plan_id": "uuid",
  "section": "protocol",
  "original_content": "...",
  "correction": "Use 0.05% trypsin instead of 0.25%",
  "experiment_domain": "cell_biology"
}
```

### GET /health
Liveness probe.

---

## Testing

```bash
# All tests (domain tests require no running services)
make test

# Domain only (fastest)
make test-domain
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Get at console.groq.com |
| `SEMANTIC_SCHOLAR_API_KEY` | ❌ | Free at semanticscholar.org/product/api |
| `NCBI_API_KEY` | ❌ | Free at ncbi.nlm.nih.gov/account |
| `DATABASE_URL` | ✅ | PostgreSQL async URL (default: postgres on 5433) |
| `REDIS_URL` | ❌ | Redis URL (default: redis://localhost:6379) |
| `APP_ENV` | ❌ | "development" or "production" |

---

## Tech Stack

- **Python 3.11** + **FastAPI** + **uvicorn**
- **LangGraph** — stateful multi-agent pipeline
- **Groq Llama 3.3 70B** — free, fast LLM
- **PostgreSQL** + **SQLAlchemy 2.0 async** — plan storage
- **Redis** — response caching
- **Pydantic v2** — all data validation
- **httpx** — async HTTP for literature APIs
- **Bootstrap 5 + Vanilla JS** — frontend (zero build step)
