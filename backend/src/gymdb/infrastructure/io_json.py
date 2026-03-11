import json
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from gymdb.domain.models import Gym

SCHEMA_VERSION = "1.3"


def _serialize_inferred(gym: Gym) -> dict[str, dict]:
    return {
        key: result.model_dump(mode="json")
        for key, result in gym.inferred.items()
    }


def write_json(gyms: list[Gym], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "count": len(gyms),
        "inference_meta": (gyms[0].inference_meta if gyms else {}),
        "results": [
            {
                "id": g.id,
                "name": g.name,
                "lat": g.lat,
                "lon": g.lon,
                "confidence_score": g.confidence_score,
                "osm_refs": g.osm_refs,
                "tags": g.tags,
                "inferred": _serialize_inferred(g),
                "inference_meta": g.inference_meta,
                "source_provenance": g.source_provenance,
            }
            for g in gyms
        ],
    }

    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f"{path.stem}.",
        suffix=".tmp",
        delete=False,
    ) as temp_file:
        json.dump(payload, temp_file, indent=2)
        temp_path = Path(temp_file.name)

    temp_path.replace(path)
