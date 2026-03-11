from gymdb.domain.constants import (
    SPECIALTY_BODYBUILDING,
    SPECIALTY_BOXING,
    SPECIALTY_CLIMBING,
    SPECIALTY_CROSSFIT,
    SPECIALTY_GENERAL,
    SPECIALTY_MARTIAL_ARTS,
    SPECIALTY_POWERLIFTING,
    SPECIALTY_WEIGHTLIFTING,
    SPECIALTY_YOGA,
    TIER_BASIC,
    TIER_MID,
    TIER_PREMIUM,
)
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
_SPECIALTY_RULES: tuple[tuple[str, frozenset[str], tuple[str, ...]], ...] = (
    (
        SPECIALTY_CROSSFIT,
        frozenset({"crossfit"}),
        ("crossfit",),
    ),
    (
        SPECIALTY_POWERLIFTING,
        frozenset({"powerlifting", "strongman"}),
        ("powerlifting", "power", "barbell"),
    ),
    (
        SPECIALTY_WEIGHTLIFTING,
        frozenset({"olympic_weightlifting", "weightlifting"}),
        ("weightlifting", "weightlifting club", "olympic"),
    ),
    (
        SPECIALTY_BODYBUILDING,
        frozenset({"bodybuilding"}),
        ("bodybuilding", "physique"),
    ),
    (
        SPECIALTY_BOXING,
        frozenset({"boxing", "kickboxing"}),
        ("boxing", "kickboxing"),
    ),
    (
        SPECIALTY_MARTIAL_ARTS,
        frozenset({"martial_arts", "jiu_jitsu", "judo", "karate", "mma"}),
        ("mma", "jiu", "jitsu", "martial", "dojo", "boxing gym"),
    ),
    (
        SPECIALTY_YOGA,
        frozenset({"yoga", "pilates"}),
        ("yoga", "pilates"),
    ),
    (
        SPECIALTY_CLIMBING,
        frozenset({"climbing", "bouldering"}),
        ("climbing", "bouldering"),
    ),
)


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


def infer_specialty(
    features: dict,
    *,
    capabilities: set[str] | None = None,
) -> tuple[str, list[str]]:
    active_capabilities = capabilities or combined_capabilities(features)

    for specialty, required_capabilities, keywords in _SPECIALTY_RULES:
        if active_capabilities & required_capabilities:
            return specialty, [f"matched specialty capabilities for {specialty}"]

        for brand in features["brand"]:
            if any(keyword in brand for keyword in keywords):
                return specialty, [f"name suggests {specialty}"]

    return SPECIALTY_GENERAL, ["defaulted to general fitness"]


def infer_tier(premium_score: int, is_24_7: bool) -> tuple[str, list[str]]:
    reasons = [f"premium_score={premium_score}"]
    if is_24_7:
        reasons.append("24/7 access adds value")

    if premium_score >= 7:
        return TIER_PREMIUM, reasons
    if premium_score >= 3:
        return TIER_MID, reasons
    return TIER_BASIC, reasons
