"""
Query service — natural-language knowledge base queries.
Semantic search (ChromaDB) + SQL fallback + LLM answer with citations.
Supports session_id filtering for session and tenant isolation.
"""
import logging

from sqlalchemy.orm import Session

from app.ai.model import get_llm_provider, parse_json_response
from app.models.finding import Finding
from app.models.source import Source
from app.models.sub_question import SubQuestion
from app.storage.vector_store import VectorStore

logger = logging.getLogger("research_agent.services.query")

SYSTEM_PROMPT = """You are a research knowledge base assistant. Answer the user's question using ONLY the provided research findings. 
Do not add information from your training data.
If the findings don't contain enough information, say so clearly.
Always cite which finding numbers you used.

Respond ONLY with valid JSON:
{"answer": "detailed answer referencing the findings...", "confidence": 0.8}"""


async def query_knowledge(
    question: str,
    db: Session,
    vector_store: VectorStore,
    session_id: str | None = None,
) -> dict:
    """
    1. Semantic search ChromaDB for relevant findings (with optional session_id filter)
    2. SQL keyword fallback (scoped to session_id if provided)
    3. LLM synthesizes an answer with citations
    """
    question = question.strip()
    if not question:
        return {"answer": "Please provide a question.", "findings_used": [], "confidence": 0.0}

    # Semantic search with optional session_id isolation
    semantic_results = []
    try:
        semantic_results = vector_store.search_findings(
            query=question,
            n_results=10,
            session_id=session_id,
        )
    except Exception as exc:
        logger.warning("Semantic search failed: %s", exc)

    semantic_ids = {r["id"] for r in semantic_results}

    # SQL keyword fallback for words not covered by semantic search
    keywords = [w for w in question.lower().split() if len(w) > 3]
    sql_findings: list[Finding] = []
    if keywords:
        try:
            query = db.query(Finding)
            if session_id:
                subq_ids = [sq.id for sq in db.query(SubQuestion.id).filter(SubQuestion.session_id == session_id).all()]
                if subq_ids:
                    src_ids = [s.id for s in db.query(Source.id).filter(Source.sub_question_id.in_(subq_ids)).all()]
                    if src_ids:
                        query = query.filter(Finding.source_id.in_(src_ids))
                    else:
                        query = query.filter(False)
                else:
                    query = query.filter(False)

            for kw in keywords[:3]:  # Max 3 keywords
                safe_kw = kw.replace("%", "").replace("_", "")  # Sanitize SQL wildcard characters
                if safe_kw:
                    query = query.filter(Finding.text.ilike(f"%{safe_kw}%"))
            sql_findings = query.limit(10).all()
        except Exception as exc:
            logger.warning("SQL keyword search failed: %s", exc)

    # Merge: semantic results first, then SQL supplements
    all_finding_ids: list[str] = list(semantic_ids)
    for f in sql_findings:
        if f.id not in semantic_ids:
            all_finding_ids.append(f.id)

    all_finding_ids = all_finding_ids[:12]  # Cap at 12 findings for context

    if not all_finding_ids:
        msg = "No relevant findings found in the knowledge base for your question."
        if session_id:
            msg += f" (Scoped to session: {session_id})"
        else:
            msg += " Try running a research session first."
        return {
            "answer": msg,
            "findings_used": [],
            "confidence": 0.0,
        }

    # Fetch finding details with sources
    db_findings = db.query(Finding).filter(Finding.id.in_(all_finding_ids)).all()
    source_ids = list({f.source_id for f in db_findings})
    db_sources = db.query(Source).filter(Source.id.in_(source_ids)).all()
    source_map = {s.id: s for s in db_sources}

    # Build context for LLM with clear boundary demarcation
    finding_lines = []
    for i, f in enumerate(db_findings):
        src = source_map.get(f.source_id)
        src_info = f" (Source: {src.domain})" if src else ""
        finding_lines.append(f"<finding index=\"{i}\" classification=\"{f.classification}\" confidence=\"{f.confidence:.2f}\"{src_info}>\n{f.text}\n</finding>")

    prompt = (
        f"User question: {question}\n\n"
        "Available research findings:\n" + "\n".join(finding_lines) + "\n\n"
        "Answer the question using ONLY the findings above. Reference finding numbers where relevant."
    )

    try:
        llm = get_llm_provider()
        raw = await llm.generate(prompt, system=SYSTEM_PROMPT, json_mode=True)
        data = parse_json_response(raw)
        answer = str(data.get("answer", "")) if isinstance(data, dict) else ""
        confidence = float(data.get("confidence", 0.5)) if isinstance(data, dict) else 0.5
    except Exception as exc:
        logger.error("Query LLM failed: %s", exc)
        answer = "An error occurred while generating the answer from the knowledge base."
        confidence = 0.0

    findings_used = []
    for f in db_findings:
        src = source_map.get(f.source_id)
        findings_used.append({
            "finding_id": f.id,
            "text": f.text,
            "classification": f.classification,
            "confidence": f.confidence,
            "source_url": src.url if src else None,
            "source_domain": src.domain if src else None,
        })

    return {
        "answer": answer,
        "findings_used": findings_used,
        "confidence": max(0.0, min(1.0, confidence)),
    }
