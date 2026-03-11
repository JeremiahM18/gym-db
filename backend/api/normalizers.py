import hashlib
from datetime import UTC, datetime
from typing import Any


def normalize_inference_meta(meta: dict | None) -> dict:
    if not meta:
        return {
            "engine": "rule_based",
            "version": "1.0.0",
            "generated_at": datetime.now(UTC),
            "deterministic_hash": hashlib.sha256(b"default").hexdigest(),
        }
    
    return {
        "engine": meta.get("engine", "rule_based"),
        "version": str(meta.get("version", "1.0.0")),
        "generated_at": meta.get(
            "generated_at",
            datetime.now(UTC),
            ),
        "deterministic_hash": meta.get(
            "deterministic_hash",
            hashlib.sha256(b"default").hexdigest(),
        ),
    }

def normalize_inference(inference: dict[str, Any] | None) -> dict[str, dict]:
    """
    Ensure v2 inference contract:
    - Only emit real inference results
    - Never invent placeholder inference
    """
    if not inference:
        return {}
    
    out = {}

    for key, result in inference.items():
        if not result:
            continue

        # InferenceResult object
        if hasattr(result, "value"):
            out[key] = {
                "value": result.value,
                "confidence": result.confidence or 0.0,
                "reasons": result.reasons or [],
                "source": "rule",
            }
        else:
            # dict-shaped inference
            out[key] = {
                "value": result.get("value"),
                "confidence": result.get("confidence", 0.0),
                "reasons": result.get("reasons", []),
                "source": "rule",
            }

    return out
    

