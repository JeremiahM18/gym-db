from gymdb.domain.constants import (
    IS_24_7,
    LIFTER_FRIENDLY,
    PREMIUM_SCORE,
    TIER,
    TIER_MID,
    TIER_PREMIUM,
)
from gymdb.infer.result import InferenceResult


def _value(inferred: dict[str, InferenceResult], key: str):
    """
    Safely extract inferred[key]["value"].
    Supports normalized inference dicts.
    """
    item = inferred.get(key)
    if not item:
        return None
    
    # Normalized inference (API-safe)
    if isinstance(item, dict):
        return item.get("value")
    
    # Raw InferenceResult (engine-internal)
    return getattr(item, "value", None)

def summarize_inference(
    inferred: dict[str, InferenceResult]
) -> dict[str, str]:
    summaries: dict[str, str] = {}

    # Tier summary
    tier = _value(inferred, TIER)
    is_24_7 = _value(inferred, IS_24_7)
    premium_score = _value(inferred, PREMIUM_SCORE)
    lifter_friendly = _value(inferred, LIFTER_FRIENDLY)

    if tier == TIER_PREMIUM:
        summaries[TIER] = "Premium gym with high-quality amenities"
    elif tier == TIER_MID:
        summaries[TIER] = "Mid-tier gym with solid amenities"
    else:
        summaries[TIER] = "Basic gym"

    if is_24_7 is True:
        summaries[IS_24_7] = "Open 24/7"

    if isinstance(premium_score, int):
        summaries[PREMIUM_SCORE] = f"Premium score: {premium_score}"

    if lifter_friendly is True:
        summaries[LIFTER_FRIENDLY] = "Strength-focused gym"

    return summaries



