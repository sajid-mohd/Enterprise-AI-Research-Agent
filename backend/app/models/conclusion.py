from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, func
from app.storage.database import Base


class Conclusion(Base):
    __tablename__ = "conclusions"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("research_sessions.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    text = Column(Text, nullable=False)
    confidence = Column(Float, default=0.5)
    key_points = Column(Text, default="[]")
    limitations = Column(Text, default="[]")
    created_at = Column(DateTime, default=func.now(), index=True)


class ConclusionFinding(Base):
    __tablename__ = "conclusion_findings"

    conclusion_id = Column(String, ForeignKey("conclusions.id", ondelete="CASCADE"), primary_key=True, index=True)
    finding_id = Column(String, ForeignKey("findings.id", ondelete="CASCADE"), primary_key=True, index=True)
    relationship_type = Column(String, default="supporting")
