from bs4 import BeautifulSoup
import trafilatura
from urllib.parse import urlparse

def extract_domain(url):
    try: return urlparse(url).netloc
    except: return ""

def compute_word_count(text):
    return len(text.split())

def estimate_reliability(domain, source_type, word_count):
    score = 0.5
    if source_type == "wikipedia": score = 0.75
    elif domain.endswith(".gov") or domain.endswith(".edu"): score = 0.8
    elif domain.endswith(".org"): score = 0.65
    if word_count < 200: score -= 0.1
    return score

def clean_html(html):
    res = trafilatura.extract(html)
    if not res:
        soup = BeautifulSoup(html, "html.parser")
        for s in soup(["script", "style"]): s.extract()
        res = soup.get_text()
    return res[:8000] if res else ""
