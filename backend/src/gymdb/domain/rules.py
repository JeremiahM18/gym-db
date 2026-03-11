from gymdb.domain.constants import TIER_BASIC, TIER_MID, TIER_PREMIUM
from gymdb.domain.features import combined_capabilities

_STRENGTH_CAPABILITIES = frozenset(
    {
        "weightlifting",
        "powerlifting",
        "strongman",
        "olympic_weightlifting",
        "fitness",
    }
)
_STRENGTH_BRAND_KEYWORDS = ("barbell", "power", "strength")


def infer_24_7(features: dict) -> tuple[bool, list[str]]:
    if "24_7" in features["attributes"]:
        return True, ["derived from opening_hours"]
    return False, []


def infer_lifter_friendly(
    features: dict,
    *,
    capabilities: set[str] | None = None,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    active_capabilities = capabilities or combined_capabilities(features)

    if active_capabilities & _STRENGTH_CAPABILITIES:
        reasons.append("has strength training amenities")
        return True, reasons

    for brand in features["brand"]:
        if any(keyword in brand for keyword in _STRENGTH_BRAND_KEYWORDS):
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
