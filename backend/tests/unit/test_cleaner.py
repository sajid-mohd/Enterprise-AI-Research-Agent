"""Unit tests for the cleaner module — no external calls needed."""
from app.research.cleaner import (
    extract_domain,
    compute_word_count,
    estimate_reliability,
    clean_html,
)


def test_extract_domain():
    assert extract_domain("https://www.example.com/path") == "www.example.com"


def test_extract_domain_no_scheme():
    # Graceful with bare domain
    result = extract_domain("example.com")
    assert "example.com" in result or result == ""


def test_compute_word_count():
    assert compute_word_count("hello world foo") == 3


def test_compute_word_count_empty():
    assert compute_word_count("") == 0


def test_estimate_reliability_wikipedia():
    score = estimate_reliability("en.wikipedia.org", "wikipedia", 500)
    assert score >= 0.7


def test_estimate_reliability_gov():
    score = estimate_reliability("cdc.gov", "web", 500)
    assert score >= 0.75


def test_estimate_reliability_default():
    score = estimate_reliability("someblog.com", "web", 300)
    assert 0.0 <= score <= 1.0


def test_estimate_reliability_low_word_count():
    score_high = estimate_reliability("example.com", "web", 500)
    score_low = estimate_reliability("example.com", "web", 100)
    assert score_low <= score_high


def test_clean_html_strips_tags():
    html = "<html><body><p>Hello world</p><script>alert(1)</script></body></html>"
    result = clean_html(html)
    assert "Hello world" in result
    assert "<script>" not in result
    assert "alert(1)" not in result


def test_clean_html_truncates():
    big_html = "<p>" + ("word " * 10000) + "</p>"
    result = clean_html(big_html)
    assert len(result) <= 8001  # Small buffer for truncation
