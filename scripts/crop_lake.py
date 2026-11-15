"""Step 1: cut Sambhar Salt Lake out of each NISAR file.

Streams only the needed pixels (no full ~6 GB download) and saves one file
per date to outputs/crops/, plus a quick-look image for checking.

Examples
    python scripts/crop_lake.py 2026-05-11 --show-structure   # first run: inspect the file
    python scripts/crop_lake.py 2026-05-11 2026-08-15
    python scripts/crop_lake.py all
    python scripts/crop_lake.py 2026-05-11 --local path/to/file.h5
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make `sambhar` importable

import h5py
import numpy as np

from sambhar import config, nisar
from sambhar.granules import Granule, load_granules, open_remote
from sambhar.grid import make_grid, sample_onto_grid
from sambhar.plots import quicklook
from sambhar.storage import Crop, save_crop
from sambhar.water import to_decibels


def crop_granule(h5: h5py.File, granule: Granule, show_structure: bool = False) -> Crop:
    """Extract HH and HV over Sambhar from an open NISAR file."""
    if show_structure:
        nisar.print_structure(h5)

    images = nisar.backscatter_group(h5)
    print(f"[{granule.date}] {nisar.describe(images)}")

    grid = make_grid(config.SAMBHAR_BBOX, nisar.epsg_code(images), config.GRID_RESOLUTION_M)
    x, y = images["xCoordinates"][:], images["yCoordinates"][:]
    hh = sample_onto_grid(images["HHHH"], x, y, grid)
    hv = sample_onto_grid(images["HVHV"], x, y, grid)

    # Pixels the file itself flags as invalid count as "no observation".
    mask = sample_onto_grid(images["mask"], x, y, grid)
    invalid = np.isin(mask, config.INVALID_MASK_VALUES)
    hh[invalid] = np.nan
    hv[invalid] = np.nan
    return Crop(granule.date, granule.mode, granule.release, hh, hv, grid)


def process(granule: Granule, local_file: str | None, show_structure: bool) -> None:
    out_file = config.CROPS_DIR / f"{granule.date}.npz"
    if out_file.exists() and not show_structure:
        print(f"[{granule.date}] already cropped, skipping")
        return

    with (h5py.File(local_file, "r") if local_file else open_remote(granule.url)) as h5:
        crop = crop_granule(h5, granule, show_structure)

    save_crop(crop, config.CROPS_DIR)
    quicklook(to_decibels(crop.hh), to_decibels(crop.hv),
              f"{crop.date} [{crop.mode}]", config.CROPS_DIR / f"{crop.date}.png")
    print(f"[{granule.date}] saved {out_file.name} and quick-look image")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dates", nargs="+", help="dates (YYYY-MM-DD) or 'all'")
    parser.add_argument("--show-structure", action="store_true", help="print the HDF5 file layout")
    parser.add_argument("--local", help="use an already-downloaded .h5 file (one date only)")
    args = parser.parse_args()

    granules = {g.date: g for g in load_granules()}
    wanted = list(granules) if args.dates == ["all"] else args.dates

    for date in wanted:
        if date not in granules:
            print(f"[{date}] not in data/granules.csv, skipping")
            continue
        try:
            process(granules[date], args.local, args.show_structure)
        except Exception as error:  # keep going with the other dates
            print(f"[{date}] FAILED: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
