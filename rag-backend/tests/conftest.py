import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to ensure modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.core.db import Base, get_db, DocumentEmbedding

# Create test database engine (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Create tables before tests run
def setup_module():
    logger.info("Setting up test database tables")
    Base.metadata.create_all(bind=test_engine)

# Cleanup after tests
def teardown_module():
    logger.info("Dropping test database tables")
    Base.metadata.drop_all(bind=test_engine)

# Override the get_db dependency
@pytest.fixture(scope="function")
def test_db():
    # Create tables for test database
    Base.metadata.create_all(bind=test_engine)
    logger.info("Creating tables for test")
    
    # Create a new session for each test
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create a fixture to override the dependency in FastAPI app
@pytest.fixture(scope="function")
def client(test_db):
    # Override the dependency to use test database
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    # Store original dependency
    original_dependency = app.dependency_overrides.copy()
    
    # Override with test dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    with TestClient(app) as test_client:
        yield test_client
    
    # Reset dependency override after test
    app.dependency_overrides = original_dependency 