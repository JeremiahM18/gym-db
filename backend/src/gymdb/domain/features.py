import re


def _truthy(v: str | None) -> bool:
    if v is None:
        return False
    return v.strip().lower() in {"yes", "true", "1"}

def has_any(feature_set: set[str], candidates: set[str]) -> bool:
    return not feature_set.isdisjoint(candidates)

def split_semicolon(v: str | None) -> set[str]:
    if not v:
        return set()
    return {x.strip().lower() for x in v.split(";")}

def combined_capabilities(features: dict) -> set[str]:
    return features["amenities"] | features["sports"] | features["attributes"]

def extract_features(tags: dict) -> dict[str, set[str]]:
    # Normalize OSM tags into semantic feature sets
    features: dict[str, set[str]] = {
        "amenities": set(),
        "sports": set(),
        "attributes": set(),
        "brand": set(),
    }

    # Amenity-style boolean tags
    for k, v in tags.items():
        if _truthy(v):
            features["amenities"].add(k.lower())

    # Handle sport=swimming; fitness; basketball
    if "sport" in tags:
        features["sports"] |= split_semicolon(tags["sport"])

    # Handle other attributes
    if "leisure" in tags:
        features["amenities"].add(tags["leisure"].lower())

    if "website" in tags or "contact:website" in tags:
        features["attributes"].add("website")

    if "opening_hours" in tags:
        features["attributes"].add("opening_hours")

        oh = tags["opening_hours"].lower()
        if "24/7" in oh or re.search(r"\b0{1,2}:?00\s*-\s*24:?00\b", oh):
            features["attributes"].add("24_7")

    # Brand tags
    if "brand" in tags:
        features["brand"].add(tags["brand"].lower())
    if "name" in tags:
        features["brand"].add(tags["name"].lower())

    return features

