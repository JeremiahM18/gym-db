from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException

from gymdb.domain.inference import RULESET_VERSION
from gymdb.domain.models import Gym
from gymdb.domain.processing import normalize_name
from gymdb.observe.summaries import summarize_inference


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


def serialize_gym(gym: dict) -> dict:
    """
    Produce a fully-normalized v2 gym dict for API responses.

    Shared by the gym list, single-gym, and review endpoints.
    """
    out = dict(gym)
    out["norm_name"] = str(out.get("norm_name") or normalize_name(out["name"]))

    raw = out.pop("inferred", None) or out.get("inference")
    out["inference"] = normalize_inference(raw)
    out["inference_meta"] = normalize_inference_meta(gym.get("inference_meta"))
    out["source_provenance"] = normalize_source_provenance(gym.get("source_provenance"))
    out["inference_summary"] = summarize_inference(out["inference"])
    return out


def serialize_domain_gym(gym: Gym) -> dict:
    return serialize_gym(
        {
            "id": gym.id,
            "name": gym.name,
            "norm_name": gym.norm_name,
            "lat": gym.lat,
            "lon": gym.lon,
            "confidence_score": gym.confidence_score,
            "osm_refs": gym.osm_refs,
            "tags": gym.tags,
            "inferred": gym.inferred,
            "inference_meta": gym.inference_meta,
            "source_provenance": gym.source_provenance,
        }
    )


def translate_store_error(exc: Exception) -> HTTPException:
    """Translate store-layer exceptions to HTTP responses."""
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=503, detail=str(exc))
    if isinstance(exc, KeyError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, RuntimeError):
        return HTTPException(status_code=503, detail=str(exc))
    return HTTPException(status_code=500, detail="Internal server error")
