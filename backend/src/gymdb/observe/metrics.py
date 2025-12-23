from collections import Counter

_inference_hits = Counter()


def record_inference_hits(inferred: dict[str, dict]) -> None:
    """
    Count which inference keys are produced. 
    Expects normalized inference dicts (v2 contracts).
    """
    for key, result in inferred.items():
        if result.get("value") is not None:
            _inference_hits[key] += 1


def snapshot_metrics() -> dict[str, int]:
    """
    Snapshot current inference hit counts.
    """
    return dict(_inference_hits)