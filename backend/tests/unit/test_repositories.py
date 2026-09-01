"""Unit tests for repositories using in-memory SQLite."""
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.storage.database import Base
from app.models.research_session import ResearchSession
from app.models.sub_question import SubQuestion
from app.models.source import Source
from app.models.finding import Finding
from app.models.conclusion import Conclusion, ConclusionFinding
from app.models.contradiction import Contradiction


def make_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine


def make_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()


def test_create_and_get_session():
    engine = make_engine()
    db = make_session(engine)
    session_id = str(uuid.uuid4())
    s = ResearchSession(id=session_id, question="Test question?", status="pending")
    db.add(s)
    db.commit()

    found = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    assert found is not None
    assert found.question == "Test question?"
    assert found.status == "pending"
    db.close()


def test_create_sub_question():
    engine = make_engine()
    db = make_session(engine)
    session_id = str(uuid.uuid4())
    s = ResearchSession(id=session_id, question="Q?", status="pending")
    db.add(s)

    sq_id = str(uuid.uuid4())
    sq = SubQuestion(id=sq_id, session_id=session_id, question="Sub Q?", research_intent="test", status="pending")
    db.add(sq)
    db.commit()

    found = db.query(SubQuestion).filter(SubQuestion.session_id == session_id).all()
    assert len(found) == 1
    assert found[0].question == "Sub Q?"
    db.close()


def test_create_finding():
    engine = make_engine()
    db = make_session(engine)
    session_id = str(uuid.uuid4())
    s = ResearchSession(id=session_id, question="Q?", status="pending")
    db.add(s)

    sq = SubQuestion(id=str(uuid.uuid4()), session_id=session_id, question="SQ?", research_intent="r", status="pending")
    db.add(sq)

    src = Source(
        id=str(uuid.uuid4()), sub_question_id=sq.id, url="https://example.com",
        title="Test", domain="example.com", source_type="web",
        raw_content="raw", cleaned_content="clean", word_count=100, reliability_score=0.5
    )
    db.add(src)

    f = Finding(id=str(uuid.uuid4()), source_id=src.id, text="A finding", classification="supporting", confidence=0.8)
    db.add(f)
    db.commit()

    found = db.query(Finding).filter(Finding.source_id == src.id).all()
    assert len(found) == 1
    assert found[0].text == "A finding"
    assert found[0].classification == "supporting"
    db.close()


def test_update_session_status():
    engine = make_engine()
    db = make_session(engine)
    session_id = str(uuid.uuid4())
    s = ResearchSession(id=session_id, question="Q?", status="pending")
    db.add(s)
    db.commit()

    s.status = "completed"
    db.commit()

    found = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    assert found.status == "completed"
    db.close()


def test_conclusion_finding_link():
    engine = make_engine()
    db = make_session(engine)
    session_id = str(uuid.uuid4())
    s = ResearchSession(id=session_id, question="Q?", status="completed")
    db.add(s)

    sq = SubQuestion(id=str(uuid.uuid4()), session_id=session_id, question="SQ?", research_intent="r", status="completed")
    db.add(sq)

    src = Source(id=str(uuid.uuid4()), sub_question_id=sq.id, url="https://x.com", title="X", domain="x.com", source_type="web", raw_content="r", cleaned_content="c", word_count=50, reliability_score=0.5)
    db.add(src)

    f = Finding(id=str(uuid.uuid4()), source_id=src.id, text="Finding text", classification="supporting", confidence=0.9)
    db.add(f)

    c = Conclusion(id=str(uuid.uuid4()), session_id=session_id, text="Conclusion", confidence=0.8, key_points="[]", limitations="[]")
    db.add(c)
    db.flush()

    link = ConclusionFinding(conclusion_id=c.id, finding_id=f.id, relationship_type="supporting")
    db.add(link)
    db.commit()

    links = db.query(ConclusionFinding).filter(ConclusionFinding.conclusion_id == c.id).all()
    assert len(links) == 1
    assert links[0].relationship_type == "supporting"
    db.close()
