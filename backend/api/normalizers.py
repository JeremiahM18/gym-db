import hashlib
from datetime import UTC, datetime
from typing import Any

from gymdb.domain.inference import RULESET_VERSION


def normalize_inference_meta(meta: dict | None) -> dict:
    if not meta:
        return {
            "engine": "rule_based",
            "version": RULESET_VERSION,
            "generated_at": datetime.now(UTC),
            "deterministic_hash": hashlib.sha256(b"default").hexdigest(),
            "field_confidence": {},
            "contradictions": {},
        }

    return {
        "engine": meta.get("engine", "rule_based"),
        "version": str(meta.get("version", RULESET_VERSION)),
        "generated_at": meta.get("generated_at", datetime.now(UTC)),
        "deterministic_hash": meta.get(
            "deterministic_hash",
            hashlib.sha256(b"default").hexdigest(),
        ),
        "field_confidence": meta.get("field_confidence", {}),
        "contradictions": meta.get("contradictions", {}),
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

        if hasattr(result, "value"):
            out[key] = {
                "value": result.value,
                "confidence": result.confidence or 0.0,
                "reasons": result.reasons or [],
                "source": "rule",
            }
        else:
            out[key] = {
                "value": result.get("value"),
                "confidence": result.get("confidence", 0.0),
                "reasons": result.get("reasons", []),
                "source": "rule",
            }

    return out


def normalize_source_provenance(provenance: dict | None) -> dict:
    if not provenance:
        return {
            "primary": "osm",
            "confirmed_by": [],
            "match_status": "unconfirmed",
            "external_refs": {},
        }

    external_refs = provenance.get("external_refs")
    if not isinstance(external_refs, dict):
        external_refs = {}

    return {
        "primary": str(provenance.get("primary", "osm")),
        "confirmed_by": list(provenance.get("confirmed_by", [])),
        "match_status": str(provenance.get("match_status", "unconfirmed")),
        "external_refs": external_refs,
    }
