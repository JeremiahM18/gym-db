import pytest
from fastapi.testclient import TestClient

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from src.gymdb.db.db_engine import get_engine, reset_engine
from src.gymdb.db.models.job_receipt import metadata as receipt_metadata

from src.gymdb.models import Gym
from src.gymdb.inference import apply_inference
from api.main import app
from api.deps import get_store
from api.auth.dependencies import require_user

# @pytest.fixture()
# def client():
#     """
#     Shared FastAPI test client for API contract + smoke tests.
#     """
#     return TestClient(app)

class TestGymStore:
    default_region = "us"

    def __init__(self):
        self.db = None

    def filter(self, **kwargs):
        return [
            {
                "id": "test-gym-1",
                "name": "Test Gym",
                "norm_name": "test_gym",
                "region": "us",

                "lat": 36.1627,
                "lon": -86.7816,
                "osm_refs": [
                    {"type": "node", "id": 123456}
                ],

                "inference": {
                    "is_24_7": {
                        "value": True,
                        "confidence": 0.9,
                        "reasons": ["opening_hours=24/7"],
                        "source": "rule",
                    }
                },
                "inference_meta": {
                    "engine": "rule_based",
                    "version": "1.0.0",
                },
            }
        ]

    def get_by_id(self, region: str, gym_id: str):
        if gym_id == "test-gym-1":
            return self.filter()[0]
        return None

@pytest.fixture
def client():
    """
    Default API client with deterministic inference data.
    Used by API v2 + embedding tests.
    """
    app.dependency_overrides[get_store] = lambda: TestGymStore()

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def gym_factory():
    """
    Factory for creating Gym domain objects in tests.
    Keeps inference and processing tests consistent.
    """
    def _make(tags: dict) -> Gym:
        return Gym(
            name="Test Gym",
            norm_name="test_gym",
            lat=0.0,
            lon=0.0,
            osm_refs=[{"type": "node", "id": 1}],
            tags=tags,
        )
    return _make

@pytest.fixture
def infer():
    """
    Inference application fixture.
    """
    return apply_inference

@pytest.fixture()
def override_auth():
    app.dependency_overrides[require_user] = lambda: {"sub": "test-user"}
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def db_session(monkeypatch):
    """
    Database session for integration tests.
    Creates schema + tables inside a transaction and rolls back.
    """

    # 1. Override the *actual* source of truth
    from src.gymdb.settings import settings

    monkeypatch.setattr(
        settings, 
        "postgres_dsn", 
        "postgresql+psycopg://gymdb_test:gymdb_test@localhost:5432/gymdb_test")

    # 2. Reset engine so it uses the test DSN
    reset_engine()

    # 3. Create a fresh engine bound to the test database
    engine = get_engine()

    # 4 Create schema + tables OUTSIDE the test transaction
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS ops CASCADE"))
        conn.execute(text("CREATE SCHEMA ops"))
        receipt_metadata.create_all(conn)

    # 5. Start a transaction for the test
    connection = engine.connect()
    transaction = connection.begin()

    Session = sessionmaker(bind=connection)
    session = Session()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()