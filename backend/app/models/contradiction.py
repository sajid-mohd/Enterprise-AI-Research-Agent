from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, func
from app.storage.database import Base


class Contradiction(Base):
    __tablename__ = "contradictions"

    id = Column(String, primary_key=True)
    finding_a_id = Column(String, ForeignKey("findings.id", ondelete="CASCADE"), index=True, nullable=False)
    finding_b_id = Column(String, ForeignKey("findings.id", ondelete="CASCADE"), index=True, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, default="medium", index=True)
    confidence = Column(Float, default=0.7)
    created_at = Column(DateTime, default=func.now(), index=True)
