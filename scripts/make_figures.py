"""Slide and README figures, written to docs/figures/:

    area_over_time.png     main (DHDH) series with threshold range, HH-only line, QPDH dates as points
    comparison_<date>.png  HH, coherence and result side by side for one date
    frequency_map.png      water-detection frequency with the lake outline

Run after:  python scripts/map_water.py --mode DHDH
            python scripts/sensitivity.py --mode QPDH

Example
    python scripts/make_figures.py
"""
import csv
import sys
from datetime import date as Date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make `sambhar` importable

import numpy as np

from sambhar import config
from sambhar.coherence import coherence_for_date
from sambhar.granules import load_gunw_pairs
from sambhar.pans import pans_mask
from sambhar.plots import slide_area_over_time, slide_comparison, slide_frequency_map
from sambhar.storage import load_crop
from sambhar.water import classify_dark_unstable, classify_water, reduce_speckle, to_decibels

LAKE_MARGIN_PX = 40   # space around the lake outline in the map figures


def read_csv(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def main_series(rows: list[dict]) -> dict:
    """Main-series columns for the area chart, with NaN rows where dates are far apart (no line drawn)."""
    series = {"dates": [], "km2": [], "km2_min": [], "km2_max": [], "hh_only_km2": []}
    for row in rows:
        if series["dates"]:
            gap = (Date.fromisoformat(row["date"]) - Date.fromisoformat(series["dates"][-1])).days
            if gap > config.FIGURE_GAP_DAYS:
                series["dates"].append(series["dates"][-1])
                for key in ("km2", "km2_min", "km2_max", "hh_only_km2"):
                    series[key].append(np.nan)
        series["dates"].append(row["date"])
        series["km2"].append(float(row["water_km2"]))
        series["km2_min"].append(float(row["water_km2_min"]))
        series["km2_max"].append(float(row["water_km2_max"]))
        series["hh_only_km2"].append(float(row["hh_only_water_km2"]))
    return series


def other_mode_series(rows: list[dict]) -> dict:
    """Chosen-threshold area and range over all thresholds per date, from a sensitivity CSV."""
    series = {"dates": [], "km2": [], "km2_min": [], "km2_max": []}
    for date in sorted({r["date"] for r in rows}):
        values = [r for r in rows if r["date"] == date]
        chosen = [float(r["water_km2"]) for r in values
                  if float(r["threshold_db"]) == config.WATER_THRESHOLD_DB
                  and float(r["coherence_threshold"]) == config.COHERENCE_THRESHOLD]
        series["dates"].append(date)
        series["km2"].append(chosen[0])
        series["km2_min"].append(min(float(r["water_km2"]) for r in values))
        series["km2_max"].append(max(float(r["water_km2"]) for r in values))
    return series


def around_lake(lake: np.ndarray) -> tuple[slice, slice]:
    """Row and column window around the lake outline."""
    rows, cols = np.nonzero(lake)
    return (slice(max(rows.min() - LAKE_MARGIN_PX, 0), rows.max() + LAKE_MARGIN_PX),
            slice(max(cols.min() - LAKE_MARGIN_PX, 0), cols.max() + LAKE_MARGIN_PX))


def main():
    out = config.FIGURES_DIR
    out.mkdir(parents=True, exist_ok=True)
    results = config.RESULTS_DIR

    main_rows = read_csv(results / "water_area.csv")
    other_rows = read_csv(results / "sensitivity_QPDH.csv")
    slide_area_over_time(main_series(main_rows), other_mode_series(other_rows), out / "area_over_time.png")

    date = config.FIGURE_COMPARISON_DATE
    crop = load_crop(config.CROPS_DIR / f"{date}.npz")
    lake = pans_mask(config.LAKE_GEOJSON, crop.grid)
    window = around_lake(lake)
    hh_db = reduce_speckle(to_decibels(crop.hh), config.SPECKLE_WINDOW)
    coherence, pair, _ = coherence_for_date(date, load_gunw_pairs(), config.COHERENCE_DIR)
    detected, valid = classify_dark_unstable(hh_db, coherence, config.WATER_THRESHOLD_DB,
                                             config.COHERENCE_THRESHOLD)
    hh_dark = classify_water(hh_db, config.WATER_THRESHOLD_DB)[0] & valid
    title = (f"{Date.fromisoformat(date):%d %B %Y}: HH < {config.WATER_THRESHOLD_DB:g} dB "
             f"AND coherence < {config.COHERENCE_THRESHOLD:g} (pair to {pair.secondary_date})")
    slide_comparison(hh_db[window], coherence[window], detected[window], hh_dark[window], lake[window],
                     title, out / f"comparison_{date}.png")

    saved = np.load(results / "frequency.npz")
    n_valid = saved["n_valid"]
    n_dates_text = f"{len(main_rows)} dual-pol dates, Apr-Oct 2026 ({n_valid.min()}-{n_valid.max()} valid observations per pixel)"
    slide_frequency_map(saved["frequency"][window], lake[window], n_dates_text, out / "frequency_map.png")
    print(f"Figures written to {out}")


if __name__ == "__main__":
    main()
