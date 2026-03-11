from typing import Literal, TypedDict

InferenceValue = bool | int | str


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


CONFIDENCE_SCORE = "confidence_score"
INFERRED = "inferred"

IS_24_7 = "is_24_7"
LIFTER_FRIENDLY = "lifter_friendly"
TIER = "tier"
PREMIUM_SCORE = "premium_score"

TIER_BASIC = "basic"
TIER_MID = "mid"
TIER_PREMIUM = "premium"

INFERENCE_META = "inference_meta"
INFERENCE_ENGINE = "engine"
INFERENCE_VERSION = "version"
ENGINE_RULE_BASED: Literal["rule_based"] = "rule_based"
