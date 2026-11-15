"""Do the two radar modes (DHDH dual-pol, QPDH quad-pol) measure the same brightness?

For each pair of neighbouring dates in config.MODE_CHECK_PAIRS, compares HH and HV (dB)
on stable ground: pixels whose 12-day coherence is at least config.STABLE_COHERENCE in
every cropped pair touching either date, i.e. ground that did not change. Same-mode
date pairs show how much HH differs between dates anyway; a mode problem shows up as a
mixed-mode difference clearly larger than that.

Also prints farmland coherence for every cropped 12-day pair, to see whether
mixed-mode pairs (DHDH with QPDH) give different coherence than same-mode pairs.

Example
    python scripts/check_modes.py
"""
import sys
from datetime import date as Date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make `sambhar` importable

import numpy as np

from sambhar import config
from sambhar.coherence import pair_file
from sambhar.granules import load_granules, load_gunw_pairs
from sambhar.grid import box_mask
from sambhar.storage import load_crop
from sambhar.water import reduce_speckle, to_decibels


def stable_ground(date_a: str, date_b: str, pairs, shape) -> tuple[np.ndarray, list]:
    """Pixels with coherence >= STABLE_COHERENCE in every cropped 12-day pair touching either date."""
    used = [p for p in pairs if {p.reference_date, p.secondary_date} & {date_a, date_b}
            and pair_file(p, config.COHERENCE_DIR).exists()]
    stable = np.ones(shape, dtype=bool)
    for p in used:
        coherence = np.load(pair_file(p, config.COHERENCE_DIR))["coherence"]
        stable &= np.nan_to_num(coherence, nan=0.0) >= config.STABLE_COHERENCE
    return stable, used


def compare_dates(date_a: str, date_b: str, pairs, modes: dict) -> None:
    """Print the median HH and HV change from date_a to date_b on stable ground."""
    a, b = (load_crop(config.CROPS_DIR / f"{d}.npz") for d in (date_a, date_b))
    stable, used = stable_ground(date_a, date_b, pairs, a.grid.shape)
    if not used:
        print(f"  {date_a} -> {date_b}: no cropped coherence pair yet, skipped")
        return

    changes = []
    for pol in ("hh", "hv"):
        db_a = reduce_speckle(to_decibels(getattr(a, pol)), config.SPECKLE_WINDOW)
        db_b = reduce_speckle(to_decibels(getattr(b, pol)), config.SPECKLE_WINDOW)
        both = stable & np.isfinite(db_a) & np.isfinite(db_b)
        q25, q50, q75 = np.percentile((db_b - db_a)[both], [25, 50, 75])
        changes.append(f"{np.median(db_a[both]):.1f} -> {np.median(db_b[both]):.1f}"
                       f"  change {q50:+5.2f} ({q25:+.1f} to {q75:+.1f})")

    days = (Date.fromisoformat(date_b) - Date.fromisoformat(date_a)).days
    kind = "MIXED" if modes[date_a] != modes[date_b] else "same "
    print(f"  {date_a} -> {date_b}  {kind} {modes[date_a]}->{modes[date_b]} {days:>3} d"
          f"  stable {stable.sum() * a.grid.pixel_area_km2:6.1f} km2 ({len(used)} pairs)"
          f"\n      HH {changes[0]}\n      HV {changes[1]}")


def farmland_coherence(pairs, modes: dict, grid) -> None:
    """Median farmland coherence of every cropped 12-day pair, labelled by radar modes."""
    farmland = box_mask(grid, config.CHECK_REGIONS["farmland"])
    for p in pairs:
        if not pair_file(p, config.COHERENCE_DIR).exists():
            continue
        coherence = np.load(pair_file(p, config.COHERENCE_DIR))["coherence"]
        kind = "MIXED" if modes[p.reference_date] != modes[p.secondary_date] else "same "
        print(f"  {p.reference_date} -> {p.secondary_date}  {kind} {modes[p.reference_date]}->"
              f"{modes[p.secondary_date]}  farmland coherence {np.nanmedian(coherence[farmland]):.2f}")


def main():
    pairs = load_gunw_pairs()
    modes = {g.date: g.mode for g in load_granules()}

    print(f"Median dB on stable ground (coherence >= {config.STABLE_COHERENCE}) on each date,"
          " and the per-pixel change: median (25% to 75%)")
    for date_a, date_b in config.MODE_CHECK_PAIRS:
        if not all((config.CROPS_DIR / f"{d}.npz").exists() for d in (date_a, date_b)):
            print(f"  {date_a} -> {date_b}: not cropped yet, skipped")
            continue
        compare_dates(date_a, date_b, pairs, modes)

    print("\nFarmland coherence per 12-day pair:")
    any_crop = next(config.CROPS_DIR.glob("*.npz"))
    farmland_coherence(pairs, modes, load_crop(any_crop).grid)


if __name__ == "__main__":
    main()
