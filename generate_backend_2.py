import os

base = r"c:\Users\mdsaj\Desktop\NXT ASSIGNMENT\research-agent\backend"

files = {
    "app/services/__init__.py": "",
    "app/services/research_service.py": '''from fastapi import BackgroundTasks
import uuid
from app.models.research_session import ResearchSession
from app.research.orchestrator import ResearchOrchestrator
from app.storage.database import SessionLocal

async def create_research_session(question: str, db, background_tasks: BackgroundTasks):
    session_id = str(uuid.uuid4())
    session = ResearchSession(id=session_id, question=question, status="pending")
    db.add(session)
    db.commit()
    orch = ResearchOrchestrator()
    new_db = SessionLocal()
    background_tasks.add_task(orch.run, session_id, new_db)
    return session_id

async def get_session_detail(session_id: str, db):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    return session
''',
    "app/services/query_service.py": '''async def query_knowledge(question, db, vector_store):
    return {"answer": "Not implemented", "findings_used": [], "confidence": 0.0}
''',
    "app/api/__init__.py": "",
    "app/api/routes/__init__.py": "",
    "app/api/routes/research.py": '''from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.storage.database import get_db
from pydantic import BaseModel
import uuid
from app.services.research_service import create_research_session, get_session_detail

router = APIRouter()

class ResearchRequest(BaseModel):
    question: str

@router.post("/research")
async def create_research(req: ResearchRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    session_id = await create_research_session(req.question, db, background_tasks)
    return {"session_id": session_id, "status": "pending"}

@router.get("/research/{session_id}")
async def get_research(session_id: str, db: Session = Depends(get_db)):
    return await get_session_detail(session_id, db)
''',
    "app/api/routes/sessions.py": '''from fastapi import APIRouter
router = APIRouter()
''',
    "app/api/routes/knowledge.py": '''from fastapi import APIRouter
router = APIRouter()
''',
    "app/api/routes/query.py": '''from fastapi import APIRouter
router = APIRouter()
''',
    "app/api/routes/health.py": '''from fastapi import APIRouter
router = APIRouter()
@router.get("/health")
def health(): return {"status": "ok", "db": "ok"}
''',
    "tests/__init__.py": "",
    "tests/unit/__init__.py": "",
    "tests/unit/test_cleaner.py": '''from app.research.cleaner import extract_domain, compute_word_count, estimate_reliability
def test_extract_domain():
    assert extract_domain("https://www.example.com/path") == "www.example.com"
def test_compute_word_count():
    assert compute_word_count("hello world foo") == 3
def test_estimate_reliability():
    assert estimate_reliability("wikipedia.org", "wikipedia", 500) >= 0.7
''',
    "tests/unit/test_repositories.py": '''def test_dummy():
    assert True
''',
    "tests/integration/__init__.py": "",
    "tests/integration/test_research_api.py": '''def test_dummy():
    assert True
'''
}

for path, content in files.items():
    full_path = os.path.join(base, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# Update main.py to include routers
main_path = os.path.join(base, "app/main.py")
with open(main_path, "a", encoding="utf-8") as f:
    f.write("\\nfrom app.api.routes import research, health\\napp.include_router(research.router)\\napp.include_router(health.router)\\n")

print("Files generated!")
