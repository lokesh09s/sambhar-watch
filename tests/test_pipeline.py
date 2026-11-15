"""End-to-end test on a synthetic NISAR-like file with a lake of known size.

The fake file mimics the GCOV layout. A 9 km x 4 km elliptical "lake"
(area = pi * 9 * 4 = 113.1 km2) is made dark; the pipeline should measure
about the same area.

Run:  python -m pytest tests/      (or simply: python tests/test_pipeline.py)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import h5py
import numpy as np
from pyproj import Transformer

from sambhar import config
from sambhar.granules import Granule
from sambhar.water import classify_water, detection_frequency, reduce_speckle, to_decibels

EPSG = 32643  # UTM zone 43N, which covers Sambhar
LAKE_AREA_KM2 = np.pi * 9 * 4
# Northern edge of the study area (north of 27.06 N, far from the lake) is flagged invalid in the mask.
MASKED_NORTH_OF_Y = Transformer.from_crs("EPSG:4326", f"EPSG:{EPSG}", always_xy=True).transform(75.0, 27.06)[1]


def make_fake_gcov(path: Path, with_lake: bool) -> None:
    to_map = Transformer.from_crs("EPSG:4326", f"EPSG:{EPSG}", always_xy=True)
    x0, y0 = to_map.transform(74.5, 27.4)
    x = np.arange(x0, x0 + 80_000, 10.0)
    y = np.arange(y0, y0 - 80_000, -10.0)
    rng = np.random.default_rng(0)
    land = rng.gamma(4, 0.1 / 4, (y.size, x.size)).astype(np.float32)     # about -10 dB
    if with_lake:
        gx, gy = np.meshgrid(x, y)
        cx, cy = to_map.transform(75.08, 26.95)
        lake = ((gx - cx) / 9000) ** 2 + ((gy - cy) / 4000) ** 2 < 1
        land[lake] = rng.gamma(4, 0.003 / 4, lake.sum())                  # about -25 dB
    mask = np.ones(land.shape, dtype=np.uint8)                           # sub-swath 1: valid
    mask[y > MASKED_NORTH_OF_Y] = 0                                      # strip flagged invalid
    with h5py.File(path, "w") as h5:
        g = h5.create_group("science/LSAR/GCOV/grids/frequencyA")
        g["xCoordinates"], g["yCoordinates"] = x, y
        g.create_dataset("projection", data=np.uint32(EPSG)).attrs["epsg_code"] = EPSG
        g.create_dataset("HHHH", data=land, chunks=(512, 512))
        g.create_dataset("HVHV", data=land * 0.2, chunks=(512, 512))
        g.create_dataset("mask", data=mask, chunks=(512, 512))


def test_lake_area_is_recovered(tmp_path=Path("/tmp")):
    from scripts.crop_lake import crop_granule  # noqa: E402

    fake = tmp_path / "fake_gcov.h5"
    make_fake_gcov(fake, with_lake=True)
    with h5py.File(fake) as h5:
        crop = crop_granule(h5, Granule("2026-08-15", "DHDH", "provisional", "local"))

    hh_db = reduce_speckle(to_decibels(crop.hh), config.SPECKLE_WINDOW)
    water, valid = classify_water(hh_db, threshold_db=-18.0)
    area = water.sum() * crop.grid.pixel_area_km2

    north_of_line = crop.grid.y > MASKED_NORTH_OF_Y
    assert not valid[north_of_line].any(), "mask 0 pixels must be invalid"
    assert valid[~north_of_line].all()
    assert abs(area - LAKE_AREA_KM2) / LAKE_AREA_KM2 < 0.03, f"measured {area:.1f} km2"


def test_frequency_uses_valid_observations():
    water = np.array([[[True]], [[False]], [[False]]])
    valid = np.array([[[True]], [[True]], [[False]]])   # third date has no data
    frequency, n_valid = detection_frequency(water, valid)
    assert n_valid[0, 0] == 2
    assert frequency[0, 0] == 0.5                        # 1 of 2 valid, not 1 of 3


def test_gunw_mask_decoding():
    from sambhar.coherence import valid_samples
    mask = np.array([11,          # sub-swath 1 on both passes: valid
                     111,         # same, flagged as water by the static map: still valid
                     10,          # second pass invalid
                     1,           # first pass invalid
                     255,         # outside the data
                     11 + 256])   # anomaly flag set on the second pass
    assert valid_samples(mask).tolist() == [True, True, False, False, False, False]


def test_date_coherence_takes_higher_pair(tmp_path=Path("/tmp")):
    from sambhar.coherence import coherence_for_date, pair_file
    from sambhar.granules import GunwPair
    before = GunwPair("2026-05-11", "2026-05-23", "local")
    after = GunwPair("2026-05-23", "2026-06-04", "local")
    np.savez(pair_file(before, tmp_path), coherence=np.array([0.2, np.nan, 0.6]))
    np.savez(pair_file(after, tmp_path), coherence=np.array([0.5, 0.1, np.nan]))

    coherence, n_pairs = coherence_for_date("2026-05-23", [before, after], tmp_path)
    assert n_pairs == 2
    assert coherence.tolist() == [0.5, 0.1, 0.6]       # higher value; one pair where the other is missing
    assert coherence_for_date("2026-05-11", [before, after], tmp_path)[1] == 1
    assert coherence_for_date("2026-07-10", [before, after], tmp_path) == (None, 0)


def test_dark_stable_surface_is_not_detected():
    from sambhar.water import classify_dark_unstable
    hh_db = np.array([-25.0, -25.0, -10.0, -25.0])
    coherence = np.array([0.1, 0.7, 0.1, np.nan])        # water, dry crust, bright land, no coherence
    detected, valid = classify_dark_unstable(hh_db, coherence, threshold_db=-18.0, coherence_threshold=0.3)
    assert detected.tolist() == [True, False, False, False]
    assert valid.tolist() == [True, True, True, False]


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    test_lake_area_is_recovered()
    test_frequency_uses_valid_observations()
    test_gunw_mask_decoding()
    test_date_coherence_takes_higher_pair()
    test_dark_stable_surface_is_not_detected()
    print("All tests passed.")
