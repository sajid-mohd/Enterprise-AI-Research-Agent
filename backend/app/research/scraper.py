"""
Web scraper with SSRF protection, size limits, and timeout controls.
"""
import ipaddress
import logging
import socket
from urllib.parse import urlparse

import httpx

from app.core.config import settings

logger = logging.getLogger("research_agent.scraper")

MAX_CONTENT_BYTES = 2 * 1024 * 1024  # 2MB max download per source


def _is_safe_url(url: str) -> bool:
    """Validate that the URL is HTTP/HTTPS and does not target internal/private networks (SSRF prevention)."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # Block localhost aliases
        lower_host = hostname.lower()
        if lower_host in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return False

        # Check if the hostname is a direct IP address
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                return False
        except ValueError:
            # It's a domain name - resolve to check IP
            try:
                resolved_ips = socket.getaddrinfo(hostname, None)
                for res in resolved_ips:
                    ip_str = res[4][0]
                    ip = ipaddress.ip_address(ip_str)
                    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                        return False
            except socket.gaierror:
                return False

        return True
    except Exception as exc:
        logger.warning("URL safety check failed for %s: %s", url, exc)
        return False


class Scraper:
    async def fetch(self, url: str) -> str | None:
        """Fetch page text content safely. Returns None on failure or if URL is unsafe."""
        if not url or not _is_safe_url(url):
            logger.warning("Rejected unsafe or malformed URL: %s", url)
            return None

        timeout = getattr(settings, "SCRAPER_TIMEOUT", 15)
        headers = {
            "User-Agent": "ResearchAgent/1.0 (+https://github.com/enterprise-ai/research-agent)",
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                headers=headers,
                follow_redirects=True,
                max_redirects=3,
            ) as client:
                response = await client.get(url)
                if response.status_code >= 400:
                    logger.debug("Fetch returned status %d for %s", response.status_code, url)
                    return None

                # Check Content-Type (prefer HTML and text)
                content_type = response.headers.get("Content-Type", "").lower()
                if "application/pdf" in content_type or "image/" in content_type or "video/" in content_type:
                    logger.debug("Skipping non-text Content-Type: %s for %s", content_type, url)
                    return None

                # Enforce max size limit
                content_bytes = response.content[:MAX_CONTENT_BYTES]
                return content_bytes.decode("utf-8", errors="replace")

        except httpx.TimeoutException:
            logger.warning("Timeout fetching %s (exceeded %ds)", url, timeout)
            return None
        except httpx.RequestError as exc:
            logger.warning("Request error fetching %s: %s", url, exc)
            return None
        except Exception as exc:
            logger.warning("Unexpected error fetching %s: %s", url, exc)
            return None
