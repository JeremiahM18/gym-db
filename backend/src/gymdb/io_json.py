import json
from pathlib import Path
from gymdb.models import Gym

def write_json(gyms: list[Gym], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "name": g.name,
            "lat": g.lat,
            "lon": g.lon,
            "confidence_score": g.confidence_score,
            "osm_refs": g.osm_refs,
            "tags": g.tags,
        }
        for g in gyms
    ]
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")