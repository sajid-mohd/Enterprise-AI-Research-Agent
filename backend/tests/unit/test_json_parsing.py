"""Unit tests for robust LLM JSON parsing and extraction."""
from app.ai.model import parse_json_response, _extract_json_candidate


def test_parse_direct_json():
    text = '{"name": "test", "val": 123}'
    res = parse_json_response(text)
    assert res == {"name": "test", "val": 123}


def test_parse_markdown_fence_json():
    text = '```json\n{"name": "test", "val": 123}\n```'
    res = parse_json_response(text)
    assert res == {"name": "test", "val": 123}


def test_parse_markdown_fence_no_lang():
    text = '```\n[{"id": "sq1", "question": "What is AI?"}]\n```'
    res = parse_json_response(text)
    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0]["id"] == "sq1"


def test_parse_conversational_prefix_and_suffix():
    text = """Certainly! Here is the JSON response you requested:
```json
{
  "subquestions": [
    {"id": "sq1", "question": "Adoption rate?", "research_intent": "Understand scope"}
  ]
}
```
Let me know if you need anything else!"""
    res = parse_json_response(text)
    assert isinstance(res, dict)
    assert "subquestions" in res
    assert len(res["subquestions"]) == 1


def test_parse_bare_conversational_wrapper():
    text = 'Sure thing, here you go: {"status": "success", "items": [1, 2, 3]} - hope that helps.'
    res = parse_json_response(text)
    assert isinstance(res, dict)
    assert res == {"status": "success", "items": [1, 2, 3]}


def test_parse_trailing_commas():
    text = '{"items": ["a", "b",], "total": 2,}'
    res = parse_json_response(text)
    assert isinstance(res, dict)
    assert res.get("total") == 2
    assert res.get("items") == ["a", "b"]


def test_parse_empty_string():
    assert parse_json_response("") == {}
    assert parse_json_response("   ") == {}


def test_parse_completely_invalid():
    text = "Sorry, I cannot fulfill this request as an AI assistant."
    res = parse_json_response(text)
    assert res == {}
