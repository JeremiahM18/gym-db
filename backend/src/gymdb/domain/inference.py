"""
Inference entrypoint.
"""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from gymdb.domain.constants import ENGINE_RULE_BASED
from gymdb.domain.models import Gym
from gymdb.domain.processing import compute_gym_id
from gymdb.infer.engine import run_inference
from gymdb.infer.meta import InferenceMeta
from gymdb.observe.metrics import record_inference_hits

RULESET_VERSION = "1.1.0"


def _canonicalize_tags(tags: dict[str, Any]) -> dict[str, str]:
    """Convert tags into a deterministic string map."""
    clean: dict[str, str] = {}

    for key, value in tags.items():
        if isinstance(value, (str, int, float, bool)):
            clean[key] = str(value)

    return clean


def _compute_deterministic_hash(
    *,
    gym_id: str,
    tags: dict[str, Any],
    inference_version: str,
) -> str:
    """Compute the inference hash for a gym and ruleset version."""
    payload = {
        "gym_id": gym_id,
        "tags": _canonicalize_tags(tags),
        "version": inference_version,
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def apply_inference(gym: Gym) -> None:
    """Run inference and stamp inference metadata on a gym."""
    gym_id = gym.id or compute_gym_id(gym.norm_name, gym.lat, gym.lon)
    gym.id = gym_id

    diagnostics = run_inference(gym)

    deterministic_hash = _compute_deterministic_hash(
        gym_id=gym_id,
        tags=gym.tags,
        inference_version=RULESET_VERSION,
    )

    meta = InferenceMeta(
        engine=ENGINE_RULE_BASED,
        version=RULESET_VERSION,
        generated_at=datetime.now(UTC),
        deterministic_hash=deterministic_hash,
        field_confidence=diagnostics.field_confidence,
        contradictions=diagnostics.contradictions,
    )
    record_inference_hits(gym.inferred)
    gym.inference_meta = meta.model_dump(mode="json")
