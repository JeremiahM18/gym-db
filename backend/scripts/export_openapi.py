from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.main import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the GymDB OpenAPI schema")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("openapi.json"),
        help="Where to write the generated OpenAPI schema",
    )
    args = parser.parse_args()

    args.out.write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
    print(f"Wrote OpenAPI schema to {args.out}")


if __name__ == "__main__":
    main()
