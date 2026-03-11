"""
Inference engine.

Coordinates signal extraction and decision logic to produce
deterministic, explainable inferred attributes.
"""

from gymdb.models import Gym
from gymdb.domain import (
    IS_24_7,
    PREMIUM_SCORE,
    LIFTER_FRIENDLY,
    TIER,
)

from gymdb.infer.result import InferenceResult
from gymdb.infer.decisions import compute_premium_score
from gymdb.features import extract_features
from gymdb.rules import infer_24_7, infer_lifter_friendly, infer_tier 

def run_inference(gym: Gym) -> None:
    """
    Run all inference logic for a single gym.
    Mutates the gym in-place.
    """
    
    # Feature extraction 
    features = extract_features(gym.tags)

    capabilities = (
        features["amenities"]
        | features["sports"]
        | features["attributes"]
    )

    attributes = features["attributes"]

    # Premium score
    premium_value, premium_reasons = compute_premium_score(
        capabilities=capabilities,
        attributes=attributes,
    )

    premium_confidence = round(min(premium_value / 10.0, 1.0), 2)

    premium_result = InferenceResult(
        value = premium_value,
        reasons = premium_reasons,
        confidence = premium_confidence,
    )

    # 24/7
    is_24_7_value, is_24_7_reasons = infer_24_7(features)
    is_24_7_result = InferenceResult(
        value = is_24_7_value,
        reasons = is_24_7_reasons,
        confidence = 1.0 if is_24_7_value else 0.6,
    )

    # Lifter friendly
    lifter_value, lifter_reasons = infer_lifter_friendly(features)
    lifter_result = InferenceResult(
        value = lifter_value,
        reasons = lifter_reasons,
        # Confidence intentionally omitted
    )

    # Tier
    tier_value, tier_reasons = infer_tier(
        premium_score=premium_value, 
        is_24_7=is_24_7_value,
    )

    tier_result = InferenceResult(
        value = tier_value,
        reasons = tier_reasons,
        # Confidence can be added later if needed
    )

   
    # Persist inferred results
    gym.inferred.update({
        PREMIUM_SCORE: premium_result,
        IS_24_7: is_24_7_result,
        LIFTER_FRIENDLY: lifter_result,
        TIER: tier_result,
    })
