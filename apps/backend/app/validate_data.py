from __future__ import annotations

import argparse
import sys

from app.data_store import load_station_bundle
from app.data_validation import validate_station_bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Nukemichi station demo data.")
    parser.add_argument("station_id", help="Station ID to validate, for example: ikebukuro")
    args = parser.parse_args(argv)

    bundle = load_station_bundle(args.station_id)
    issues = validate_station_bundle(bundle)

    print(f"Validated {bundle.station.station_id}: {len(issues)} issues")
    for issue in issues:
        print(f"- [{issue.code}] {issue.message}")

    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
