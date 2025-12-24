from __future__ import annotations

from pathlib import Path

from gymdb.config import DEFAULT_LAT, DEFAULT_LON, DEFAULT_RADIUS_MILES
from gymdb.overpass_client import fetch_gyms
from gymdb.processing import deduplicate, compute_gym_id
from gymdb.scoring import compute_confidence
from gymdb.inference import apply_inference
from gymdb.io_json import write_json


def run_ingest(
    *,
    lat: float = DEFAULT_LAT,
    lon: float = DEFAULT_LON,
    radius_miles: float = DEFAULT_RADIUS_MILES,
    out: Path = Path("data/gyms_raw.json"),
) -> dict:
    """
    Run a deterministic GymDB ingestion pipeline.

    Returns structured metrics for job auditing.
    """
    elements = fetch_gyms(radius_miles * 1609.344, lat, lon)

    gyms = deduplicate(elements)

    for g in gyms:
        g.id = compute_gym_id(g.norm_name, g.lat, g.lon)
        compute_confidence(g)
        apply_inference(g)

    write_json(gyms, out)

    return {
        "lat": lat,
        "lon": lon,
        "radius_miles": radius_miles,
        "gyms_fetched": len(elements),
        "gyms_written": len(gyms),
        "output_path": str(out),
    }
