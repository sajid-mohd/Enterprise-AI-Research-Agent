from sqlalchemy import Column, String, Text, DateTime, func
from app.storage.database import Base


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id = Column(String, primary_key=True)
    question = Column(Text, nullable=False)
    status = Column(String, default="pending", index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
