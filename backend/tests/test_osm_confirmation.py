from __future__ import annotations

from gymdb.application.coverage import apply_osm_confirmation
from gymdb.domain.models import Gym
from gymdb.domain.provenance import ConfirmedBy, MatchStatus


def _tomtom_gym(
    name: str,
    lat: float = 35.920,
    lon: float = -86.862,
    *,
    extra_tags: dict | None = None,
) -> Gym:
    gym = Gym(
        name=name,
        norm_name=name.lower().replace(" ", "_"),
        lat=lat,
        lon=lon,
        osm_refs=[],
        tags={"leisure": "fitness_centre", "name": name, **(extra_tags or {})},
    )
    gym.source_provenance = {
        "primary": "tomtom",
        "confirmed_by": [],
        "match_status": MatchStatus.TOMTOM_ONLY.value,
        "external_refs": {},
    }
    return gym


def _osm_element(
    name: str,
    lat: float = 35.920,
    lon: float = -86.862,
    *,
    extra_tags: dict | None = None,
) -> dict:
    return {
        "type": "node",
        "id": 1,
        "lat": lat,
        "lon": lon,
        "tags": {"leisure": "fitness_centre", "name": name, **(extra_tags or {})},
    }


# ---------------------------------------------------------------------------
# OSM_CONFIRMED: exact name match within threshold
# ---------------------------------------------------------------------------


def test_exact_name_match_yields_osm_confirmed():
    gym = _tomtom_gym("Franklin Strength Club")
    elements = [_osm_element("Franklin Strength Club")]

    apply_osm_confirmation([gym], elements)

    assert gym.source_provenance["match_status"] == MatchStatus.OSM_CONFIRMED.value
    assert ConfirmedBy.OSM.value in gym.source_provenance["confirmed_by"]


def test_osm_confirmed_is_case_insensitive():
    gym = _tomtom_gym("CrossFit Franklin")
    elements = [_osm_element("crossfit franklin")]

    apply_osm_confirmation([gym], elements)

    assert gym.source_provenance["match_status"] == MatchStatus.OSM_CONFIRMED.value


# ---------------------------------------------------------------------------
# OSM_NEARBY: different name but within distance
# ---------------------------------------------------------------------------


def test_name_mismatch_within_distance_yields_osm_nearby():
    gym = _tomtom_gym("Franklin Strength Club")
    elements = [_osm_element("FSC Gym")]  # same lat/lon, different name

    apply_osm_confirmation([gym], elements)

    assert gym.source_provenance["match_status"] == MatchStatus.OSM_NEARBY.value
    assert gym.source_provenance["confirmed_by"] == []


# ---------------------------------------------------------------------------
# TOMTOM_ONLY: no OSM element within distance
# ---------------------------------------------------------------------------


def test_no_nearby_element_leaves_tomtom_only():
    gym = _tomtom_gym("Ghost Gym", lat=35.920, lon=-86.862)
    elements = [_osm_element("Remote Gym", lat=36.500, lon=-87.500)]  # ~75 km away

    apply_osm_confirmation([gym], elements)

    assert gym.source_provenance["match_status"] == MatchStatus.TOMTOM_ONLY.value
    assert gym.source_provenance["confirmed_by"] == []


def test_empty_elements_list_is_a_noop():
    gym = _tomtom_gym("Some Gym")
    original_provenance = dict(gym.source_provenance)

    apply_osm_confirmation([gym], [])

    assert gym.source_provenance == original_provenance


# ---------------------------------------------------------------------------
# Skips non-TOMTOM_ONLY gyms
# ---------------------------------------------------------------------------


def test_already_osm_confirmed_gym_is_not_downgraded():
    gym = _tomtom_gym("Confirmed Gym")
    gym.source_provenance["match_status"] = MatchStatus.OSM_CONFIRMED.value
    gym.source_provenance["confirmed_by"] = [ConfirmedBy.OSM.value]
    elements = [_osm_element("Completely Different Name")]

    apply_osm_confirmation([gym], elements)

    assert gym.source_provenance["match_status"] == MatchStatus.OSM_CONFIRMED.value


# ---------------------------------------------------------------------------
# Tag enrichment
# ---------------------------------------------------------------------------


def test_osm_enrichment_keys_are_merged_into_gym_tags():
    gym = _tomtom_gym("Franklin Strength Club")
    elements = [
        _osm_element(
            "Franklin Strength Club",
            extra_tags={
                "opening_hours": "Mo-Fr 06:00-22:00",
                "phone": "+1-615-555-0100",
                "website": "https://franklinstrength.example.com",
            },
        )
    ]

    apply_osm_confirmation([gym], elements)

    assert gym.tags.get("opening_hours") == "Mo-Fr 06:00-22:00"
    assert gym.tags.get("phone") == "+1-615-555-0100"
    assert gym.tags.get("website") == "https://franklinstrength.example.com"


def test_enrichment_does_not_overwrite_existing_gym_tags():
    gym = _tomtom_gym(
        "Franklin Strength Club",
        extra_tags={"website": "https://existing.example.com"},
    )
    elements = [
        _osm_element(
            "Franklin Strength Club",
            extra_tags={"website": "https://osm.example.com"},
        )
    ]

    apply_osm_confirmation([gym], elements)

    assert gym.tags["website"] == "https://existing.example.com"


def test_enrichment_not_applied_when_no_match():
    gym = _tomtom_gym("Ghost Gym", lat=35.920, lon=-86.862)
    elements = [
        _osm_element(
            "Remote Gym",
            lat=36.500,
            lon=-87.500,
            extra_tags={"opening_hours": "24/7"},
        )
    ]

    apply_osm_confirmation([gym], elements)

    assert "opening_hours" not in gym.tags


# ---------------------------------------------------------------------------
# Confirmed_by namespace guard: OSM.value must not collide with TOMTOM_BRAND
# ---------------------------------------------------------------------------


def test_confirmed_by_uses_osm_namespace_not_tomtom():
    gym = _tomtom_gym("Franklin Strength Club")
    elements = [_osm_element("Franklin Strength Club")]

    apply_osm_confirmation([gym], elements)

    confirmed = gym.source_provenance["confirmed_by"]
    assert ConfirmedBy.OSM.value in confirmed
    assert ConfirmedBy.TOMTOM_BRAND.value not in confirmed
