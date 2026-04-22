"""
Tests for TomTom brand corroboration (TOMTOM_CORROBORATED tier).

Verifies:
- Spatially close brand result upgrades TOMTOM_ONLY → TOMTOM_CORROBORATED
- Broad queries do not trigger brand search (route-level gate)
- Brand search failure is non-fatal (route returns 200)
- OSM_CONFIRMED and OSM_NEARBY gyms are never downgraded
- The TOMTOM_CORROBORATED confidence hard cap is enforced by scoring
- confirmed_by contains TOMTOM_BRAND, not OSM
"""
from __future__ import annotations

import pytest
from requests import RequestException

from api.main import app
from api.settings import APISettings, get_settings
from gymdb.application.coverage import apply_tomtom_brand_corroboration
from gymdb.domain.models import Gym
from gymdb.domain.provenance import (
    TOMTOM_CORROBORATED_HARD_CAP,
    ConfirmedBy,
    MatchStatus,
)
from gymdb.domain.scoring import compute_confidence
from gymdb.infrastructure.tomtom_client import TomTomPlace


# ---------------------------------------------------------------------------
# Unit tests for apply_tomtom_brand_corroboration
# ---------------------------------------------------------------------------


def _gym_with_status(name: str, status: MatchStatus, lat: float = 35.920, lon: float = -86.862) -> Gym:
    gym = Gym(
        name=name,
        norm_name=name.lower().replace(" ", "_"),
        lat=lat,
        lon=lon,
        osm_refs=[],
        tags={"leisure": "fitness_centre", "name": name},
    )
    gym.source_provenance = {
        "primary": "tomtom",
        "confirmed_by": [],
        "match_status": status.value,
        "external_refs": {},
    }
    return gym


def _brand_result(name: str, lat: float = 35.920, lon: float = -86.862) -> TomTomPlace:
    return TomTomPlace(
        id="brand-1", name=name, lat=lat, lon=lon,
        address="1 Main St", city="Franklin", country_code="US", url=None, raw={},
    )


def test_close_brand_result_upgrades_tomtom_only_to_corroborated():
    gym = _gym_with_status("CrossFit Franklin", MatchStatus.TOMTOM_ONLY)
    brand = _brand_result("CrossFit Franklin")

    apply_tomtom_brand_corroboration([gym], [brand])

    assert gym.source_provenance["match_status"] == MatchStatus.TOMTOM_CORROBORATED.value
    assert ConfirmedBy.TOMTOM_BRAND.value in gym.source_provenance["confirmed_by"]


def test_distant_brand_result_leaves_tomtom_only_unchanged():
    gym = _gym_with_status("CrossFit Franklin", MatchStatus.TOMTOM_ONLY, lat=35.920, lon=-86.862)
    brand = _brand_result("CrossFit Franklin", lat=36.500, lon=-87.500)  # ~75 km away

    apply_tomtom_brand_corroboration([gym], [brand])

    assert gym.source_provenance["match_status"] == MatchStatus.TOMTOM_ONLY.value


def test_empty_brand_results_is_a_noop():
    gym = _gym_with_status("Some Gym", MatchStatus.TOMTOM_ONLY)
    original = dict(gym.source_provenance)

    apply_tomtom_brand_corroboration([gym], [])

    assert gym.source_provenance == original


def test_osm_confirmed_gym_is_not_downgraded():
    gym = _gym_with_status("Life Time", MatchStatus.OSM_CONFIRMED)
    gym.source_provenance["confirmed_by"] = [ConfirmedBy.OSM.value]
    brand = _brand_result("Life Time")  # same lat/lon

    apply_tomtom_brand_corroboration([gym], [brand])

    assert gym.source_provenance["match_status"] == MatchStatus.OSM_CONFIRMED.value
    assert ConfirmedBy.OSM.value in gym.source_provenance["confirmed_by"]
    assert ConfirmedBy.TOMTOM_BRAND.value not in gym.source_provenance["confirmed_by"]


