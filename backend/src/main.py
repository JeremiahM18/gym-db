import argparse
from pathlib import Path

from gymdb.config import DEFAULT_LAT, DEFAULT_LON, DEFAULT_RADIUS_MILES
from gymdb.overpass_client import fetch_gyms
from gymdb.processing import deduplicate
from gymdb.scoring import compute_confidence
from gymdb.io_json import write_json
from gymdb.inference import apply_inference
from gymdb.processing import compute_gym_id

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

    elements = fetch_gyms(args.radius_miles * 1609.344, args.lat, args.lon)

    gyms = deduplicate(elements)

    for g in gyms:
        g.id =  compute_gym_id(g.norm_name, g.lat, g.lon)
        compute_confidence(g)
        apply_inference(g)

    write_json(gyms, args.out)

    print(f"Processed {len(gyms)} gyms -> {args.out}")

if __name__ == "__main__":
    main()