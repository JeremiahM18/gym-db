"""
Inference weights.

Weights control how much each signal contributes to a decision.
Keeping them centralized makes the inference engine tunable without
rewriting decision logic.
"""

PREMIUM_WATER_AMENITIES_WEIGHT = 2
PREMIUM_WELLNESS_AMENITIES_WEIGHT = 2
PREMIUM_CONVENIENCE_AMENITIES_WEIGHT = 2

PREMIUM_HAS_WEBSITE_WEIGHT = 1
PREMIUM_HAS_OPENING_HOURS_WEIGHT = 1

PREMIUM_SCORE_MAX = 10
