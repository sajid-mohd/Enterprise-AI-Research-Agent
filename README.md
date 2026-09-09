# Enterprise AI Research Agent


A web-based **Enterprise Research Intelligence Platform** that accepts any research question, conducts structured multi-source research, extracts and compares findings, detects contradictions, and synthesizes a traceable, evidence-backed conclusion.

---

## Project Overview

This system turns a business question into structured, evidence-backed research. Instead of asking an AI for an opinion, it gathers information from multiple real sources, stores all evidence, compares findings, identifies disagreements, and produces a conclusion that the user can trace back to its underlying sources.

### Key capabilities

- **Dynamic research** — any question works; no hard-coded answers
- **Real web search** — DuckDuckGo + Wikipedia; real retrieval on every run
- **AI pipeline** — LLM-powered decomposition, extraction, contradiction detection, and synthesis
- **Full traceability** — Conclusion → Finding → Source → URL
- **Persistent knowledge base** — SQLite + ChromaDB; all research is stored and queryable
- **Natural-language knowledge query** — semantic search over stored findings with AI answer generation
- **Live pipeline progress** — frontend polls every 2s and shows each step as it completes

---

## Architecture

```
┌─────────────────────────────────────┐
│              FRONTEND               │
│  React + Vite + Tailwind CSS        │
│                                     │
│  Dashboard · Research Console       │
│  Research Result · Knowledge        │
│  Explorer · Query Knowledge         │
└──────────────────┬──────────────────┘
                   │ HTTP / JSON
                   ▼
┌─────────────────────────────────────┐
│         APPLICATION / API           │
│  FastAPI + Background Tasks         │
│                                     │
│  POST /research  GET /research/{id} │
│  GET /sessions   GET /findings      │
│  GET /sources    GET /contradictions│
│  POST /query     GET /health        │
└──────────────────┬──────────────────┘
                   │
         ┌─────────┴──────────┐
         ▼                    ▼
┌─────────────────┐  ┌─────────────────┐
│  AI INTELLIGENCE│  │ EXTERNAL RESEARCH│
│                 │  │                 │
│ QuestionDec-    │  │ DuckDuckGo      │
│ omposer         │  │ Wikipedia API   │
│ FindingExtractor│  │ HTTP Scraper    │
│ Contradiction   │  │ HTML Cleaner    │
│ Detector        │  └─────────────────┘
│ Conclusion      │
│ Synthesizer     │
└─────────┬───────┘
          │
┌─────────┴───────────────────────────┐
│         DATA & KNOWLEDGE            │
│                                     │
│  SQLite (structured data)           │
│    ResearchSession · SubQuestion    │
│    Source · Finding · Contradiction │
│    Conclusion · ConclusionFinding   │
│                                     │
│  ChromaDB (semantic search)         │
│    Finding embeddings               │
└─────────────────────────────────────┘
```

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- A free API key from [console.groq.com](https://console.groq.com) (recommended) or [aistudio.google.com](https://aistudio.google.com)

### 1. Clone / navigate to project

```bash
cd research-agent
```

### 2. Backend setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set PROVIDER and the matching API key
```

### 3. Configure `.env`

```env
PROVIDER=groq                        # groq | gemini | anthropic
GROQ_API_KEY=gsk_your_key_here       # get free key at console.groq.com
DB_PATH=data/research.db
CHROMA_PATH=data/chroma
```

### 4. Run the backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is now available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 5. Frontend setup

```bash
cd ../frontend
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `PROVIDER` | Yes | `groq` | LLM provider: `groq`, `gemini`, or `anthropic` |
| `GROQ_API_KEY` | If groq | — | Free at console.groq.com |
| `GEMINI_API_KEY` | If gemini | — | Free at aistudio.google.com |
| `ANTHROPIC_API_KEY` | If anthropic | — | Paid |
| `GENERATOR_MODEL` | No | provider default | Override model name |
| `DB_PATH` | No | `data/research.db` | SQLite database path |
| `CHROMA_PATH` | No | `data/chroma` | ChromaDB persistent path |
| `MAX_SOURCES_PER_SUBQUESTION` | No | `3` | Sources fetched per sub-question |
| `MAX_SUBQUESTIONS` | No | `5` | Max sub-questions per session |
| `SCRAPER_TIMEOUT` | No | `15` | HTTP timeout in seconds |

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v -p no:asyncio
```

Tests cover:
- HTML cleaning and text extraction
- Domain extraction and reliability scoring
- All ORM models via in-memory SQLite
- API routes via FastAPI TestClient

---

## API Reference

| Method | Route | Description |
|---|---|---|
| `POST` | `/research` | Submit research question |
| `GET` | `/research/{id}` | Full session detail |
| `GET` | `/sessions` | Paginated session list |
| `GET` | `/findings` | List findings (filterable) |
| `GET` | `/findings/{id}` | Single finding with provenance |
| `GET` | `/sources/{id}` | Source with all findings |
| `GET` | `/contradictions` | List contradictions |
| `GET` | `/contradictions/{id}` | Single contradiction |
| `POST` | `/query` | Natural-language knowledge query |
| `GET` | `/health` | System health check |

---

## Library Inventory

| Library | Version | License | Purpose |
|---|---|---|---|
| FastAPI | ≥0.111 | MIT | API framework |
| SQLAlchemy | ≥2.0 | MIT | ORM |
| ChromaDB | ≥0.5 | Apache 2.0 | Vector store / semantic search |
| trafilatura | ≥1.12 | GPL-3.0 | HTML → text extraction |
| httpx | ≥0.27 | BSD | Async HTTP client |
| duckduckgo-search | ≥6.0 | MIT | Web search provider |
| wikipedia | ≥1.4 | MIT | Wikipedia search provider |
| pydantic | ≥2.0 | MIT | Data validation |
| pydantic-settings | ≥2.0 | MIT | Settings from env |
| python-dotenv | ≥1.0 | BSD | .env loading |
| beautifulsoup4 | ≥4.12 | MIT | HTML fallback parser |
| groq | ≥0.9 | MIT | Groq LLM provider |
| google-genai | ≥1.0 | Apache 2.0 | Gemini LLM provider |
| anthropic | ≥0.40 | MIT | Anthropic LLM provider |
| React | 18 | MIT | Frontend UI |
| Vite | 5 | MIT | Frontend build tool |
| Tailwind CSS | 3 | MIT | Styling |
| React Router | 6 | MIT | Frontend routing |
| Axios | ≥1.6 | MIT | HTTP client |
| lucide-react | ≥0.300 | ISC | UI icons |

> **Note on trafilatura (GPL-3.0):** trafilatura is the highest-quality open-source HTML text extractor available. If GPL-3.0 is a concern, it can be replaced with beautifulsoup4 (MIT) alone — the `clean_html()` function already includes a beautifulsoup4 fallback.

---

## Limitations

- **Research takes 60–120 seconds** — real web search + scraping + multiple LLM calls per session
- **DuckDuckGo rate limits** — DuckDuckGo may throttle rapid successive requests; add delays between sessions if needed
- **Source quality varies** — the system retrieves real web pages and some may have thin content
- **LLM accuracy** — findings are extracted from real source text; the system cannot verify all factual claims
- **No authentication** — this is a prototype; production deployment would need auth and rate limiting

---

## Scalability Path (100 → 100,000 records)

```
Current:
  FastAPI (sync background tasks) → SQLite → ChromaDB

Future:
  Load Balancer
    → Multiple FastAPI instances (stateless)
    → Message Queue (e.g. Celery + Redis)
    → Research Worker Pool
    → PostgreSQL + pgvector
    → Object storage for raw content
```

Additional changes for scale:
1. Move to async job queue (Celery/ARQ)
2. Add Redis caching for repeated queries
3. Use PostgreSQL with proper indexing
4. Batch LLM calls where possible
5. Add observability (structured logs → Loki/Datadog)
6. Add rate limiting per IP/user

---

## AI Design Decisions

### Why a structured pipeline, not an autonomous agent?
A structured workflow is predictable, testable, easier to debug, and cheaper to run. Each step has clear inputs/outputs. An autonomous agent is appropriate when the task space is open-ended; research decomposition → search → extract → synthesize is a well-defined workflow.

### Why DuckDuckGo + Wikipedia?
Both are free, no API key required, and return real current results. Wikipedia provides high-quality structured content. DuckDuckGo covers broader web content.

### Why SQLite + ChromaDB?
SQLite is zero-config, persistent, and fully sufficient for a prototype. ChromaDB provides semantic search over findings without requiring a separate vector database service. Production would move to PostgreSQL + pgvector.

### Why not fine-tuning?
The problem requires access to external, current knowledge and full traceability of sources — not a static private behavior. RAG (retrieval-augmented generation) is the right architecture.

### How are hallucinations handled?
The synthesizer is instructed to use ONLY the provided findings. If evidence is insufficient, the system explicitly says so and assigns low confidence rather than inventing a conclusion.
