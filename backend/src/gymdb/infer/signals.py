"""
Inference signals.

Signals are small, reusable pieces of evidence derived from normalized features.
They do not make decisions or apply thresholds.
"""

_WATER_AMENITIES = frozenset({"swimming_pool", "pool", "hot_tub", "spa"})
_WELLNESS_AMENITIES = frozenset({"sauna", "steam_room", "massage"})
_CONVENIENCE_AMENITIES = frozenset({"shower", "childcare", "cafe"})


def _has_any(features: set[str], candidates: frozenset[str]) -> bool:
    return not features.isdisjoint(candidates)


def has_water_amenities(capabilities: set[str]) -> tuple[bool, str | None]:
    if _has_any(capabilities, _WATER_AMENITIES):
        return True, "has water amenities"
    return False, None


def has_wellness_amenities(capabilities: set[str]) -> tuple[bool, str | None]:
    if _has_any(capabilities, _WELLNESS_AMENITIES):
        return True, "has wellness amenities"
    return False, None


def has_convenience_amenities(capabilities: set[str]) -> tuple[bool, str | None]:
    if _has_any(capabilities, _CONVENIENCE_AMENITIES):
        return True, "has convenience amenities"
    return False, None


def has_website(attributes: set[str]) -> tuple[bool, str | None]:
    if "website" in attributes:
        return True, "has website"
    return False, None


def has_opening_hours(attributes: set[str]) -> tuple[bool, str | None]:
    if "opening_hours" in attributes:
        return True, "has opening hours"
    return False, None
