import argparse
from pathlib import Path

from gymdb.config import DEFAULT_LAT, DEFAULT_LON, DEFAULT_RADIUS_MILES
from gymdb.application.ingest import run_ingest


def main():
    parser = argparse.ArgumentParser(description="Build GymDB dataset")

    parser.add_argument("--lat", type=float, default=DEFAULT_LAT)
    parser.add_argument("--lon", type=float, default=DEFAULT_LON)
    parser.add_argument(
        "--radius-miles", type=float, default=DEFAULT_RADIUS_MILES
    )

    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/gyms_raw.json"),
        help="Output dataset path",
    )

    args = parser.parse_args()

    metrics = run_ingest(
        lat=args.lat,
        lon=args.lon,
        radius_miles=args.radius_miles,
        out=args.out,
    )

    print(f"Processed {metrics['gyms_written']} gyms -> {metrics['output_path']}")


if __name__ == "__main__":
    main()


