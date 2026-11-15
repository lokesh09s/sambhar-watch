"""Project-wide settings. Change values here, not inside the code."""
from pathlib import Path

# Folders
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CROPS_DIR = ROOT / "outputs" / "crops"
RESULTS_DIR = ROOT / "outputs" / "results"

GRANULES_CSV = DATA_DIR / "granules.csv"   # list of NISAR files (date, mode, release, url)
PANS_GEOJSON = DATA_DIR / "pans.geojson"   # salt-pan polygons drawn by hand (lon/lat)
GUNW_PAIRS_CSV = DATA_DIR / "gunw_pairs.csv"   # 12-day interferogram pairs (reference, secondary, url)
COHERENCE_DIR = ROOT / "outputs" / "coherence"

# Study area: box around Sambhar Salt Lake in longitude/latitude (WGS84).
# (lon_min, lat_min, lon_max, lat_max). Check it on the first quick-look image.
SAMBHAR_BBOX = (74.90, 26.82, 75.28, 27.08)

# Every date is resampled onto the same grid with this pixel size (metres),
# so that dates can be compared pixel by pixel.
GRID_RESOLUTION_M = 20.0

# Values of the GCOV 'mask' layer that mean "no valid measurement here":
# 0 = partially focused or invalid radar samples, 255 = outside the radar swath.
# (1-254 give the sub-swath number of a valid sample.)
INVALID_MASK_VALUES = (0, 255)

# Speckle filter: size of the averaging window in pixels (1 = no filtering).
SPECKLE_WINDOW = 3

# Small test boxes (lon_min, lat_min, lon_max, lat_max) used to compare surface types
# in the coherence check. Drawn by eye on the HH quick-look; outlines are shown on its figure.
CHECK_REGIONS = {
    "central lake": (75.05, 26.91, 75.10, 26.95),
    "salt pans": (75.14, 26.91, 75.20, 26.95),
    "farmland": (74.92, 26.83, 74.98, 26.87),
}

# Water threshold for HH backscatter in dB: pixels darker than this are "water".
# Placeholder value: choose it from Sambhar evidence (histogram + Sentinel-2), then record why here.
WATER_THRESHOLD_DB = -18.0
