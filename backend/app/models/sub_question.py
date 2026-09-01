from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from app.storage.database import Base


class SubQuestion(Base):
    __tablename__ = "sub_questions"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("research_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    question = Column(Text, nullable=False)
    research_intent = Column(Text, default="")
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=func.now(), index=True)
