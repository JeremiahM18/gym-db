import json
from pathlib import Path
from datetime import datetime, timezone
from gymdb.models import Gym

SCHEMA_VERSION = "1.1"

def write_json(gyms: list[Gym], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(gyms),
        "results": [
            {
                "id": g.id,
                "name": g.name,
                "lat": g.lat,
                "lon": g.lon,
                "confidence_score": g.confidence_score,
                "osm_refs": g.osm_refs,
                "tags": g.tags,
                "inferred": g.inferred,
                "inference_reasons": g.inference_reasons,
            }
            for g in gyms
        ],
    }

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")