"""Copy pipeline results into web/data/ so the static website can show them.

Reads outputs/results/ (made by map_water.py) and writes to web/data/:
    water_area.csv, map_info.json, frequency.png, overlays/<date>.png   copied as they are
    rule_comparison.png      copied if present (HH only vs HH + coherence, per date)
    sensitivity_<mode>.csv   copied if present (area per date for each threshold pair, from sensitivity.py)
    frequency_overlay.png    water-detection frequency as a transparent map layer
    frequency_lookup.json    frequency and valid-observation count on a coarse grid, for map clicks
    comparison/<date>.png    pixels dark in HH but removed by the coherence rule
                             (only if results has overlays_hh_only/)
    pans.geojson, lake.geojson   salt-pan and lake outlines (only if the files exist)
    optical/<s2_date>.jpg    Sentinel-2 true colour from validation_data/sentinel2/ (same 20 m grid as the radar)
    optical/index.json       each optical date with its nearest radar date (none if more than 6 days apart)

Examples
    python scripts/export_web.py
    python scripts/export_web.py --results outputs/demo/results   # FAKE demo
"""
import argparse
import json
import math
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # make `sambhar` importable

import matplotlib
matplotlib.use("Agg")  # draw to files, no window needed
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from sambhar import config

WEB_DATA = ROOT / "web" / "data"
LOOKUP_MAX_SIZE = 400   # longest side of the click-lookup grid; keeps the JSON around 1 MB
OPTICAL_DIR = ROOT / "validation_data" / "sentinel2"
OPTICAL_MAX_DAYS = 6    # same as validate.py: half the 12-day repeat
COMPARISON_RGBA = (240, 140, 0, 220)   # orange, matches .swatch-stable in web/style.css


def frequency_overlay(frequency: np.ndarray, path: Path) -> None:
    """Transparent PNG: blue, darker where water was detected more often.

    Pixels never detected as water, or with no data, are fully transparent.
    Colours run from 30% to 100% of matplotlib's "Blues", matching the legend in web/style.css.
    """
    f = np.nan_to_num(frequency)
    rgba = plt.get_cmap("Blues")(0.3 + 0.7 * f, bytes=True)
    rgba[..., 3] = np.where(f > 0, 220, 0)
    plt.imsave(path, rgba)


def comparison_overlay(hh_only_png: Path, final_png: Path, path: Path) -> None:
    """Transparent PNG: orange where HH alone says "dark" but HH + coherence does not (dark but stable)."""
    dark = plt.imread(hh_only_png)[..., 3] > 0
    kept = plt.imread(final_png)[..., 3] > 0
    image = np.zeros(dark.shape + (4,), dtype=np.uint8)
    image[dark & ~kept] = COMPARISON_RGBA
    plt.imsave(path, image)


def frequency_lookup(frequency: np.ndarray, n_valid: np.ndarray) -> dict:
    """Every `step`-th pixel of the frequency map, small enough for the browser to load.

    frequency_pct is a whole-number percentage, or -1 where there was no valid observation.
    """
    step = max(1, math.ceil(max(frequency.shape) / LOOKUP_MAX_SIZE))
    start = step // 2
    f = frequency[start::step, start::step]
    n = n_valid[start::step, start::step]
    return {
        "step": step,
        "full_rows": frequency.shape[0], "full_cols": frequency.shape[1],
        "rows": f.shape[0], "cols": f.shape[1],
        "frequency_pct": np.where(np.isfinite(f), np.rint(f * 100), -1).astype(int).ravel().tolist(),
        "n_valid": n.astype(int).ravel().tolist(),
    }


def copy_outline(source: Path, name: str) -> None:
    """Copy a hand-drawn outline to web/data/<name>, or remove an old copy if the file does not exist."""
    target = WEB_DATA / name
    if source.exists():
        shutil.copy(source, target)
    else:
        target.unlink(missing_ok=True)
        print(f"Note: {source} not found, so the map has no {name} layer.")


