from api.main import app
from api.settings import APISettings, get_settings
from gymdb.infrastructure.tomtom_client import TomTomPlace


def test_live_search_requires_auth(client):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        enable_dev_auth_bypass=False,
        tomtom_api_key="test-key",
    )
    try:
        resp = client.get("/v2/live/search?place=Franklin%2C%20TN")
        assert resp.status_code == 401
    finally:
        client.app.dependency_overrides.pop(get_settings, None)


def test_live_search_requires_tomtom_key(client, override_auth):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key=None,
    )
    try:
        resp = client.get("/v2/live/search?place=Franklin%2C%20TN")
    finally:
        client.app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 503
    assert "TOMTOM_API_KEY" in resp.text


def test_live_search_returns_results(client, override_auth, monkeypatch):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key="test-key",
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.geocode",
        lambda self, query, limit=1: [
            TomTomPlace(
                id="place-1",
                name="Franklin, TN",
                lat=35.9251,
                lon=-86.8689,
                address="Franklin, TN",
                city="Franklin",
                country_code="US",
                url=None,
                raw={},
            )
        ],
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.search",
        lambda self,
        query,
        limit=25,
        country_set="US",
        lat=None,
        lon=None,
        radius_m=None,
        geobias_lat=None,
        geobias_lon=None: [
            TomTomPlace(
                id="poi-1",
                name="Franklin Strength Club",
                lat=35.9201,
                lon=-86.8621,
                address="101 Main St, Franklin, TN",
                city="Franklin",
                country_code="US",
                url="https://franklinstrength.example.com",
                raw={},
            )
        ],
    )

    try:
        resp = client.get("/v2/live/search?place=Franklin%2C%20TN&q=gym&radius_m=25000")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 200
    data = resp.json()
    assert data["place_query"] == "Franklin, TN"
    assert data["query"] == "gym"
    assert data["count"] == 1
    assert data["origin"]["name"] == "Franklin, TN"
    assert data["results"][0]["name"] == "Franklin Strength Club"
    assert data["results"][0]["provider"] == "tomtom"
    assert data["results"][0]["distance_m"] > 0
