"""
Multi-source search provider (DuckDuckGo web search + Wikipedia).
"""
import logging
import re
from abc import ABC, abstractmethod

logger = logging.getLogger("research_agent.search")

# Configure Wikipedia User-Agent to avoid Wikimedia API 403 Forbidden
try:
    import wikipedia
    wikipedia.set_user_agent("EnterpriseResearchAgent/1.0 (research@enterprise-agent.io)")
except Exception as e:
    logger.warning("Could not set Wikipedia User-Agent: %s", e)


def _clean_search_query(query: str) -> str:
    """Clean and simplify research sub-questions for search engines."""
    # Remove special characters, question marks, quotes
    q = re.sub(r"[?\"'“”‘’\(\)\[\]]", " ", query).strip()
    q = re.sub(r"\s+", " ", q)
    # If query is too long (> 12 words), keep the most informative words
    words = q.split()
    if len(words) > 10:
        # Keep first 10 words
        q = " ".join(words[:10])
    return q


class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str) -> list[dict]:
        """Returns list of dicts: {"url": str, "title": str, "snippet": str, "source_type": str}"""
        ...


class DuckDuckGoProvider(SearchProvider):
    def search(self, query: str, max_results: int = 5) -> list[dict]:
        results = []
        clean_q = _clean_search_query(query)
        try:
            from duckduckgo_search import DDGS
            with DDGS(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as ddgs:
                raw = list(ddgs.text(clean_q, max_results=max_results))
                if not raw and clean_q != query:
                    raw = list(ddgs.text(query[:80], max_results=max_results))
                if raw:
                    for r in raw:
                        href = r.get("href") or r.get("link")
                        title = r.get("title", "")
                        body = r.get("body") or r.get("snippet", "")
                        if href:
                            results.append({
                                "url": href,
                                "title": title,
                                "snippet": body,
                                "source_type": "web",
                            })
        except Exception as exc:
            logger.warning("DuckDuckGo search error for query '%s': %s", clean_q, exc)
        return results


class WikipediaProvider(SearchProvider):
    def search(self, query: str, max_results: int = 2) -> list[dict]:
        results = []
        clean_q = _clean_search_query(query)
        try:
            import wikipedia
            titles = wikipedia.search(clean_q, results=max_results)
            if not titles and len(clean_q.split()) > 4:
                # Try shorter 3-word query
                short_q = " ".join(clean_q.split()[:3])
                titles = wikipedia.search(short_q, results=max_results)

            for title in titles:
                try:
                    page = wikipedia.page(title, auto_suggest=False)
                    results.append({
                        "url": page.url,
                        "title": page.title,
                        "snippet": page.summary[:1000] if hasattr(page, "summary") else "",
                        "source_type": "wikipedia",
                    })
                except wikipedia.exceptions.DisambiguationError as dis_err:
                    if dis_err.options:
                        try:
                            first_opt = dis_err.options[0]
                            page = wikipedia.page(first_opt, auto_suggest=False)
                            results.append({
                                "url": page.url,
                                "title": page.title,
                                "snippet": page.summary[:1000] if hasattr(page, "summary") else "",
                                "source_type": "wikipedia",
                            })
                        except Exception:
                            continue
                except (wikipedia.exceptions.PageError, Exception) as exc:
                    logger.debug("Wikipedia page retrieval failed for '%s': %s", title, exc)
                    continue
        except Exception as exc:
            logger.warning("Wikipedia search error for query '%s': %s", clean_q, exc)
        return results


class MultiSearchProvider(SearchProvider):
    def __init__(self):
        self.ddg = DuckDuckGoProvider()
        self.wiki = WikipediaProvider()

    def search(self, query: str) -> list[dict]:
        results = []
        seen_urls: set[str] = set()

        # 1. DuckDuckGo web results
        for r in self.ddg.search(query, max_results=4):
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                results.append(r)

        # 2. Wikipedia authoritative results
        for r in self.wiki.search(query, max_results=2):
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                results.append(r)

        logger.info("Search query '%s' yielded %d unique results", query, len(results))
        return results
