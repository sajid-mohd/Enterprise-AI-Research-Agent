"""Integration tests — explicitly rebuilds engine to use correct test DB."""
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="module")
def test_client():
    """
    Create a TestClient that uses a freshly built file-based SQLite engine.
    This bypasses module-cache issues with settings.DB_PATH.
    """
    import app.models.research_session  # noqa: F401
    import app.models.sub_question      # noqa: F401
    import app.models.source            # noqa: F401
    import app.models.finding           # noqa: F401
    import app.models.contradiction     # noqa: F401
    import app.models.conclusion        # noqa: F401

    import app.storage.database as db_module
    from app.storage.database import Base, get_db

    # Build a fresh file-based engine for integration tests
    test_db_path = "data/test_research_integration.db"
    os.makedirs("data", exist_ok=True)
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    test_engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Create all tables in the test engine
    Base.metadata.create_all(bind=test_engine)

    # Patch the module-level engine and SessionLocal
    original_engine = db_module.engine
    original_session_local = db_module.SessionLocal
    db_module.engine = test_engine
    db_module.SessionLocal = TestSession

    from app.main import app

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    # Restore originals
    db_module.engine = original_engine
    db_module.SessionLocal = original_session_local
    app.dependency_overrides.pop(get_db, None)

    # Cleanup test DB
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except OSError:
            pass


def test_health_endpoint(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json()["db"] == "ok"


def test_get_sessions_returns_list(test_client):
    response = test_client.get("/sessions")
    assert response.status_code == 200
    assert "sessions" in response.json()
    assert isinstance(response.json()["sessions"], list)


def test_get_findings_returns_list(test_client):
    response = test_client.get("/findings")
    assert response.status_code == 200
    assert "findings" in response.json()


def test_get_contradictions_returns_list(test_client):
    response = test_client.get("/contradictions")
    assert response.status_code == 200
    assert "contradictions" in response.json()


def test_get_research_not_found(test_client):
    response = test_client.get(f"/research/{uuid.uuid4()}")
    assert response.status_code == 404


def test_get_nonexistent_finding(test_client):
    response = test_client.get(f"/findings/{uuid.uuid4()}")
    assert response.status_code == 404


def test_get_nonexistent_source(test_client):
    response = test_client.get(f"/sources/{uuid.uuid4()}")
    assert response.status_code == 404


def test_post_research_rejects_short_question(test_client):
    response = test_client.post("/research", json={"question": "AI?"})
    assert response.status_code == 422


def test_post_research_rejects_oversized_question(test_client):
    response = test_client.post("/research", json={"question": "A" * 2005})
    assert response.status_code == 422


def test_post_research_creates_session(test_client):
    with patch("app.services.research_service.ResearchOrchestrator") as MockOrch, \
         patch("app.services.research_service.SessionLocal") as MockSL:
        MockOrch.return_value.run = AsyncMock()
        MockSL.return_value = MagicMock()
        response = test_client.post(
            "/research",
            json={"question": "How is AI transforming healthcare logistics?"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["status"] == "pending"


def test_session_appears_after_create(test_client):
    with patch("app.services.research_service.ResearchOrchestrator") as MockOrch, \
         patch("app.services.research_service.SessionLocal") as MockSL:
        MockOrch.return_value.run = AsyncMock()
        MockSL.return_value = MagicMock()
        resp = test_client.post(
            "/research",
            json={"question": "What AI technologies are changing manufacturing?"},
        )
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]
    detail = test_client.get(f"/research/{session_id}")
    assert detail.status_code == 200
    assert detail.json()["question"] == "What AI technologies are changing manufacturing?"
