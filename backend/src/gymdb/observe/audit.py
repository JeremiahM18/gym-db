from gymdb.domain import InferenceResult


def diff_inference(
    before: dict[str, InferenceResult],
    after: dict[str, InferenceResult],
) -> dict[str, dict]:
    """
    Compute a value-level diff between two inference states.
    Returns only changed fields.
    """
    diffs: dict[str, dict] = {}

    for key in set(before) | set(after):
        before_val = before.get(key, {}).get("value")
        after_val = after.get(key, {}).get("value")

        if before_val != after_val:
            diffs[key] = {
                "before": before_val,
                "after": after_val,
            }

    return diffs