import pytest
from fastapi.testclient import TestClient


from src.gymdb.models import Gym
from src.gymdb.inference import apply_inference
from api.main import app

@pytest.fixture()
def client():
    """
    Shared FastAPI test client for API contract + smoke tests.
    """
    return TestClient(app)

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