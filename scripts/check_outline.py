"""Robustness check: the hand-drawn lake outline misses part of the western lake bed.

Looks at a zone OUTSIDE the outline, within config.OUTLINE_CHECK_BUFFER_M of it, on the
west / south-west side: south-west of the lake's long axis, or west of its western tip.
Prints the zone's size, the area detected there with the default rule on the dates in
config.OUTLINE_CHECK_DATES, and whether the drop between them holds when the zone is added.
Changes no results.

Example
    python scripts/check_outline.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make `sambhar` importable

import numpy as np

from sambhar import config
from sambhar.coherence import coherence_for_date
from sambhar.granules import load_gunw_pairs
from sambhar.pans import pans_mask
from sambhar.storage import load_crop
from sambhar.water import classify_dark_unstable, reduce_speckle, to_decibels


def within_distance(mask: np.ndarray, radius_px: int) -> np.ndarray:
    """True for pixels within radius_px (straight-line distance) of any True pixel of `mask`."""
    rows, cols = mask.shape
    counts = np.pad(np.cumsum(mask, axis=1), ((0, 0), (1, 0)))   # counts[:, k] = True pixels left of column k
    column = np.arange(cols)
    near = np.zeros_like(mask)
    for dy in range(-radius_px, radius_px + 1):
        reach = int(np.sqrt(radius_px ** 2 - dy ** 2))   # how far sideways the circle extends at this row offset
        in_row = counts[:, np.minimum(column + reach + 1, cols)] > counts[:, np.maximum(column - reach, 0)]
        if dy >= 0:
            near[dy:] |= in_row[:rows - dy]
        else:
            near[:dy] |= in_row[-dy:]
    return near


def south_west_side(lake: np.ndarray) -> np.ndarray:
    """True for pixels south-west of the lake's long axis, or west of the lake's western tip."""
    lake_rows, lake_cols = np.nonzero(lake)
    centre = np.array([lake_cols.mean(), lake_rows.mean()])
    spread = np.cov(np.vstack([lake_cols, lake_rows]))
    long_axis = np.linalg.eigh(spread)[1][:, -1]
    across = np.array([-long_axis[1], long_axis[0]])
    if across[0] - across[1] > 0:      # make `across` point south-west (west = -x, south = +row)
        across = -across
    cols, rows = np.meshgrid(np.arange(lake.shape[1]), np.arange(lake.shape[0]))
    return ((cols - centre[0]) * across[0] + (rows - centre[1]) * across[1] > 0) | (cols < lake_cols.min())


def main():
    pairs = load_gunw_pairs()
    grid = load_crop(config.CROPS_DIR / f"{config.OUTLINE_CHECK_DATES[0]}.npz").grid
    km2 = grid.pixel_area_km2
    lake = pans_mask(config.LAKE_GEOJSON, grid)
    radius_px = int(config.OUTLINE_CHECK_BUFFER_M / grid.resolution_m)
    zone = within_distance(lake, radius_px) & ~lake & south_west_side(lake)
    lake_cols = np.nonzero(lake)[1]
    arm_edge = lake_cols.min() + config.OUTLINE_CHECK_ARM_FRACTION * (lake_cols.max() - lake_cols.min())
    arm = zone & (np.arange(lake.shape[1]) < arm_edge)   # the western arm; the rest of the zone holds separate ponds
    print(f"Zone: outside the outline, within {config.OUTLINE_CHECK_BUFFER_M / 1000:g} km, west / south-west side:"
          f" {zone.sum() * km2:.1f} km2 (lake outline: {lake.sum() * km2:.1f} km2)")

    frequency = np.load(config.RESULTS_DIR / "frequency.npz")["frequency"]
    print(f"Detected on at least half of the main-series dates: {(zone & (frequency >= 0.5)).sum() * km2:.1f} km2"
          f" in the zone, of which {(arm & (frequency >= 0.5)).sum() * km2:.1f} km2 in the western arm;"
          f" {(lake & (frequency >= 0.5)).sum() * km2:.1f} km2 inside the outline")

    for date in config.OUTLINE_CHECK_DATES:
        crop = load_crop(config.CROPS_DIR / f"{date}.npz")
        hh_db = reduce_speckle(to_decibels(crop.hh), config.SPECKLE_WINDOW)
        coherence, _, _ = coherence_for_date(date, pairs, config.COHERENCE_DIR)
        detected, _ = classify_dark_unstable(hh_db, coherence, config.WATER_THRESHOLD_DB, config.COHERENCE_THRESHOLD)
        inside, outside = (detected & lake).sum() * km2, (detected & zone).sum() * km2
        in_arm = (detected & arm).sum() * km2
        print(f"{date}: inside outline {inside:.1f} km2 | zone {outside:.1f} km2 (together {inside + outside:.1f})"
              f" | western arm only {in_arm:.1f} km2 (together {inside + in_arm:.1f})")


if __name__ == "__main__":
    main()
