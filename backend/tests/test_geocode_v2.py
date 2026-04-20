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


def test_geocode_supports_non_us_candidates(client, override_auth, monkeypatch):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key="test-key",
    )
    captured: dict[str, object] = {}

    def fake_geocode(self, query, limit=5, country_set=None):
        captured["query"] = query
        captured["limit"] = limit
        captured["country_set"] = country_set
        return [
            TomTomPlace(
                id="place-london",
                name="London, UK",
                lat=51.5072,
                lon=-0.1276,
                address="London, UK",
                city="London",
                country_code="GB",
                url=None,
                raw={},
            )
        ]

    monkeypatch.setattr("api.routes_v2.TomTomClient.geocode", fake_geocode)

    try:
        resp = client.get("/v2/geocode?q=London")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 200
    data = resp.json()
    assert captured["query"] == "London"
    assert captured["country_set"] is None
    assert data["results"][0]["name"] == "London, UK"
    assert data["results"][0]["country_code"] == "GB"
