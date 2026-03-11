from typing import Any

from gymdb.infer.result import InferenceResult


class Gym:
    def __init__(
        self,
        name: str,
        norm_name: str,
        lat: float,
        lon: float,
        osm_refs: list[dict[str, Any]],
        tags: dict[str, Any],
    ):
        self.id: str | None = None
        self.name = name
        self.norm_name = norm_name
        self.lat = lat
        self.lon = lon
        self.osm_refs = osm_refs
        self.tags = tags
        self.confidence_score: float | None = None

        self.inferred: dict[str, InferenceResult] = {}
        self.inference_meta: dict[str, Any] = {}
