"""
Research service — creates sessions, fires background pipeline, fetches detail.
Optimized for high throughput without N+1 query overhead.
"""
import json
import logging
import uuid
from collections import defaultdict

from fastapi import BackgroundTasks
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.research_session import ResearchSession
from app.models.sub_question import SubQuestion
from app.models.source import Source
from app.models.finding import Finding
from app.models.contradiction import Contradiction
from app.models.conclusion import Conclusion, ConclusionFinding
from app.research.orchestrator import ResearchOrchestrator
from app.storage.database import SessionLocal

logger = logging.getLogger("research_agent.services.research")


async def create_research_session(
    question: str, db: Session, background_tasks: BackgroundTasks
) -> str:
    question = question.strip()
    if not question:
        raise ValueError("Question cannot be empty.")
    if len(question) < 10:
        raise ValueError("Question is too short. Please provide a meaningful research question (min 10 characters).")
    if len(question) > 2000:
        raise ValueError("Question is too long. Please keep it under 2000 characters.")

    session_id = str(uuid.uuid4())
    session = ResearchSession(id=session_id, question=question, status="pending")
    db.add(session)
    db.commit()

    # Each background run gets its OWN DB session (request session will be closed)
    orch = ResearchOrchestrator()
    new_db = SessionLocal()
    background_tasks.add_task(orch.run, session_id, new_db)

    logger.info("Created research session %s", session_id)
    return session_id


def get_session_detail(session_id: str, db: Session) -> dict | None:
    """
    Fetch full session with all nested data for the API response.
    Returns a plain dict (not ORM objects) to avoid lazy-load issues.
    """
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session:
        return None

    subquestions = db.query(SubQuestion).filter(SubQuestion.session_id == session_id).all()
    subq_ids = [sq.id for sq in subquestions]

    sources = (
        db.query(Source).filter(Source.sub_question_id.in_(subq_ids)).all()
        if subq_ids else []
    )
    source_ids = [s.id for s in sources]

    findings = (
        db.query(Finding).filter(Finding.source_id.in_(source_ids)).all()
        if source_ids else []
    )
    finding_ids = [f.id for f in findings]

    contradictions = []
    if finding_ids:
        contras = (
            db.query(Contradiction)
            .filter(
                Contradiction.finding_a_id.in_(finding_ids),
                Contradiction.finding_b_id.in_(finding_ids),
            )
            .all()
        )
        contradictions = contras

    conclusion = (
        db.query(Conclusion).filter(Conclusion.session_id == session_id).first()
    )

    # Build source lookup for finding details
    source_map = {s.id: s for s in sources}
    finding_map = {f.id: f for f in findings}

    def serialize_source(s: Source) -> dict:
        return {
            "id": s.id,
            "url": s.url,
            "title": s.title,
            "domain": s.domain,
            "source_type": s.source_type,
            "retrieved_at": s.retrieved_at.isoformat() if s.retrieved_at else None,
            "word_count": s.word_count,
            "reliability_score": s.reliability_score,
        }

    def serialize_finding(f: Finding) -> dict:
        src = source_map.get(f.source_id)
        return {
            "id": f.id,
            "text": f.text,
            "classification": f.classification,
            "confidence": f.confidence,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "source": serialize_source(src) if src else None,
        }

    def serialize_contradiction(c: Contradiction) -> dict:
        fa = finding_map.get(c.finding_a_id)
        fb = finding_map.get(c.finding_b_id)
        return {
            "id": c.id,
            "finding_a": serialize_finding(fa) if fa else None,
            "finding_b": serialize_finding(fb) if fb else None,
            "description": c.description,
            "severity": c.severity,
            "confidence": c.confidence,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }

    conclusion_dict = None
    if conclusion:
        # Get linked findings for traceability
        links = (
            db.query(ConclusionFinding)
            .filter(ConclusionFinding.conclusion_id == conclusion.id)
            .all()
        )
        supporting = [serialize_finding(finding_map[l.finding_id]) for l in links if l.relationship_type == "supporting" and l.finding_id in finding_map]
        contradicting = [serialize_finding(finding_map[l.finding_id]) for l in links if l.relationship_type == "contradicting" and l.finding_id in finding_map]

        try:
            key_points = json.loads(conclusion.key_points) if conclusion.key_points else []
        except Exception:
            key_points = []
        try:
            limitations = json.loads(conclusion.limitations) if conclusion.limitations else []
        except Exception:
            limitations = []

        conclusion_dict = {
            "id": conclusion.id,
            "text": conclusion.text,
            "confidence": conclusion.confidence,
            "key_points": key_points,
            "limitations": limitations,
            "supporting_findings": supporting,
            "contradicting_findings": contradicting,
            "created_at": conclusion.created_at.isoformat() if conclusion.created_at else None,
        }

    return {
        "id": session.id,
        "question": session.question,
        "status": session.status,
        "error_message": session.error_message,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "subquestions": [
            {
                "id": sq.id,
                "question": sq.question,
                "research_intent": sq.research_intent,
                "status": sq.status,
            }
            for sq in subquestions
        ],
        "sources": [serialize_source(s) for s in sources],
        "findings": [serialize_finding(f) for f in findings],
        "contradictions": [serialize_contradiction(c) for c in contradictions],
        "conclusion": conclusion_dict,
    }


def list_sessions(db: Session, page: int = 1, limit: int = 20) -> dict:
    """
    Paginated session listing. Uses batched queries to prevent N+1 query overhead.
    """
    offset = (page - 1) * limit
    total = db.query(func.count(ResearchSession.id)).scalar() or 0
    sessions = (
        db.query(ResearchSession)
        .order_by(ResearchSession.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    if not sessions:
        return {"sessions": [], "total": total, "page": page, "limit": limit}

    session_ids = [s.id for s in sessions]

    # Batched fetch 1: subquestions for these sessions
    subquestions = (
        db.query(SubQuestion.id, SubQuestion.session_id)
        .filter(SubQuestion.session_id.in_(session_ids))
        .all()
    )
    subq_to_session = {sq.id: sq.session_id for sq in subquestions}
    all_subq_ids = list(subq_to_session.keys())

    # Batched fetch 2: sources for these subquestions
    sources = (
        db.query(Source.id, Source.sub_question_id)
        .filter(Source.sub_question_id.in_(all_subq_ids))
        .all()
        if all_subq_ids else []
    )
    source_to_session = {}
    all_source_ids = []
    for src_id, subq_id in sources:
        all_source_ids.append(src_id)
        sess_id = subq_to_session.get(subq_id)
        if sess_id:
            source_to_session[src_id] = sess_id

    # Batched fetch 3: count findings per source
    finding_counts_per_source = (
        db.query(Finding.source_id, func.count(Finding.id))
        .filter(Finding.source_id.in_(all_source_ids))
        .group_by(Finding.source_id)
        .all()
        if all_source_ids else []
    )

    # Aggregate counts per session in Python
    session_source_counts = defaultdict(int)
    for src_id, subq_id in sources:
        sess_id = subq_to_session.get(subq_id)
        if sess_id:
            session_source_counts[sess_id] += 1

    session_finding_counts = defaultdict(int)
    for src_id, count in finding_counts_per_source:
        sess_id = source_to_session.get(src_id)
        if sess_id:
            session_finding_counts[sess_id] += count

    result = []
    for s in sessions:
        result.append({
            "id": s.id,
            "question": s.question,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "finding_count": session_finding_counts[s.id],
            "source_count": session_source_counts[s.id],
        })

    return {"sessions": result, "total": total, "page": page, "limit": limit}