def test_osm_nearby_gym_is_not_downgraded():
    gym = _gym_with_status("Unnamed Gym", MatchStatus.OSM_NEARBY)
    brand = _brand_result("Unnamed Gym")  # same lat/lon

    apply_tomtom_brand_corroboration([gym], [brand])

    assert gym.source_provenance["match_status"] == MatchStatus.OSM_NEARBY.value


def test_confirmed_by_uses_tomtom_brand_namespace_not_osm():
    gym = _gym_with_status("CrossFit Franklin", MatchStatus.TOMTOM_ONLY)
    brand = _brand_result("CrossFit Franklin")

    apply_tomtom_brand_corroboration([gym], [brand])

    confirmed = gym.source_provenance["confirmed_by"]
    assert ConfirmedBy.TOMTOM_BRAND.value in confirmed
    assert ConfirmedBy.OSM.value not in confirmed


def test_corroborated_confidence_capped_below_osm_nearby_floor():
    """The TOMTOM_CORROBORATED hard cap must hold even for a fully-tagged gym."""
    gym = _gym_with_status("CrossFit Franklin", MatchStatus.TOMTOM_ONLY)
    gym.tags.update({
        "addr:housenumber": "100", "addr:street": "Main St", "addr:city": "Franklin",
        "website": "https://example.com", "phone": "+1-615-555-0100",
        "opening_hours": "24/7", "brand": "CrossFit", "brand:wikidata": "Q123",
        "operator": "CrossFit HQ", "operator:wikidata": "Q456",
        "contact:instagram": "@cf", "contact:facebook": "cf",
    })
    brand = _brand_result("CrossFit Franklin")
    apply_tomtom_brand_corroboration([gym], [brand])

    score = compute_confidence(gym)

    assert score <= TOMTOM_CORROBORATED_HARD_CAP


# ---------------------------------------------------------------------------
# Route-level integration tests
# ---------------------------------------------------------------------------

_FRANKLIN_ORIGIN = TomTomPlace(
    id="place-1", name="Franklin, TN", lat=35.9251, lon=-86.8689,
    address="Franklin, TN", city="Franklin", country_code="US", url=None, raw={},
)
_FRANKLIN_GYM = TomTomPlace(
    id="poi-1", name="CrossFit Franklin", lat=35.9201, lon=-86.8621,
    address="101 Main St, Franklin, TN", city="Franklin", country_code="US",
    url=None, raw={},
)
_BRAND_RESULT = TomTomPlace(
    id="brand-1", name="CrossFit Franklin", lat=35.9202, lon=-86.8622,
    address="101 Main St, Franklin, TN", city="Franklin", country_code="US",
    url=None, raw={},
)


@pytest.fixture(autouse=True)
def _noop_background_enrich(monkeypatch):
    monkeypatch.setattr("api.routes_v2.background_overpass_enrich", lambda **kw: None)


def test_brand_specific_query_triggers_corroboration(client, override_auth, monkeypatch):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(tomtom_api_key="test-key")
    monkeypatch.setattr("api.routes_v2.TomTomClient.geocode", lambda *a, **kw: [_FRANKLIN_ORIGIN])
    monkeypatch.setattr("api.routes_v2.TomTomClient.search_gyms", lambda *a, **kw: [_FRANKLIN_GYM])
    monkeypatch.setattr("api.routes_v2.TomTomClient.search", lambda *a, **kw: [_BRAND_RESULT])
    monkeypatch.setattr("api.routes_v2.load_cached_elements", lambda *a, **kw: None)

    try:
        resp = client.get("/v2/live/search?place=Franklin%2C+TN&q=CrossFit+Franklin")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 200
    result = resp.json()["results"][0]
    assert result["source_provenance"]["match_status"] == MatchStatus.TOMTOM_CORROBORATED.value
    assert ConfirmedBy.TOMTOM_BRAND.value in result["source_provenance"]["confirmed_by"]


