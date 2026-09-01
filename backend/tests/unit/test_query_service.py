"""Unit tests for query_service including tenant and session isolation."""
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.storage.database import Base
from app.models.research_session import ResearchSession
from app.models.sub_question import SubQuestion
from app.models.source import Source
from app.models.finding import Finding
from app.services.query_service import query_knowledge


def setup_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_query_knowledge_empty_question():
    async def run():
        db = setup_db()
        mock_vs = MagicMock()
        res = await query_knowledge("", db, mock_vs)
        assert res["confidence"] == 0.0
        assert "Please provide a question" in res["answer"]
        db.close()

    asyncio.run(run())


def test_query_knowledge_with_session_isolation():
    async def run():
        db = setup_db()
        # Create session 1
        s1_id = str(uuid.uuid4())
        s1 = ResearchSession(id=s1_id, question="Healthcare AI?", status="completed")
        db.add(s1)
        sq1 = SubQuestion(id=str(uuid.uuid4()), session_id=s1_id, question="Diag accuracy?", research_intent="x", status="completed")
        db.add(sq1)
        src1 = Source(id=str(uuid.uuid4()), sub_question_id=sq1.id, url="https://cdc.gov/ai", title="CDC", domain="cdc.gov", source_type="web", word_count=500)
        db.add(src1)
        f1 = Finding(id=str(uuid.uuid4()), source_id=src1.id, text="Diagnostic accuracy increased by 18% in radiology.", classification="supporting", confidence=0.9)
        db.add(f1)

        # Create session 2
        s2_id = str(uuid.uuid4())
        s2 = ResearchSession(id=s2_id, question="Finance AI?", status="completed")
        db.add(s2)
        sq2 = SubQuestion(id=str(uuid.uuid4()), session_id=s2_id, question="Fraud detection?", research_intent="y", status="completed")
        db.add(sq2)
        src2 = Source(id=str(uuid.uuid4()), sub_question_id=sq2.id, url="https://sec.gov/ai", title="SEC", domain="sec.gov", source_type="web", word_count=600)
        db.add(src2)
        f2 = Finding(id=str(uuid.uuid4()), source_id=src2.id, text="Fraud detection caught 40% more anomalies.", classification="supporting", confidence=0.85)
        db.add(f2)
        db.commit()

        mock_vs = MagicMock()
        mock_vs.search_findings.return_value = []

        with patch("app.services.query_service.get_llm_provider") as mock_get_llm:
            mock_provider = AsyncMock()
            mock_provider.generate.return_value = '{"answer": "Radiology diagnostic accuracy improved by 18%.", "confidence": 0.9}'
            mock_get_llm.return_value = mock_provider

            # Query scoped to Session 1 only
            res = await query_knowledge(
                question="accuracy radiology",
                db=db,
                vector_store=mock_vs,
                session_id=s1_id,
            )

            assert len(res["findings_used"]) == 1
            assert res["findings_used"][0]["finding_id"] == f1.id
            assert res["findings_used"][0]["source_domain"] == "cdc.gov"

        db.close()

    asyncio.run(run())
