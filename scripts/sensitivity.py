"""Sensitivity check: how much do the in-lake areas depend on the chosen thresholds?

For every date with coherence, re-applies the rule "HH < T AND coherence < C" for each
T in config.SENSITIVITY_THRESHOLDS_DB and C in config.SENSITIVITY_COHERENCE, inside
the lake outline, then compares the spread caused by the thresholds on one date with
the difference between dates (the seasonal signal).

Writes outputs/results/sensitivity_<mode>.csv (one row per date and threshold pair).

Examples
    python scripts/sensitivity.py --mode DHDH
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make `sambhar` and `scripts` importable

import numpy as np

from sambhar import config
from sambhar.coherence import coherence_for_date
from sambhar.granules import load_gunw_pairs
from sambhar.water import classify_dark_unstable, reduce_speckle, to_decibels
from scripts.map_water import areas, region_masks, select_crops


def area_table(crops, regions, pairs) -> list[dict]:
    """In-lake areas for every date and every threshold pair."""
    rows = []
    for c in crops:
        coherence, pair, direction = coherence_for_date(c.date, pairs, config.COHERENCE_DIR)
        if coherence is None:
            print(f"[{c.date}] no 12-day coherence pair, left out")
            continue
        hh_db = reduce_speckle(to_decibels(c.hh), config.SPECKLE_WINDOW)
        for t in config.SENSITIVITY_THRESHOLDS_DB:
            for coh in config.SENSITIVITY_COHERENCE:
                detected, _ = classify_dark_unstable(hh_db, coherence, t, coh)
                rows.append({"date": c.date, "mode": c.mode, "threshold_db": t, "coherence_threshold": coh,
                             "coherence_pair": f"{pair.reference_date} to {pair.secondary_date}",
                             "pair_direction": direction,
                             **areas(detected, regions, c.grid.pixel_area_km2, "water")})
    return rows


def summarise(rows: list[dict], scope_label: str) -> None:
    """Print, per date, the area at the chosen thresholds and its range over all threshold pairs,
    then compare the largest single-date range with the difference between dates."""
    dates = sorted({r["date"] for r in rows})
    chosen = {r["date"]: r["water_km2"] for r in rows
              if r["threshold_db"] == config.WATER_THRESHOLD_DB and r["coherence_threshold"] == config.COHERENCE_THRESHOLD}
    print(f"\nArea {scope_label} (km2). Chosen: T = {config.WATER_THRESHOLD_DB} dB, C = {config.COHERENCE_THRESHOLD}")
    print(f"  {'date':<12}{'chosen':>8}{'min':>8}{'max':>8}{'range':>8}")
    spreads = []
    for date in dates:
        values = [r["water_km2"] for r in rows if r["date"] == date]
        spreads.append(max(values) - min(values))
        print(f"  {date:<12}{chosen[date]:>8.1f}{min(values):>8.1f}{max(values):>8.1f}{spreads[-1]:>8.1f}")

    print("\nDifference between dates (max - min over dates), for each threshold pair:")
    between = []
    for t in config.SENSITIVITY_THRESHOLDS_DB:
        line = []
        for coh in config.SENSITIVITY_COHERENCE:
            values = [r["water_km2"] for r in rows if r["threshold_db"] == t and r["coherence_threshold"] == coh]
            between.append(max(values) - min(values))
            line.append(f"C={coh}: {between[-1]:5.1f}")
        print(f"  T={t:>5}  " + "   ".join(line))

    widest = max(spreads)
    print(f"\nLargest threshold-induced range on one date: {widest:.1f} km2 (median {np.median(spreads):.1f})")
    print(f"Difference between dates: {min(between):.1f} to {max(between):.1f} km2 depending on the thresholds")
    if max(between) < widest:
        print("=> The difference between dates is SMALLER than the threshold-induced range:"
              " the choice of thresholds changes the areas more than the season does.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["DHDH", "QPDH"], help="use only one radar mode")
    parser.add_argument("--include-validated", action="store_true", help="also use validated-release dates")
    args = parser.parse_args()

    crops = select_crops(args.mode, args.include_validated)
    regions, scope_label = region_masks(crops[0].grid)
    rows = area_table(crops, regions, load_gunw_pairs())

    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.RESULTS_DIR / f"sensitivity_{args.mode or 'all'}.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summarise(rows, scope_label)


if __name__ == "__main__":
    main()
