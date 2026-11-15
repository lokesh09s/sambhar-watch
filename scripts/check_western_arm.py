"""Robustness check: how big is the western arm that the lake outline misses, and does it matter?

The hand-drawn outline (data/lake.geojson) cuts off a dark arm of the lake bed in the
north-west. This script:
  1. delineates the arm on config.ARM_DELINEATION_DATE: the area outside the outline with
     low 12-day coherence that is connected to the outline's western third;
  2. prints its size and whether it reaches the edge of the study grid;
  3. prints the area detected in it on every main-series (DHDH) date;
  4. checks whether the drop between config.OUTLINE_CHECK_DATES still holds when the arm
     is added, for every threshold pair of the sensitivity check.
It changes no results and does not change the outline.

Example
    python scripts/check_western_arm.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make `sambhar` and `scripts` importable

import numpy as np

from sambhar import config
from sambhar.coherence import coherence_for_date
from sambhar.granules import load_gunw_pairs
from sambhar.pans import pans_mask
from sambhar.storage import load_crop
from sambhar.water import classify_dark_unstable, reduce_speckle, to_decibels
from scripts.map_water import select_crops


def grow_by_one(mask: np.ndarray) -> np.ndarray:
    """The mask plus every pixel directly above, below, left or right of it."""
    grown = mask.copy()
    grown[1:] |= mask[:-1]
    grown[:-1] |= mask[1:]
    grown[:, 1:] |= mask[:, :-1]
    grown[:, :-1] |= mask[:, 1:]
    return grown


def connected_to(seed: np.ndarray, allowed: np.ndarray) -> np.ndarray:
    """All `allowed` pixels that can be reached from `seed` by steps through `allowed` pixels."""
    region = seed & allowed
    while True:
        grown = grow_by_one(region) & allowed
        if grown.sum() == region.sum():
            return region
        region = grown


def delineate_arm(lake: np.ndarray, pairs) -> np.ndarray:
    """The missed arm: low-coherence area outside the outline, connected to the outline's western third."""
    coherence, _, _ = coherence_for_date(config.ARM_DELINEATION_DATE, pairs, config.COHERENCE_DIR)
    low_coherence = reduce_speckle(coherence, config.ARM_SMOOTHING_WINDOW) < config.COHERENCE_THRESHOLD
    outside = low_coherence & ~lake

    lake_cols = np.nonzero(lake)[1]
    western_third = lake_cols.min() + config.ARM_SEED_FRACTION * (lake_cols.max() - lake_cols.min())
    touching_outline = grow_by_one(lake) & outside
    touching_outline[:, int(western_third):] = False
    return connected_to(touching_outline, outside)


def detected_areas(crop, pairs, lake, arm, threshold_db, coherence_threshold):
    """Detected area (km2) inside the outline and in the arm for one date, or None if it has no coherence."""
    coherence, _, _ = coherence_for_date(crop.date, pairs, config.COHERENCE_DIR)
    if coherence is None:
        return None
    hh_db = reduce_speckle(to_decibels(crop.hh), config.SPECKLE_WINDOW)
    detected, _ = classify_dark_unstable(hh_db, coherence, threshold_db, coherence_threshold)
    km2 = crop.grid.pixel_area_km2
    return (detected & lake).sum() * km2, (detected & arm).sum() * km2


def main():
    pairs = load_gunw_pairs()
    crops = {c.date: c for c in select_crops("DHDH", include_validated=False)}
    grid = crops[config.ARM_DELINEATION_DATE].grid
    lake = pans_mask(config.LAKE_GEOJSON, grid)
    arm = delineate_arm(lake, pairs)

    on_edge = arm[0].sum() + arm[-1].sum() + arm[:, 0].sum() + arm[:, -1].sum()
    print(f"Western arm (delineated on {config.ARM_DELINEATION_DATE}): {arm.sum() * grid.pixel_area_km2:.1f} km2")
    print(f"Pixels on the edge of the study grid: {on_edge}"
          f" (westernmost pixel is {np.nonzero(arm)[1].min() * grid.resolution_m / 1000:.1f} km inside the west edge)")

    print("\nDetected area, km2 (default thresholds)")
    print(f"  {'date':<12}{'inside outline':>15}{'in the arm':>12}{'together':>10}")
    for date, crop in crops.items():
        areas = detected_areas(crop, pairs, lake, arm, config.WATER_THRESHOLD_DB, config.COHERENCE_THRESHOLD)
        if areas:
            print(f"  {date:<12}{areas[0]:>15.1f}{areas[1]:>12.1f}{sum(areas):>10.1f}")

    first, second = config.OUTLINE_CHECK_DATES
    print(f"\nDrop from {first} to {second} with the arm added, km2")
    drops = []
    for threshold_db in config.SENSITIVITY_THRESHOLDS_DB:
        for coherence_threshold in config.SENSITIVITY_COHERENCE:
            before = sum(detected_areas(crops[first], pairs, lake, arm, threshold_db, coherence_threshold))
            after = sum(detected_areas(crops[second], pairs, lake, arm, threshold_db, coherence_threshold))
            drops.append(before - after)
            print(f"  HH < {threshold_db:g} dB, coherence < {coherence_threshold:g}:"
                  f"  {before:6.1f} -> {after:5.1f}  drop {drops[-1]:5.1f}")
    print(f"The second date is lower in {sum(d > 0 for d in drops)} of {len(drops)} threshold pairs"
          f" (drop {min(drops):.1f} to {max(drops):.1f} km2).")


if __name__ == "__main__":
    main()
