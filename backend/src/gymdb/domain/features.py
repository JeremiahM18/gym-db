import re
from typing import Any

_TRUTHY_VALUES = frozenset({"yes", "true", "1"})
_SPLIT_SEPARATOR = ";"
_OPEN_24_7_RE = re.compile(r"\b0{1,2}:?00\s*-\s*24:?00\b")


def _truthy(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return value.strip().lower() in _TRUTHY_VALUES


def split_semicolon(value: Any) -> set[str]:
    if not isinstance(value, str) or not value:
        return set()
    return {part.strip().lower() for part in value.split(_SPLIT_SEPARATOR)}


def combined_capabilities(features: dict[str, set[str]]) -> set[str]:
    return features["amenities"] | features["sports"] | features["attributes"]


def extract_features(tags: dict[str, Any]) -> dict[str, set[str]]:
    features: dict[str, set[str]] = {
        "amenities": set(),
        "sports": set(),
        "attributes": set(),
        "brand": set(),
    }

    for key, value in tags.items():
        if _truthy(value):
            features["amenities"].add(key.lower())

    sport = tags.get("sport")
    if sport is not None:
        features["sports"].update(split_semicolon(sport))

    leisure = tags.get("leisure")
    if isinstance(leisure, str):
        features["amenities"].add(leisure.lower())

    if "website" in tags or "contact:website" in tags:
        features["attributes"].add("website")

    opening_hours = tags.get("opening_hours")
    if isinstance(opening_hours, str):
        features["attributes"].add("opening_hours")

        normalized_hours = opening_hours.lower()
        if "24/7" in normalized_hours or _OPEN_24_7_RE.search(normalized_hours):
            features["attributes"].add("24_7")

    brand = tags.get("brand")
    if isinstance(brand, str):
        features["brand"].add(brand.lower())

    name = tags.get("name")
    if isinstance(name, str):
        features["brand"].add(name.lower())

    return features
