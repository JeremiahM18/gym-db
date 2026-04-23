import time as _time
from pathlib import Path

import pytest
from requests import RequestException

from api.auth.dependencies import require_user
from api.background_tasks import background_overpass_enrich
from api.main import app
from api.settings import APISettings, get_settings
from gymdb.infrastructure.live_search_cache import LiveSearchCacheEntry
from gymdb.infrastructure.tomtom_client import TomTomPlace


@pytest.fixture(autouse=True)
def _noop_background_enrich(monkeypatch):
    """Prevent background Overpass calls from reaching the real network in tests."""
    monkeypatch.setattr(
        "api.routes_v2.background_overpass_enrich",
        lambda **kwargs: None,
    )


_FRANKLIN_ORIGIN = TomTomPlace(
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

_FRANKLIN_GYM = TomTomPlace(
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
        lambda self, query, limit=1, country_set=None: [_FRANKLIN_ORIGIN],
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.search_gyms",
        lambda self, lat, lon, radius_m, limit=100, country_set=None: [_FRANKLIN_GYM],
    )

    try:
        resp = client.get("/v2/live/search?place=Franklin%2C%20TN&q=gym&radius_m=25000")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 200
    data = resp.json()
    assert data["search_id"]
    assert data["status"] == "enriching"
    assert data["enrichment_status"] == "pending"
    assert data["poll_after_ms"] == 2000
    assert data["revision"] == 0
    assert data["place_query"] == "Franklin, TN"
    assert data["query"] == "gym"
    assert data["count"] == 1
    assert data["origin"]["name"] == "Franklin, TN"
    assert data["results"][0]["name"] == "Franklin Strength Club"
    assert data["results"][0]["source_provenance"]["primary"] == "tomtom"
    assert (
        data["results"][0]["tags"]["website"] == "https://franklinstrength.example.com"
    )
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


def test_live_search_returns_503_when_gym_search_fails(
    client, override_auth, monkeypatch
):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key="test-key",
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.geocode",
        lambda self, query, limit=1, country_set=None: [_FRANKLIN_ORIGIN],
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.search_gyms",
        lambda self, lat, lon, radius_m, limit=100, country_set=None: (
            _ for _ in ()
        ).throw(RequestException("TomTom down")),
    )

    try:
        resp = client.get("/v2/live/search?place=Franklin%2C%20TN")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 503
    assert "gym search is temporarily unavailable" in resp.text


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
        lambda self, query, limit=1, country_set=None: [_FRANKLIN_ORIGIN],
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.search_gyms",
        lambda self, lat, lon, radius_m, limit=100, country_set=None: [_FRANKLIN_GYM],
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


def test_live_search_applies_osm_confirmation_from_fresh_cache(
    client, override_auth, monkeypatch
):
    """When a fresh OSM cache entry covers the search area, gyms that match an
    OSM element by name should be promoted to OSM_CONFIRMED provenance."""

    osm_elements = [
        {
            "type": "node",
            "id": 99,
            "lat": _FRANKLIN_GYM.lat,
            "lon": _FRANKLIN_GYM.lon,
            "tags": {
                "leisure": "fitness_centre",
                "name": _FRANKLIN_GYM.name,
                "opening_hours": "Mo-Su 06:00-22:00",
            },
        }
    ]
    fresh_cache = LiveSearchCacheEntry(
        cache_path=Path("/fake/cache.json"),
        cached_at_epoch_s=_time.time(),
        elements=osm_elements,
    )

    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key="test-key",
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.geocode",
        lambda self, query, limit=1, country_set=None: [_FRANKLIN_ORIGIN],
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.search_gyms",
        lambda self, lat, lon, radius_m, limit=100, country_set=None: [_FRANKLIN_GYM],
    )
    monkeypatch.setattr(
        "api.routes_v2.load_cached_elements",
        lambda cache_root, lat, lon, radius_m: fresh_cache,
    )

    try:
        resp = client.get("/v2/live/search?place=Franklin%2C%20TN&q=gym")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ready"
    assert payload["enrichment_status"] == "skipped"
    assert payload["poll_after_ms"] is None
    result = payload["results"][0]
    assert result["source_provenance"]["match_status"] == "osm_confirmed"
    assert "osm" in result["source_provenance"]["confirmed_by"]
    assert result["tags"].get("opening_hours") == "Mo-Su 06:00-22:00"


