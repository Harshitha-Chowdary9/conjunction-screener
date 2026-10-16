"""Screen a small satellite catalog for close approaches.

Usage:
    python examples/run_screening.py                    # bundled sample TLEs (offline)
    python examples/run_screening.py --live stations    # fresh TLEs from CelesTrak

Prints every close approach under the threshold in the next 24 hours and
writes a 3D plot of the closest one to examples/closest_approach.png.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from conjunction_screener import (  # noqa: E402
    closest_approach,
    dedupe_same_orbit,
    fetch_group,
    load_sample_tles,
    screen_catalog,
)
from conjunction_screener.visualize import plot_close_approach  # noqa: E402

PLOT_PATH = Path(__file__).resolve().parent / "closest_approach.png"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", metavar="GROUP", help="CelesTrak group to download instead of the bundled sample")
    parser.add_argument("--hours", type=float, default=24.0, help="screening window in hours")
    parser.add_argument("--threshold", type=float, default=50.0, help="miss-distance threshold in km")
    args = parser.parse_args()

    if args.live:
        print(f"Downloading current TLEs for CelesTrak group {args.live!r} ...")
        records = fetch_group(args.live)
    else:
        print("Using the bundled sample TLEs (CelesTrak 'stations' snapshot, 2026-10-15).")
        records = load_sample_tles()
    before = len(records)
    records = dedupe_same_orbit(records)
    if len(records) < before:
        print(f"Merged {before - len(records)} object(s) sharing one orbit "
              f"(e.g. docked station modules).")
    print(f"{len(records)} objects. Screening {len(records) * (len(records) - 1) // 2} pairs "
          f"over {args.hours:g} h ...")

    start = datetime.now(timezone.utc).replace(microsecond=0)
    approaches = screen_catalog(records, start, duration_hours=args.hours, threshold_km=args.threshold)

    if approaches:
        print(f"\n{len(approaches)} close approach(es) under {args.threshold:g} km:")
        for approach in approaches[:20]:
            print(" ", approach)
    else:
        print(f"\nNo approaches under {args.threshold:g} km in this window.")

    # Plot the single closest pair regardless of threshold, so there is
    # always something to look at.
    print("\nFinding the closest pair overall for the plot ...")
    best = None
    for i, rec_a in enumerate(records):
        for rec_b in records[i + 1:]:
            candidate = closest_approach(rec_a, rec_b, start, duration_hours=args.hours)
            if best is None or candidate.distance_km < best.distance_km:
                best = candidate
                best_pair = (rec_a, rec_b)
    print("Closest pair:", best)
    path = plot_close_approach(best_pair[0], best_pair[1], best, PLOT_PATH)
    print(f"Plot written to {path}")


if __name__ == "__main__":
    main()
