"""Saving and loading cropped images (one .npz file per date)."""
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


def save_crop(crop: Crop, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{crop.date}.npz"
    np.savez_compressed(path, date=crop.date, mode=crop.mode, release=crop.release,
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