def test_live_search_session_poll_returns_same_snapshot_when_pending(
    client, override_auth, monkeypatch
):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key="test-key",
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.geocode",
        lambda self, query, limit=1, country_set=None: [_FRANKLIN_ORIGIN],
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.search_gyms",
        lambda self, lat, lon, radius_m, limit=100, country_set=None: [_FRANKLIN_GYM],
    )

    try:
        initial = client.get("/v2/live/search?place=Franklin%2C%20TN&q=gym")
        search_id = initial.json()["search_id"]
        follow_up = client.get(f"/v2/live/search/{search_id}")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert initial.status_code == 200
    assert follow_up.status_code == 200
    assert follow_up.json() == initial.json()


def test_live_search_session_is_scoped_to_the_authenticated_user(
    client, override_auth, monkeypatch
):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key="test-key",
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.geocode",
        lambda self, query, limit=1, country_set=None: [_FRANKLIN_ORIGIN],
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.search_gyms",
        lambda self, lat, lon, radius_m, limit=100, country_set=None: [_FRANKLIN_GYM],
    )

    try:
        initial = client.get("/v2/live/search?place=Franklin%2C%20TN&q=gym")
        search_id = initial.json()["search_id"]
        client.app.dependency_overrides[require_user] = lambda: {"sub": "other-user"}
        follow_up = client.get(f"/v2/live/search/{search_id}")
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides[require_user] = lambda: {"sub": "test-user"}

    assert initial.status_code == 200
    assert follow_up.status_code == 404
    assert follow_up.json()["error"]["message"]["detail"] == (
        "Live search session not found."
    )


def test_background_enrichment_updates_live_search_session_snapshot(
    client, override_auth, monkeypatch
):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key="test-key",
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.geocode",
        lambda self, query, limit=1, country_set=None: [_FRANKLIN_ORIGIN],
    )
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.search_gyms",
        lambda self, lat, lon, radius_m, limit=100, country_set=None: [_FRANKLIN_GYM],
    )
    monkeypatch.setattr(
        "api.background_tasks.fetch_gyms",
        lambda *args, **kwargs: [
            {
                "type": "node",
                "id": 99,
                "lat": _FRANKLIN_GYM.lat,
                "lon": _FRANKLIN_GYM.lon,
                "tags": {
                    "leisure": "fitness_centre",
                    "name": _FRANKLIN_GYM.name,
                    "opening_hours": "Mo-Su 05:00-23:00",
                },
            }
        ],
    )

    try:
        initial = client.get("/v2/live/search?place=Franklin%2C%20TN&q=gym")
        payload = initial.json()
        search_id = payload["search_id"]
        settings = APISettings(tomtom_api_key="test-key")

        background_overpass_enrich(
            lat=_FRANKLIN_ORIGIN.lat,
            lon=_FRANKLIN_ORIGIN.lon,
            radius_m=25000,
            origin_name=_FRANKLIN_ORIGIN.address or _FRANKLIN_ORIGIN.name,
            cache_root=settings.live_search_cache_root,
            timeout_seconds=settings.live_search_overpass_timeout_seconds,
            max_attempts=settings.live_search_overpass_max_attempts,
            search_id=search_id,
            session_root=settings.live_search_session_root,
        )
        updated = client.get(f"/v2/live/search/{search_id}")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert initial.status_code == 200
    assert updated.status_code == 200
    updated_payload = updated.json()
    assert updated_payload["status"] == "ready"
    assert updated_payload["enrichment_status"] == "completed"
    assert updated_payload["revision"] == 1
    assert updated_payload["search_id"] == search_id
    result = updated_payload["results"][0]
    assert result["source_provenance"]["match_status"] == "osm_confirmed"
    assert result["tags"]["opening_hours"] == "Mo-Su 05:00-23:00"
