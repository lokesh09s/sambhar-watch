"""Step 3: check our water maps against points labelled on Sentinel-2 images.

Input: a CSV with columns lon, lat, label, date (extra columns are ignored).
    label  water, salt_crust or land, as seen on a cloud-free Sentinel-2 image
    date   the Sentinel-2 image date, YYYY-MM-DD
See data/validation_points_TEMPLATE.csv.

Each point is compared with our water map from the NISAR date closest to its
Sentinel-2 date, made exactly as map_water.py does (same dates and threshold,
read from map_info.json). Points with no NISAR date within --max-days are skipped.

Writes to outputs/results/:
    validation.csv           one row per point: label, NISAR date used, HH dB, radar result
    validation_summary.txt   confusion matrix, overall accuracy, water precision and recall,
                             and separately how often salt crust was wrongly called water

Examples
    python scripts/validate.py data/validation_points.csv
    python scripts/validate.py data/validation_points.csv --max-days 3
    python scripts/validate.py points.csv --crops outputs/demo/crops --results outputs/demo/results   # FAKE demo
"""
import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make `sambhar` importable

import numpy as np
from pyproj import Transformer

from sambhar import config
from sambhar.storage import load_crop
from sambhar.water import classify_water, reduce_speckle, to_decibels

LABELS = ["water", "salt_crust", "land"]


def read_points(path: Path) -> list[dict]:
    """Read and check the labelled points. Stops with a clear message on a bad row."""
    points = []
    with open(path, newline="") as f:
        for line_number, row in enumerate(csv.DictReader(f), start=2):
            label = row["label"].strip()
            if label not in LABELS:
                raise SystemExit(f"{path}, line {line_number}: label '{label}' is not one of {LABELS}")
            try:
                points.append({"lon": float(row["lon"]), "lat": float(row["lat"]), "label": label,
                               "s2_date": date.fromisoformat(row["date"].strip())})
            except ValueError as error:
                raise SystemExit(f"{path}, line {line_number}: {error}")
    return points


def nearest_date(s2_date: date, nisar_dates: list[str]) -> tuple[str, int]:
    """The NISAR date closest to the Sentinel-2 date, and how many days apart they are."""
    gaps = [abs((date.fromisoformat(d) - s2_date).days) for d in nisar_dates]
    best = int(np.argmin(gaps))
    return nisar_dates[best], gaps[best]


def radar_result(lon: float, lat: float, hh_db: np.ndarray, water: np.ndarray, grid) -> tuple[str, float]:
    """What our water map says at a point: 'water', 'not_water' or 'no_data', plus the HH value in dB."""
    to_map = Transformer.from_crs("EPSG:4326", f"EPSG:{grid.epsg}", always_xy=True)
    x, y = to_map.transform(lon, lat)
    col = int(round((x - grid.x[0]) / grid.resolution_m))
    row = int(round((grid.y[0] - y) / grid.resolution_m))   # y runs north to south
    if not (0 <= row < grid.shape[0] and 0 <= col < grid.shape[1]) or not np.isfinite(hh_db[row, col]):
        return "no_data", float("nan")
    return ("water" if water[row, col] else "not_water"), float(hh_db[row, col])


def summarise(rows: list[dict], threshold_db: float, max_days: int) -> str:
    """Plain-text summary: confusion matrix and the scores, from the points that could be compared."""
    used = [r for r in rows if r["radar_result"] in ("water", "not_water")]
    count = lambda label, result: sum(r["label"] == label and r["radar_result"] == result for r in used)
    ratio = lambda a, b: f"{a / b:.1%} ({a}/{b})" if b else "n/a (no points)"

    true_water = count("water", "water")                                   # water called water
    missed_water = count("water", "not_water")                             # water called not water
    false_water = count("salt_crust", "water") + count("land", "water")    # dry called water
    correct = true_water + count("salt_crust", "not_water") + count("land", "not_water")
    crust_total = count("salt_crust", "water") + count("salt_crust", "not_water")
    land_total = count("land", "water") + count("land", "not_water")

    lines = [
        "Validation of NISAR water maps against Sentinel-2 labelled points",
        f"Threshold: HH < {threshold_db} dB.  Nearest NISAR date within {max_days} days.",
        f"Points compared: {len(used)} of {len(rows)} "
        f"(skipped: {sum(r['radar_result'] == 'no_data' for r in rows)} no radar data, "
        f"{sum(r['radar_result'] == 'too_far_in_time' for r in rows)} no NISAR date close enough)",
        "",
        "Confusion matrix (rows: Sentinel-2 label, columns: radar result)",
        f"{'':12}{'water':>10}{'not water':>11}",
    ]
    lines += [f"{label:12}{count(label, 'water'):>10}{count(label, 'not_water'):>11}" for label in LABELS]
    lines += [
        "",
        f"Overall accuracy (water vs not water): {ratio(correct, len(used))}",
        f"Water precision (radar 'water' that really is water): {ratio(true_water, true_water + false_water)}",
        f"Water recall (real water that radar found): {ratio(true_water, true_water + missed_water)}",
        "",
        f"Salt crust wrongly called water: {ratio(count('salt_crust', 'water'), crust_total)}",
        f"Land wrongly called water: {ratio(count('land', 'water'), land_total)}",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("points", type=Path, help="CSV of labelled points (lon, lat, label, date)")
    parser.add_argument("--max-days", type=int, default=6,
                        help="skip points with no NISAR date this close (default 6, half the 12-day repeat)")
    parser.add_argument("--crops", type=Path, default=config.CROPS_DIR, help="cropped dates (default outputs/crops)")
    parser.add_argument("--results", type=Path, default=config.RESULTS_DIR,
                        help="folder with map_info.json; results are written here too (default outputs/results)")
    args = parser.parse_args()

    if not (args.results / "map_info.json").exists():
        raise SystemExit(f"No map_info.json in {args.results}. Run scripts/map_water.py first.")
    info = json.loads((args.results / "map_info.json").read_text())
    threshold = info["threshold_db"]

    water_maps = {}   # NISAR date -> (crop, hh_db, water), loaded only when a point needs it
    rows = []
    for p in read_points(args.points):
        nisar_date, days = nearest_date(p["s2_date"], info["dates"])
        row = {"lon": p["lon"], "lat": p["lat"], "label": p["label"], "s2_date": p["s2_date"].isoformat(),
               "nisar_date": nisar_date, "days_apart": days, "hh_db": "", "radar_result": "too_far_in_time"}
        if days <= args.max_days:
            if nisar_date not in water_maps:
                crop = load_crop(args.crops / f"{nisar_date}.npz")
                hh_db = reduce_speckle(to_decibels(crop.hh), config.SPECKLE_WINDOW)
                water_maps[nisar_date] = (crop, hh_db, classify_water(hh_db, threshold)[0])
            crop, hh_db, water = water_maps[nisar_date]
            row["radar_result"], hh = radar_result(p["lon"], p["lat"], hh_db, water, crop.grid)
            row["hh_db"] = "" if np.isnan(hh) else round(hh, 2)
        rows.append(row)

    if not rows:
        raise SystemExit(f"No points in {args.points}.")

    args.results.mkdir(parents=True, exist_ok=True)
    with open(args.results / "validation.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = summarise(rows, threshold, args.max_days)
    (args.results / "validation_summary.txt").write_text(summary + "\n")
    print(summary)
    print(f"\nWritten to {args.results / 'validation.csv'} and validation_summary.txt")


if __name__ == "__main__":
    main()
