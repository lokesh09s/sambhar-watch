"""Step 3: check our maps against points labelled on Sentinel-2 images.

Input: a CSV with columns lon, lat, label, date (extra columns are ignored).
    label  water, salt_crust or land, as seen on a cloud-free Sentinel-2 image
           (rows with an empty label are skipped, so a half-labelled file can be used)
    date   the Sentinel-2 image date (or the NISAR date it was matched to), YYYY-MM-DD
See data/validation_points_TEMPLATE.csv.

Each point is compared with our result on the NISAR date closest to its date,
made exactly as map_water.py does: dates, T and C are read from map_info.json, and
coherence comes from the 12-day pair STARTING on that date. Two rules are tested:
    HH + coherence   HH < T AND coherence < C   (the current rule)
    HH only          HH < T, on the same pixels (for comparison)
Points with no NISAR date within --max-days are skipped.

Writes to outputs/results/:
    validation.csv           one row per point: label, NISAR date, HH dB, coherence, result of each rule
    validation_summary.txt   for each rule: confusion matrix, overall accuracy, water precision and
                             recall, and separately how often salt crust (and land) was called water

Examples
    python scripts/validate.py validation_data/points_2026-05-11.csv
    python scripts/validate.py points.csv --max-days 3
    python scripts/validate.py points.csv --crops outputs/demo/crops --coherence outputs/demo/coherence \\
        --results outputs/demo/results                                                  # FAKE demo
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
from sambhar.coherence import coherence_for_date
from sambhar.granules import load_gunw_pairs
from sambhar.storage import load_crop
from sambhar.water import classify_dark_unstable, classify_water, reduce_speckle, to_decibels

LABELS = ["water", "salt_crust", "land"]
RULES = {"result_hh_coherence": "HH + coherence (current rule)", "result_hh_only": "HH only (for comparison)"}


def read_points(path: Path) -> tuple[list[dict], int]:
    """Read and check the labelled points. Returns (points, number of rows with no label yet).

    Stops with a clear message on a row with an unknown label or a bad number or date.
    """
    points, unlabelled = [], 0
    with open(path, newline="") as f:
        for line_number, row in enumerate(csv.DictReader(f), start=2):
            label = (row["label"] or "").strip()
            if not label:
                unlabelled += 1
                continue
            if label not in LABELS:
                raise SystemExit(f"{path}, line {line_number}: label '{label}' is not one of {LABELS}")
            try:
                points.append({"lon": float(row["lon"]), "lat": float(row["lat"]), "label": label,
                               "s2_date": date.fromisoformat(row["date"].strip())})
            except ValueError as error:
                raise SystemExit(f"{path}, line {line_number}: {error}")
    return points, unlabelled


def nearest_date(s2_date: date, nisar_dates: list[str]) -> tuple[str, int]:
    """The NISAR date closest to the Sentinel-2 date, and how many days apart they are."""
    gaps = [abs((date.fromisoformat(d) - s2_date).days) for d in nisar_dates]
    best = int(np.argmin(gaps))
    return nisar_dates[best], gaps[best]


def rule_maps(nisar_date: str, crops_dir: Path, coherence_dir: Path, pairs,
              threshold_db: float, coherence_threshold: float) -> dict:
    """HH (dB), coherence, and the result of both rules on one NISAR date, as map_water.py makes them."""
    crop = load_crop(crops_dir / f"{nisar_date}.npz")
    hh_db = reduce_speckle(to_decibels(crop.hh), config.SPECKLE_WINDOW)
    coherence, _ = coherence_for_date(nisar_date, pairs, coherence_dir)
    if coherence is None:
        raise SystemExit(f"No coherence for {nisar_date} in {coherence_dir}. Run scripts/check_coherence.py first.")
    detected, valid = classify_dark_unstable(hh_db, coherence, threshold_db, coherence_threshold)
    hh_dark, _ = classify_water(hh_db, threshold_db)
    return {"grid": crop.grid, "hh_db": hh_db, "coherence": coherence, "valid": valid,
            "result_hh_coherence": detected, "result_hh_only": hh_dark & valid}


def pixel_of(lon: float, lat: float, grid) -> tuple[int, int] | None:
    """(row, col) of the grid pixel containing a lon/lat point, or None if it is outside the grid."""
    to_map = Transformer.from_crs("EPSG:4326", f"EPSG:{grid.epsg}", always_xy=True)
    x, y = to_map.transform(lon, lat)
    col = int(round((x - grid.x[0]) / grid.resolution_m))
    row = int(round((grid.y[0] - y) / grid.resolution_m))   # y runs north to south
    if 0 <= row < grid.shape[0] and 0 <= col < grid.shape[1]:
        return row, col
    return None


def summarise_rule(rows: list[dict], key: str, title: str) -> list[str]:
    """Confusion matrix and scores for one rule, from the points that could be compared."""
    used = [r for r in rows if r[key] in ("water", "not_water")]
    count = lambda label, result: sum(r["label"] == label and r[key] == result for r in used)
    ratio = lambda a, b: f"{a / b:.1%} ({a}/{b})" if b else "n/a (no points)"

    true_water = count("water", "water")                                   # water called water
    missed_water = count("water", "not_water")                             # water called not water
    false_water = count("salt_crust", "water") + count("land", "water")    # dry called water
    correct = true_water + count("salt_crust", "not_water") + count("land", "not_water")
    crust_total = count("salt_crust", "water") + count("salt_crust", "not_water")
    land_total = count("land", "water") + count("land", "not_water")

    lines = [
        f"== {title} ==",
        "Confusion matrix (rows: Sentinel-2 label, columns: radar result)",
        f"{'':12}{'water':>10}{'not water':>11}",
    ]
    lines += [f"{label:12}{count(label, 'water'):>10}{count(label, 'not_water'):>11}" for label in LABELS]
    lines += [
        f"Overall accuracy (water vs not water): {ratio(correct, len(used))}",
        f"Water precision (radar 'water' that really is water): {ratio(true_water, true_water + false_water)}",
        f"Water recall (real water that radar found): {ratio(true_water, true_water + missed_water)}",
        f"Salt crust wrongly called water: {ratio(count('salt_crust', 'water'), crust_total)}",
        f"Land wrongly called water: {ratio(count('land', 'water'), land_total)}",
        "",
    ]
    return lines


def summarise(rows: list[dict], unlabelled: int, info: dict, max_days: int) -> str:
    """Plain-text summary: settings, skipped points, then the scores of each rule."""
    skipped = lambda reason: sum(r["result_hh_coherence"] == reason for r in rows)
    lines = [
        "Validation against Sentinel-2 labelled points",
        f"T = {info['threshold_db']} dB, C = {info['coherence_threshold']} (coherence from the 12-day pair starting on each date).",
        f"Nearest NISAR date within {max_days} days.",
        f"Points compared: {len(rows) - skipped('no_data') - skipped('too_far_in_time')} of {len(rows)} labelled "
        f"(skipped: {skipped('no_data')} no radar data, {skipped('too_far_in_time')} no NISAR date close enough; "
        f"{unlabelled} rows not labelled yet)",
        "",
    ]
    for key, title in RULES.items():
        lines += summarise_rule(rows, key, title)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("points", type=Path, help="CSV of labelled points (lon, lat, label, date)")
    parser.add_argument("--max-days", type=int, default=6,
                        help="skip points with no NISAR date this close (default 6, half the 12-day repeat)")
    parser.add_argument("--crops", type=Path, default=config.CROPS_DIR, help="cropped dates (default outputs/crops)")
    parser.add_argument("--coherence", type=Path, default=config.COHERENCE_DIR,
                        help="cropped coherence pairs (default outputs/coherence)")
    parser.add_argument("--results", type=Path, default=config.RESULTS_DIR,
                        help="folder with map_info.json; results are written here too (default outputs/results)")
    args = parser.parse_args()

    if not (args.results / "map_info.json").exists():
        raise SystemExit(f"No map_info.json in {args.results}. Run scripts/map_water.py first.")
    info = json.loads((args.results / "map_info.json").read_text())
    points, unlabelled = read_points(args.points)
    if not points:
        raise SystemExit(f"No labelled points in {args.points} ({unlabelled} rows without a label).")

    pairs = load_gunw_pairs()
    maps = {}   # NISAR date -> rule_maps(...), made only when a point needs that date
    rows = []
    for p in points:
        nisar_date, days = nearest_date(p["s2_date"], info["dates"])
        row = {"lon": p["lon"], "lat": p["lat"], "label": p["label"], "s2_date": p["s2_date"].isoformat(),
               "nisar_date": nisar_date, "days_apart": days, "hh_db": "", "coherence": "",
               "result_hh_coherence": "too_far_in_time", "result_hh_only": "too_far_in_time"}
        if days <= args.max_days:
            if nisar_date not in maps:
                maps[nisar_date] = rule_maps(nisar_date, args.crops, args.coherence, pairs,
                                             info["threshold_db"], info["coherence_threshold"])
            m = maps[nisar_date]
            pixel = pixel_of(p["lon"], p["lat"], m["grid"])
            if pixel is None or not m["valid"][pixel]:
                row["result_hh_coherence"] = row["result_hh_only"] = "no_data"
            else:
                row["hh_db"], row["coherence"] = round(float(m["hh_db"][pixel]), 2), round(float(m["coherence"][pixel]), 3)
                for key in RULES:
                    row[key] = "water" if m[key][pixel] else "not_water"
        rows.append(row)

    args.results.mkdir(parents=True, exist_ok=True)
    with open(args.results / "validation.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = summarise(rows, unlabelled, info, args.max_days)
    (args.results / "validation_summary.txt").write_text(summary + "\n")
    print(summary)
    print(f"\nWritten to {args.results / 'validation.csv'} and validation_summary.txt")


if __name__ == "__main__":
    main()
