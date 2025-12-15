from typing import Dict, List, Any

class Gym:
    def __init__(
            self,
            name: str,
            norm_name: str,
            lat: float,
            lon: float,
            osm_refs: List[Dict],
            tags: Dict,
    ):
        self.id: str | None = None
        self.name = name
        self.norm_name = norm_name
        self.lat = lat
        self.lon = lon
        self.osm_refs = osm_refs
        self.tags = tags
        self.confidence_score: float | None = None

        # inference outputs
        self.inferred: Dict[str, Any] = {}
        self.inference_reasons: Dict[str, List[str]] = {}