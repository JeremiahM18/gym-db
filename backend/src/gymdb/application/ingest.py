from __future__ import annotations

from pathlib import Path

from gymdb.application.coverage import apply_tomtom_coverage
from gymdb.config import DEFAULT_LAT, DEFAULT_LON, DEFAULT_RADIUS_MILES
from gymdb.domain.inference import apply_inference
from gymdb.domain.processing import compute_gym_id, deduplicate
from gymdb.domain.scoring import compute_confidence
from gymdb.infrastructure.datasets.read_model import materialize_dataset_read_model
from gymdb.infrastructure.datasets.registry import DatasetRegistry
from gymdb.infrastructure.io_json import write_json
from gymdb.infrastructure.overpass_client import fetch_gyms
from gymdb.infrastructure.settings import settings
from gymdb.infrastructure.tomtom_client import TomTomClient


def _enrich_with_tomtom(
    gyms,
    *,
    lat: float,
    lon: float,
    radius_miles: float,
) -> dict[str, int]:
    if not settings.tomtom_api_key or not gyms:
        return {"matched": 0, "name_mismatch": 0, "missing_from_osm": 0}

    client = TomTomClient(
        api_key=settings.tomtom_api_key,
        base_url=settings.tomtom_base_url,
    )
    places = client.search_gyms(
        lat=lat,
        lon=lon,
        radius_m=int(radius_miles * 1609.344),
        limit=max(len(gyms) * 2, 100),
    )
    _, summary = apply_tomtom_coverage(gyms, places)
    return summary.to_dict()


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

    coverage_summary = _enrich_with_tomtom(
        gyms,
        lat=lat,
        lon=lon,
        radius_miles=radius_miles,
    )

    for g in gyms:
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
        "coverage_matched": coverage_summary["matched"],
        "coverage_name_mismatch": coverage_summary["name_mismatch"],
        "coverage_missing_from_osm": coverage_summary["missing_from_osm"],
    }


def run_ingest_for_region(
    *,
    registry: DatasetRegistry,
    region: str,
    radius_miles: float | None = None,
) -> dict:
    metadata = registry.region_metadata(region)
    dataset_path = registry.dataset_path(region)
    metrics = run_ingest(
        lat=metadata["lat"],
        lon=metadata["lon"],
        radius_miles=radius_miles or metadata.get("radius_miles", DEFAULT_RADIUS_MILES),
        out=dataset_path,
    )
    read_model_path = materialize_dataset_read_model(
        region=region,
        dataset_path=dataset_path,
    )
    return {
        **metrics,
        "read_model_path": str(read_model_path),
    }
