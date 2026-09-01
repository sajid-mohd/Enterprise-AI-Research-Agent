"""Query route — POST /query for natural-language knowledge base queries."""
import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.storage.database import get_db
from app.storage.vector_store import VectorStore
from app.services.query_service import query_knowledge

logger = logging.getLogger("research_agent.api.query")
router = APIRouter()

_vector_store_instance: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    session_id: str | None = None


@router.post("/query")
async def query(req: QueryRequest, db: Session = Depends(get_db)):
    """Natural-language query against the stored knowledge base with optional session isolation."""
    vs = get_vector_store()
    result = await query_knowledge(
        question=req.question,
        db=db,
        vector_store=vs,
        session_id=req.session_id,
    )
    return result
