from typing import Any

from gymdb.infer.result import InferenceResult


def _extract_value(result: InferenceResult | dict[str, Any] | None) -> Any:
    if result is None:
        return None
    if isinstance(result, dict):
        return result.get("value")
    return result.value


def diff_inference(
    before: dict[str, InferenceResult],
    after: dict[str, InferenceResult],
) -> dict[str, dict[str, Any]]:
    """
    Compute a value-level diff between two inference states.
    Returns only changed fields.
    """
    diffs: dict[str, dict[str, Any]] = {}

    for key in set(before) | set(after):
        before_val = _extract_value(before.get(key))
        after_val = _extract_value(after.get(key))

        if before_val != after_val:
            diffs[key] = {
                "before": before_val,
                "after": after_val,
            }

    return diffs
