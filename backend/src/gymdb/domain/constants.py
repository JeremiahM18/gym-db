from typing import TypedDict, Union


InferenceValue = Union[bool, int, str]

class InferenceResultData(TypedDict, total=False):
    """
    Structured result of an inference decision.

    value:
        The inferred value (bool, int, or str)

    reasons:
        Explanations describing why the value was inferred
    """
    value: InferenceValue
    reasons: list[str]
    confidence: float | None



# --- Dataset schema keys ---

CONFIDENCE_SCORE = "confidence_score"
INFERRED = "inferred"

# --- Inferred field names ---

IS_24_7 = "is_24_7"
LIFTER_FRIENDLY = "lifter_friendly"
TIER = "tier"
PREMIUM_SCORE = "premium_score"

# --- Valid tier values ---
TIER_BASIC = "basic"
TIER_MID = "mid"
TIER_PREMIUM = "premium"

# --- Inference metadata ---
INFERENCE_META = "inference_meta"
INFERENCE_ENGINE =  "engine"
INFERENCE_VERSION = "version"
ENGINE_RULE_BASED = "rule_based"


