import argparse
from pathlib import Path

from gymdb.config import DEFAULT_LAT, DEFAULT_LON, DEFAULT_RADIUS_MILES
from gymdb.overpass_client import fetch_gyms
from gymdb.processing import deduplicate
from gymdb.scoring import compute_confidence
from gymdb.io_json import write_json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lat", type=float, default=DEFAULT_LAT)
    parser.add_argument("--lon", type=float, default=DEFAULT_LON)
    parser.add_argument(
        "--radius-miles", type=float, default=DEFAULT_RADIUS_MILES
    )
    args = parser.parse_args()

    elements = fetch_gyms(args.radius_miles * 1609.344, args.lat, args.lon)
    gyms = deduplicate(elements)

    for g in gyms:
        compute_confidence(g)

    write_json(gyms, Path("data/gyms_raw.json"))

    print(f"Processed {len(gyms)} gyms")

if __name__ == "__main__":
    main()