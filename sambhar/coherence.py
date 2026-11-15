"""Interferometric coherence from NISAR GUNW (geocoded interferogram) files.

Coherence (0 to 1) measures how similar the radar echo from a pixel is on two
passes 12 days apart. Open water moves, so its echo is different every time
and coherence is low. A stable surface such as salt crust or bare ground keeps
its structure, so coherence stays high. Brightness alone cannot make this
distinction: calm water and smooth crust can both look dark.

Dataset paths are searched for rather than hard-coded, as in nisar.py.
"""
from pathlib import Path

import h5py
import numpy as np

from sambhar import nisar
from sambhar.granules import GunwPair
from sambhar.grid import Grid, sample_onto_grid


def coherence_group(h5: h5py.File) -> h5py.Group:
    """The group holding the coherence layer.

    GUNW files have two: one next to the wrapped interferogram (finer, about
    20 m) and one next to the unwrapped phase (coarser). We prefer the finer one.
    """
    paths = nisar.find_datasets(h5, "coherenceMagnitude")
    finest = [p for p in paths if "wrappedInterferogram" in p and "unwrapped" not in p] or paths
    if not finest:
        raise RuntimeError("No coherenceMagnitude found. Print the file structure to inspect it.")
    return h5[finest[0].rsplit("/", 1)[0]]


def valid_samples(mask: np.ndarray) -> np.ndarray:
    """True where the GUNW 'mask' layer says both radar passes are usable.

    The mask packs several flags into one integer per pixel:
      bits 0-7, read as a 3-digit number: water flag (static map, not used here),
               sub-swath of the first pass, sub-swath of the second pass (0 = invalid);
      bits 8-23: data-anomaly flags for each pass (0 = no anomaly).
    255 means outside the data.
    """
    mask = mask.astype(np.int64)
    subswaths = mask & 0xFF
    first_pass_ok = (subswaths // 10) % 10 > 0
    second_pass_ok = subswaths % 10 > 0
    no_anomaly = (mask >> 8) & 0xFFFF == 0
    return (mask != 255) & first_pass_ok & second_pass_ok & no_anomaly


def crop_coherence(h5: h5py.File, grid: Grid) -> np.ndarray:
    """Coherence (0-1) of an open GUNW file, resampled onto our study grid. Invalid pixels are NaN."""
    group = coherence_group(h5)
    epsg = nisar.epsg_code(group)
    if epsg != grid.epsg:
        raise RuntimeError(f"GUNW projection EPSG:{epsg} differs from the study grid EPSG:{grid.epsg}.")

    x, y = group["xCoordinates"][:], group["yCoordinates"][:]
    coherence = sample_onto_grid(group["coherenceMagnitude"], x, y, grid)

    # The mask sits one level up, shared by all polarisations. Pixels outside the file come back as NaN.
    # (Sampling returns float32, which holds these flag values exactly: they use at most 24 bits.)
    shared = group.parent
    mask = sample_onto_grid(shared["mask"], shared["xCoordinates"][:], shared["yCoordinates"][:], grid)
    usable = np.isfinite(mask) & valid_samples(np.nan_to_num(mask, nan=255))
    coherence[~usable] = np.nan
    return coherence


def pair_file(pair: GunwPair, folder: Path) -> Path:
    """Where the cropped coherence of a pair is saved."""
    return folder / f"{pair.reference_date}_{pair.secondary_date}.npz"


def coherence_for_date(date: str, pairs: list[GunwPair], folder: Path):
    """Coherence for one radar date, from the cropped 12-day pairs that include it.

    Uses the HIGHER of the pair before and the pair after, pixel by pixel, so a
    pixel counts as unstable only if it was unstable in both. Where only one
    pair has data, that pair is used. Returns (coherence, number of pairs),
    or (None, 0) if no cropped pair includes this date.
    """
    files = [pair_file(p, folder) for p in pairs if date in (p.reference_date, p.secondary_date)]
    files = [f for f in files if f.exists()]
    if not files:
        return None, 0
    stack = np.array([np.load(f)["coherence"] for f in files])
    return np.fmax.reduce(stack, axis=0), len(files)
