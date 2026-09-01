"""Health check route."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.storage.database import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)):
    """System health check — verifies DB connection."""
    db_status = "ok"
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception as exc:
        db_status = f"error: {exc}"

    vector_status = "ok"
    try:
        from app.storage.vector_store import VectorStore
        vs = VectorStore()
        if vs.client is None:
            vector_status = "unavailable"
    except Exception as exc:
        vector_status = f"error: {exc}"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "db": db_status,
        "vector_store": vector_status,
        "provider": settings.PROVIDER,
    }
