"""

Inference decisions.

Decisions combine weighted signals to produce inferred attributes.
"""

from typing import Tuple, List, Set

from gymdb.infer import signals
from gymdb.infer.weights import (
    PREMIUM_WATER_AMENITIES_WEIGHT,
    PREMIUM_WELLNESS_AMENITIES_WEIGHT,
    PREMIUM_CONVENIENCE_AMENITIES_WEIGHT,
    PREMIUM_HAS_WEBSITE_WEIGHT,
    PREMIUM_HAS_OPENING_HOURS_WEIGHT,
    PREMIUM_SCORE_MAX,
)


def compute_premium_score(
        capabilities: Set[str],
        attributes: Set[str],
) -> Tuple[int, List[str]]:
    # Compute premium score based on weighted evidence signals
    score = 0
    reasons: List[str] = []

    # Water amenities
    value, reason = signals.has_water_amenities(capabilities)
    if value:
        score += PREMIUM_WATER_AMENITIES_WEIGHT
        reasons.append(reason)

    # Wellness amenities
    value, reason = signals.has_wellness_amenities(capabilities)
    if value:
        score += PREMIUM_WELLNESS_AMENITIES_WEIGHT
        reasons.append(reason)

    # Convenience amenities
    value, reason = signals.has_convenience_amenities(capabilities)
    if value:
        score += PREMIUM_CONVENIENCE_AMENITIES_WEIGHT
        reasons.append(reason)

    # Website
    value, reason = signals.has_website(attributes)
    if value:
        score += PREMIUM_HAS_WEBSITE_WEIGHT
        reasons.append(reason)

    # Opening hours
    value, reason = signals.has_opening_hours(attributes)
    if value: 
        score += PREMIUM_HAS_OPENING_HOURS_WEIGHT
        reasons.append(reason)

    return min(score, PREMIUM_SCORE_MAX), reasons
