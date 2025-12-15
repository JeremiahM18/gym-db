"""
Inference engine.

Coordinates signal extraction and decision logic to produce
deterministic, explainable inferred attributes.
"""

from gymdb.models import Gym
from gymdb.domain import (
    InferenceResult,
    IS_24_7,
    PREMIUM_SCORE,
    LIFTER_FRIENDLY,
    TIER,
)

from gymdb.infer.decisions import compute_premium_score
from gymdb.inference import (
    extract_features, 
    infer_24_7, 
    infer_lifter_friendly, 
    infer_tier
)

def run_inference(gym: Gym) -> None:
    """
    Run all inference logic for a single gym.
    Mutates the gym in-place.
    """
    
    # Extract normalized features
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

    premium_result: InferenceResult = {
        "value": premium_value,
        "reasons": premium_reasons,
    }

    # Existing inferences (unchanged)
    is_24_7, r_24_7 = infer_24_7(features)
    lifter_friendly, r_lifter = infer_lifter_friendly(features)
    tier, r_tier = infer_tier(premium_value, is_24_7)

    # New structured inference
    gym.inferred[PREMIUM_SCORE] = premium_result

    # Compatibility (temporary)
    gym.inference_reasons[PREMIUM_SCORE] = premium_reasons

    # Write inferred values
    gym.inferred.update({
        IS_24_7: is_24_7,
        LIFTER_FRIENDLY: lifter_friendly,
        TIER: tier,
    })

    # Write reasons (merged, explainable)
    gym.inference_reasons.update({
        IS_24_7: r_24_7,
        LIFTER_FRIENDLY: r_lifter,
        TIER: r_tier,
    })