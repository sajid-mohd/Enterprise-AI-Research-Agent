"""Unit tests for Scraper safety and SSRF protection."""
import asyncio
from app.research.scraper import Scraper, _is_safe_url


def test_safe_urls():
    assert _is_safe_url("https://en.wikipedia.org/wiki/Artificial_intelligence") is True
    assert _is_safe_url("http://example.com/article") is True


def test_reject_invalid_schemes():
    assert _is_safe_url("file:///etc/passwd") is False
    assert _is_safe_url("ftp://files.example.com") is False
    assert _is_safe_url("gopher://old.service") is False
    assert _is_safe_url("javascript:alert(1)") is False
    assert _is_safe_url("data:text/html,<h1>hi</h1>") is False


def test_reject_loopback_and_local():
    assert _is_safe_url("http://localhost/admin") is False
    assert _is_safe_url("http://127.0.0.1:8000/health") is False
    assert _is_safe_url("http://0.0.0.0:8000") is False


def test_reject_cloud_metadata_ips():
    # AWS / GCP / Azure instance metadata IP
    assert _is_safe_url("http://169.254.169.254/latest/meta-data/") is False


def test_reject_private_subnet_ips():
    # RFC 1918 private subnets
    assert _is_safe_url("http://10.0.0.1/internal") is False
    assert _is_safe_url("http://192.168.1.1/router") is False
    assert _is_safe_url("http://172.16.0.5/api") is False


def test_scraper_rejects_unsafe_fetch():
    async def run():
        scraper = Scraper()
        result = await scraper.fetch("http://127.0.0.1:8000/secret")
        assert result is None

    asyncio.run(run())
