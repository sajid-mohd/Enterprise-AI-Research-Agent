"""
Regression and verification test suite for the end-to-end pipeline:
1. Successful finding extraction with multi-format responses (dict and list).
2. Robust handling of malformed / invalid LLM JSON.
3. LLM extraction exception handling and error propagation.
4. Short / empty source content guard.
5. Finding database persistence with valid foreign keys.
6. Classification fallback preservation (never discard valid findings).
7. Invariant: 0 findings => 0 contradictions.
8. Conclusion synthesis with evidence links.
"""
import asyncio
import uuid
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.storage.database import Base
from app.models.research_session import ResearchSession
from app.models.sub_question import SubQuestion
from app.models.source import Source
from app.models.finding import Finding
from app.ai.extractor import FindingExtractor, FindingData
from app.ai.synthesizer import ConclusionSynthesizer
from app.services.research_service import get_session_detail


@pytest.fixture
def memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()


def test_successful_finding_extraction_dict_format():
    async def run():
        extractor = FindingExtractor()
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value="""```json
        {
            "findings": [
                {"text": "AI reduced supply chain delays by 35% in logistics hubs.", "classification": "supporting", "confidence": 0.9},
                {"text": "Legacy IT systems created friction during deployment.", "classification": "contradicting", "confidence": 0.8}
            ]
        }
        ```""")

        with patch("app.ai.extractor.get_llm_provider", return_value=mock_llm):
            findings = await extractor.extract(
                source_content="A" * 200,
                subquestion="How is AI impacting logistics?",
                source_url="https://example.com/logistics",
            )

        assert len(findings) == 2
        assert findings[0].classification == "supporting"
        assert findings[0].confidence == 0.9
        assert "35%" in findings[0].text
        assert findings[1].classification == "contradicting"

    asyncio.run(run())


def test_successful_finding_extraction_raw_list_format():
    async def run():
        extractor = FindingExtractor()
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value="""[
            {"text": "Predictive maintenance algorithms decreased downtime by 20%.", "classification": "emerging", "confidence": 0.85}
        ]""")

        with patch("app.ai.extractor.get_llm_provider", return_value=mock_llm):
            findings = await extractor.extract(
                source_content="B" * 200,
                subquestion="What are maintenance trends?",
                source_url="https://example.com/maintenance",
            )

        assert len(findings) == 1
        assert findings[0].classification == "emerging"
        assert findings[0].confidence == 0.85

    asyncio.run(run())


def test_finding_extraction_invalid_classification_defaults_to_uncertain():
    async def run():
        extractor = FindingExtractor()
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value="""{
            "findings": [
                {"text": "Autonomous vehicles are being piloted in restricted zones.", "classification": "INVALID_TYPE", "confidence": 0.75}
            ]
        }""")

        with patch("app.ai.extractor.get_llm_provider", return_value=mock_llm):
            findings = await extractor.extract(
                source_content="C" * 200,
                subquestion="Are autonomous vehicles used?",
                source_url="https://example.com/av",
            )

        assert len(findings) == 1
        assert findings[0].classification == "uncertain"
        assert findings[0].confidence == 0.75

    asyncio.run(run())


def test_finding_extraction_empty_source_content_guard():
    async def run():
        extractor = FindingExtractor()
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock()

        with patch("app.ai.extractor.get_llm_provider", return_value=mock_llm):
            findings = await extractor.extract(
                source_content="Too short",
                subquestion="Any question?",
                source_url="https://example.com/short",
            )

        assert len(findings) == 0
        mock_llm.generate.assert_not_called()

    asyncio.run(run())


def test_finding_extraction_llm_exception_propagates():
    async def run():
        extractor = FindingExtractor()
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(side_effect=RuntimeError("Groq Rate Limit Exceeded"))

        with patch("app.ai.extractor.get_llm_provider", return_value=mock_llm):
            with pytest.raises(RuntimeError):
                await extractor.extract(
                    source_content="D" * 200,
                    subquestion="Test subquestion",
                    source_url="https://example.com/fail",
                )

    asyncio.run(run())


def test_finding_persistence_and_relationship(memory_db):
    session = ResearchSession(id=str(uuid.uuid4()), question="Test Session Question", status="extracting")
    memory_db.add(session)
    memory_db.commit()

    sq = SubQuestion(id=str(uuid.uuid4()), session_id=session.id, question="Sub Q 1", research_intent="Intent 1", status="completed")
    memory_db.add(sq)
    memory_db.commit()

    source = Source(
        id=str(uuid.uuid4()),
        sub_question_id=sq.id,
        url="https://example.com/data",
        title="Test Title",
        domain="example.com",
        source_type="web",
        word_count=450,
        reliability_score=0.8,
        raw_content="<html>raw</html>",
        cleaned_content="Cleaned text content",
    )
    memory_db.add(source)
    memory_db.commit()

    finding = Finding(
        id=str(uuid.uuid4()),
        source_id=source.id,
        text="Extracted factual claim about system efficiency.",
        classification="supporting",
        confidence=0.88,
    )
    memory_db.add(finding)
    memory_db.commit()

    stored_f = memory_db.query(Finding).filter(Finding.id == finding.id).first()
    assert stored_f is not None
    assert stored_f.source_id == source.id
    assert stored_f.classification == "supporting"
    assert stored_f.confidence == 0.88


def test_zero_findings_yields_zero_contradictions(memory_db):
    session = ResearchSession(id=str(uuid.uuid4()), question="Zero findings question", status="completed")
    memory_db.add(session)
    memory_db.commit()

    detail = get_session_detail(session.id, memory_db)
    assert detail is not None
    assert len(detail["findings"]) == 0
    assert len(detail["contradictions"]) == 0


def test_conclusion_synthesizer_with_evidence():
    async def run():
        synthesizer = ConclusionSynthesizer()
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value="""{
            "conclusion": "AI significantly improves supply chain operations by reducing lead times.",
            "key_points": ["Lead times reduced by 30%", "Predictive dispatch prevents stockouts"],
            "limitations": ["Integration with legacy ERP remains costly"],
            "supporting_finding_indices": [0],
            "contradicting_finding_indices": [],
            "confidence": 0.85
        }""")

        findings = [FindingData(text="Lead times reduced by 30% via AI dispatch.", classification="supporting", confidence=0.9)]

        with patch("app.ai.synthesizer.get_llm_provider", return_value=mock_llm):
            data = await synthesizer.synthesize(
                question="How does AI improve supply chain?",
                subquestions=[],
                findings=findings,
                contradictions=[],
            )

        assert "supply chain" in data.conclusion
        assert data.confidence == 0.85
        assert len(data.key_points) == 2
        assert data.supporting_finding_indices == [0]

    asyncio.run(run())
