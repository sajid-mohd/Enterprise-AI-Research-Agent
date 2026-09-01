import os

base = r"c:\Users\mdsaj\Desktop\NXT ASSIGNMENT\research-agent\backend"

files = {
    "app/__init__.py": "",
    "app/core/__init__.py": "",
    "app/core/logging.py": "import logging\n\nlogging.basicConfig(level=logging.INFO)",
    "app/core/exceptions.py": "class BaseException(Exception): pass",
    "app/models/__init__.py": "from .research_session import ResearchSession\nfrom .sub_question import SubQuestion\nfrom .source import Source\nfrom .finding import Finding\nfrom .contradiction import Contradiction\nfrom .conclusion import Conclusion, ConclusionFinding",
    "app/models/research_session.py": '''from sqlalchemy import Column, String, Text, DateTime, func
from app.storage.database import Base
class ResearchSession(Base):
    __tablename__ = "research_sessions"
    id = Column(String, primary_key=True)
    question = Column(Text)
    status = Column(String)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
''',
    "app/models/sub_question.py": '''from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from app.storage.database import Base
class SubQuestion(Base):
    __tablename__ = "sub_questions"
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("research_sessions.id"))
    question = Column(Text)
    research_intent = Column(Text)
    status = Column(String)
    created_at = Column(DateTime, default=func.now())
''',
    "app/models/source.py": '''from sqlalchemy import Column, String, Text, DateTime, Integer, Float, ForeignKey, func
from app.storage.database import Base
class Source(Base):
    __tablename__ = "sources"
    id = Column(String, primary_key=True)
    sub_question_id = Column(String, ForeignKey("sub_questions.id"))
    url = Column(Text)
    title = Column(Text)
    domain = Column(String)
    source_type = Column(String)
    publication_date = Column(String, nullable=True)
    retrieved_at = Column(DateTime, default=func.now())
    raw_content = Column(Text)
    cleaned_content = Column(Text)
    word_count = Column(Integer)
    reliability_score = Column(Float, default=0.5)
''',
    "app/models/finding.py": '''from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, func
from app.storage.database import Base
class Finding(Base):
    __tablename__ = "findings"
    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("sources.id"))
    text = Column(Text)
    classification = Column(String)
    confidence = Column(Float)
    created_at = Column(DateTime, default=func.now())
''',
    "app/models/contradiction.py": '''from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, func
from app.storage.database import Base
class Contradiction(Base):
    __tablename__ = "contradictions"
    id = Column(String, primary_key=True)
    finding_a_id = Column(String, ForeignKey("findings.id"))
    finding_b_id = Column(String, ForeignKey("findings.id"))
    description = Column(Text)
    severity = Column(String)
    confidence = Column(Float)
    created_at = Column(DateTime, default=func.now())
''',
    "app/models/conclusion.py": '''from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, func
from app.storage.database import Base
class Conclusion(Base):
    __tablename__ = "conclusions"
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("research_sessions.id"), unique=True)
    text = Column(Text)
    confidence = Column(Float)
    key_points = Column(Text)
    limitations = Column(Text)
    created_at = Column(DateTime, default=func.now())

class ConclusionFinding(Base):
    __tablename__ = "conclusion_findings"
    conclusion_id = Column(String, ForeignKey("conclusions.id"), primary_key=True)
    finding_id = Column(String, ForeignKey("findings.id"), primary_key=True)
    relationship_type = Column(String)
''',
    "app/storage/__init__.py": "",
    "app/storage/database.py": '''import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)
engine = create_engine(f"sqlite:///{settings.DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
''',
    "app/storage/vector_store.py": '''import chromadb
from app.core.config import settings
import os
class VectorStore:
    def __init__(self):
        try:
            os.makedirs(settings.CHROMA_PATH, exist_ok=True)
            self.client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
            self.collection = self.client.get_or_create_collection("research_findings")
        except Exception as e:
            self.client = None
    
    def add_finding(self, finding_id, text, metadata):
        if self.client:
            self.collection.add(ids=[finding_id], documents=[text], metadatas=[metadata])
            
    def search_findings(self, query, n_results=10):
        if not self.client: return []
        res = self.collection.query(query_texts=[query], n_results=n_results)
        if not res["ids"] or not res["ids"][0]: return []
        results = []
        for i in range(len(res["ids"][0])):
            results.append({"id": res["ids"][0][i], "text": res["documents"][0][i], "metadata": res["metadatas"][0][i], "distance": res["distances"][0][i] if "distances" in res else 0})
        return results
''',
    "app/ai/__init__.py": "",
    "app/ai/model.py": '''from app.core.config import settings
import json
import asyncio

class LLMProvider:
    async def generate(self, prompt: str, system: str = "", json_mode: bool = False) -> str:
        raise NotImplementedError

class GroqProvider(LLMProvider):
    async def generate(self, prompt: str, system: str = "", json_mode: bool = False) -> str:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        for i in range(3):
            try:
                res = await client.chat.completions.create(
                    model=settings.GENERATOR_MODEL or "llama-3.1-8b-instant",
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                    response_format={"type": "json_object"} if json_mode else None
                )
                return res.choices[0].message.content
            except Exception:
                if i == 2: raise
                await asyncio.sleep(2**i)
        return ""

def get_llm_provider():
    return GroqProvider()
''',
    "app/ai/decomposer.py": '''import json
from app.ai.model import get_llm_provider
class QuestionDecomposer:
    async def decompose(self, question: str):
        llm = get_llm_provider()
        prompt = f"Decompose this into 3-5 subquestions: {question}"
        sys = "Respond ONLY with valid JSON. No explanation. format: {'subquestions': [{'id': 'sq1', 'question': '...', 'research_intent': '...'}]}"
        res = await llm.generate(prompt, sys, json_mode=True)
        try:
            return json.loads(res).get("subquestions", [])
        except:
            return []
''',
    "app/ai/extractor.py": '''import json
from app.ai.model import get_llm_provider
class FindingExtractor:
    async def extract(self, source_content, subquestion, source_url):
        llm = get_llm_provider()
        prompt = f"Extract findings for '{subquestion}' from: {source_content[:8000]}"
        sys = "Respond ONLY with valid JSON. format: {'findings': [{'text': '...', 'classification': 'supporting', 'confidence': 0.9}]}"
        res = await llm.generate(prompt, sys, json_mode=True)
        try:
            return json.loads(res).get("findings", [])
        except:
            return []
''',
    "app/ai/contradiction.py": '''import json
from app.ai.model import get_llm_provider
class ContradictionDetector:
    async def detect(self, findings):
        llm = get_llm_provider()
        findings_text = "\n".join([f"{i}. {f['text']}" for i, f in enumerate(findings)])
        prompt = f"Find contradictions in:\n{findings_text}"
        sys = "Respond ONLY with valid JSON. format: {'contradictions': [{'finding_a_index': 0, 'finding_b_index': 1, 'description': '...', 'severity': 'high', 'confidence': 0.8}]}"
        res = await llm.generate(prompt, sys, json_mode=True)
        try:
            return json.loads(res).get("contradictions", [])
        except:
            return []
''',
    "app/ai/synthesizer.py": '''import json
from app.ai.model import get_llm_provider
class ConclusionSynthesizer:
    async def synthesize(self, question, subquestions, findings, contradictions):
        llm = get_llm_provider()
        prompt = f"Synthesize a conclusion for {question}"
        sys = "Respond ONLY with valid JSON. format: {'conclusion': '...', 'key_points': [], 'limitations': [], 'supporting_finding_indices': [], 'contradicting_finding_indices': [], 'confidence': 0.8}"
        res = await llm.generate(prompt, sys, json_mode=True)
        try:
            return json.loads(res)
        except:
            return {}
''',
    "app/research/__init__.py": "",
    "app/research/search.py": '''from duckduckgo_search import DDGS
import wikipedia

class SearchProvider:
    def search(self, query): raise NotImplementedError

class MultiSearchProvider(SearchProvider):
    def search(self, query):
        results = []
        try:
            for r in DDGS().text(query, max_results=5):
                results.append({"url": r["href"], "title": r["title"], "snippet": r["body"], "source_type": "web"})
        except: pass
        try:
            for r in wikipedia.search(query, results=2):
                page = wikipedia.page(r)
                results.append({"url": page.url, "title": page.title, "snippet": page.summary, "source_type": "wikipedia"})
        except: pass
        return results
''',
    "app/research/scraper.py": '''import httpx
class Scraper:
    async def fetch(self, url):
        try:
            async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "ResearchAgent/1.0"}) as client:
                res = await client.get(url)
                if res.status_code < 400: return res.text
        except: pass
        return None
''',
    "app/research/cleaner.py": '''from bs4 import BeautifulSoup
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
''',
    "app/research/orchestrator.py": '''import uuid
from app.ai.decomposer import QuestionDecomposer
from app.research.search import MultiSearchProvider

class ResearchOrchestrator:
    async def run(self, session_id, db):
        try:
            pass # Implement full orchestrator logic here later
        except Exception as e:
            pass
''',
    "app/main.py": '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.storage.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "ok", "db": "ok"}
'''
}

for path, content in files.items():
    full_path = os.path.join(base, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Files generated!")
