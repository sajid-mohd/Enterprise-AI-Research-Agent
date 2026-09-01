from sqlalchemy import Column, String, Text, DateTime, Integer, Float, ForeignKey, func
from app.storage.database import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(String, primary_key=True)
    sub_question_id = Column(String, ForeignKey("sub_questions.id", ondelete="CASCADE"), index=True, nullable=False)
    url = Column(Text, nullable=False)
    title = Column(Text, default="")
    domain = Column(String, index=True, default="")
    source_type = Column(String, default="web")
    publication_date = Column(String, nullable=True)
    retrieved_at = Column(DateTime, default=func.now(), index=True)
    raw_content = Column(Text, default="")
    cleaned_content = Column(Text, default="")
    word_count = Column(Integer, default=0)
    reliability_score = Column(Float, default=0.5)
