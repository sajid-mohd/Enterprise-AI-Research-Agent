"""
pytest conftest — sets env vars BEFORE any app module is imported.
This is the ROOT conftest so it loads before any test file is imported.
Keep DB_PATH as a file (not :memory:) for thread safety with SQLAlchemy.
"""
import os
import shutil

# Use a dedicated test DB (not the real one, not :memory:)
TEST_DB_PATH = "data/test_research.db"
TEST_CHROMA_PATH = "data/chroma_test"

# Force test environment — override .env file values
os.environ["DB_PATH"] = TEST_DB_PATH
os.environ["CHROMA_PATH"] = TEST_CHROMA_PATH
os.environ["PROVIDER"] = "groq"
os.environ["GROQ_API_KEY"] = "test_key_for_tests"

# Clean up any stale test DB from previous runs
if os.path.exists(TEST_DB_PATH):
    try:
        os.remove(TEST_DB_PATH)
    except OSError:
        pass
