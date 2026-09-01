"""Research routes — POST /research, GET /research/{id}"""
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.storage.database import get_db
from app.services.research_service import create_research_session, get_session_detail

logger = logging.getLogger("research_agent.api.research")
router = APIRouter()


class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) < 10:
            raise ValueError("Question must be at least 10 characters.")
        return v


@router.post("/research")
async def start_research(
    req: ResearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Submit a research question. Returns a session ID immediately."""
    try:
        session_id = await create_research_session(req.question, db, background_tasks)
        return {"session_id": session_id, "status": "pending"}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed to create research session: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to start research.")


@router.get("/research/{session_id}")
def get_research(session_id: str, db: Session = Depends(get_db)):
    """Get full session detail including sub-questions, sources, findings, contradictions, conclusion."""
    detail = get_session_detail(session_id, db)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    return detail
