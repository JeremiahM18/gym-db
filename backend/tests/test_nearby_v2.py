from api.deps import get_db
from api.main import app
from api.settings import APISettings, get_settings
from tests.fakes import FakeDB


def test_nearby_requires_auth(client):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        enable_dev_auth_bypass=False,
    )
    try:
        resp = client.get("/v2/gyms/geo/nearby?lat=36.16&lon=-86.78&radius_m=1000")
        assert resp.status_code == 401
    finally:
        client.app.dependency_overrides.pop(get_settings, None)


def test_nearby_shape_authenticated(client, override_auth, monkeypatch):
    monkeypatch.setattr(
        "api.geo.nearby_routes.get_nearby_gyms",
        lambda conn, lat, lon, radius_m, limit: [],
    )

    app.dependency_overrides[get_db] = lambda: FakeDB()

    try:
        resp = client.get("/v2/gyms/geo/nearby?lat=36.16&lon=-86.78&radius_m=1000")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    data = resp.json()
    assert "count" in data
    assert "results" in data
    assert isinstance(data["results"], list)
