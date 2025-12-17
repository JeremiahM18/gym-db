import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture(scope="session")
def client():
    """
    Shared FastAPI test client for API contract + smoke tests.
    """
    return TestClient(app)