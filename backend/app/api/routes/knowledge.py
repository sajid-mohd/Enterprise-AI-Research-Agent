"""Knowledge routes — findings, sources, contradictions."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.storage.database import get_db
from app.models.finding import Finding
from app.models.source import Source
from app.models.contradiction import Contradiction
from app.models.sub_question import SubQuestion

logger = logging.getLogger("research_agent.api.knowledge")
router = APIRouter()


def _serialize_source(s: Source, include_content: bool = False) -> dict:
    data = {
        "id": s.id,
        "url": s.url,
        "title": s.title,
        "domain": s.domain,
        "source_type": s.source_type,
        "retrieved_at": s.retrieved_at.isoformat() if s.retrieved_at else None,
        "word_count": s.word_count,
        "reliability_score": s.reliability_score,
    }
    if include_content:
        data["cleaned_content"] = s.cleaned_content
    return data


def _serialize_finding(f: Finding, source_map: dict = None) -> dict:
    src = (source_map or {}).get(f.source_id)
    return {
        "id": f.id,
        "text": f.text,
        "classification": f.classification,
        "confidence": f.confidence,
        "created_at": f.created_at.isoformat() if f.created_at else None,
        "source": {
            "id": src.id,
            "url": src.url,
            "title": src.title,
            "domain": src.domain,
        } if src else None,
    }


@router.get("/findings")
def list_findings(
    classification: str | None = Query(default=None),
    session_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List findings with optional filters."""
    query = db.query(Finding)

    if session_id:
        # Filter by session: find source_ids → finding_ids
        subq_ids = [sq.id for sq in db.query(SubQuestion).filter(SubQuestion.session_id == session_id).all()]
        if not subq_ids:
            return {"findings": []}
        source_ids = [s.id for s in db.query(Source).filter(Source.sub_question_id.in_(subq_ids)).all()]
        if not source_ids:
            return {"findings": []}
        query = query.filter(Finding.source_id.in_(source_ids))

    if classification:
        query = query.filter(Finding.classification == classification)

    findings = query.order_by(Finding.created_at.desc()).limit(limit).all()
    source_ids = list({f.source_id for f in findings})
    sources = db.query(Source).filter(Source.id.in_(source_ids)).all()
    source_map = {s.id: s for s in sources}

    return {"findings": [_serialize_finding(f, source_map) for f in findings]}


@router.get("/findings/{finding_id}")
def get_finding(finding_id: str, db: Session = Depends(get_db)):
    f = db.query(Finding).filter(Finding.id == finding_id).first()
    if not f:
        raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found.")
    src = db.query(Source).filter(Source.id == f.source_id).first()
    return _serialize_finding(f, {f.source_id: src} if src else {})


@router.get("/sources/{source_id}")
def get_source(source_id: str, db: Session = Depends(get_db)):
    src = db.query(Source).filter(Source.id == source_id).first()
    if not src:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found.")
    findings = db.query(Finding).filter(Finding.source_id == source_id).all()
    data = _serialize_source(src, include_content=True)
    data["findings"] = [_serialize_finding(f) for f in findings]
    return data


@router.get("/contradictions")
def list_contradictions(
    session_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """List all contradictions, optionally filtered by session."""
    if session_id:
        subq_ids = [sq.id for sq in db.query(SubQuestion).filter(SubQuestion.session_id == session_id).all()]
        source_ids = [s.id for s in db.query(Source).filter(Source.sub_question_id.in_(subq_ids)).all()] if subq_ids else []
        finding_ids = [f.id for f in db.query(Finding).filter(Finding.source_id.in_(source_ids)).all()] if source_ids else []
        if not finding_ids:
            return {"contradictions": []}
        contradictions = db.query(Contradiction).filter(
            Contradiction.finding_a_id.in_(finding_ids),
            Contradiction.finding_b_id.in_(finding_ids),
        ).all()
    else:
        contradictions = db.query(Contradiction).order_by(Contradiction.created_at.desc()).limit(100).all()

    all_finding_ids = list({c.finding_a_id for c in contradictions} | {c.finding_b_id for c in contradictions})
    findings = db.query(Finding).filter(Finding.id.in_(all_finding_ids)).all()
    source_ids = list({f.source_id for f in findings})
    sources = db.query(Source).filter(Source.id.in_(source_ids)).all()
    source_map = {s.id: s for s in sources}
    finding_map = {f.id: _serialize_finding(f, source_map) for f in findings}

    result = []
    for c in contradictions:
        fa = finding_map.get(c.finding_a_id)
        fb = finding_map.get(c.finding_b_id)
        if fa and fb:
            result.append({
                "id": c.id,
                "finding_a": fa,
                "finding_b": fb,
                "description": c.description,
                "severity": c.severity,
                "confidence": c.confidence,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            })
    return {"contradictions": result}


@router.get("/contradictions/{contradiction_id}")
def get_contradiction(contradiction_id: str, db: Session = Depends(get_db)):
    c = db.query(Contradiction).filter(Contradiction.id == contradiction_id).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Contradiction {contradiction_id} not found.")
    findings = db.query(Finding).filter(Finding.id.in_([c.finding_a_id, c.finding_b_id])).all()
    source_ids = list({f.source_id for f in findings})
    sources = db.query(Source).filter(Source.id.in_(source_ids)).all()
    source_map = {s.id: s for s in sources}
    finding_map = {f.id: _serialize_finding(f, source_map) for f in findings}
    return {
        "id": c.id,
        "finding_a": finding_map.get(c.finding_a_id),
        "finding_b": finding_map.get(c.finding_b_id),
        "description": c.description,
        "severity": c.severity,
        "confidence": c.confidence,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }
