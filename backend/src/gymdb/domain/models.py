from typing import Any

from gymdb.infer.result import InferenceResult


class Gym:
    __slots__ = (
        "id",
        "name",
        "norm_name",
        "lat",
        "lon",
        "osm_refs",
        "tags",
        "confidence_score",
        "inferred",
        "inference_meta",
        "source_provenance",
    )

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
        self.source_provenance: dict[str, Any] = {
            "primary": "osm",
            "confirmed_by": [],
            "match_status": "unconfirmed",
            "external_refs": {},
        }
