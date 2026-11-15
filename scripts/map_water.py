"""Step 2: maps of dark unstable surface (water or wet brine), area per date, and detection frequency.

Rule (provisional, see config.py): a pixel is detected when HH is darker than
the threshold AND its 12-day coherence is low (the surface changed between passes).
The HH-only result is kept next to it, to show how much dark but stable surface
(dry crust, dry fields) coherence removes.

Reads outputs/crops/*.npz (crop_lake.py) and outputs/coherence/*.npz
(check_coherence.py) and writes to outputs/results/:
    water_area.csv        area per date (km2) with the combined rule (water_*) and HH only (hh_only_water_*),
                          all INSIDE the lake outline (data/lake.geojson; whole study box if missing):
                          total, inside / outside mapped pans ("salt works and mapped pans"), plus
                          *_study_box_km2 for context. water_km2_min / _max: range of water_km2 over
                          the threshold pairs in config.SENSITIVITY_*. coherence_pair: the one 12-day pair
                          used; pair_direction: forward (starts on the date) or backward (ends on it,
                          used only when no pair starts on it); pair_modes: radar modes of its two dates.
    rule_comparison.png   HH-only vs combined area per date
    frequency.png         detection frequency (detections / valid observations) and observation count
    overlays/<date>.png           combined-rule layers for the web map
    overlays_hh_only/<date>.png   HH-only layers, for comparison
    map_info.json         map bounds, dates, thresholds and class name, used by the web app

Each date uses one 12-day coherence pair: the one starting on it, else the one ending on it.
Dates with neither are left out.

Examples
    python scripts/map_water.py                         # thresholds from config.py
    python scripts/map_water.py --threshold -17.5 --coherence-threshold 0.35
    python scripts/map_water.py --suggest-threshold     # print Otsu suggestions per date, then stop
    python scripts/map_water.py --mode DHDH             # only dual-pol dates
"""
import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make `sambhar` importable

import numpy as np

from sambhar import config
from sambhar.coherence import coherence_for_date
from sambhar.granules import load_granules, load_gunw_pairs
from sambhar.pans import pans_mask
from sambhar.plots import frequency_map, rule_comparison, water_overlay
from sambhar.storage import load_all_crops, save_npz
from sambhar.water import (classify_dark_unstable, classify_water, detection_frequency,
                           otsu_threshold, reduce_speckle, to_decibels)


def select_crops(mode: str | None, include_validated: bool):
    crops = load_all_crops(config.CROPS_DIR)
    if mode:
        crops = [c for c in crops if c.mode == mode]
    if not include_validated:
        crops = [c for c in crops if c.release == "provisional"]
    if not crops:
        raise SystemExit("No cropped dates found. Run scripts/crop_lake.py first.")
    return crops


def region_masks(grid) -> tuple[dict, str]:
    """Pixel maps of the areas reported, keyed by column-name suffix, and a label for the area.

    Areas are counted inside the lake outline only: pan shapes outside the lake are rough
    rectangles, so they are not used. Without a lake outline, the whole study box is used.
    """
    everything = np.ones(grid.shape, dtype=bool)
    in_pans = (pans_mask(config.PANS_GEOJSON, grid) if config.PANS_GEOJSON.exists()
               else np.zeros(grid.shape, dtype=bool))
    if not in_pans.any():
        print("Note: no data/pans.geojson found, so 'inside pans' areas will be zero.")
    # pans_mask turns any hand-drawn polygons into a pixel mask, so it also reads the lake outline.
    if config.LAKE_GEOJSON.exists():
        scope, scope_label = pans_mask(config.LAKE_GEOJSON, grid), "inside lake outline"
    else:
        print("Note: no data/lake.geojson found, so areas cover the whole study box.")
        scope, scope_label = everything, "in study box"

    regions = {
        "": scope,
        "_inside_mapped_pans": scope & in_pans,
        "_outside_mapped_pans": scope & ~in_pans,
        "_study_box": everything,   # context only: includes other ponds and channels
    }
    return regions, scope_label


def areas(detected, regions: dict, pixel_area_km2: float, prefix: str) -> dict:
    """Detected area (km2) in each region, as CSV columns."""
    return {f"{prefix}{suffix}_km2": round(float((detected & region).sum()) * pixel_area_km2, 3)
            for suffix, region in regions.items()}


