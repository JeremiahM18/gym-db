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
from gymdb.infer.quality import (
    InferenceDiagnostics,
    compute_field_confidence,
    detect_contradictions,
)
from gymdb.infer.result import InferenceResult


def run_inference(gym: Gym) -> InferenceDiagnostics:
    """
    Run all inference logic for a single gym.
    Mutates the gym in-place and returns diagnostics.
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

    inferred = {
        PREMIUM_SCORE: InferenceResult(
            value=premium_value,
            reasons=premium_reasons,
        ),
        IS_24_7: InferenceResult(
            value=is_24_7_value,
            reasons=is_24_7_reasons,
        ),
        LIFTER_FRIENDLY: InferenceResult(
            value=lifter_value,
            reasons=lifter_reasons,
        ),
        SPECIALTY: InferenceResult(
            value=specialty_value,
            reasons=specialty_reasons,
        ),
        TIER: InferenceResult(
            value=tier_value,
            reasons=tier_reasons,
        ),
    }

    contradictions = detect_contradictions(features, inferred)
    field_confidence = compute_field_confidence(features, inferred, contradictions)

    for field, confidence in field_confidence.items():
        inferred[field].confidence = confidence

    gym.inferred = inferred
    return InferenceDiagnostics(
        field_confidence=field_confidence,
        contradictions=contradictions,
    )
