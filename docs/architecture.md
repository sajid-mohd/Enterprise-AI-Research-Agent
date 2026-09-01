# Architecture — Enterprise AI Research Agent

## Overview

The system is a **five-stage AI pipeline** that converts a free-text research question into a structured, evidence-backed conclusion with full source traceability.

Each stage is independent, observable, and stored to the database — so partial results are available even if a later stage fails.

---

## System Diagram

```
User Question
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: DECOMPOSITION                                         │
│  LLM breaks question into 3-5 targeted sub-questions            │
│  SubQuestion records created in SQLite                          │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: SEARCH + SCRAPE                                       │
│  DuckDuckGo + Wikipedia → top URLs per sub-question             │
│  AsyncHTTP scrapes each URL                                     │
│  trafilatura / BeautifulSoup cleans HTML → plain text           │
│  Source records created in SQLite                               │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 3: EXTRACTION + EMBEDDING                                │
│  LLM extracts 1-5 key findings per source                       │
│  Each finding: text + classification + confidence               │
│  Classifications: supporting | contradicting | emerging |       │
│                   uncertain                                     │
│  Finding records created in SQLite                              │
│  Findings embedded → ChromaDB for semantic search              │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 4: CONTRADICTION DETECTION                               │
│  LLM compares pairs of 'contradicting'-classified findings      │
│  Identifies genuine contradictions with severity + confidence   │
│  Contradiction records created in SQLite                        │
│  Deduplication prevents A-B + B-A double counting              │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 5: SYNTHESIS                                             │
│  LLM synthesizes conclusion from all findings                   │
│  Must cite specific findings by index                           │
│  Assigns overall confidence (0.0-1.0)                           │
│  Lists key points + known limitations                           │
│  Conclusion + ConclusionFinding link records in SQLite          │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
Conclusion with full evidence traceability
```

---

## Component Architecture

### FastAPI Application (`app/main.py`)
- Async ASGI application
- Background task scheduling (FastAPI `BackgroundTasks`)
- 5 routers: research, sessions, knowledge, query, health
- CORS middleware for frontend

### AI Intelligence Layer (`app/ai/`)

| Module | Class | Role |
|---|---|---|
| `model.py` | `GroqProvider`, `GeminiProvider`, `AnthropicProvider` | LLM provider abstraction with retry logic |
| `decomposer.py` | `QuestionDecomposer` | Breaks question into sub-questions |
| `extractor.py` | `FindingExtractor` | Extracts findings from source text |
| `contradiction.py` | `ContradictionDetector` | Compares findings for conflicts |
| `synthesizer.py` | `ConclusionSynthesizer` | Synthesizes final conclusion |

### Research Engine (`app/research/`)

| Module | Role |
|---|---|
| `orchestrator.py` | Coordinates all 5 pipeline stages |
| `search.py` | DuckDuckGo + Wikipedia search |
| `scraper.py` | Async HTTP scraping with timeout |
| `cleaner.py` | HTML → plain text, reliability scoring |

### Data Layer (`app/storage/`)

| Module | Role |
|---|---|
| `database.py` | SQLAlchemy engine, SessionLocal, Base |
| `vector_store.py` | ChromaDB wrapper for semantic search |

---

## Status Flow

```
pending → decomposing → searching → extracting → analyzing → synthesizing → completed
                                                                         ↘ failed
```

Each status transition is written to `research_sessions.status` in SQLite. The frontend polls `/research/{id}` every 2 seconds to display live progress.

---

## Traceability Chain

```
Conclusion
  ↓ (ConclusionFinding table)
Finding(s)
  ↓ (Finding.source_id FK)
Source
  ↓ (Source.url)
External URL
```

Every claim in the conclusion can be traced to:
1. The specific finding text that supports it
2. The source URL that the finding was extracted from
3. The sub-question that triggered that source to be researched
4. The original research question

---

## Request Lifecycle

```
POST /research
  → Creates ResearchSession (status=pending)
  → Returns {session_id} immediately
  → Schedules background task: orchestrator.run(session_id, db)
  → Background task runs 5 stages, updating status at each step
  → Returns to client before pipeline completes

GET /research/{session_id}
  → Returns current session state including all collected data
  → Frontend polls this every 2s until status=completed|failed
```

---

## Concurrency Model

- FastAPI serves the API synchronously with async route handlers
- The research pipeline runs as a FastAPI `BackgroundTask`
- Background task gets its **own** SQLAlchemy `SessionLocal()` (not the request session)
- Synchronous operations (DB queries, search) run in a thread pool via `run_in_executor`
- ChromaDB operations are wrapped in try/except — if ChromaDB is unavailable, embedding is skipped gracefully

---

## Error Handling

| Error | Behavior |
|---|---|
| Search fails | Log warning, continue with fewer results |
| Scrape fails | Log warning, skip source, continue |
| LLM call fails | Retry up to `MAX_RETRIES` times, then raise |
| LLM returns invalid JSON | `parse_json_response()` returns `{}`, fallback behavior in each AI module |
| ChromaDB unavailable | Graceful degradation — all methods become no-ops |
| Pipeline stage fails | Mark session as `status=failed`, store error_message |
