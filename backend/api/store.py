import json
from pathlib import Path
from typing import List, Dict, Any
from api.registry import DatasetRegistry
from gymdb.processing import haversine_meters
from gymdb.domain import CONFIDENCE_SCORE, INFERRED

class GymStore:
    def __init__(self, registry: DatasetRegistry):
        self.registry = registry
        self._gyms_by_region: Dict[str, list[dict]] = {}

    def load_region(self, region: str):
        if region in self._gyms_by_region:
            return
        

        path = self.registry.dataset_path(region)
        data = json.loads(path.read_text(encoding="utf-8"))
        self._gyms_by_region[region] = data["results"]

    def gyms(self, region: str) -> List[dict]:
        self.load_region(region)
        return self._gyms_by_region[region]
    
    def get_by_id(self, region: str, gym_id: str) -> Dict[str, Any] | None:
        for g in self.gyms(region):
            if g.get("id") == gym_id:
                return g
        return None

    def filter(
        self,
        region: str,
        min_conf: float | None = None,
        tier: str | None = None,
        lifter_friendly: bool | None = None,
        is_24_7: bool | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_m: float | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[dict]:
        gyms = self.gyms(region)

        if min_conf is not None:
            gyms = [
                g for g in gyms
                if g.get(CONFIDENCE_SCORE, 0) >= min_conf
            ]

        if tier is not None:
            gyms = [
                g for g in gyms
                if g.get(INFERRED, {}).get("tier") == tier
            ]

        if lifter_friendly is not None:
            gyms = [
                g for g in gyms
                if g.get(INFERRED, {}).get("lifter_friendly") is lifter_friendly
            ]

        if is_24_7 is not None:
            gyms = [
                g for g in gyms
                if g.get(INFERRED, {}).get("is_24_7") is is_24_7
            ]

        if lat is not None and lon is not None and radius_m is not None:
            gyms = [
                g for g in gyms
                if haversine_meters(lat, lon, g["lat"], g["lon"]) <= radius_m
            ]

        return gyms[offset : offset + limit]