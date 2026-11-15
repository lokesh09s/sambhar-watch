"""Step 3: check our maps against points labelled on Sentinel-2 images.

Input: one or more CSV files, or folders of them (e.g. validation_data/labels/, files
labels_<date>_<name>.csv), with columns id, lon, lat, date, label (extra columns are ignored).
    label  water, white_uncertain, salt_crust or land, as seen on a cloud-free Sentinel-2 image.
           Rows with an empty label are skipped and counted.
    date   the Sentinel-2 image date, YYYY-MM-DD
See data/validation_points_TEMPLATE.csv.

Each point is compared with the NISAR date closest to its date among the cropped dates
(e.g. 2026-08-29 -> 2026-08-27), made exactly as map_water.py does: T and C from
map_info.json, coherence from that date's single 12-day pair (forward, else backward).
Two rules are tested:
    HH + coherence   HH < T AND coherence < C   (the current rule)
    HH only          HH < T, on the same pixels (for comparison)
Each point is also placed inside the lake outline (data/lake.geojson) or in the buffer around it.
Points with no NISAR date within --max-days are skipped.

Scores: accuracy, precision and recall compare water against the dry labels (salt_crust, land).
white_uncertain is left out of them and reported on its own: how often radar called it water.

Writes to outputs/results/:
    validation.csv           one row per labelled point, with both rules' results
    validation_summary.csv   one row per date x zone x rule (and for all dates), with the scores
    validation_summary.txt   the same as a readable table, plus a confusion matrix per rule

Examples
    python scripts/validate.py validation_data/labels/
    python scripts/validate.py validation_data/labels/labels_2026-05-11_asha.csv --max-days 3
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
from sambhar.pans import pans_mask
from sambhar.storage import load_crop
from sambhar.water import classify_dark_unstable, classify_water, reduce_speckle, to_decibels

LABELS = ["water", "white_uncertain", "salt_crust", "land"]
DRY_LABELS = ["salt_crust", "land"]
RULES = {"result_hh_coherence": "HH + coherence", "result_hh_only": "HH only"}
ZONES = ["inside lake", "buffer"]


def label_files(paths: list[Path]) -> list[Path]:
    """The CSV files to read: each folder contributes all its *.csv files."""
    files = []
    for path in paths:
        files += sorted(path.glob("*.csv")) if path.is_dir() else [path]
    if not files:
        raise SystemExit(f"No CSV files found in {', '.join(map(str, paths))}.")
    return files


def read_points(path: Path) -> tuple[list[dict], int]:
    """Read one labels file. Returns (labelled points, number of rows with an empty label).

    Stops with a clear message on an unknown label or a bad number or date.
    """
    parts = path.stem.split("_", 2)   # labels_<date>_<name> -> name; any other file name is used as it is
    labeller = parts[2] if parts[0] == "labels" and len(parts) == 3 else path.stem
    points, unlabelled = [], 0
    with open(path, newline="") as f:
        for line_number, row in enumerate(csv.DictReader(f), start=2):
            label = (row.get("label") or "").strip().lower()
            if not label:
                unlabelled += 1
                continue
            if label not in LABELS:
                raise SystemExit(f"{path}, line {line_number}: label '{label}' is not one of {LABELS}")
            try:
                points.append({"file": path.name, "labeller": labeller, "id": row.get("id", ""),
                               "lon": float(row["lon"]), "lat": float(row["lat"]), "label": label,
                               "s2_date": date.fromisoformat(row["date"].strip())})
            except (ValueError, KeyError) as error:
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
    coherence, pair, direction = coherence_for_date(nisar_date, pairs, coherence_dir)
    if coherence is None:
        raise SystemExit(f"No 12-day coherence pair for {nisar_date} in {coherence_dir}.")
    detected, valid = classify_dark_unstable(hh_db, coherence, threshold_db, coherence_threshold)
    hh_dark, _ = classify_water(hh_db, threshold_db)
    return {"grid": crop.grid, "mode": crop.mode, "hh_db": hh_db, "coherence": coherence, "valid": valid,
            "pair": f"{pair.reference_date} to {pair.secondary_date} ({direction})",
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


def scores(rows: list[dict], key: str) -> dict:
    """Counts (hits, total) for each score of one rule, from the rows that could be compared."""
    used = [r for r in rows if r[key] in ("water", "not_water")]
    called_water = lambda labels: sum(r["label"] in labels and r[key] == "water" for r in used)
    total = lambda labels: sum(r["label"] in labels for r in used)
    true_water = called_water(["water"])
    dry_called_water = called_water(DRY_LABELS)
    correct = true_water + total(DRY_LABELS) - dry_called_water
    return {
        "points": len(used),
        "accuracy": (correct, total(["water"] + DRY_LABELS)),
        "water_precision": (true_water, true_water + dry_called_water),
        "water_recall": (true_water, total(["water"])),
        "salt_crust_called_water": (called_water(["salt_crust"]), total(["salt_crust"])),
        "white_uncertain_called_water": (called_water(["white_uncertain"]), total(["white_uncertain"])),
        "land_called_water": (called_water(["land"]), total(["land"])),
    }


def percent(hits: int, total: int) -> str:
    return f"{hits / total:.0%} ({hits}/{total})" if total else "-"


def summary_rows(rows: list[dict]) -> list[dict]:
    """One row per date x zone x rule, plus 'all dates' and 'both zones', with the score counts."""
    dates = sorted({r["nisar_date"] for r in rows})
    out = []
    for when in dates + ["all dates"]:
        for zone in ZONES + ["both zones"]:
            chosen = [r for r in rows if (when == "all dates" or r["nisar_date"] == when)
                      and (zone == "both zones" or r["zone"] == zone)]
            if not chosen:
                continue
            for key, rule in RULES.items():
                out.append({"nisar_date": when, "zone": zone, "rule": rule, **scores(chosen, key)})
    return out


def summary_text(rows: list[dict], table: list[dict], skipped: dict, info: dict, max_days: int) -> str:
    """Readable summary: settings, what was skipped, the score table, and a confusion matrix per rule."""
    columns = ["accuracy", "water_precision", "water_recall", "salt_crust_called_water",
               "white_uncertain_called_water", "land_called_water"]
    headers = ["accuracy", "precision", "recall", "crust->water", "white->water", "land->water"]
    lines = [
        "Validation against Sentinel-2 labelled points",
        f"T = {info['threshold_db']} dB, C = {info['coherence_threshold']}; coherence from each date's 12-day pair; "
        f"nearest NISAR date within {max_days} days.",
        "Accuracy / precision / recall: water vs dry (salt_crust + land); white_uncertain is reported on its own.",
        f"Labelled points used: {len(rows)}. Skipped: {skipped['unlabelled']} empty labels, "
        f"{skipped['too_far']} with no NISAR date close enough, {skipped['no_data']} with no radar data.",
        "Dates: " + "; ".join(f"{d} -> NISAR {r['nisar_date']} {r['mode']}, pair {r['pair']}"
                              for d, r in sorted({r['s2_date']: r for r in rows}.items())),
        "",
        f"{'NISAR date':<12}{'zone':<13}{'rule':<16}{'points':>7}" + "".join(f"{h:>16}" for h in headers),
    ]
    for t in table:
        lines.append(f"{t['nisar_date']:<12}{t['zone']:<13}{t['rule']:<16}{t['points']:>7}" +
                     "".join(f"{percent(*t[c]):>16}" for c in columns))
    for key, rule in RULES.items():
        lines += ["", f"Confusion matrix, {rule}, all dates and zones (rows: Sentinel-2 label, columns: radar)",
                  f"{'':18}{'water':>8}{'not water':>11}"]
        lines += [f"{label:18}{sum(r['label'] == label and r[key] == 'water' for r in rows):>8}"
                  f"{sum(r['label'] == label and r[key] == 'not_water' for r in rows):>11}" for label in LABELS]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("labels", type=Path, nargs="+", help="labels CSV files or folders of them")
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
    nisar_dates = sorted(p.stem for p in args.crops.glob("*.npz"))
    if not nisar_dates:
        raise SystemExit(f"No cropped dates in {args.crops}. Run scripts/crop_lake.py first.")

    points, skipped = [], {"unlabelled": 0, "too_far": 0, "no_data": 0}
    for path in label_files(args.labels):
        found, unlabelled = read_points(path)
        points += found
        skipped["unlabelled"] += unlabelled
        print(f"{path.name}: {len(found)} labelled, {unlabelled} empty")
    if not points:
        raise SystemExit("No labelled points yet (all labels empty).")

    pairs = load_gunw_pairs()
    maps, in_lake = {}, None   # maps: NISAR date -> rule_maps(...), made only when a point needs that date
    rows = []
    for p in points:
        nisar_date, days = nearest_date(p["s2_date"], nisar_dates)
        if days > args.max_days:
            skipped["too_far"] += 1
            continue
        if nisar_date not in maps:
            maps[nisar_date] = rule_maps(nisar_date, args.crops, args.coherence, pairs,
                                         info["threshold_db"], info["coherence_threshold"])
        m = maps[nisar_date]
        if in_lake is None:   # every date is on the same grid
            in_lake = (pans_mask(config.LAKE_GEOJSON, m["grid"]) if config.LAKE_GEOJSON.exists()
                       else np.ones(m["grid"].shape, dtype=bool))
        pixel = pixel_of(p["lon"], p["lat"], m["grid"])
        if pixel is None or not m["valid"][pixel]:
            skipped["no_data"] += 1
            continue
        rows.append({
            "file": p["file"], "labeller": p["labeller"], "id": p["id"], "lon": p["lon"], "lat": p["lat"],
            "label": p["label"], "s2_date": p["s2_date"].isoformat(), "nisar_date": nisar_date, "mode": m["mode"],
            "pair": m["pair"], "days_apart": days, "zone": ZONES[0] if in_lake[pixel] else ZONES[1],
            "hh_db": round(float(m["hh_db"][pixel]), 2), "coherence": round(float(m["coherence"][pixel]), 3),
            **{key: "water" if m[key][pixel] else "not_water" for key in RULES},
        })
    if not rows:
        raise SystemExit(f"No point could be compared (skipped: {skipped}).")

    table = summary_rows(rows)
    args.results.mkdir(parents=True, exist_ok=True)
    with open(args.results / "validation.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with open(args.results / "validation_summary.csv", "w", newline="") as f:
        writer = csv.writer(f)
        score_names = [k for k in table[0] if k not in ("nisar_date", "zone", "rule", "points")]
        writer.writerow(["nisar_date", "zone", "rule", "points"] +
                        [f"{name}_{part}" for name in score_names for part in ("hits", "total")])
        for t in table:
            writer.writerow([t["nisar_date"], t["zone"], t["rule"], t["points"]] +
                            [count for name in score_names for count in t[name]])

    text = summary_text(rows, table, skipped, info, args.max_days)
    (args.results / "validation_summary.txt").write_text(text + "\n")
    print("\n" + text)
    print(f"\nWritten to {args.results}: validation.csv, validation_summary.csv, validation_summary.txt")


if __name__ == "__main__":
    main()
