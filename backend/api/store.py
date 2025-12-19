from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

from api.registry import DatasetRegistry
from src.gymdb.processing import haversine_meters
from src.gymdb.domain import (
    CONFIDENCE_SCORE, INFERRED, IS_24_7, 
    LIFTER_FRIENDLY, TIER
)

class GymStore:
    """
    Read-only access layer over precomputed gym datasets.
    Responsible for filetering slicing and inference access.
    """
    def __init__(self, registry: DatasetRegistry):
        self.registry = registry
        self._gyms_by_region: Dict[str, list[dict]] = {}
        
    # --- Properties ---

    @property
    def default_region(self) -> str:
        """
        Default region exposed for API consumers.
        """
        return self.registry.default_region
    
    # --- Loading --- 

    def load_region(self, region: str) -> None:
        """
        Lazily load in a region dataset into memory.
        """
        if region in self._gyms_by_region:
            return
        

        path = self.registry.dataset_path(region)
        data = json.loads(path.read_text(encoding="utf-8"))
        self._gyms_by_region[region] = data["results"]

    def gyms(self, region: str) -> List[dict]:
        self.load_region(region)
        return self._gyms_by_region[region]
    
    # --- Access ---

    def get_by_id(self, region: str, gym_id: str) -> Dict[str, Any] | None:
        for g in self.gyms(region):
            if g.get("id") == gym_id:
                return g
        return None
    
    def _infer_value(self, gym: dict, key: str):
        """
        Safely extract the inferred value for a given key.
        """
        return (
            gym.get(INFERRED, {})
            .get(key, {}).get("value")
        )
    
    # --- Filtering ---

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
                if self._infer_value(g, TIER) == tier
            ]

        if lifter_friendly is not None:
            gyms = [
                g for g in gyms
                if self._infer_value(g, LIFTER_FRIENDLY) is lifter_friendly
            ]

        if is_24_7 is not None:
            gyms = [
                g for g in gyms
                if self._infer_value(g, IS_24_7) is is_24_7
            ]

        if lat is not None and lon is not None and radius_m is not None:
            gyms = [
                g for g in gyms
                if haversine_meters(lat, lon, g["lat"], g["lon"]) <= radius_m
            ]

        return gyms[offset : offset + limit]