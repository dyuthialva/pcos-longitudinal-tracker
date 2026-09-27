import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import get_db
from backend.models.base import Base
from backend.services.synthetic_data import seed_synthetic_patients

# Shared StaticPool in-memory SQLite engine
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)
Base.metadata.create_all(bind=engine)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    seed_synthetic_patients(db, force_recreate=True)
    db.close()

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    return TestClient(app)
