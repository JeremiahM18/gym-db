"""
Inference signals.

Signals are small, reusable pieces of evidence derived from normalized features.
They do not make decisions or apply thresholds.
"""
from typing import Tuple, Optional, Set

# helpers

def _has_any(features: Set[str], candidates: Set[str]) -> bool:
    return not features.isdisjoint(candidates)

# premium-related signals

def has_water_amenities(capabilites: Set[str]) -> Tuple[bool, Optional[str]]:
    # Signal: gym offers water-based amenities 
    keys = {"swimming_pool", "pool", "hot_tub", "spa"}
    if _has_any(capabilites, keys):
        return True, "has water amenities"
    return False, None

def has_wellness_amenities(capabilities: Set[str]) -> Tuple[bool, Optional[str]]:
    # Signal: gym offers wellness amenities
    keys = {"sauna", "steam_room", "massage"}
    if _has_any(capabilities, keys):
        return True, "has wellness amenities"
    return False, None

def has_convenience_amenities(capabilities: Set[str]) -> Tuple[bool, Optional[str]]:
    # Signal: gym offers convenience amenities
    keys = {"shower", "childcare", "cafe"}
    if _has_any(capabilities, keys):
        return True, "has convenience amenities"
    return False, None

def has_website(attributes: Set[str]) -> Tuple[bool, Optional[str]]:
    # Signal: gym has a website listed
    if "website" in attributes:
        return True, "has website"
    return False, None

def has_opening_hours(attributes: Set[str]) -> Tuple[bool, Optional[str]]:
    # Signal: gym provides opening hours metadata
    if "opening_hours" in attributes:
        return True, "has opening hours"
    return False, None

