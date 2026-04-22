from __future__ import annotations

from enum import Enum
from typing import Any, Final


class MatchStatus(str, Enum):
    TOMTOM_ONLY = "tomtom_only"
    TOMTOM_CORROBORATED = "tomtom_corroborated"
    OSM_NEARBY = "osm_nearby"
    OSM_CONFIRMED = "osm_confirmed"


class ConfirmedBy(str, Enum):
    OSM = "osm"
    TOMTOM_BRAND = "tomtom:brand_search"


class PrimarySource(str, Enum):
    TOMTOM = "tomtom"
    OSM = "osm"


# Confidence floors: the scored value is raised to at least this threshold.
CONFIDENCE_FLOOR: Final[dict[MatchStatus, float]] = {
    MatchStatus.TOMTOM_ONLY: 0.40,
    MatchStatus.TOMTOM_CORROBORATED: 0.40,
    MatchStatus.OSM_NEARBY: 0.70,
    MatchStatus.OSM_CONFIRMED: 0.85,
}

# Additive boost applied on top of the tag-density score before the floor.
PROVENANCE_BOOST: Final[dict[MatchStatus, float]] = {
    MatchStatus.TOMTOM_ONLY: 0.00,
    MatchStatus.TOMTOM_CORROBORATED: 0.06,
    MatchStatus.OSM_NEARBY: 0.00,
    MatchStatus.OSM_CONFIRMED: 0.00,
}

# TOMTOM_CORROBORATED can never exceed this value, enforcing band non-overlap
# with OSM tiers (floor 0.70).  max(TOMTOM_CORROBORATED) < min(OSM_NEARBY).
TOMTOM_CORROBORATED_HARD_CAP: Final[float] = 0.68

# Haversine threshold for treating an OSM element as "nearby" a TomTom gym.
OSM_MATCH_DISTANCE_METERS: Final[float] = 250.0

# OSM tag keys whose values are copied onto a gym during enrichment.
OSM_ENRICH_KEYS: Final[frozenset[str]] = frozenset(
    {
        "opening_hours",
        "phone",
        "contact:phone",
        "website",
        "contact:website",
        "operator",
        "brand",
        "addr:street",
        "addr:housenumber",
        "addr:postcode",
    }
)


def is_cross_source_confirmed(provenance: dict[str, Any]) -> bool:
    """True only when OSM independently corroborates a TomTom gym."""
    return ConfirmedBy.OSM in provenance.get("confirmed_by", [])


def is_osm_involved(provenance: dict[str, Any]) -> bool:
    """True when the gym reached OSM_NEARBY or OSM_CONFIRMED tier."""
    return provenance.get("match_status") in (
        MatchStatus.OSM_NEARBY,
        MatchStatus.OSM_CONFIRMED,
    )


def is_internally_corroborated(provenance: dict[str, Any]) -> bool:
    """True when TomTom brand search agreed with category search (same DB — weak signal)."""
    return provenance.get("match_status") == MatchStatus.TOMTOM_CORROBORATED
