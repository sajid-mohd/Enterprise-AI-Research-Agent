"""
pytest conftest — sets up in-memory SQLite for all tests.
Patches database.engine and SessionLocal before any app module imports them.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session", autouse=True)
def patch_database():
    """Replace the real SQLite engine with an in-memory one for the test session."""
    import app.storage.database as db_module
    import app.models.research_session  # noqa: F401 — register models
    import app.models.sub_question      # noqa: F401
    import app.models.source            # noqa: F401
    import app.models.finding           # noqa: F401
    import app.models.contradiction     # noqa: F401
    import app.models.conclusion        # noqa: F401

    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Create all tables
    db_module.Base.metadata.create_all(bind=test_engine)

    # Patch module-level engine and SessionLocal
    original_engine = db_module.engine
    original_session_local = db_module.SessionLocal

    db_module.engine = test_engine
    db_module.SessionLocal = TestSession

    yield test_engine

    # Restore
    db_module.engine = original_engine
    db_module.SessionLocal = original_session_local
