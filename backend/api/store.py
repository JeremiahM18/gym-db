import json
from pathlib import Path
from typing import List, Dict, Any
from gymdb.domain import CONFIDENCE_SCORE, INFERRED

DATA_PATH = Path("data/gyms_raw.json")

class GymStore:
    def __init__(self, path: Path = DATA_PATH):
        self.path = path
        self._gyms: List[Dict[str, Any]] = []

    def load(self) -> "GymStore":
        if not self.path.exists():
            raise RuntimeError(
                f"Dataset not found at {self.path}. "
                "Please run the GymDB pipeline first."
            )
        self._gyms = json.loads(self.path.read_text(encoding="utf-8"))
        return self
    
    def get_by_id(self, gym_id: str) -> Dict[str, Any] | None:
        for g in self._gyms:
            if g.get("id") == gym_id:
                return g
        return None
    
    def all(self) -> List[Dict[str, Any]]:
        return self._gyms

    def filter(
        self,
        min_conf: float | None = None,
        tier: str | None = None,
        lifter_friendly: bool | None = None,
        is_24_7: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        gyms = self._gyms

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

        return gyms[offset : offset + limit]