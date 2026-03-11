"""
Inference signals.

Signals are small, reusable pieces of evidence derived from normalized features.
They do not make decisions or apply thresholds.
"""

# helpers

def _has_any(features: set[str], candidates: set[str]) -> bool:
    return not features.isdisjoint(candidates)

# premium-related signals

def has_water_amenities(capabilites: set[str]) -> tuple[bool, str | None]:
    # Signal: gym offers water-based amenities 
    keys = {"swimming_pool", "pool", "hot_tub", "spa"}
    if _has_any(capabilites, keys):
        return True, "has water amenities"
    return False, None

def has_wellness_amenities(capabilities: set[str]) -> tuple[bool, str | None]:
    # Signal: gym offers wellness amenities
    keys = {"sauna", "steam_room", "massage"}
    if _has_any(capabilities, keys):
        return True, "has wellness amenities"
    return False, None

def has_convenience_amenities(capabilities: set[str]) -> tuple[bool, str | None]:
    # Signal: gym offers convenience amenities
    keys = {"shower", "childcare", "cafe"}
    if _has_any(capabilities, keys):
        return True, "has convenience amenities"
    return False, None

def has_website(attributes: set[str]) -> tuple[bool, str | None]:
    # Signal: gym has a website listed
    if "website" in attributes:
        return True, "has website"
    return False, None

def has_opening_hours(attributes: set[str]) -> tuple[bool, str | None]:
    # Signal: gym provides opening hours metadata
    if "opening_hours" in attributes:
        return True, "has opening hours"
    return False, None


