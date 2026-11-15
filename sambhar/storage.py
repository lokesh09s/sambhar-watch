"""Saving and loading cropped images (one .npz file per date)."""
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from sambhar.grid import Grid


@dataclass
class Crop:
    """HH and HV backscatter (linear power, gamma-zero) of the study area on one date."""
    date: str
    mode: str
    release: str
    hh: np.ndarray
    hv: np.ndarray
    grid: Grid


def save_npz(path: Path, **arrays) -> None:
    """Save arrays to a compressed .npz file, all or nothing.

    Writes to a temporary file in the same folder, then renames it into place.
    An interrupted save therefore never leaves a half-written file at `path`,
    which later runs would otherwise skip as "already done".
    """
    temporary = path.with_name(path.name + ".partial")
    with open(temporary, "wb") as f:
        np.savez_compressed(f, **arrays)
    os.replace(temporary, path)   # atomic on the same file system


def save_crop(crop: Crop, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{crop.date}.npz"
    save_npz(path, date=crop.date, mode=crop.mode, release=crop.release,
             hh=crop.hh, hv=crop.hv, x=crop.grid.x, y=crop.grid.y,
             epsg=crop.grid.epsg, resolution_m=crop.grid.resolution_m)
    return path


def load_crop(path: Path) -> Crop:
    d = np.load(path)
    grid = Grid(x=d["x"], y=d["y"], epsg=int(d["epsg"]), resolution_m=float(d["resolution_m"]))
    return Crop(date=str(d["date"]), mode=str(d["mode"]), release=str(d["release"]),
                hh=d["hh"], hv=d["hv"], grid=grid)


def load_all_crops(folder: Path) -> list[Crop]:
    return [load_crop(p) for p in sorted(folder.glob("*.npz"))]
