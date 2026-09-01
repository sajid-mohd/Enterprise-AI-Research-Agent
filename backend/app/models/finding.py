from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, func
from app.storage.database import Base


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("sources.id", ondelete="CASCADE"), index=True, nullable=False)
    text = Column(Text, nullable=False)
    classification = Column(String, default="uncertain", index=True)
    confidence = Column(Float, default=0.5)
    created_at = Column(DateTime, default=func.now(), index=True)
