"""
Public inference entrypoint.

Provides a stable API for running inference and stamping
inference metadata. All inference logic is delegated to
the inference engine.
"""

from datetime import datetime, timezone

from gymdb.models import Gym
from gymdb.domain import (
    INFERENCE_META,                  # storage slot (string key)
    INFERENCE_ENGINE,
    ENGINE_RULE_BASED,
)

from gymdb.infer.meta import InferenceMeta # the structure
from gymdb.infer.engine import run_inference

import hashlib
import json

RULESET_VERSION ="1.0.0"

# --- Helpers ---

def _canonicalize_tags(tags: dict) -> dict:
    """
    Convert gym tags into a JSON-serializable, deterministic form.

    Removes non-primitive values and sorts keys.
    """
    clean: dict[str, str] = {}

    for k, v in tags.items():
        # Only keep primitive, meaningful tag values
        if isinstance(v, (str, int, float, bool)):
            clean[k] = str(v)
        elif v is None:
            continue
        else:
            # Ignore non-serializable / non-deterministic values
            continue

    return dict(sorted(clean.items()))

def _compute_deterministic_hash(
        *,
        gym_id: str,
        tags: dict,
        inference_version: str,
) -> str:
    """
    Compute a deterministic hash for inference reproducibility.

    Same inputs + smae version => same hash.
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
    run_inference(gym)

    deterministic_hash = _compute_deterministic_hash(
        gym_id=gym.id,
        tags=gym.tags,
        inference_version=RULESET_VERSION,

    )

    gym.inference_meta = InferenceMeta(
        engine = ENGINE_RULE_BASED,
        version = RULESET_VERSION,
        generated_at = datetime.now(timezone.utc),
        deterministic_hash = deterministic_hash,
    )

