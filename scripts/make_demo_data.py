"""Make FAKE demo data so the website can be built and tested before real results exist.

    *** FAKE DATA: every map and number produced here is synthetic. ***

For each NISAR date in data/granules.csv, a synthetic NISAR-like file is made
with tests/test_pipeline.py's make_fake_gcov, then painted with:
    - a lake that shrinks in the dry season and fills in the monsoon
    - salt pans (data/pans_example.geojson) that hold brine for part of the year
    - a ring of wet salt crust after the lake retreats (dark enough to fool the classifier)
    - one date with the eastern part missing, so valid-observation counts differ
Each file then goes through the real pipeline: crop_lake.py --local, then map_water.py.

Everything is written to outputs/demo/ (never outputs/crops or outputs/results),
so it cannot mix with real NISAR results.

Run:   python scripts/make_demo_data.py
Then:  python scripts/export_web.py --results outputs/demo/results --pans data/pans_example.geojson
"""
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
from sambhar.granules import load_granules
from sambhar.grid import Grid, make_grid
from sambhar.pans import pans_mask
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
GAP_DATE = "2026-02-16"                 # this date "misses" the east of the scene

WATER_POWER = 0.003       # about -25 dB, like calm water
WET_CRUST_POWER = 0.012   # about -19 dB, just below the -18 dB threshold


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


def paint(image: np.ndarray, where: np.ndarray, mean_power: float, rng) -> None:
    """Replace pixels with speckled values around `mean_power` (same noise as make_fake_gcov)."""
    image[where] = rng.gamma(4, mean_power / 4, int(where.sum()))


def make_fake_date(path: Path, date: str, distance: np.ndarray, pans: np.ndarray, rng) -> None:
    """Write a fake NISAR file for one date, with lake, pans and wet crust for that month."""
    month = int(date[5:7])
    lake_edge = LAKE_SIZE_BY_MONTH[month] ** 2   # distance is squared, so square the size too

    make_fake_gcov(path, with_lake=False)
    with h5py.File(path, "r+") as h5:
        images = h5["science/LSAR/GCOV/grids/frequencyA"]
        hh = images["HHHH"][:]
        if month in WET_CRUST_MONTHS:
            paint(hh, (distance >= lake_edge) & (distance < lake_edge * 1.3), WET_CRUST_POWER, rng)
        paint(hh, distance < lake_edge, WATER_POWER, rng)
        if month in PANS_HOLD_BRINE_MONTHS:
            paint(hh, pans, WATER_POWER, rng)
        if date == GAP_DATE:
            hh[:, -hh.shape[1] // 4:] = 0   # zero becomes "no data" in to_decibels
        images["HHHH"][...] = hh
        images["HVHV"][...] = hh * 0.2


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

    sys.argv = ["map_water.py"]   # default threshold from config.py
    map_water.main()

    mark_as_fake(config.RESULTS_DIR / "map_info.json")
    (DEMO_DIR / "README.txt").write_text(
        "FAKE DEMO DATA. Made by scripts/make_demo_data.py to test the website.\n"
        "Nothing in this folder comes from NISAR. Do not use it for results.\n")
    print(f"\nFAKE demo data written to {DEMO_DIR}")


if __name__ == "__main__":
    main()
