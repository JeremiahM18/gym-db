from collections import Counter
from gymdb.domain import InferenceResult

_inference_hits = Counter()


def record_inference_hits(inferred: dict[str, InferenceResult]) -> None:
    """
    Count which inference keys are produced. This is a lightweight metric.
    """
    for key, result in inferred.items():
        val = result.get("value")
        if val is not None:
            _inference_hits[key] += 1


def snapshot_metrics() -> dict:
    return dict(_inference_hits)