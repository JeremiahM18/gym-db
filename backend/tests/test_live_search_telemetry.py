"""
Tests for live-search telemetry instrumentation.

The shared ops-state store is isolated per test by the global test fixture in
conftest, so every test starts from a clean snapshot.
"""

from __future__ import annotations

import time as _time
from pathlib import Path

from api.main import app
from api.settings import APISettings, get_settings
from gymdb.infrastructure.live_search_cache import LiveSearchCacheEntry
from gymdb.infrastructure.overpass_client import OverpassUnavailableError
from gymdb.infrastructure.tomtom_client import TomTomPlace
from gymdb.observe.metrics import (
    record_cache_probe,
    record_enrich_dispatched,
    record_enrich_outcome,
    record_osm_confirmation_outcomes,
    snapshot_live_search_metrics,
)

# ---------------------------------------------------------------------------
# record_cache_probe
# ---------------------------------------------------------------------------


def test_cache_miss_recorded_when_no_entry():
    record_cache_probe(cache_exists=False, is_fresh=False)
    snap = snapshot_live_search_metrics()
    assert snap["cache_miss"] == 1
    assert snap["cache_hit"] == 0
    assert snap["cache_stale"] == 0


def test_cache_hit_recorded_when_fresh_entry_exists():
    record_cache_probe(cache_exists=True, is_fresh=True)
    snap = snapshot_live_search_metrics()
    assert snap["cache_hit"] == 1
    assert snap["cache_miss"] == 0
    assert snap["cache_stale"] == 0


def test_cache_stale_recorded_when_entry_exists_but_expired():
    record_cache_probe(cache_exists=True, is_fresh=False)
    snap = snapshot_live_search_metrics()
    assert snap["cache_stale"] == 1
    assert snap["cache_hit"] == 0
    assert snap["cache_miss"] == 0


# ---------------------------------------------------------------------------
# record_enrich_dispatched
# ---------------------------------------------------------------------------


def test_enrich_dispatched_increments_counter():
    record_enrich_dispatched()
    record_enrich_dispatched()
    snap = snapshot_live_search_metrics()
    assert snap["enrich_dispatched"] == 2


# ---------------------------------------------------------------------------
# record_enrich_outcome
# ---------------------------------------------------------------------------


def test_enrich_success_recorded():
    record_enrich_outcome(success=True)
    snap = snapshot_live_search_metrics()
    assert snap["enrich_success"] == 1
    assert snap["enrich_failure"] == 0
    assert snap["enrich_write_failure"] == 0


def test_enrich_failure_recorded_on_overpass_error():
    record_enrich_outcome(success=False)
    snap = snapshot_live_search_metrics()
    assert snap["enrich_failure"] == 1
    assert snap["enrich_success"] == 0
    assert snap["enrich_write_failure"] == 0


def test_enrich_write_failure_recorded():
    record_enrich_outcome(success=False, write_failed=True)
    snap = snapshot_live_search_metrics()
    assert snap["enrich_write_failure"] == 1
    assert snap["enrich_failure"] == 0
    assert snap["enrich_success"] == 0


# ---------------------------------------------------------------------------
# record_osm_confirmation_outcomes
# ---------------------------------------------------------------------------


def test_osm_confirmation_outcomes_accumulated():
    record_osm_confirmation_outcomes(osm_confirmed=3, osm_nearby=1, tomtom_only=6)
    record_osm_confirmation_outcomes(osm_confirmed=0, osm_nearby=2, tomtom_only=4)
    snap = snapshot_live_search_metrics()
    assert snap["osm_confirmed"] == 3
    assert snap["osm_nearby"] == 3
    assert snap["tomtom_only"] == 10


# ---------------------------------------------------------------------------
# snapshot_live_search_metrics — fixed key set
# ---------------------------------------------------------------------------


def test_snapshot_returns_all_keys_even_when_zero():
    snap = snapshot_live_search_metrics()
    expected_keys = {
        "cache_hit",
        "cache_miss",
        "cache_stale",
        "enrich_dispatched",
        "enrich_success",
        "enrich_failure",
        "enrich_write_failure",
        "osm_confirmed",
        "osm_nearby",
        "tomtom_only",
    }
    assert set(snap.keys()) == expected_keys
    assert all(v == 0 for v in snap.values())


# ---------------------------------------------------------------------------
# background_tasks integration — record_enrich_outcome called from task
# ---------------------------------------------------------------------------


def test_background_overpass_enrich_records_success_on_clean_run(monkeypatch):
    from api.background_tasks import background_overpass_enrich

    monkeypatch.setattr(
        "api.background_tasks.fetch_gyms",
        lambda *a, **kw: [
            {"type": "node", "id": 1, "lat": 35.0, "lon": -86.0, "tags": {}}
        ],
    )
    monkeypatch.setattr(
        "api.background_tasks.write_cached_elements",
        lambda *a, **kw: Path("/fake/cache.json"),
    )

    background_overpass_enrich(
        lat=35.0,
        lon=-86.0,
        radius_m=25000,
        origin_name="Franklin, TN",
        cache_root=Path("/fake"),
        timeout_seconds=5,
        max_attempts=1,
    )

    snap = snapshot_live_search_metrics()
    assert snap["enrich_success"] == 1
    assert snap["enrich_failure"] == 0