def test_broad_query_does_not_trigger_brand_search(client, override_auth, monkeypatch):
    brand_search_called = []

    client.app.dependency_overrides[get_settings] = lambda: APISettings(tomtom_api_key="test-key")
    monkeypatch.setattr("api.routes_v2.TomTomClient.geocode", lambda *a, **kw: [_FRANKLIN_ORIGIN])
    monkeypatch.setattr("api.routes_v2.TomTomClient.search_gyms", lambda *a, **kw: [_FRANKLIN_GYM])
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.search",
        lambda *a, **kw: brand_search_called.append(1) or [],
    )
    monkeypatch.setattr("api.routes_v2.load_cached_elements", lambda *a, **kw: None)

    try:
        resp = client.get("/v2/live/search?place=Franklin%2C+TN&q=gym")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 200
    assert brand_search_called == [], "brand search must not be called for broad query 'gym'"
    result = resp.json()["results"][0]
    assert result["source_provenance"]["match_status"] == MatchStatus.TOMTOM_ONLY.value


def test_brand_search_failure_is_non_fatal(client, override_auth, monkeypatch):
    client.app.dependency_overrides[get_settings] = lambda: APISettings(tomtom_api_key="test-key")
    monkeypatch.setattr("api.routes_v2.TomTomClient.geocode", lambda *a, **kw: [_FRANKLIN_ORIGIN])
    monkeypatch.setattr("api.routes_v2.TomTomClient.search_gyms", lambda *a, **kw: [_FRANKLIN_GYM])
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.search",
        lambda *a, **kw: (_ for _ in ()).throw(RequestException("brand search down")),
    )
    monkeypatch.setattr("api.routes_v2.load_cached_elements", lambda *a, **kw: None)

    try:
        resp = client.get("/v2/live/search?place=Franklin%2C+TN&q=CrossFit+Franklin")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 200
    result = resp.json()["results"][0]
    # Brand search failed → gym stays at TOMTOM_ONLY (no upgrade, no error)
    assert result["source_provenance"]["match_status"] == MatchStatus.TOMTOM_ONLY.value


def test_osm_confirmed_not_overwritten_by_brand_search(client, override_auth, monkeypatch):
    import time as _time
    from pathlib import Path
    from gymdb.infrastructure.live_search_cache import LiveSearchCacheEntry

    osm_elements = [{
        "type": "node", "id": 99,
        "lat": _FRANKLIN_GYM.lat, "lon": _FRANKLIN_GYM.lon,
        "tags": {"leisure": "fitness_centre", "name": _FRANKLIN_GYM.name},
    }]
    fresh_cache = LiveSearchCacheEntry(
        cache_path=Path("/fake/cache.json"),
        cached_at_epoch_s=_time.time(),
        elements=osm_elements,
    )

    client.app.dependency_overrides[get_settings] = lambda: APISettings(tomtom_api_key="test-key")
    monkeypatch.setattr("api.routes_v2.TomTomClient.geocode", lambda *a, **kw: [_FRANKLIN_ORIGIN])
    monkeypatch.setattr("api.routes_v2.TomTomClient.search_gyms", lambda *a, **kw: [_FRANKLIN_GYM])
    monkeypatch.setattr("api.routes_v2.TomTomClient.search", lambda *a, **kw: [_BRAND_RESULT])
    monkeypatch.setattr("api.routes_v2.load_cached_elements", lambda *a, **kw: fresh_cache)

    try:
        resp = client.get("/v2/live/search?place=Franklin%2C+TN&q=CrossFit+Franklin")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 200
    result = resp.json()["results"][0]
    # OSM_CONFIRMED from the cache must not be overwritten by the brand search
    assert result["source_provenance"]["match_status"] == MatchStatus.OSM_CONFIRMED.value
    assert ConfirmedBy.OSM.value in result["source_provenance"]["confirmed_by"]
