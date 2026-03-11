import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from api.auth.dependencies import require_user
from api.deps import get_gym_store
from api.main import app
from api.settings import APISettings, get_settings
from gymdb.domain.inference import apply_inference
from gymdb.domain.models import Gym
from gymdb.infrastructure.db.db_engine import get_engine, reset_engine
from gymdb.infrastructure.db.models.job_receipt import metadata as receipt_metadata

# Fake Gym Store

class FakeGymStore:
    """
    Deterministic, in-memory GymStore replacement for API tests.
    """
    default_region = "us"

    def __init__(self):
        # Intentionally bypass parent constructor
        pass

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

# FastAPI Client Fixture

@pytest.fixture
def client():
    """
    Default API client with deterministic gym data.
    Auth is NOT bypassed here.
    """
    app.dependency_overrides[get_gym_store] = lambda: FakeGymStore()

    yield TestClient(app)

    app.dependency_overrides.pop(get_gym_store, None)


@pytest.fixture()
def override_auth():
    """
    Explicitly bypass authentication for test that require a "logged in" user.
    """
    app.dependency_overrides[require_user] = lambda: {"sub": "test-user"}
    yield
    app.dependency_overrides.pop(require_user, None)


@pytest.fixture()
def disable_dev_auth_bypass():
    """
    Guarantee dev auth bypass is OFF during test unless explicity overridden.
    Prevents accidental 200 responses without Authorization header.
    """
    app.dependency_overrides[get_settings] = lambda: APISettings(
        postgres_dsn="postgresql+psycopg://test",
        aws_region="test",
        cognito_user_pool_id="test",
        cognito_app_client_id="test",
        cognito_issuer="https://example.com",
        enable_internal=True,
        enable_dev_auth_bypass=False,       # IMPORTANT
    )
    yield
    app.dependency_overrides.pop(get_settings, None)

# Domain / Inference Fixtures

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

# Database Integration Fixture


@pytest.fixture
def db_session(monkeypatch):
    """
    Database session for integration tests.
    Creates schema + tables inside a transaction and rolls back.
    """

    # 1. Override the *actual* source of truth
    from gymdb.infrastructure.db.db_engine import (
        clear_test_connection,
        set_test_connection,
    )
    from gymdb.infrastructure.settings import settings

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
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS ops"))
        receipt_metadata.create_all(conn)
        conn.execute(text("TRUNCATE TABLE ops.job_receipts RESTART IDENTITY CASCADE"))

    # 5. Start a transaction for the test
    connection = engine.connect()
    transaction = connection.begin()

    set_test_connection(connection)

    Session = sessionmaker(bind=connection)
    session = Session()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        clear_test_connection()
        connection.close()



