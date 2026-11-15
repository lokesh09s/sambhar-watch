"""Coherence check: can 12-day coherence tell water apart from smooth salt crust?

For each chosen interferogram pair (given by its first date), crops the
coherence layer onto the study grid, prints median HH and coherence for the
test regions in config.CHECK_REGIONS, and saves a figure to outputs/coherence/.
Needs the GCOV crop of the first date (scripts/crop_lake.py) for HH and the grid.

Examples
    python scripts/check_coherence.py 2026-05-11 2026-08-15
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make `sambhar` importable

import numpy as np

from sambhar import config
from sambhar.coherence import crop_coherence
from sambhar.granules import GunwPair, load_gunw_pairs, open_remote
from sambhar.grid import Grid, box_mask
from sambhar.plots import coherence_check
from sambhar.storage import load_crop
from sambhar.water import reduce_speckle, to_decibels


def coherence_for(pair: GunwPair, grid: Grid) -> np.ndarray:
    """Cropped coherence for a pair, streamed from the GUNW file the first time and saved."""
    path = config.COHERENCE_DIR / f"{pair.reference_date}_{pair.secondary_date}.npz"
    if path.exists():
        return np.load(path)["coherence"]
    with open_remote(pair.url) as h5:
        coherence = crop_coherence(h5, grid)
    config.COHERENCE_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, coherence=coherence)
    return coherence


def check(pair: GunwPair) -> None:
    """Print region statistics and save the HH / coherence figure for one pair."""
    crop = load_crop(config.CROPS_DIR / f"{pair.reference_date}.npz")
    hh_db = reduce_speckle(to_decibels(crop.hh), config.SPECKLE_WINDOW)
    coherence = coherence_for(pair, crop.grid)
    regions = {name: box_mask(crop.grid, box) for name, box in config.CHECK_REGIONS.items()}

    label = f"{pair.reference_date} to {pair.secondary_date}"
    print(f"\n{label}  (HH from {pair.reference_date})")
    print(f"  {'region':<14}{'HH median dB':>14}{'coherence median':>18}{'coherence 25-75%':>18}{'pixels':>9}")
    for name, region in regions.items():
        inside = region & np.isfinite(hh_db) & np.isfinite(coherence)
        q25, q50, q75 = np.percentile(coherence[inside], [25, 50, 75])
        print(f"  {name:<14}{np.median(hh_db[inside]):>14.1f}{q50:>18.2f}{f'{q25:.2f}-{q75:.2f}':>18}{inside.sum():>9}")

    figure = config.COHERENCE_DIR / f"{pair.reference_date}_{pair.secondary_date}.png"
    coherence_check(hh_db, coherence, regions, label, figure)
    print(f"  figure: {figure}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dates", nargs="+", help="first date (YYYY-MM-DD) of each pair in data/gunw_pairs.csv")
    args = parser.parse_args()

    pairs = {p.reference_date: p for p in load_gunw_pairs()}
    for date in args.dates:
        if date not in pairs:
            print(f"[{date}] no 12-day pair starts on this date, skipping")
            continue
        check(pairs[date])


if __name__ == "__main__":
    main()
