"""Project-wide settings. Change values here, not inside the code."""
from pathlib import Path

# Folders
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CROPS_DIR = ROOT / "outputs" / "crops"
RESULTS_DIR = ROOT / "outputs" / "results"

GRANULES_CSV = DATA_DIR / "granules.csv"   # list of NISAR files (date, mode, release, url)
PANS_GEOJSON = DATA_DIR / "pans.geojson"   # salt-pan polygons drawn by hand (lon/lat)
LAKE_GEOJSON = DATA_DIR / "lake.geojson"   # outline of Sambhar Lake drawn by hand (lon/lat)
# How the pan class is named in outputs. Shape 1 of pans.geojson covers the whole eastern
# salt-works section (reservoirs + pans), so this is more than individual pans.
PANS_LABEL = "salt works and mapped pans"
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

# Classification rule (PROVISIONAL, 15 Nov 2026, until checked against Sentinel-2):
#   a pixel is a "dark unstable surface" when  HH < WATER_THRESHOLD_DB  AND  coherence < COHERENCE_THRESHOLD.
# Why (scripts/check_coherence.py; medians of CHECK_REGIONS, HH dB / 12-day coherence):
#   central lake bed  -23.4 / 0.19 (May pair)   -21.9 / 0.23 (Aug pair)
#   farmland          -15.5 / 0.59 (May pair)   -12.4 / 0.51 (Aug pair)
# - HH alone fails: dry-season farmland darkens. At -18 dB, 273 km2 of the study box is dark on
#   11 May (172 km2 on 15 Aug), and 129 km2 of the May dark area has coherence >= 0.3 (mostly land).
# - HH must stay loose: wind-roughened monsoon water is brighter (only 23 km2 below -22 dB on 15 Aug).
# - Coherence 0.3 lies between the lake (25-75%: 0.15-0.29) and farmland (0.41-0.69) in both seasons.
# - Low lake coherence is not just noise: the noise floor is about -26.8 dB, so a stable surface
#   at -23 dB could still reach coherence of about 0.5-0.8.
WATER_THRESHOLD_DB = -18.0
COHERENCE_THRESHOLD = 0.3
CLASS_NAME = "dark unstable surface (water or wet brine)"   # until Sentinel-2 confirms it is water

# Threshold values tried in the sensitivity check (scripts/sensitivity.py).
SENSITIVITY_THRESHOLDS_DB = (-17.0, -18.0, -19.0, -20.0)
SENSITIVITY_COHERENCE = (0.25, 0.30, 0.35)
