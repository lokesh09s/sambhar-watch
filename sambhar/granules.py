"""Which NISAR files we use, and how to open them."""
import csv
from dataclasses import dataclass

import h5py

from sambhar.config import GRANULES_CSV, GUNW_PAIRS_CSV


@dataclass(frozen=True)
class Granule:
    """One NISAR GCOV acquisition over Sambhar."""
    date: str      # acquisition date, YYYY-MM-DD
    mode: str      # DHDH (dual-pol) or QPDH (quad-pol); both contain HH and HV
    release: str   # "provisional" or "validated" processing release
    url: str       # HTTPS link to the HDF5 file at NASA's Alaska Satellite Facility


def load_granules(path=GRANULES_CSV) -> list[Granule]:
    """Read the list of NISAR files from data/granules.csv."""
    with open(path, newline="") as f:
        return [Granule(**row) for row in csv.DictReader(f)]


@dataclass(frozen=True)
class GunwPair:
    """One NISAR GUNW interferogram: the same place seen twice, 12 days apart."""
    reference_date: str   # first acquisition, YYYY-MM-DD
    secondary_date: str   # second acquisition, YYYY-MM-DD
    url: str


def load_gunw_pairs(path=GUNW_PAIRS_CSV) -> list[GunwPair]:
    """Read the list of interferogram pairs from data/gunw_pairs.csv."""
    with open(path, newline="") as f:
        return [GunwPair(**row) for row in csv.DictReader(f)]


_https_session = None


def open_remote(url: str) -> h5py.File:
    """Open a remote NISAR file without downloading it.

    Only the parts of the file we actually read are transferred, so cropping
    the lake takes a few hundred MB instead of the full ~6 GB file.
    Requires a free NASA Earthdata account (asked for on first use).
    """
    global _https_session
    import earthaccess  # imported here so the rest of the code works offline

    if _https_session is None:
        earthaccess.login()
        _https_session = earthaccess.get_fsspec_https_session()
    remote_file = _https_session.open(url, mode="rb", block_size=8 * 1024**2, cache_type="blockcache")
    return h5py.File(remote_file, "r")
