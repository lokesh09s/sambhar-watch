"""Step 2: water maps, water area per date, and water-detection frequency.

Reads outputs/crops/*.npz (from crop_lake.py) and writes to outputs/results/:
    water_area.csv     water area per date: total, inside mapped pans, outside mapped pans
    frequency.png      how often each pixel was detected as water, and how many valid observations
    overlays/<date>.png transparent water layers for the web map
    map_info.json      map bounds and dates, used by the web app

Examples
    python scripts/map_water.py                         # uses WATER_THRESHOLD_DB from config.py
    python scripts/map_water.py --threshold -17.5
    python scripts/map_water.py --suggest-threshold     # print Otsu suggestions per date, then stop
    python scripts/map_water.py --mode DHDH             # only dual-pol dates
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make `sambhar` importable

import numpy as np

from sambhar import config
from sambhar.pans import pans_mask
from sambhar.plots import frequency_map, water_overlay
from sambhar.storage import load_all_crops
from sambhar.water import (classify_water, detection_frequency, otsu_threshold,
                           reduce_speckle, to_decibels)


def select_crops(mode: str | None, include_validated: bool):
    crops = load_all_crops(config.CROPS_DIR)
    if mode:
        crops = [c for c in crops if c.mode == mode]
    if not include_validated:
        crops = [c for c in crops if c.release == "provisional"]
    if not crops:
        raise SystemExit("No cropped dates found. Run scripts/crop_lake.py first.")
    return crops


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--threshold", type=float, default=config.WATER_THRESHOLD_DB,
                        help="HH dB threshold (default from config.py)")
    parser.add_argument("--suggest-threshold", action="store_true",
                        help="print Otsu threshold suggestions per date and exit")
    parser.add_argument("--mode", choices=["DHDH", "QPDH"], help="use only one radar mode")
    parser.add_argument("--include-validated", action="store_true",
                        help="also use validated-release dates (check consistency first)")
    args = parser.parse_args()

    crops = select_crops(args.mode, args.include_validated)
    grid = crops[0].grid
    hh_db = {c.date: reduce_speckle(to_decibels(c.hh), config.SPECKLE_WINDOW) for c in crops}

    if args.suggest_threshold:
        for c in crops:
            print(f"{c.date} [{c.mode}]  Otsu suggestion: {otsu_threshold(hh_db[c.date]):.1f} dB")
        print("Suggestions only: check against the histograms and Sentinel-2 before choosing.")
        return

    in_pans = (pans_mask(config.PANS_GEOJSON, grid) if config.PANS_GEOJSON.exists()
               else np.zeros(grid.shape, dtype=bool))
    if not in_pans.any():
        print("Note: no data/pans.geojson found, so 'inside pans' areas will be zero.")

    out = config.RESULTS_DIR
    (out / "overlays").mkdir(parents=True, exist_ok=True)

    rows, water_stack, valid_stack = [], [], []
    for c in crops:
        if c.grid.shape != grid.shape or c.grid.epsg != grid.epsg:
            print(f"[{c.date}] different grid, skipping")
            continue
        water, valid = classify_water(hh_db[c.date], args.threshold)
        water_stack.append(water)
        valid_stack.append(valid)
        water_overlay(water, out / "overlays" / f"{c.date}.png")

        km2 = lambda mask: round(float(mask.sum()) * grid.pixel_area_km2, 3)
        rows.append({
            "date": c.date, "mode": c.mode, "release": c.release, "threshold_db": args.threshold,
            "valid_area_km2": km2(valid),
            "water_km2": km2(water),
            "water_inside_mapped_pans_km2": km2(water & in_pans),
            "water_outside_mapped_pans_km2": km2(water & ~in_pans),
        })
        print(f"[{c.date}] water {rows[-1]['water_km2']} km2")

    with open(out / "water_area.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    frequency, n_valid = detection_frequency(np.array(water_stack), np.array(valid_stack))
    frequency_map(frequency, n_valid, out / "frequency.png")
    np.savez_compressed(out / "frequency.npz", frequency=frequency, n_valid=n_valid)

    with open(out / "map_info.json", "w") as f:
        json.dump({"bounds_latlon": grid.bounds_latlon(), "epsg": grid.epsg,
                   "resolution_m": grid.resolution_m, "threshold_db": args.threshold,
                   "dates": [r["date"] for r in rows]}, f, indent=2)

    print(f"\nResults written to {out}")


if __name__ == "__main__":
    main()
