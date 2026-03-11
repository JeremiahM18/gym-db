"""
Inference decisions.

Decisions combine weighted signals to produce inferred attributes.
"""

from gymdb.infer import signals
from gymdb.infer.weights import (
    PREMIUM_CONVENIENCE_AMENITIES_WEIGHT,
    PREMIUM_HAS_OPENING_HOURS_WEIGHT,
    PREMIUM_HAS_WEBSITE_WEIGHT,
    PREMIUM_SCORE_MAX,
    PREMIUM_WATER_AMENITIES_WEIGHT,
    PREMIUM_WELLNESS_AMENITIES_WEIGHT,
)


def _append_reason(reasons: list[str], reason: str | None) -> None:
    if reason is not None:
        reasons.append(reason)


def compute_premium_score(
    capabilities: set[str],
    attributes: set[str],
) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    value, reason = signals.has_water_amenities(capabilities)
    if value:
        score += PREMIUM_WATER_AMENITIES_WEIGHT
        _append_reason(reasons, reason)

    value, reason = signals.has_wellness_amenities(capabilities)
    if value:
        score += PREMIUM_WELLNESS_AMENITIES_WEIGHT
        _append_reason(reasons, reason)

    value, reason = signals.has_convenience_amenities(capabilities)
    if value:
        score += PREMIUM_CONVENIENCE_AMENITIES_WEIGHT
        _append_reason(reasons, reason)

    value, reason = signals.has_website(attributes)
    if value:
        score += PREMIUM_HAS_WEBSITE_WEIGHT
        _append_reason(reasons, reason)

    value, reason = signals.has_opening_hours(attributes)
    if value:
        score += PREMIUM_HAS_OPENING_HOURS_WEIGHT
        _append_reason(reasons, reason)

    return min(score, PREMIUM_SCORE_MAX), reasons
