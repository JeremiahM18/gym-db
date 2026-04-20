from requests import RequestException

from api.main import app
from api.settings import APISettings, get_settings
from gymdb.infrastructure.overpass_client import OverpassUnavailableError
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
        "api.routes_v2.fetch_gyms",
        lambda radius_meters, lat, lon: [
            {
                "type": "node",
                "id": 101,
                "lat": 35.9201,
                "lon": -86.8621,
                "tags": {
                    "name": "Franklin Strength Club",
                    "amenity": "gym",
                    "website": "https://franklinstrength.example.com",
                    "addr:city": "Franklin",
                    "addr:state": "TN",
                    "addr:street": "Main St",
                    "addr:housenumber": "101",
                },
            }
        ],
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.search_gyms",
        lambda self,
        lat,
        lon,
        radius_m,
        limit=100,
        country_set=None: [
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
    assert data["results"][0]["source_provenance"]["primary"] == "osm"
    assert data["results"][0]["source_provenance"]["confirmed_by"] == ["tomtom"]
    assert data["results"][0]["tags"]["website"] == "https://franklinstrength.example.com"
    assert data["results"][0]["distance_m"] > 0


def test_live_search_returns_404_when_place_is_not_found(
    client, override_auth, monkeypatch
):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key="test-key",
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.geocode",
        lambda self, query, limit=1, country_set=None: [],
    )

    try:
        resp = client.get("/v2/live/search?place=Atlantis")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 404
    assert (
        resp.json()["error"]["message"]["detail"]
        == 'No place match found for "Atlantis".'
    )


def test_live_search_returns_503_when_place_resolution_fails(
    client, override_auth, monkeypatch
):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key="test-key",
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.geocode",
        lambda self, query, limit=1, country_set=None: (_ for _ in ()).throw(
            RequestException("tomtom down")
        ),
    )

    try:
        resp = client.get("/v2/live/search?place=Franklin%2C%20TN")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 503
    assert "place resolution is temporarily unavailable" in resp.text


def test_live_search_returns_503_when_overpass_fails(
    client, override_auth, monkeypatch
):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key="test-key",
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.geocode",
        lambda self, query, limit=1, country_set=None: [
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
        "api.routes_v2.fetch_gyms",
        lambda radius_meters, lat, lon: (_ for _ in ()).throw(
            OverpassUnavailableError("Overpass is temporarily unavailable.")
        ),
    )

    try:
        resp = client.get("/v2/live/search?place=Franklin%2C%20TN")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 503
    assert "Overpass is temporarily unavailable" in resp.text


def test_live_search_allows_non_us_origin(client, override_auth, monkeypatch):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key="test-key",
    )
    captured: dict[str, object] = {}

    def fake_geocode(self, query, limit=1, country_set=None):
        captured["geocode_country_set"] = country_set
        return [
            TomTomPlace(
                id="place-ldn",
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

    def fake_search_gyms(self, lat, lon, radius_m, limit=100, country_set=None):
        captured["search_country_set"] = country_set
        return [
            TomTomPlace(
                id="poi-ldn-1",
                name="London Strength Club",
                lat=51.5080,
                lon=-0.1280,
                address="London, UK",
                city="London",
                country_code="GB",
                url="https://londonstrength.example.com",
                raw={},
            )
        ]

    monkeypatch.setattr("api.routes_v2.TomTomClient.geocode", fake_geocode)
    monkeypatch.setattr(
        "api.routes_v2.fetch_gyms",
        lambda radius_meters, lat, lon: [
            {
                "type": "node",
                "id": 201,
                "lat": 51.5080,
                "lon": -0.1280,
                "tags": {
                    "name": "London Strength Club",
                    "amenity": "gym",
                    "addr:city": "London",
                    "website": "https://londonstrength.example.com",
                },
            }
        ],
    )
    monkeypatch.setattr("api.routes_v2.TomTomClient.search_gyms", fake_search_gyms)

    try:
        resp = client.get("/v2/live/search?place=London%2C%20UK&q=gym&radius_m=10000")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 200
    data = resp.json()
    assert captured["geocode_country_set"] is None
    assert captured["search_country_set"] is None
    assert data["origin"]["name"] == "London, UK"
    assert data["origin"]["country_code"] == "GB"
    assert data["results"][0]["name"] == "London Strength Club"


def test_live_search_is_rate_limited(client, override_auth, monkeypatch):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key="test-key",
        live_search_rate_limit=1,
        live_search_window_seconds=60,
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.geocode",
        lambda self, query, limit=1, country_set=None: [
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
        "api.routes_v2.fetch_gyms",
        lambda radius_meters, lat, lon: [
            {
                "type": "node",
                "id": 101,
                "lat": 35.9201,
                "lon": -86.8621,
                "tags": {
                    "name": "Franklin Strength Club",
                    "amenity": "gym",
                },
            }
        ],
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.search_gyms",
        lambda self, lat, lon, radius_m, limit=100, country_set=None: [],
    )

    try:
        first = client.get("/v2/live/search?place=Franklin%2C%20TN")
        second = client.get("/v2/live/search?place=Franklin%2C%20TN")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["Retry-After"] == "60"
    assert "rate limited" in second.text
