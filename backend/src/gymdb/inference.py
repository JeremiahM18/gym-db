import re
from gymdb.models import Gym
from gymdb.domain import (INFERRED, INFERENCE_REASONS, IS_24_7, PREMIUM_SCORE, LIFTER_FRIENDLY, TIER, TIER_PREMIUM, TIER_MID, TIER_BASIC, INFERENCE_META, INFERENCE_ENGINE, INFERENCE_VERSION, ENGINE_RULE_BASED)

RULESET_VERSION ="1.0.0"

# Helper functions

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

# Feature extraction

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

# Inference groups

PREMIUM_AMENITY_GROUPS = {
    "water_amenities": {
        "swimming_pool",
        "pool",
        "hot_tub",
        "spa",
    },
    "wellness": {
        "sauna",
        "steam_room",
        "massage",
    },
    "convenience": {
        "shower",
        "childcare",
        "cafe",
    },
}

LIFTER_AMENITY_GROUPS = {
    "strength_training": {
        "weightlifting",
        "powerlifting",
        "strongman",
        "olympic_weightlifting",
        "fitness",
    }
}

# Inference logic

def infer_24_7(features: dict) -> tuple[bool, list[str]]:
    if "24_7" in features["attributes"]:
        return True, ["derived from opening_hours"]
    return False, []

def infer_premium_score(features: dict) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    caps = combined_capabilities(features)

    for group_name, keys in PREMIUM_AMENITY_GROUPS.items():
        if has_any(caps, keys):
            score += 2
            reasons.append(f"has {group_name}")

    # strong "real business / establishment" signal
    if "website" in features["attributes"]:
        score += 1
        reasons.append("has website")

    # opening hours being present is a positive signal
    if "opening_hours" in features["attributes"]:
        score += 1
        reasons.append("has opening_hours")

    return min(score, 10), reasons

def infer_lifter_friendly(features: dict) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    caps = combined_capabilities(features)

    for group_name, keys in LIFTER_AMENITY_GROUPS.items():
        if has_any(caps, keys):
            reasons.append(f"has {group_name}")
            return True, reasons
        
    # Name-based fallback
    for b in features["brand"]:
        if any(word in b for word in ["barbell", "power", "strength"]):
            reasons.append("name suggests strength focus")
            return True, reasons
    
    return False, reasons

def infer_tier(premium_score: int, is_24_7: bool) -> tuple[str, list[str]]:
    reasons = [f"premium_score={premium_score}"]
    if is_24_7:
        reasons.append("24/7 access adds value")

    if premium_score >= 7:
        return TIER_PREMIUM, reasons
    if premium_score >= 3:
        return TIER_MID, reasons
    return TIER_BASIC, reasons

def apply_inference(gym: Gym) -> None:
    features = extract_features(gym.tags)

    is_24_7, r1 = infer_24_7(features)
    premium_score, r2 = infer_premium_score(features)
    lifter_friendly, r3 = infer_lifter_friendly(features)
    tier, r4 = infer_tier(premium_score, is_24_7)

    gym.inferred.update({
        IS_24_7: is_24_7,
        PREMIUM_SCORE: premium_score,
        LIFTER_FRIENDLY: lifter_friendly,
        TIER: tier,
    })

    gym.inference_reasons.update({
        IS_24_7: r1,
        PREMIUM_SCORE: r2,
        LIFTER_FRIENDLY: r3,
        TIER: r4,
    })

    gym.inference_meta.update({
        INFERENCE_ENGINE: ENGINE_RULE_BASED,
        INFERENCE_VERSION: RULESET_VERSION,
    })
