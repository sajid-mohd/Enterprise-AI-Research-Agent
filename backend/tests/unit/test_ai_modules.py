"""Unit tests for AI reasoning modules (Decomposer, Extractor, Contradiction, Synthesizer)."""
import asyncio
from unittest.mock import AsyncMock, patch
from app.ai.decomposer import QuestionDecomposer
from app.ai.extractor import FindingExtractor
from app.ai.contradiction import ContradictionDetector
from app.ai.synthesizer import ConclusionSynthesizer


def test_decomposer_successful_llm():
    async def run():
        decomposer = QuestionDecomposer()
        mock_json = '{"subquestions": [{"id": "sq1", "question": "Adoption metrics?", "research_intent": "Quantify adoption"}, {"id": "sq2", "question": "Key risks?", "research_intent": "Assess risk"}]}'

        with patch("app.ai.decomposer.get_llm_provider") as mock_get_llm:
            mock_provider = AsyncMock()
            mock_provider.generate.return_value = mock_json
            mock_get_llm.return_value = mock_provider

            subqs = await decomposer.decompose("How is AI transforming healthcare?")
            assert len(subqs) == 2
            assert subqs[0].question == "Adoption metrics?"
            assert subqs[0].research_intent == "Quantify adoption"

    asyncio.run(run())


def test_decomposer_fallback_on_error():
    async def run():
        decomposer = QuestionDecomposer()

        with patch("app.ai.decomposer.get_llm_provider") as mock_get_llm:
            mock_provider = AsyncMock()
            mock_provider.generate.side_effect = RuntimeError("API Rate Limit")
            mock_get_llm.return_value = mock_provider

            subqs = await decomposer.decompose("What are quantum computing applications?")
            assert len(subqs) == 4
            assert "quantum computing applications" in subqs[0].question

    asyncio.run(run())


def test_extractor_filters_short_content():
    async def run():
        extractor = FindingExtractor()
        # Content under 100 chars should immediately return empty list without calling LLM
        findings = await extractor.extract(
            source_content="Too short.",
            subquestion="What are benefits?",
            source_url="https://example.com",
        )
        assert findings == []

    asyncio.run(run())


def test_extractor_parses_findings():
    async def run():
        extractor = FindingExtractor()
        mock_json = '{"findings": [{"text": "AI reduced supply chain delays by 35% in 2024.", "classification": "supporting", "confidence": 0.92}, {"text": "High cost remains an obstacle for 45% of SMBs.", "classification": "contradicting", "confidence": 0.85}]}'

        with patch("app.ai.extractor.get_llm_provider") as mock_get_llm:
            mock_provider = AsyncMock()
            mock_provider.generate.return_value = mock_json
            mock_get_llm.return_value = mock_provider

            findings = await extractor.extract(
                source_content="A long report detailing supply chain transformations and challenges with substantial text for testing.",
                subquestion="Impact on supply chains?",
                source_url="https://example.com/logistics",
            )
            assert len(findings) == 2
            assert findings[0].classification == "supporting"
            assert findings[0].confidence == 0.92
            assert findings[1].classification == "contradicting"

    asyncio.run(run())


def test_contradiction_detector_validates_indices():
    async def run():
        detector = ContradictionDetector()
        findings = [
            {"text": "Costs decreased by 20% in 2024.", "classification": "supporting"},
            {"text": "Costs increased by 15% during the same period.", "classification": "contradicting"},
            {"text": "Staff size remained unchanged.", "classification": "uncertain"},
        ]
        mock_json = '{"contradictions": [{"finding_a_index": 0, "finding_b_index": 1, "description": "Opposing cost trends.", "severity": "high", "confidence": 0.95}, {"finding_a_index": 0, "finding_b_index": 99, "description": "Invalid index", "severity": "low", "confidence": 0.5}]}'

        with patch("app.ai.contradiction.get_llm_provider") as mock_get_llm:
            mock_provider = AsyncMock()
            mock_provider.generate.return_value = mock_json
            mock_get_llm.return_value = mock_provider

            contras = await detector.detect(findings)
            # Should keep valid pair (0, 1) and filter out out-of-range index 99
            assert len(contras) == 1
            assert contras[0].finding_a_index == 0
            assert contras[0].finding_b_index == 1
            assert contras[0].severity == "high"

    asyncio.run(run())


def test_synthesizer_empty_findings():
    async def run():
        synthesizer = ConclusionSynthesizer()
        conclusion = await synthesizer.synthesize(
            question="What is the impact of AI?",
            subquestions=[],
            findings=[],
            contradictions=[],
        )
        assert conclusion.confidence == 0.0
        assert "insufficient" in conclusion.conclusion.lower()

    asyncio.run(run())
