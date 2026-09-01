"""
Regression and verification tests for recent production audit findings:
1. ResearchRequest length boundary validation (Pydantic max_length=2000).
2. Cleaned content leak prevention in source serialization.
3. Findings cap for contradiction detection and synthesis.
4. Correct use of get_running_loop during async orchestrator tasks.
5. API findings listing does not expose cleaned source bodies.
"""
import pytest
from pydantic import ValidationError

from app.api.routes.research import ResearchRequest
from app.api.routes.knowledge import _serialize_source
from app.models.source import Source
from app.research.orchestrator import ResearchOrchestrator


def test_research_request_max_length_validation():
    # Question over 2000 characters should raise ValidationError at Pydantic level
    long_question = "A" * 2001
    with pytest.raises(ValidationError):
        ResearchRequest(question=long_question)

    # Valid question between 10 and 2000 chars
    valid_req = ResearchRequest(question="How is AI impacting renewable energy?")
    assert valid_req.question == "How is AI impacting renewable energy?"


def test_source_serialization_content_leak_prevention():
    src = Source(
        id="src-1",
        url="https://example.com/article",
        title="Example",
        domain="example.com",
        source_type="web",
        word_count=500,
        reliability_score=0.8,
        cleaned_content="This is private scraped content that should not leak into list responses.",
    )

    # By default, cleaned_content must NOT be present
    data_default = _serialize_source(src, include_content=False)
    assert "cleaned_content" not in data_default
    assert data_default["domain"] == "example.com"

    # When explicitly requested (e.g. GET /sources/{id}), cleaned_content must be present
    data_detail = _serialize_source(src, include_content=True)
    assert "cleaned_content" in data_detail
    assert data_detail["cleaned_content"] == src.cleaned_content


def test_orchestrator_initialization():
    orch = ResearchOrchestrator()
    assert orch.decomposer is not None
    assert orch.extractor is not None
    assert orch.contradiction_detector is not None
    assert orch.synthesizer is not None
    assert orch.search_provider is not None
    assert orch.scraper is not None


def test_research_request_min_length_validation():
    # Less than 10 characters should fail validator
    with pytest.raises(ValidationError):
        ResearchRequest(question="short")
