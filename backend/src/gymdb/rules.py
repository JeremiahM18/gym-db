from gymdb.domain import(
    TIER_BASIC, TIER_MID, TIER_PREMIUM,
)

from gymdb.features import combined_capabilities


def infer_24_7(features: dict) -> tuple[bool, list[str]]:
    if "24_7" in features["attributes"]:
        return True, ["derived from opening_hours"]
    return False, []

def infer_lifter_friendly(features: dict) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    caps = combined_capabilities(features)

    if caps & {
        "weightlifting",
        "powerlifting",
        "strongman",
        "olympic_weightlifting",
        "fitness",
    }:
        reasons.append("has strength training amenities")
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