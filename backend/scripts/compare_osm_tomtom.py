from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from gymdb.application.coverage import best_osm_match, classify, summarize_matches
from gymdb.infrastructure.settings import settings
from gymdb.infrastructure.tomtom_client import TomTomClient


def load_osm_dataset(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    results = payload.get("results") if isinstance(payload, dict) else payload
    if not isinstance(results, list):
        raise ValueError(f"Dataset at {path} does not contain a results list")
    return results


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
        api_key=settings.tomtom_api_key,
        base_url=settings.tomtom_base_url,
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

    summary = summarize_matches(matches).to_dict()

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
