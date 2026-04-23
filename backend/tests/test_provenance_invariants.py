"""
Machine-enforced invariants for the tiered source-provenance confidence model.

These tests are the authoritative guard against band overlap.  Any change to
CONFIDENCE_FLOOR, PROVENANCE_BOOST, or TOMTOM_CORROBORATED_HARD_CAP must keep
every assertion in this file passing.
"""

from __future__ import annotations

import pytest

from gymdb.domain.models import Gym
from gymdb.domain.provenance import (
    CONFIDENCE_FLOOR,
    TOMTOM_CORROBORATED_HARD_CAP,
    ConfirmedBy,
    MatchStatus,
    is_cross_source_confirmed,
    is_internally_corroborated,
    is_osm_involved,
)
from gymdb.domain.scoring import compute_confidence


def _gym_with_status(status: MatchStatus, *, extra_tags: dict | None = None) -> Gym:
    tags: dict = {"leisure": "fitness_centre", "name": "Test Gym"}
    if extra_tags:
        tags.update(extra_tags)
    gym = Gym(
        name="Test Gym",
        norm_name="test_gym",
        lat=35.0,
        lon=-86.0,
        osm_refs=[],
        tags=tags,
    )
    gym.source_provenance = {
        "primary": "tomtom",
        "confirmed_by": [],
        "match_status": status.value,
        "external_refs": {},
    }
    return gym


# ---------------------------------------------------------------------------
# Band non-overlap invariants
# ---------------------------------------------------------------------------


def test_tomtom_corroborated_hard_cap_is_below_osm_nearby_floor():
    """max(TOMTOM_CORROBORATED) < min(OSM_NEARBY) — the hard non-overlap invariant."""
    assert TOMTOM_CORROBORATED_HARD_CAP < CONFIDENCE_FLOOR[MatchStatus.OSM_NEARBY]


def test_osm_nearby_floor_is_below_osm_confirmed_floor():
    assert (
        CONFIDENCE_FLOOR[MatchStatus.OSM_NEARBY]
        < CONFIDENCE_FLOOR[MatchStatus.OSM_CONFIRMED]
    )


def test_tomtom_only_and_corroborated_share_floor():
    assert (
        CONFIDENCE_FLOOR[MatchStatus.TOMTOM_ONLY]
        == CONFIDENCE_FLOOR[MatchStatus.TOMTOM_CORROBORATED]
    )


# ---------------------------------------------------------------------------
# Floor enforcement: a sparse gym is lifted to the correct floor
# ---------------------------------------------------------------------------


def test_tomtom_only_floor_applied_to_sparse_gym():
    gym = _gym_with_status(MatchStatus.TOMTOM_ONLY)
    score = compute_confidence(gym)
    assert score >= CONFIDENCE_FLOOR[MatchStatus.TOMTOM_ONLY]


def test_osm_nearby_floor_applied_to_sparse_gym():
    gym = _gym_with_status(MatchStatus.OSM_NEARBY)
    score = compute_confidence(gym)
    assert score >= CONFIDENCE_FLOOR[MatchStatus.OSM_NEARBY]


def test_osm_confirmed_floor_applied_to_sparse_gym():
    gym = _gym_with_status(MatchStatus.OSM_CONFIRMED)
    score = compute_confidence(gym)
    assert score >= CONFIDENCE_FLOOR[MatchStatus.OSM_CONFIRMED]


# ---------------------------------------------------------------------------
# Hard cap: TOMTOM_CORROBORATED can never reach the OSM tier
# ---------------------------------------------------------------------------


def test_tomtom_corroborated_hard_cap_enforced_even_for_rich_gym():
    """A gym with every tag filled in must still not exceed the hard cap."""
    gym = _gym_with_status(
        MatchStatus.TOMTOM_CORROBORATED,
        extra_tags={
            "addr:housenumber": "100",
            "addr:street": "Main St",
            "addr:city": "Franklin",
            "website": "https://example.com",
            "phone": "+1-615-555-0100",
            "opening_hours": "24/7",
            "brand": "Example Brand",
            "brand:wikidata": "Q123",
            "operator": "Example Operator",
            "operator:wikidata": "Q456",
            "contact:instagram": "@example",
            "contact:facebook": "example",
        },
    )
    score = compute_confidence(gym)
    assert score <= TOMTOM_CORROBORATED_HARD_CAP


# ---------------------------------------------------------------------------
# OSM-absence neutrality: legacy / unset provenance must not receive floors
# ---------------------------------------------------------------------------


def test_legacy_unconfirmed_provenance_scores_low():
    """Default provenance ("unconfirmed") must not trigger any floor."""
    gym = Gym(
        name="Gym",
        norm_name="gym",
        lat=35.0,
        lon=-86.0,
        osm_refs=[],
        tags={"leisure": "fitness_centre", "name": "Gym"},
    )
    # source_provenance defaults to {"match_status": "unconfirmed", ...}
    score = compute_confidence(gym)
    assert score <= 0.12


def test_legacy_matched_provenance_still_scores_via_external_validation():
    """Old ingest-style "matched" provenance must not receive the new floors
    but must still benefit from _external_validation_score."""
    gym = Gym(
        name="Life Time",
        norm_name="life_time",
        lat=35.0,
        lon=-86.0,
        osm_refs=[],
        tags={"leisure": "fitness_centre", "name": "Life Time", "brand": "Life Time"},
    )
    gym.source_provenance = {
        "primary": "osm",
        "confirmed_by": ["tomtom"],
        "match_status": "matched",
        "external_refs": {
            "tomtom": {
                "provider": "tomtom",
                "external_id": "tt-1",
                "name": "Life Time",
                "distance_m": 24.0,
                "url": "https://www.lifetime.life/",
                "status": "matched",
            }
        },
    }
    score = compute_confidence(gym)
    # Must score via tag density + external validation, not provenance floors.
    # The TOMTOM_ONLY floor (0.40) must NOT apply here.
    assert score >= 0.30  # old validation bonus applies
    assert (
        score < CONFIDENCE_FLOOR[MatchStatus.OSM_NEARBY]
    )  # not floor-lifted to OSM tier


# ---------------------------------------------------------------------------
# Predicate correctness
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "confirmed_by, expected",
    [
        ([ConfirmedBy.OSM], True),
        (["osm"], True),
        ([ConfirmedBy.TOMTOM_BRAND], False),
        (["tomtom:brand_search"], False),
        ([], False),
    ],
)
def test_is_cross_source_confirmed(confirmed_by, expected):
    provenance = {"confirmed_by": confirmed_by}
    assert is_cross_source_confirmed(provenance) is expected


@pytest.mark.parametrize(
    "status, expected",
    [
        (MatchStatus.OSM_NEARBY.value, True),
        (MatchStatus.OSM_CONFIRMED.value, True),
        (MatchStatus.TOMTOM_ONLY.value, False),
        (MatchStatus.TOMTOM_CORROBORATED.value, False),
        ("unconfirmed", False),
    ],
)
def test_is_osm_involved(status, expected):
    provenance = {"match_status": status}
    assert is_osm_involved(provenance) is expected


@pytest.mark.parametrize(
    "status, expected",
    [
        (MatchStatus.TOMTOM_CORROBORATED.value, True),
        (MatchStatus.TOMTOM_ONLY.value, False),
        (MatchStatus.OSM_CONFIRMED.value, False),
        ("matched", False),
    ],
)
def test_is_internally_corroborated(status, expected):
    provenance = {"match_status": status}
    assert is_internally_corroborated(provenance) is expected
