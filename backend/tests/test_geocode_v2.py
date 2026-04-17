from api.main import app
from api.settings import APISettings, get_settings
from gymdb.infrastructure.tomtom_client import TomTomPlace


def test_geocode_requires_auth(client):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        enable_dev_auth_bypass=False,
        tomtom_api_key="test-key",
    )
    try:
        resp = client.get("/v2/geocode?q=Nashville")
        assert resp.status_code == 401
    finally:
        client.app.dependency_overrides.pop(get_settings, None)


def test_geocode_requires_tomtom_key(client, override_auth):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key=None,
    )
    try:
        resp = client.get("/v2/geocode?q=Nashville")
    finally:
        client.app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 503
    assert "TOMTOM_API_KEY" in resp.text


def test_geocode_returns_candidates(client, override_auth, monkeypatch):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key="test-key",
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.geocode",
        lambda self, query, limit=5: [
            TomTomPlace(
                id="place-1",
                name="Nashville, TN",
                lat=36.1627,
                lon=-86.7816,
                address="Nashville, TN",
                city="Nashville",
                country_code="US",
                url=None,
                raw={},
            )
        ],
    )

    try:
        resp = client.get("/v2/geocode?q=Nashville")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "Nashville"
    assert data["count"] == 1
    assert data["results"][0]["name"] == "Nashville, TN"
    assert data["results"][0]["lat"] == 36.1627