def area_range(hh_db, coherence, region, pixel_area_km2: float) -> tuple[float, float]:
    """Smallest and largest detected area in `region` over all threshold pairs of the sensitivity check."""
    found = [float((classify_dark_unstable(hh_db, coherence, t, c)[0] & region).sum()) * pixel_area_km2
             for t in config.SENSITIVITY_THRESHOLDS_DB for c in config.SENSITIVITY_COHERENCE]
    return round(min(found), 3), round(max(found), 3)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--threshold", type=float, default=config.WATER_THRESHOLD_DB,
                        help="HH dB threshold (default from config.py)")
    parser.add_argument("--coherence-threshold", type=float, default=config.COHERENCE_THRESHOLD,
                        help="12-day coherence threshold (default from config.py)")
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

    regions, scope_label = region_masks(grid)
    pairs = load_gunw_pairs()
    modes = {g.date: g.mode for g in load_granules()}
    out = config.RESULTS_DIR
    for folder in ("overlays", "overlays_hh_only"):
        shutil.rmtree(out / folder, ignore_errors=True)   # drop dates from earlier runs
        (out / folder).mkdir(parents=True)

    rows, detected_stack, valid_stack = [], [], []
    for c in crops:
        if c.grid.shape != grid.shape or c.grid.epsg != grid.epsg:
            print(f"[{c.date}] different grid, skipping")
            continue
        coherence, pair, direction = coherence_for_date(c.date, pairs, config.COHERENCE_DIR)
        if coherence is None:
            print(f"[{c.date}] no 12-day coherence pair starts or ends on this date, left out")
            continue

        detected, valid = classify_dark_unstable(hh_db[c.date], coherence, args.threshold,
                                                 args.coherence_threshold)
        hh_dark, _ = classify_water(hh_db[c.date], args.threshold)
        hh_dark &= valid   # compare both rules on exactly the same pixels
        detected_stack.append(detected)
        valid_stack.append(valid)
        water_overlay(detected, out / "overlays" / f"{c.date}.png")
        water_overlay(hh_dark, out / "overlays_hh_only" / f"{c.date}.png")

        row = {"date": c.date, "mode": c.mode, "release": c.release, "threshold_db": args.threshold,
               "coherence_threshold": args.coherence_threshold,
               "coherence_pair": f"{pair.reference_date} to {pair.secondary_date}", "pair_direction": direction,
               "pair_modes": f"{modes[pair.reference_date]}-{modes[pair.secondary_date]}",
               "valid_area_km2": round(float((valid & regions[""]).sum()) * grid.pixel_area_km2, 3)}
        row.update(areas(detected, regions, grid.pixel_area_km2, "water"))
        row["water_km2_min"], row["water_km2_max"] = area_range(hh_db[c.date], coherence, regions[""],
                                                               grid.pixel_area_km2)
        row.update(areas(hh_dark, regions, grid.pixel_area_km2, "hh_only_water"))
        rows.append(row)
        print(f"[{c.date}] {scope_label}, km2 (pans / outside pans):"
              f"  HH only {row['hh_only_water_km2']} ({row['hh_only_water_inside_mapped_pans_km2']}"
              f" / {row['hh_only_water_outside_mapped_pans_km2']})"
              f"  ->  HH + coherence {row['water_km2']} ({row['water_inside_mapped_pans_km2']}"
              f" / {row['water_outside_mapped_pans_km2']}), range {row['water_km2_min']}-{row['water_km2_max']}")

    if not rows:
        raise SystemExit("No date has coherence. Run scripts/check_coherence.py all first.")

    with open(out / "water_area.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    rule_comparison([r["date"] for r in rows], [r["hh_only_water_km2"] for r in rows],
                    [r["water_km2"] for r in rows], scope_label, out / "rule_comparison.png")

    frequency, n_valid = detection_frequency(np.array(detected_stack), np.array(valid_stack))
    frequency_map(frequency, n_valid, out / "frequency.png")
    save_npz(out / "frequency.npz", frequency=frequency, n_valid=n_valid)

    with open(out / "map_info.json", "w") as f:
        json.dump({"bounds_latlon": grid.bounds_latlon(), "epsg": grid.epsg,
                   "resolution_m": grid.resolution_m, "threshold_db": args.threshold,
                   "coherence_threshold": args.coherence_threshold, "class_name": config.CLASS_NAME,
                   "pans_label": config.PANS_LABEL, "area_scope": scope_label,
                   "dates": [r["date"] for r in rows]}, f, indent=2)

    print(f"\nResults written to {out}")


if __name__ == "__main__":
    main()
