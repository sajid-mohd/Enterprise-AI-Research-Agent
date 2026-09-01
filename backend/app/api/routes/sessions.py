"""Sessions routes — GET /sessions, GET /sessions/{id}"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.storage.database import get_db
from app.services.research_service import list_sessions, get_session_detail

router = APIRouter()


@router.get("/sessions")
def get_sessions(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Paginated list of all research sessions."""
    return list_sessions(db, page=page, limit=limit)


@router.get("/sessions/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    """Full session detail (same as /research/{id})."""
    detail = get_session_detail(session_id, db)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    return detail
