"""Make FAKE demo data so the website can be built and tested before real results exist.

    *** FAKE DATA: every map and number produced here is synthetic. ***

For each NISAR date in data/granules.csv, a synthetic NISAR-like file is made
with tests/test_pipeline.py's make_fake_gcov, then painted with:
    - a lake that shrinks in the dry season and fills in the monsoon
    - salt pans (data/pans_example.geojson) that hold brine for part of the year
    - a ring of wet salt crust after the lake retreats (dark and unstable, like water)
    - smooth dry crust on the exposed lake bed in Mar-Jun (dark like water, but stable)
    - one date with the eastern part missing, so valid-observation counts differ
Each file then goes through the real pipeline: crop_lake.py --local, then map_water.py
(HH only). Fake 12-day coherence is then made for each pair in data/gunw_pairs.csv,
and the provisional rule "HH < T AND coherence < C" is applied.

Output, in the format the website expects (see web/README.md):
    outputs/demo/crops/             cropped dates, from crop_lake.py
    outputs/demo/coherence/         fake coherence per pair, same format as outputs/coherence/
    outputs/demo/results/           overlays/ (HH + coherence), overlays_hh_only/ (from map_water.py),
                                    water_area.csv (with coherence_pairs), frequency, map_info.json

Everything is written to outputs/demo/ (never outputs/crops or outputs/results),
so it cannot mix with real NISAR results.

Run:   python scripts/make_demo_data.py
Then:  python scripts/export_web.py --results outputs/demo/results --pans data/pans_example.geojson
"""
import csv
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # make `sambhar`, `scripts` and `tests` importable

import h5py
import numpy as np
from pyproj import Transformer

from sambhar import config
from sambhar.granules import load_granules, load_gunw_pairs
from sambhar.grid import Grid, make_grid
from sambhar.pans import pans_mask
from sambhar.plots import frequency_map, water_overlay
from sambhar.storage import load_crop
from sambhar.water import classify_water, detection_frequency, reduce_speckle, to_decibels
from scripts import crop_lake, map_water
from tests.test_pipeline import EPSG, make_fake_gcov

DEMO_DIR = ROOT / "outputs" / "demo"
DEMO_PANS = config.DATA_DIR / "pans_example.geojson"

# Lake size per month, as a fraction of the full 9 km x 4 km ellipse:
# lowest before the monsoon (May-June), highest just after it (September).
LAKE_SIZE_BY_MONTH = {1: 0.75, 2: 0.65, 3: 0.55, 4: 0.45, 5: 0.35, 6: 0.3,
                      7: 0.6, 8: 0.95, 9: 1.1, 10: 1.0, 11: 0.9, 12: 0.8}
PANS_HOLD_BRINE_MONTHS = {11, 12, 1, 2, 3, 4, 5, 6}
WET_CRUST_MONTHS = {10, 11, 12, 1}      # freshly exposed lake bed is still wet
SMOOTH_CRUST_MONTHS = {3, 4, 5, 6}      # exposed lake bed has dried into smooth crust
GAP_DATE = "2026-02-16"                 # this date "misses" the east of the scene

WATER_POWER = 0.003         # about -25 dB, like calm water
WET_CRUST_POWER = 0.012     # about -19 dB, just below the -18 dB threshold
SMOOTH_CRUST_POWER = 0.008  # about -21 dB: HH alone calls it water

DEMO_COHERENCE_THRESHOLD = 0.35   # demo value only; the real C is chosen by the processing terminal


