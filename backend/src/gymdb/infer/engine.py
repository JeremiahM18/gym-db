"""
Inference engine.

Coordinates signal extraction and decision logic to produce
deterministic, explainable inferred attributes.
"""

from gymdb.domain.constants import (
    IS_24_7,
    LIFTER_FRIENDLY,
    PREMIUM_SCORE,
    SPECIALTY,
    TIER,
)
from gymdb.domain.features import extract_features
from gymdb.domain.models import Gym
from gymdb.domain.rules import (
    infer_24_7,
    infer_lifter_friendly,
    infer_specialty,
    infer_tier,
)
from gymdb.infer.decisions import compute_premium_score
from gymdb.infer.result import InferenceResult


def run_inference(gym: Gym) -> None:
    """
    Run all inference logic for a single gym.
    Mutates the gym in-place.
    """
    features = extract_features(gym.tags)
    capabilities = (
        features["amenities"]
        | features["sports"]
        | features["attributes"]
    )
    attributes = features["attributes"]

    premium_value, premium_reasons = compute_premium_score(
        capabilities=capabilities,
        attributes=attributes,
    )
    premium_confidence = round(min(premium_value / 10.0, 1.0), 2)

    is_24_7_value, is_24_7_reasons = infer_24_7(features)
    lifter_value, lifter_reasons = infer_lifter_friendly(
        features,
        capabilities=capabilities,
    )
    specialty_value, specialty_reasons = infer_specialty(
        features,
        capabilities=capabilities,
    )
    tier_value, tier_reasons = infer_tier(
        premium_score=premium_value,
        is_24_7=is_24_7_value,
    )

    gym.inferred = {
        PREMIUM_SCORE: InferenceResult(
            value=premium_value,
            reasons=premium_reasons,
            confidence=premium_confidence,
        ),
        IS_24_7: InferenceResult(
            value=is_24_7_value,
            reasons=is_24_7_reasons,
            confidence=1.0 if is_24_7_value else 0.6,
        ),
        LIFTER_FRIENDLY: InferenceResult(
            value=lifter_value,
            reasons=lifter_reasons,
        ),
        SPECIALTY: InferenceResult(
            value=specialty_value,
            reasons=specialty_reasons,
            confidence=0.9 if specialty_value != "general_fitness" else 0.5,
        ),
        TIER: InferenceResult(
            value=tier_value,
            reasons=tier_reasons,
        ),
    }
