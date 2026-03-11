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


class FakeGymStore:
    default_region = "us"

    def __init__(self):
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
                "osm_refs": [{"type": "node", "id": 123456}],
                "inference": {
                    "is_24_7": {
                        "value": True,
                        "confidence": 0.9,
                        "reasons": ["opening_hours=24/7"],
                        "source": "rule",
                    },
                    "specialty": {
                        "value": "general_fitness",
                        "confidence": 0.5,
                        "reasons": ["defaulted to general fitness"],
                        "source": "rule",
                    },
                },
                "inference_meta": {
                    "engine": "rule_based",
                    "version": "1.0.0",
                },
            }
        ]

    def nearby(self, **kwargs):
        return self.filter(**kwargs)

    def get_by_id(self, region: str, gym_id: str):
        if gym_id == "test-gym-1":
            return self.filter()[0]
        return None


@pytest.fixture
def client():
    app.dependency_overrides[get_gym_store] = lambda: FakeGymStore()

    yield TestClient(app)

    app.dependency_overrides.pop(get_gym_store, None)


@pytest.fixture()
def override_auth():
    app.dependency_overrides[require_user] = lambda: {"sub": "test-user"}
    yield
    app.dependency_overrides.pop(require_user, None)


@pytest.fixture()
def disable_dev_auth_bypass():
    app.dependency_overrides[get_settings] = lambda: APISettings(
        postgres_dsn="postgresql+psycopg://test",
        aws_region="test",
        cognito_user_pool_id="test",
        cognito_app_client_id="test",
        cognito_issuer="https://example.com",
        enable_internal=True,
        enable_dev_auth_bypass=False,
    )
    yield
    app.dependency_overrides.pop(get_settings, None)


@pytest.fixture
def gym_factory():
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
    return apply_inference


@pytest.fixture
def db_session(monkeypatch):
    from gymdb.infrastructure.db.db_engine import (
        clear_test_connection,
        set_test_connection,
    )
    from gymdb.infrastructure.settings import settings

    monkeypatch.setattr(
        settings,
        "postgres_dsn",
        "postgresql+psycopg://gymdb_test:gymdb_test@localhost:5432/gymdb_test",
    )

    reset_engine()
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS ops"))
        receipt_metadata.create_all(conn)
        conn.execute(text("TRUNCATE TABLE ops.job_receipts RESTART IDENTITY CASCADE"))

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