def lake_distance(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Squared normalised distance from the lake centre: below 1 inside the full-size lake."""
    to_map = Transformer.from_crs("EPSG:4326", f"EPSG:{EPSG}", always_xy=True)
    cx, cy = to_map.transform(75.08, 26.95)
    return (((x[None, :] - cx) / 9000) ** 2 + ((y[:, None] - cy) / 4000) ** 2).astype(np.float32)


def pans_in_fake_file(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """True where a pixel of the fake file lies inside the example salt pans.

    Only the study-area window is tested, to keep memory use small.
    """
    study = make_grid(config.SAMBHAR_BBOX, EPSG, config.GRID_RESOLUTION_M)
    cols = (x >= study.x.min()) & (x <= study.x.max())
    rows = (y >= study.y.min()) & (y <= study.y.max())
    window = Grid(x=x[cols], y=y[rows], epsg=EPSG, resolution_m=abs(x[1] - x[0]))
    mask = np.zeros((y.size, x.size), dtype=bool)
    mask[np.ix_(rows, cols)] = pans_mask(DEMO_PANS, window)
    return mask


def surfaces(date: str, distance: np.ndarray, pans: np.ndarray) -> dict:
    """Where each fake surface type is on a given date (boolean maps on the same grid as `distance`)."""
    month = int(date[5:7])
    lake_edge = LAKE_SIZE_BY_MONTH[month] ** 2   # distance is squared, so square the size too
    lake = distance < lake_edge
    exposed_bed = ~lake & (distance < 1)
    nothing = np.zeros_like(lake)
    return {
        "water": lake,
        "brine_pans": pans if month in PANS_HOLD_BRINE_MONTHS else nothing,
        "wet_crust": (~lake & (distance < lake_edge * 1.3)) if month in WET_CRUST_MONTHS else nothing,
        "smooth_crust": exposed_bed if month in SMOOTH_CRUST_MONTHS else nothing,
    }


def unstable(found: dict) -> np.ndarray:
    """Surfaces that change between passes (low coherence): water, brine and wet crust."""
    return found["water"] | found["brine_pans"] | found["wet_crust"]


def paint(image: np.ndarray, where: np.ndarray, mean_power: float, rng) -> None:
    """Replace pixels with speckled values around `mean_power` (same noise as make_fake_gcov)."""
    image[where] = rng.gamma(4, mean_power / 4, int(where.sum()))


def make_fake_date(path: Path, date: str, distance: np.ndarray, pans: np.ndarray, rng) -> None:
    """Write a fake NISAR file for one date, with the surfaces for that month."""
    found = surfaces(date, distance, pans)
    make_fake_gcov(path, with_lake=False)
    with h5py.File(path, "r+") as h5:
        images = h5["science/LSAR/GCOV/grids/frequencyA"]
        hh = images["HHHH"][:]
        paint(hh, found["smooth_crust"], SMOOTH_CRUST_POWER, rng)
        paint(hh, found["wet_crust"], WET_CRUST_POWER, rng)
        paint(hh, found["water"] | found["brine_pans"], WATER_POWER, rng)
        if date == GAP_DATE:
            hh[:, -hh.shape[1] // 4:] = 0   # zero becomes "no data" in to_decibels
        images["HHHH"][...] = hh
        images["HVHV"][...] = hh * 0.2


def make_fake_coherence(pair, rng) -> None:
    """Fake 12-day coherence for one pair: low where either date has an unstable surface, high elsewhere."""
    first = load_crop(config.CROPS_DIR / f"{pair.reference_date}.npz")
    second = load_crop(config.CROPS_DIR / f"{pair.secondary_date}.npz")
    grid = first.grid
    distance, pans = lake_distance(grid.x, grid.y), pans_mask(DEMO_PANS, grid)
    changing = unstable(surfaces(pair.reference_date, distance, pans)) | \
        unstable(surfaces(pair.secondary_date, distance, pans))

    coherence = np.where(changing, rng.normal(0.15, 0.06, grid.shape), rng.normal(0.7, 0.1, grid.shape))
    coherence = np.clip(coherence, 0, 1).astype(np.float32)
    coherence[~(np.isfinite(first.hh) & np.isfinite(second.hh) & (first.hh > 0) & (second.hh > 0))] = np.nan
    np.savez_compressed(config.COHERENCE_DIR / f"{pair.reference_date}_{pair.secondary_date}.npz",
                        coherence=coherence)


def coherence_for_date(date: str, pairs) -> tuple[np.ndarray | None, int]:
    """Mean coherence of all 12-day pairs that include this date, and how many pairs there were.

    Demo choice: with two pairs (before and after) the two are averaged.
    """
    files = [config.COHERENCE_DIR / f"{p.reference_date}_{p.secondary_date}.npz"
             for p in pairs if date in (p.reference_date, p.secondary_date)]
    if not files:
        return None, 0
    stack = np.array([np.load(f)["coherence"] for f in files])
    n = np.isfinite(stack).sum(axis=0)
    return np.where(n > 0, np.nansum(stack, axis=0) / np.maximum(n, 1), np.nan), len(files)


def apply_coherence_rule(pairs) -> None:
    """Re-make the results with the provisional rule: HH < T AND coherence < C.

    map_water.py's HH-only overlays are kept in overlays_hh_only/ for the comparison layer.
    Dates with no coherence pair cannot use the rule and are left out.
    """
    # shortcut: repeats map_water.py's loop because map_water.py has no coherence rule yet;
    # call map_water.py instead once it does.
    out = config.RESULTS_DIR
    (out / "overlays").rename(out / "overlays_hh_only")
    (out / "overlays").mkdir()
    with open(out / "water_area.csv", newline="") as f:
        hh_only_rows = list(csv.DictReader(f))

    in_pans = None
    rows, water_stack, valid_stack = [], [], []
    for row in hh_only_rows:
        coherence, n_pairs = coherence_for_date(row["date"], pairs)
        if coherence is None:
            print(f"[{row['date']}] no coherence pair, left out")
            continue
        crop = load_crop(config.CROPS_DIR / f"{row['date']}.npz")
        if in_pans is None:
            in_pans = pans_mask(config.PANS_GEOJSON, crop.grid)
        hh_db = reduce_speckle(to_decibels(crop.hh), config.SPECKLE_WINDOW)
        dark, valid = classify_water(hh_db, float(row["threshold_db"]))
        valid &= np.isfinite(coherence)
        water = dark & valid & (coherence < DEMO_COHERENCE_THRESHOLD)
        water_stack.append(water)
        valid_stack.append(valid)
        water_overlay(water, out / "overlays" / f"{row['date']}.png")

        km2 = lambda mask: round(float(mask.sum()) * crop.grid.pixel_area_km2, 3)
        rows.append({**row, "valid_area_km2": km2(valid), "water_km2": km2(water),
                     "water_inside_mapped_pans_km2": km2(water & in_pans),
                     "water_outside_mapped_pans_km2": km2(water & ~in_pans),
                     "coherence_pairs": n_pairs})
        print(f"[{row['date']}] HH only {row['water_km2']} km2 -> HH + coherence {rows[-1]['water_km2']} km2"
              f" ({n_pairs} pair{'s' if n_pairs > 1 else ''})")

    with open(out / "water_area.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for old in (out / "overlays_hh_only").glob("*.png"):   # keep both overlay folders on the same dates
        if not (out / "overlays" / old.name).exists():
            old.unlink()

    frequency, n_valid = detection_frequency(np.array(water_stack), np.array(valid_stack))
    frequency_map(frequency, n_valid, out / "frequency.png")
    np.savez_compressed(out / "frequency.npz", frequency=frequency, n_valid=n_valid)

    info = json.loads((out / "map_info.json").read_text())
    info["dates"] = [r["date"] for r in rows]
    info["coherence_threshold"] = DEMO_COHERENCE_THRESHOLD
    (out / "map_info.json").write_text(json.dumps(info, indent=2))


def mark_as_fake(map_info_path: Path) -> None:
    """Add a 'demo' flag to map_info.json so the website shows a FAKE DATA banner."""
    info = json.loads(map_info_path.read_text())
    info["demo"] = True
    info["note"] = "FAKE demo data made by scripts/make_demo_data.py. Not NISAR results."
    map_info_path.write_text(json.dumps(info, indent=2))


def main():
    if DEMO_DIR.exists():
        shutil.rmtree(DEMO_DIR)   # only ever our own demo folder

    # Point the real pipeline at the demo folders and the example pans.
    config.CROPS_DIR = DEMO_DIR / "crops"
    config.RESULTS_DIR = DEMO_DIR / "results"
    config.COHERENCE_DIR = DEMO_DIR / "coherence"
    config.PANS_GEOJSON = DEMO_PANS

    granules = [g for g in load_granules() if g.release == "provisional"]
    rng = np.random.default_rng(1)

    with tempfile.TemporaryDirectory() as tmp:
        fake_file = Path(tmp) / "fake_gcov.h5"
        make_fake_gcov(fake_file, with_lake=False)
        with h5py.File(fake_file) as h5:
            images = h5["science/LSAR/GCOV/grids/frequencyA"]
            x, y = images["xCoordinates"][:], images["yCoordinates"][:]
        distance, pans = lake_distance(x, y), pans_in_fake_file(x, y)

        for granule in granules:
            make_fake_date(fake_file, granule.date, distance, pans, rng)
            crop_lake.process(granule, str(fake_file), show_structure=False)  # same as --local

    sys.argv = ["map_water.py"]   # HH only, default threshold from config.py
    map_water.main()

    pairs = load_gunw_pairs()
    config.COHERENCE_DIR.mkdir(parents=True)
    for pair in pairs:
        make_fake_coherence(pair, rng)
    apply_coherence_rule(pairs)

    mark_as_fake(config.RESULTS_DIR / "map_info.json")
    (DEMO_DIR / "README.txt").write_text(
        "FAKE DEMO DATA. Made by scripts/make_demo_data.py to test the website.\n"
        "Nothing in this folder comes from NISAR. Do not use it for results.\n")
    print(f"\nFAKE demo data written to {DEMO_DIR}")


if __name__ == "__main__":
    main()
