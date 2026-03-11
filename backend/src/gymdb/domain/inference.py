"""
Public inference entrypoint.

Provides a stable API for running inference and stamping
inference metadata. All inference logic is delegated to
 the inference engine.
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

RULESET_VERSION = "1.0.0"


def _canonicalize_tags(tags: dict[str, Any]) -> dict[str, str]:
    """
    Convert gym tags into a JSON-serializable, deterministic form.

    Removes non-primitive values.
    """
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
    """
    Compute a deterministic hash for inference reproducibility.

    Same inputs + same version => same hash.
    """
    payload = {
        "gym_id": gym_id,
        "tags": _canonicalize_tags(tags),
        "version": inference_version,
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def apply_inference(gym: Gym) -> None:
    """
    Apply inference to a Gym entity.

    This is a stable public entrypoint. All inference logic
    is delegated to the inference engine.
    """
    gym_id = gym.id or compute_gym_id(gym.norm_name, gym.lat, gym.lon)
    gym.id = gym_id

    run_inference(gym)

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
    )
    gym.inference_meta = meta.model_dump(mode="json")
