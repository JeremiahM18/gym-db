import argparse
import re
from pathlib import Path

from gymdb.application.ingest import run_ingest
from gymdb.config import DEFAULT_LAT, DEFAULT_LON, DEFAULT_RADIUS_MILES
from gymdb.infrastructure.datasets.read_model import materialize_dataset_read_model
from gymdb.infrastructure.datasets.registry import DatasetRegistry
from gymdb.infrastructure.overpass_client import OverpassUnavailableError
from gymdb.infrastructure.settings import settings
from gymdb.infrastructure.tomtom_client import TomTomClient


def slugify_region_key(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "custom_region"


def resolve_place_query(place_query: str):
    if not settings.tomtom_api_key:
        raise SystemExit(
            "Place-based ingest requires TOMTOM_API_KEY so the requested city or place "
            "can be resolved reliably."
        )

    client = TomTomClient(
        api_key=settings.tomtom_api_key,
        base_url=settings.tomtom_base_url,
    )
    places = client.geocode(query=place_query, limit=5)
    if not places:
        raise SystemExit(f'No TomTom geocode match found for "{place_query}".')
    return places[0]


def main():
    parser = argparse.ArgumentParser(description="Build GymDB dataset")

    parser.add_argument(
        "--place",
        type=str,
        help="Resolve a city or place name through TomTom before ingesting.",
    )
    parser.add_argument("--lat", type=float, default=DEFAULT_LAT)
    parser.add_argument("--lon", type=float, default=DEFAULT_LON)
    parser.add_argument(
        "--radius-miles", type=float, default=DEFAULT_RADIUS_MILES
    )
    parser.add_argument(
        "--region-key",
        type=str,
        help=(
            "Registry key to write when using --place. Defaults to a slugified "
            "place name."
        ),
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("data/registry.json"),
        help="Dataset registry to update for place-based ingest.",
    )
    parser.add_argument(
        "--set-default-region",
        action="store_true",
        help="Set the published region as the default region in the registry.",
    )

    parser.add_argument(
        "--out",
        type=Path,
        help="Output dataset path",
    )
    parser.add_argument(
        "--allow-without-tomtom",
        action="store_true",
        help="Skip the default TomTom publish gate for local experimentation.",
    )

    args = parser.parse_args()

    target_lat = args.lat
    target_lon = args.lon
    output_path = args.out or Path("data/gyms_raw.json")
    region_key = args.region_key
    place_label: str | None = None

    if args.place:
        resolved_place = resolve_place_query(args.place)
        target_lat = resolved_place.lat
        target_lon = resolved_place.lon
        place_label = resolved_place.address or resolved_place.name
        region_key = region_key or slugify_region_key(args.place)
        output_path = args.out or args.registry.parent / f"gyms_{region_key}.json"

    try:
        metrics = run_ingest(
            lat=target_lat,
            lon=target_lon,
            radius_miles=args.radius_miles,
            out=output_path,
            require_tomtom_validation=not args.allow_without_tomtom,
        )
    except OverpassUnavailableError as exc:
        raise SystemExit(str(exc)) from exc

    if region_key is not None:
        registry = DatasetRegistry(args.registry)
        registry.upsert_region(
            region=region_key,
            file=output_path,
            lat=target_lat,
            lon=target_lon,
            radius_miles=args.radius_miles,
            place_label=place_label,
            set_default=args.set_default_region,
        )
        read_model_path = materialize_dataset_read_model(
            region=region_key,
            dataset_path=output_path,
        )
        print(f"Updated registry region `{region_key}` -> {args.registry}")
        print(f"Materialized read model -> {read_model_path}")

    if args.place:
        print(
            f'Resolved "{args.place}" -> '
            f"{place_label or args.place} ({target_lat:.6f}, {target_lon:.6f})"
        )

    print(f"Processed {metrics['gyms_written']} gyms -> {metrics['output_path']}")


if __name__ == "__main__":
    main()


