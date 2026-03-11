from dataclasses import dataclass

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
)
from gymdb.domain.features import combined_capabilities
from gymdb.infer.result import InferenceResult

_STRENGTH_CAPABILITIES = frozenset(
    {
        "weightlifting",
        "powerlifting",
        "strongman",
        "olympic_weightlifting",
        "fitness",
    }
)
_SPECIALTY_EXPECTED_CAPABILITIES: dict[str, frozenset[str]] = {
    SPECIALTY_CROSSFIT: frozenset({"crossfit"}),
    SPECIALTY_POWERLIFTING: frozenset({"powerlifting", "strongman"}),
    SPECIALTY_WEIGHTLIFTING: frozenset({"weightlifting", "olympic_weightlifting"}),
    SPECIALTY_BODYBUILDING: frozenset({"bodybuilding"}),
    SPECIALTY_BOXING: frozenset({"boxing", "kickboxing"}),
    SPECIALTY_MARTIAL_ARTS: frozenset(
        {"martial_arts", "jiu_jitsu", "judo", "karate", "mma"}
    ),
    SPECIALTY_YOGA: frozenset({"yoga", "pilates"}),
    SPECIALTY_CLIMBING: frozenset({"climbing", "bouldering"}),
}
_STRENGTH_SPECIALTIES = frozenset(
    {SPECIALTY_POWERLIFTING, SPECIALTY_WEIGHTLIFTING, SPECIALTY_BODYBUILDING}
)
_NON_STRENGTH_CAPABILITIES = frozenset(
    {
        "boxing",
        "kickboxing",
        "martial_arts",
        "jiu_jitsu",
        "judo",
        "karate",
        "mma",
        "yoga",
        "pilates",
        "climbing",
        "bouldering",
    }
)
_TWENTY_FOUR_HOUR_HINTS = ("24 hour", "24hr", "24/7")


@dataclass(frozen=True)
class InferenceDiagnostics:
    field_confidence: dict[str, float]
    contradictions: dict[str, list[str]]


def _bounded(value: float) -> float:
    return round(min(max(value, 0.05), 0.99), 2)


def _apply_penalty(
    field: str,
    base: float,
    contradictions: dict[str, list[str]],
) -> float:
    penalty = min(len(contradictions.get(field, [])) * 0.14, 0.35)
    return _bounded(base - penalty)


def detect_contradictions(
    features: dict[str, set[str]],
    inferred: dict[str, InferenceResult],
) -> dict[str, list[str]]:
    contradictions: dict[str, list[str]] = {}
    capabilities = combined_capabilities(features)
    brands = features["brand"]

    specialty_result = inferred[SPECIALTY]
    specialty_value = str(specialty_result.value)
    specialty_reasons = specialty_result.reasons
    expected_capabilities = _SPECIALTY_EXPECTED_CAPABILITIES.get(specialty_value)

    if expected_capabilities and not (capabilities & expected_capabilities):
        contradictions.setdefault(SPECIALTY, []).append(
            "specialty was inferred without matching tagged capabilities"
        )

    if (
        specialty_value in _STRENGTH_SPECIALTIES
        and capabilities & _NON_STRENGTH_CAPABILITIES
    ):
        if not (capabilities & _STRENGTH_CAPABILITIES):
            contradictions.setdefault(SPECIALTY, []).append(
                "strength specialty conflicts with non-strength activity tags"
            )

    if bool(inferred[LIFTER_FRIENDLY].value) and not (
        capabilities & _STRENGTH_CAPABILITIES
    ):
        contradictions.setdefault(LIFTER_FRIENDLY, []).append(
            "lifter-friendly inference lacks tagged strength amenities"
        )
        if any("name suggests" in reason for reason in specialty_reasons):
            contradictions.setdefault(SPECIALTY, []).append(
                "specialty depends on naming, but tags do not support strength"
            )

    if not bool(inferred[IS_24_7].value):
        if any(
            any(hint in brand for hint in _TWENTY_FOUR_HOUR_HINTS) for brand in brands
        ):
            contradictions.setdefault(IS_24_7, []).append(
                "name suggests 24/7 access but opening_hours do not confirm it"
            )

    return contradictions


def compute_field_confidence(
    features: dict[str, set[str]],
    inferred: dict[str, InferenceResult],
    contradictions: dict[str, list[str]],
) -> dict[str, float]:
    capabilities = combined_capabilities(features)
    attributes = features["attributes"]

    premium_value = int(inferred[PREMIUM_SCORE].value)
    premium_reasons = inferred[PREMIUM_SCORE].reasons
    premium_base = 0.35 + (premium_value * 0.05) + (min(len(premium_reasons), 4) * 0.05)
    premium_confidence = _apply_penalty(PREMIUM_SCORE, premium_base, contradictions)

    is_24_7_value = bool(inferred[IS_24_7].value)
    if is_24_7_value:
        is_24_7_base = 0.98
    elif "opening_hours" in attributes:
        is_24_7_base = 0.84
    else:
        is_24_7_base = 0.48
    is_24_7_confidence = _apply_penalty(IS_24_7, is_24_7_base, contradictions)

    lifter_value = bool(inferred[LIFTER_FRIENDLY].value)
    lifter_reasons = inferred[LIFTER_FRIENDLY].reasons
    if lifter_value and (capabilities & _STRENGTH_CAPABILITIES):
        lifter_base = 0.91
    elif lifter_value:
        lifter_base = 0.67
    elif capabilities & _NON_STRENGTH_CAPABILITIES:
        lifter_base = 0.76
    elif "fitness_centre" in capabilities or "fitness" in capabilities:
        lifter_base = 0.62
    else:
        lifter_base = 0.52
    if any("name suggests" in reason for reason in lifter_reasons):
        lifter_base -= 0.04
    lifter_confidence = _apply_penalty(LIFTER_FRIENDLY, lifter_base, contradictions)

    specialty_value = str(inferred[SPECIALTY].value)
    specialty_reasons = inferred[SPECIALTY].reasons
    expected_capabilities = _SPECIALTY_EXPECTED_CAPABILITIES.get(
        specialty_value, frozenset()
    )
    if specialty_value == SPECIALTY_GENERAL:
        specialty_base = 0.66 if capabilities else 0.48
    elif expected_capabilities and (capabilities & expected_capabilities):
        specialty_base = 0.93
    elif any("name suggests" in reason for reason in specialty_reasons):
        specialty_base = 0.72
    else:
        specialty_base = 0.58
    specialty_confidence = _apply_penalty(SPECIALTY, specialty_base, contradictions)

    tier_reasons = inferred[TIER].reasons
    tier_base = 0.52 + (premium_confidence * 0.32) + (min(len(tier_reasons), 2) * 0.04)
    if is_24_7_value:
        tier_base += 0.05
    tier_confidence = _apply_penalty(TIER, tier_base, contradictions)

    return {
        PREMIUM_SCORE: premium_confidence,
        IS_24_7: is_24_7_confidence,
        LIFTER_FRIENDLY: lifter_confidence,
        SPECIALTY: specialty_confidence,
        TIER: tier_confidence,
    }
