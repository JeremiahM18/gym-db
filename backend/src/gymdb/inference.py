"""
Public inference entrypoint.

Provides a stable API for running inference and stamping
inference metadata. All inference logic is delegated to
the inference engine.
"""

from gymdb.models import Gym
from gymdb.domain import (
    INFERENCE_META, INFERENCE_ENGINE, 
    INFERENCE_VERSION, ENGINE_RULE_BASED)

from gymdb.infer.engine import run_inference

RULESET_VERSION ="1.0.0"


def apply_inference(gym: Gym) -> None:
    """
    Apply inference to a Gym entity.
    
    This is a stable public entrypoint. All inference logic
    is delegated to the inference engine.
    """
    run_inference(gym)

    gym.inference_meta.update({
        INFERENCE_ENGINE: ENGINE_RULE_BASED,
        INFERENCE_VERSION: RULESET_VERSION,
    })
