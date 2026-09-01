# Demo Script — Enterprise AI Research Agent

## Setup (5 minutes before demo)

```bash
# 1. Start the backend
cd research-agent/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 2. Verify backend is healthy
curl http://localhost:8000/health
# Expected: {"status":"ok","db":"ok","vector_store":"ok","provider":"groq"}

# 3. Start the frontend (separate terminal)
cd research-agent/frontend
npm run dev
# Opens http://localhost:5173
```

---

## Demo Flow (10-15 minutes)

### 1. Show the Homepage (Dashboard)
Open `http://localhost:5173`.
- Point out: "This is the Dashboard showing all past research sessions."
- If no sessions yet: "It starts empty because all research is dynamic — nothing is pre-loaded."

### 2. Start a Live Research Session

Navigate to **Research Console** (`/research`).

Enter this question (or let the evaluator enter their own):

> **"What are the key challenges in deploying large language models in production enterprise environments?"**

Click **Start Research**.

**Narrate what's happening in real time:**
1. "The system is now decomposing this into specific sub-questions..."
2. "Now it's searching DuckDuckGo and Wikipedia for each sub-question..."
3. "The AI is extracting findings from each web page it scraped..."
4. "Now it's detecting contradictions between findings from different sources..."
5. "Finally, it's synthesizing a conclusion..."

The frontend shows a live progress indicator updating every 2 seconds.

### 3. Show the Full Results

Once complete (typically 60-120 seconds), click **View Full Results**.

Walk through each section:

**a) Executive Synthesis**
- "This is the AI's conclusion based solely on the evidence it collected."
- "The confidence score tells us how strongly the evidence supports this conclusion."

**b) Traceability Chain**
- "Every claim traces back to a specific finding."
- "Every finding traces back to a source URL."
- "The evaluator can click through to verify any claim."

**c) Research Vectors (Sub-questions)**
- "The AI broke the original question into these 4-5 targeted search vectors."

**d) Key Findings (filtered by classification)**
- Show the filter buttons: Supporting / Contradicting / Emerging / Uncertain
- "Notice the system doesn't just collect positive evidence — it actively looks for contradictions."

**e) Conflicting Information**
- "This is where the system is more sophisticated than a simple summarizer."
- "It detected genuine disagreements between sources and reported them transparently."

**f) Sources Analyzed**
- "These are real web pages and Wikipedia articles that were retrieved and processed."
- Click a source to see its domain, reliability score, and the findings extracted from it.

### 4. Demonstrate the Knowledge Query

Navigate to **Query Knowledge** (`/query`).

Enter: **"What do experts say about GPU memory requirements for production LLM deployment?"**

Show that:
- The answer is generated from the research already done — no new web search
- The findings used are cited below the answer
- This demonstrates the persistent knowledge base aspect

### 5. Surprise Record Test (if evaluator requests)

Let the evaluator enter **any brand-new question** in the Research Console. The system will:
1. Process it from scratch with no pre-loaded data
2. Search real URLs in real time
3. Extract findings from real web content
4. Detect real contradictions
5. Produce a real conclusion

**Key point to make**: "This works for any question — it's not a demo shortcut."

### 6. Show the API (optional, for technical evaluators)

Open `http://localhost:8000/docs` in a browser.

Demonstrate:
- `POST /research` — show the request/response
- `GET /sessions` — show session list
- `GET /research/{id}` — show full nested data structure
- `POST /query` — show semantic knowledge query

---

## Talking Points

### "Why is this enterprise-grade?"

1. **Structured pipeline** — not a black box; each step is observable and logged
2. **Persistent knowledge** — research is stored permanently, queryable semantically
3. **Source traceability** — every conclusion can be traced to its evidence
4. **Contradiction detection** — actively identifies conflicting evidence
5. **Confidence scoring** — quantified uncertainty, not false certainty
6. **Scalability path** — SQLite → PostgreSQL, background tasks → Celery queue

### "How does it avoid hallucination?"

- The synthesizer prompt explicitly states: "Use ONLY the provided findings. Do not add information from your training data."
- Low confidence assigned when evidence is thin
- Sources are traceable — false claims would be caught by checking the source URL

### "What happens if a source returns bad data?"

- `scraper.py` has a 15-second timeout per URL
- `cleaner.py` uses trafilatura (best-in-class HTML extractor) with BeautifulSoup fallback
- Short/thin content is penalized in reliability scoring
- If fewer sources are found, the pipeline continues with what it has

### "What about rate limits?"

- DuckDuckGo: No API key needed, but may throttle rapid requests. `MAX_SOURCES_PER_SUBQUESTION=3` limits volume.
- LLM: Groq's free tier allows ~60 requests/minute. The pipeline uses ~15 LLM calls per session.

---

## Emergency Fallback

If internet is unavailable:
```bash
# Restart with a pre-run session ID from earlier
GET http://localhost:8000/research/{previous_session_id}
```

Previously completed research is stored in SQLite and remains fully viewable without internet access.
