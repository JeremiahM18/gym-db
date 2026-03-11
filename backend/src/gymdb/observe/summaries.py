from gymdb.domain.constants import (
    IS_24_7,
    LIFTER_FRIENDLY,
    PREMIUM_SCORE,
    SPECIALTY,
    SPECIALTY_BODYBUILDING,
    SPECIALTY_BOXING,
    SPECIALTY_CLIMBING,
    SPECIALTY_CROSSFIT,
    SPECIALTY_GENERAL,
    SPECIALTY_MARTIAL_ARTS,
    SPECIALTY_POWERLIFTING,
    SPECIALTY_WEIGHTLIFTING,
    SPECIALTY_YOGA,
    TIER,
    TIER_MID,
    TIER_PREMIUM,
)
from gymdb.infer.result import InferenceResult

_SPECIALTY_SUMMARIES = {
    SPECIALTY_CROSSFIT: "CrossFit-focused training facility",
    SPECIALTY_POWERLIFTING: "Powerlifting-oriented strength gym",
    SPECIALTY_WEIGHTLIFTING: "Olympic weightlifting-focused gym",
    SPECIALTY_BODYBUILDING: "Bodybuilding-focused training gym",
    SPECIALTY_BOXING: "Boxing or striking-focused gym",
    SPECIALTY_MARTIAL_ARTS: "Martial arts-focused training facility",
    SPECIALTY_YOGA: "Yoga or Pilates-focused studio",
    SPECIALTY_CLIMBING: "Climbing-focused gym",
    SPECIALTY_GENERAL: "General fitness gym",
}


def _value(inferred: dict[str, InferenceResult], key: str):
    """
    Safely extract inferred[key]["value"].
    Supports normalized inference dicts.
    """
    item = inferred.get(key)
    if not item:
        return None

    if isinstance(item, dict):
        return item.get("value")

    return getattr(item, "value", None)


def summarize_inference(
    inferred: dict[str, InferenceResult],
) -> dict[str, str]:
    summaries: dict[str, str] = {}

    tier = _value(inferred, TIER)
    is_24_7 = _value(inferred, IS_24_7)
    premium_score = _value(inferred, PREMIUM_SCORE)
    lifter_friendly = _value(inferred, LIFTER_FRIENDLY)
    specialty = _value(inferred, SPECIALTY)

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

    if isinstance(specialty, str):
        summaries[SPECIALTY] = _SPECIALTY_SUMMARIES.get(specialty, specialty)

    return summaries
