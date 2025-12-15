from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_gyms():
    resp = client.get("/v1/gyms")
    assert resp.status_code == 200

    data = resp.json()
    assert "count" in data
    assert "results" in data
    assert isinstance(data["results"], list)

    # Dataset should not be empty if pipeline ran
    assert data["count"] == len(data["results"])

def test_gym_has_stable_id():
    resp = client.get("/v1/gyms")
    gyms = resp.json()["results"]

    assert len(gyms) > 0
    assert "id" in gyms[0]
    assert isinstance(gyms[0]["id"], str)
    assert len(gyms[0]["id"]) > 0

def test_get_gym_by_id():
    resp = client.get("/v1/gyms")
    gyms = resp.json()["results"]
    gym_id = gyms[0]["id"]

    resp = client.get(f"/v1/gyms/{gym_id}")
    assert resp.status_code == 200

    gym = resp.json()
    assert gym["id"] == gym_id