def test_background_overpass_enrich_records_failure_on_overpass_error(monkeypatch):
    from api.background_tasks import background_overpass_enrich

    monkeypatch.setattr(
        "api.background_tasks.fetch_gyms",
        lambda *a, **kw: (_ for _ in ()).throw(OverpassUnavailableError("down")),
    )

    background_overpass_enrich(
        lat=35.0,
        lon=-86.0,
        radius_m=25000,
        origin_name="Franklin, TN",
        cache_root=Path("/fake"),
        timeout_seconds=5,
        max_attempts=1,
    )

    snap = snapshot_live_search_metrics()
    assert snap["enrich_failure"] == 1
    assert snap["enrich_success"] == 0


def test_background_overpass_enrich_records_write_failure(monkeypatch):
    from api.background_tasks import background_overpass_enrich

    monkeypatch.setattr(
        "api.background_tasks.fetch_gyms",
        lambda *a, **kw: [],
    )
    monkeypatch.setattr(
        "api.background_tasks.write_cached_elements",
        lambda *a, **kw: (_ for _ in ()).throw(OSError("disk full")),
    )

    background_overpass_enrich(
        lat=35.0,
        lon=-86.0,
        radius_m=25000,
        origin_name="Franklin, TN",
        cache_root=Path("/fake"),
        timeout_seconds=5,
        max_attempts=1,
    )

    snap = snapshot_live_search_metrics()
    assert snap["enrich_write_failure"] == 1
    assert snap["enrich_success"] == 0


# ---------------------------------------------------------------------------
# Route-level telemetry — cache probe and confirmation outcomes via TestClient
# ---------------------------------------------------------------------------


def test_live_search_records_cache_miss_on_first_request(
    client, override_auth, monkeypatch
):
    origin = TomTomPlace(
        id="p1",
        name="Franklin, TN",
        lat=35.925,
        lon=-86.869,
        address="Franklin, TN",
        city="Franklin",
        country_code="US",
        url=None,
        raw={},
    )
    gym_place = TomTomPlace(
        id="g1",
        name="Test Gym",
        lat=35.920,
        lon=-86.862,
        address="1 Main St",
        city="Franklin",
        country_code="US",
        url=None,
        raw={},
    )

    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key="k"
    )
    monkeypatch.setattr("api.routes_v2.TomTomClient.geocode", lambda *a, **kw: [origin])
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.search_gyms", lambda *a, **kw: [gym_place]
    )
    monkeypatch.setattr("api.routes_v2.load_cached_elements", lambda *a, **kw: None)
    monkeypatch.setattr("api.routes_v2.background_overpass_enrich", lambda **kw: None)

    try:
        resp = client.get("/v2/live/search?place=Franklin%2C%20TN")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 200
    snap = snapshot_live_search_metrics()
    assert snap["cache_miss"] == 1
    assert snap["enrich_dispatched"] == 1


def test_live_search_records_osm_confirmation_outcomes(
    client, override_auth, monkeypatch
):
    origin = TomTomPlace(
        id="p1",
        name="Franklin, TN",
        lat=35.925,
        lon=-86.869,
        address="Franklin, TN",
        city="Franklin",
        country_code="US",
        url=None,
        raw={},
    )
    gym_place = TomTomPlace(
        id="g1",
        name="Test Gym",
        lat=35.920,
        lon=-86.862,
        address="1 Main St",
        city="Franklin",
        country_code="US",
        url=None,
        raw={},
    )
    fresh_cache = LiveSearchCacheEntry(
        cache_path=Path("/fake/cache.json"),
        cached_at_epoch_s=_time.time(),
        elements=[
            {
                "type": "node",
                "id": 99,
                "lat": gym_place.lat,
                "lon": gym_place.lon,
                "tags": {"leisure": "fitness_centre", "name": gym_place.name},
            }
        ],
    )

    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        tomtom_api_key="k"
    )
    monkeypatch.setattr("api.routes_v2.TomTomClient.geocode", lambda *a, **kw: [origin])
    monkeypatch.setattr(
        "api.routes_v2.TomTomClient.search_gyms", lambda *a, **kw: [gym_place]
    )
    monkeypatch.setattr(
        "api.routes_v2.load_cached_elements", lambda *a, **kw: fresh_cache
    )
    monkeypatch.setattr("api.routes_v2.background_overpass_enrich", lambda **kw: None)

    try:
        resp = client.get("/v2/live/search?place=Franklin%2C%20TN")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert resp.status_code == 200
    snap = snapshot_live_search_metrics()
    assert snap["osm_confirmed"] == 1
    assert snap["cache_hit"] == 1
    assert snap["enrich_dispatched"] == 0