def export_optical(radar_dates: list[str]) -> None:
    """Sentinel-2 true-colour images as JPEGs, each paired with the nearest radar date.

    The PNGs from fetch_sentinel2.py are on the same 20 m grid as the radar crops,
    so the website can lay radar overlays on them pixel for pixel.
    """
    shutil.rmtree(WEB_DATA / "optical", ignore_errors=True)
    images = sorted(OPTICAL_DIR.glob("*_truecolour.png"))
    if not images:
        print(f"Note: no Sentinel-2 images in {OPTICAL_DIR}, so the page has no optical comparison.")
        return
    (WEB_DATA / "optical").mkdir()
    entries = []
    for png in images:
        s2_date = png.name[:10]
        Image.open(png).convert("RGB").save(WEB_DATA / "optical" / f"{s2_date}.jpg", quality=80)
        gaps = {d: abs((date.fromisoformat(d) - date.fromisoformat(s2_date)).days) for d in radar_dates}
        nearest = min(gaps, key=gaps.get)
        close = gaps[nearest] <= OPTICAL_MAX_DAYS
        entries.append({"s2_date": s2_date, "nisar_date": nearest if close else None,
                        "days_apart": gaps[nearest] if close else None})
    (WEB_DATA / "optical" / "index.json").write_text(json.dumps(entries, indent=1))
    print(f"Optical: {', '.join(e['s2_date'] + ' -> ' + str(e['nisar_date']) for e in entries)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", type=Path, default=config.RESULTS_DIR,
                        help="folder written by map_water.py (default outputs/results)")
    parser.add_argument("--pans", type=Path, default=config.PANS_GEOJSON,
                        help="salt-pan polygons to show on the map (default data/pans.geojson)")
    parser.add_argument("--lake", type=Path, default=config.LAKE_GEOJSON,
                        help="lake outline to show on the map (default data/lake.geojson)")
    args = parser.parse_args()

    results = args.results
    if not (results / "map_info.json").exists():
        raise SystemExit(f"No map_info.json in {results}. Run scripts/map_water.py first.")

    WEB_DATA.mkdir(parents=True, exist_ok=True)
    for name in ["water_area.csv", "map_info.json", "frequency.png"]:
        shutil.copy(results / name, WEB_DATA / name)
    for old in WEB_DATA.glob("sensitivity_*.csv"):
        old.unlink()
    for table in results.glob("sensitivity_*.csv"):
        shutil.copy(table, WEB_DATA / table.name)
    (WEB_DATA / "rule_comparison.png").unlink(missing_ok=True)
    if (results / "rule_comparison.png").exists():
        shutil.copy(results / "rule_comparison.png", WEB_DATA / "rule_comparison.png")

    shutil.rmtree(WEB_DATA / "overlays", ignore_errors=True)   # drop dates from earlier exports
    shutil.copytree(results / "overlays", WEB_DATA / "overlays")

    shutil.rmtree(WEB_DATA / "comparison", ignore_errors=True)
    if (results / "overlays_hh_only").exists():
        (WEB_DATA / "comparison").mkdir()
        for final_png in sorted((results / "overlays").glob("*.png")):
            comparison_overlay(results / "overlays_hh_only" / final_png.name, final_png,
                               WEB_DATA / "comparison" / final_png.name)
    else:
        print("Note: no overlays_hh_only/ in results, so the map has no HH-only comparison layer.")

    saved = np.load(results / "frequency.npz")
    frequency_overlay(saved["frequency"], WEB_DATA / "frequency_overlay.png")
    with open(WEB_DATA / "frequency_lookup.json", "w") as f:
        json.dump(frequency_lookup(saved["frequency"], saved["n_valid"]), f, separators=(",", ":"))

    copy_outline(args.pans, "pans.geojson")
    copy_outline(args.lake, "lake.geojson")

    info = json.loads((results / "map_info.json").read_text())
    export_optical(info["dates"])
    label = "FAKE DEMO data" if info.get("demo") else "results"
    print(f"Exported {label} for {len(info['dates'])} dates from {results} to {WEB_DATA}")


if __name__ == "__main__":
    main()
