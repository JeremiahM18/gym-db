from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from gymdb.domain.processing import haversine_meters, normalize_name
from gymdb.infrastructure.settings import settings
from gymdb.infrastructure.tomtom_client import TomTomClient, TomTomPlace

MATCH_DISTANCE_METERS = 250.0


@dataclass(frozen=True)
class CoverageMatch:
    status: str
    osm_name: str | None
    tomtom_name: str | None
    distance_m: float | None
    osm_id: str | None
    tomtom_id: str | None
    city: str | None


def load_osm_dataset(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    results = payload.get("results") if isinstance(payload, dict) else payload
    if not isinstance(results, list):
        raise ValueError(f"Dataset at {path} does not contain a results list")
    return results


def best_osm_match(
    place: TomTomPlace, gyms: list[dict]
) -> tuple[dict | None, float | None]:
    normalized_target = normalize_name(place.name)
    best_gym: dict | None = None
    best_distance: float | None = None

    for gym in gyms:
        gym_name = str(gym.get("name") or "")
        gym_norm = str(gym.get("norm_name") or normalize_name(gym_name))
        distance = haversine_meters(
            place.lat, place.lon, float(gym["lat"]), float(gym["lon"])
        )
        if gym_norm == normalized_target and distance <= MATCH_DISTANCE_METERS:
            if best_distance is None or distance < best_distance:
                best_gym = gym
                best_distance = distance

    if best_gym is not None:
        return best_gym, best_distance

    for gym in gyms:
        distance = haversine_meters(
            place.lat, place.lon, float(gym["lat"]), float(gym["lon"])
        )
        if distance <= MATCH_DISTANCE_METERS:
            gym_name = str(gym.get("name") or "")
            gym_norm = str(gym.get("norm_name") or normalize_name(gym_name))
            if gym_norm.startswith(normalized_target) or normalized_target.startswith(
                gym_norm
            ):
                if best_distance is None or distance < best_distance:
                    best_gym = gym
                    best_distance = distance

    return best_gym, best_distance


def classify(
    place: TomTomPlace, gym: dict | None, distance_m: float | None
) -> CoverageMatch:
    if gym is None:
        return CoverageMatch(
            status="missing_from_osm",
            osm_name=None,
            tomtom_name=place.name,
            distance_m=None,
            osm_id=None,
            tomtom_id=place.id,
            city=place.city,
        )

    osm_name = str(gym.get("name") or "")
    osm_id = str(gym.get("id") or "")
    same_name = normalize_name(osm_name) == normalize_name(place.name)
    if same_name:
        return CoverageMatch(
            status="matched",
            osm_name=osm_name,
            tomtom_name=place.name,
            distance_m=distance_m,
            osm_id=osm_id,
            tomtom_id=place.id,
            city=place.city,
        )

    return CoverageMatch(
        status="name_mismatch",
        osm_name=osm_name,
        tomtom_name=place.name,
        distance_m=distance_m,
        osm_id=osm_id,
        tomtom_id=place.id,
        city=place.city,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare OSM gym dataset coverage against TomTom places"
    )
    parser.add_argument("--dataset", default="data/gyms_raw.json")
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--radius-m", type=int, default=10000)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--out", default="data/artifacts/tomtom_coverage_audit.json")
    args = parser.parse_args()

    if not settings.tomtom_api_key:
        raise SystemExit("TOMTOM_API_KEY is required to run the TomTom coverage audit")

    dataset_path = Path(args.dataset)
    gyms = load_osm_dataset(dataset_path)
    client = TomTomClient(
        api_key=settings.tomtom_api_key, base_url=settings.tomtom_base_url
    )
    places = client.search_gyms(
        lat=args.lat,
        lon=args.lon,
        radius_m=args.radius_m,
        limit=args.limit,
    )

    matches = []
    for place in places:
        gym, distance_m = best_osm_match(place, gyms)
        matches.append(classify(place, gym, distance_m))

    summary = {
        "matched": sum(1 for match in matches if match.status == "matched"),
        "name_mismatch": sum(1 for match in matches if match.status == "name_mismatch"),
        "missing_from_osm": sum(
            1 for match in matches if match.status == "missing_from_osm"
        ),
    }

    output = {
        "dataset": str(dataset_path),
        "lat": args.lat,
        "lon": args.lon,
        "radius_m": args.radius_m,
        "tomtom_results": len(places),
        "summary": summary,
        "matches": [asdict(match) for match in matches],
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
