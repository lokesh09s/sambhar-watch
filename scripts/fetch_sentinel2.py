"""Find and save Sentinel-2 L2A scenes that match each NISAR date (independent optical validation).

Data come from Microsoft Planetary Computer's free STAC API (no account needed).
Every scene is mosaicked from its MGRS tiles onto the same 20 m UTM grid as the NISAR crops,
so radar and optical pixels line up exactly.

"The lake" = the connected area that JRC Global Surface Water saw as water at least once in
1984-2021, so run scripts/fetch_jrc.py first. Cloud % is measured over that lake only.

    python scripts/fetch_sentinel2.py 2026-05-11 2026-08-15   # match and save these NISAR dates
    python scripts/fetch_sentinel2.py all                     # every date in data/granules.csv
    python scripts/fetch_sentinel2.py points 2026-01-11 2026-05-11 2026-08-29  # points to label
    python scripts/fetch_sentinel2.py scan 2026-08-01 2026-08-31     # clearest days (land cloud)
    python scripts/fetch_sentinel2.py look 2026-05-11                # true colour + lake outline

Outputs (in validation_data/):
    sentinel2/<nisar_date>_truecolour.png    true colour (Sentinel-2 "visual" product), 20 m grid
    sentinel2/<nisar_date>_B03_B08_B11.tif   20 m bands, raw L2A digital numbers (see BOA_OFFSET)
    sentinel2/<nisar_date>_SCL.tif           Sen2Cor scene classification (cloud mask), 20 m
    sentinel2_matches.csv                    nisar_date, s2_date, gap_days, cloud_pct
    points_<s2_date>.csv                     id, lon, lat, date, label (label left empty for humans)
    points_<s2_date>_numbered.png            true colour with numbered points, for labelling
    points_<s2_date>_neighbours.png          same points on neighbouring days (NEIGHBOUR_DAYS)
    points_<s2_date>_mndwi.csv               id, mndwi: optical second opinion, kept out of the
                                             labelling file so it cannot bias the labellers
"""
import csv
import functools
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

# GDAL network settings. Environment variables (not rasterio.Env) so worker threads see them too.
# Abort only a transfer that has stalled (< 1 kB/s for 60 s): a fixed timeout cuts off slow,
# healthy downloads, and Planetary Computer storage gives only ~30 kB/s per connection here.
os.environ.update(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_LOW_SPEED_LIMIT="1000",
                  GDAL_HTTP_LOW_SPEED_TIME="60", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="3")

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import planetary_computer  # noqa: E402
import pystac_client  # noqa: E402
import rasterio  # noqa: E402
from pyproj import Transformer  # noqa: E402
from rasterio.transform import from_origin  # noqa: E402
from rasterio.vrt import WarpedVRT  # noqa: E402
from scipy import ndimage  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sambhar.config import ROOT, SAMBHAR_BBOX, GRID_RESOLUTION_M  # noqa: E402
from sambhar.granules import load_granules  # noqa: E402
from sambhar.grid import Grid, make_grid  # noqa: E402
from sambhar.pans import pans_mask  # noqa: E402

# ---------------------------------------------------------------- settings
STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "sentinel-2-l2a"
EPSG = 32643                     # UTM 43N: same projection as the NISAR crops
RES_M = GRID_RESOLUTION_M        # everything on the NISAR grid (20 m)
# These assets are 10 m; their first built-in overview is exactly 20 m (averaged), and reading it
# downloads ~4x less than full resolution.
TEN_M_ASSETS = {"visual", "B02", "B03", "B04", "B08"}
MAX_GAP_DAYS = 5                 # search window: NISAR date +/- this many days
MAX_CLOUD_PCT = 20.0             # skip the date if the best scene is cloudier than this over the lake
# Some orbits only reach part of the lake. Scenes are ranked by the % of the lake that is both
# imaged and cloud-free; scenes within TIE_PCT of each other count as equal, then the closest date wins.
MIN_COVERAGE_PCT = 50.0
TIE_PCT = 1.0
# Scene Classification (SCL): 0 no data, 1 defective (also used outside the orbit swath),
# 3 cloud shadow, 8/9 cloud, 10 cirrus.
NO_DATA_CLASSES = [0, 1]
CLOUD_CLASSES = [3, 8, 9, 10]
BANDS = ["B03", "B08", "B11"]
BOA_OFFSET = -1000               # processing baseline >= 04.00: reflectance = (DN + offset) / 10000
PARALLEL_DOWNLOADS = 16          # storage is throttled per connection, so parallel reads help a lot

JRC_TIF = ROOT / "validation_data" / "jrc_occurrence.tif"   # written by scripts/fetch_jrc.py
LAKE_GEOJSON = ROOT / "data" / "lake.geojson"  # team's hand-drawn lake outline (season check)
LAKE_GAP_CLOSE_PX = 3            # bridge thin gaps (the dam) so the lake is one connected area

N_POINTS = 150
LAKE_BUFFER_M = 2000
RANDOM_SEED = 2026
LABEL_CLASSES = "water / white_uncertain / salt_crust / land"
# Days shown either side of a labelling date, so labellers can judge white areas.
NEIGHBOUR_DAYS = {"2026-05-11": ["2026-05-06", "2026-05-16"]}

OUT_DIR = ROOT / "validation_data"
SCENE_DIR = OUT_DIR / "sentinel2"
MATCHES_CSV = OUT_DIR / "sentinel2_matches.csv"
MATCH_FIELDS = ["nisar_date", "s2_date", "gap_days", "cloud_pct", "lake_coverage_pct"]

GRID = make_grid(SAMBHAR_BBOX, EPSG, RES_M)
POOL = ThreadPoolExecutor(PARALLEL_DOWNLOADS)


# ---------------------------------------------------------------- reading
def transform_of(grid: Grid):
    """Affine transform (top-left corner, pixel size) for a project grid."""
    r = grid.resolution_m
    return from_origin(grid.x[0] - r / 2, grid.y[0] + r / 2, r, r)


def read_tile(item, asset: str, attempts: int = 3) -> np.ndarray:
    """Read one tile's asset onto GRID (0 = no data), retrying truncated downloads.

    Only the blocks under the grid are downloaded (warped VRT over a cloud-optimised GeoTIFF).
    """
    options = {"OVERVIEW_LEVEL": 0} if asset in TEN_M_ASSETS and RES_M >= 20 else {}
    for attempt in range(attempts):
        try:
            href = planetary_computer.sign(item).assets[asset].href  # fresh signature: links expire
            with rasterio.open(href, **options) as src, WarpedVRT(
                    src, crs=f"EPSG:{GRID.epsg}", transform=transform_of(GRID), width=GRID.shape[1],
                    height=GRID.shape[0], nodata=0) as vrt:
                return vrt.read()
        except rasterio.errors.RasterioIOError as error:
            if attempt == attempts - 1:
                raise
            print(f"      retrying {item.id} {asset}: {str(error)[:80]}")


def mosaic(items, asset: str) -> np.ndarray:
    """Read one asset from every tile of a scene in parallel and merge them onto GRID."""
    tiles = list(POOL.map(lambda item: read_tile(item, asset), items))
    out = tiles[0]
    for data in tiles[1:]:
        empty = out[0] == 0
        out[:, empty] = data[:, empty]
    return out


def scenes_near(nisar_date: date) -> dict[date, list]:
    """All Sentinel-2 L2A tiles within MAX_GAP_DAYS of a date, grouped by acquisition day."""
    catalog = pystac_client.Client.open(STAC_URL)
    window = f"{nisar_date - timedelta(MAX_GAP_DAYS)}/{nisar_date + timedelta(MAX_GAP_DAYS)}"
    items = catalog.search(collections=[COLLECTION], bbox=SAMBHAR_BBOX, datetime=window).items()
    by_day: dict[date, list] = {}
    for item in items:
        by_day.setdefault(item.datetime.date(), []).append(item)
    return by_day


@functools.cache
def lake_mask() -> np.ndarray:
    """Lake pixels on GRID: the largest connected area JRC ever saw as water (1984-2021).

    Thin gaps such as the dam are bridged first, so the main lake and the eastern pans stay one
    area; small separate ponds and reservoirs nearby are left out.
    """
    if not JRC_TIF.exists():
        raise SystemExit(f"{JRC_TIF} missing: run scripts/fetch_jrc.py first.")
    with rasterio.open(JRC_TIF) as src, WarpedVRT(
            src, crs=f"EPSG:{GRID.epsg}", transform=transform_of(GRID), width=GRID.shape[1],
            height=GRID.shape[0], nodata=255) as vrt:
        occurrence = vrt.read(1)
    ever_water = ndimage.binary_closing((occurrence > 0) & (occurrence <= 100),
                                        iterations=LAKE_GAP_CLOSE_PX)
    blobs, _ = ndimage.label(ever_water)
    largest = 1 + int(np.argmax(np.bincount(blobs.ravel())[1:]))
    return ndimage.binary_fill_holes(blobs == largest)


def cloud_over_lake(scl: np.ndarray) -> tuple[float, float]:
    """(cloud % of the imaged lake, % of the lake imaged at all), from a Scene Classification layer."""
    scl = scl[lake_mask()]
    valid = ~np.isin(scl, NO_DATA_CLASSES)
    cloud_pct = 100 * np.isin(scl[valid], CLOUD_CLASSES).mean() if valid.any() else 100.0
    return float(cloud_pct), float(100 * valid.mean())


# ---------------------------------------------------------------- matching
def best_scene(nisar_date: date) -> dict | None:
    """The day near a NISAR date showing the most clear lake (see MIN_COVERAGE_PCT, TIE_PCT).

    Returns dict(day, items, cloud_pct, coverage_pct), or None if no scene covers enough lake.
    The caller still has to apply MAX_CLOUD_PCT.
    """
    days = sorted(scenes_near(nisar_date).items())
    stats = ThreadPoolExecutor(len(days) or 1).map(lambda d: cloud_over_lake(mosaic(d[1], "SCL")[0]), days)
    best, best_key = None, None
    for (day, items), (cloud_pct, coverage_pct) in zip(days, stats):
        gap = abs((day - nisar_date).days)
        clear_pct = coverage_pct * (1 - cloud_pct / 100)
        print(f"    {day}  gap {gap} d  lake: cloud {cloud_pct:5.1f} %  imaged {coverage_pct:3.0f} %"
              f"  clear {clear_pct:3.0f} %")
        key = (-(clear_pct // TIE_PCT), gap)
        if coverage_pct >= MIN_COVERAGE_PCT and (best_key is None or key < best_key):
            best, best_key = dict(day=day, items=items, cloud_pct=cloud_pct, coverage_pct=coverage_pct), key
    return best


def save_scene(nisar_date: date, items) -> None:
    """Write the true-colour PNG, the B03/B08/B11 GeoTIFF and the SCL GeoTIFF for one match.

    All assets download in parallel.
    """
    SCENE_DIR.mkdir(parents=True, exist_ok=True)
    rgb, scl, *bands = ThreadPoolExecutor(5).map(lambda a: mosaic(items, a), ["visual", "SCL", *BANDS])
    plt.imsave(SCENE_DIR / f"{nisar_date}_truecolour.png", np.moveaxis(rgb, 0, -1))

    profile = dict(driver="GTiff", width=GRID.shape[1], height=GRID.shape[0], crs=f"EPSG:{EPSG}",
                   transform=transform_of(GRID), nodata=0, compress="deflate")
    tags = dict(s2_items=" ".join(i.id for i in items), nisar_date=str(nisar_date))
    with rasterio.open(SCENE_DIR / f"{nisar_date}_B03_B08_B11.tif", "w", dtype="uint16",
                       count=len(BANDS), **profile) as dst:
        dst.write(np.concatenate(bands))
        dst.descriptions = tuple(BANDS)
        dst.update_tags(**tags, reflectance=f"(DN + {BOA_OFFSET}) / 10000")
    with rasterio.open(SCENE_DIR / f"{nisar_date}_SCL.tif", "w", dtype="uint8", count=1, **profile) as dst:
        dst.write(scl)
        dst.update_tags(**tags, classes="Sen2Cor SCL: 1 defective, 3 shadow, 4 vegetation, "
                        "5 bare, 6 water, 7 unclassified, 8/9 cloud, 10 cirrus, 11 snow")


def update_matches(row: dict) -> None:
    """Add or replace one NISAR date's row in sentinel2_matches.csv (re-runs overwrite)."""
    existing = {}
    if MATCHES_CSV.exists():
        with open(MATCHES_CSV) as f:
            existing = {r["nisar_date"]: r for r in csv.DictReader(f)}
    existing[row["nisar_date"]] = row
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(MATCHES_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MATCH_FIELDS)
        writer.writeheader()
        writer.writerows(sorted(existing.values(), key=lambda r: r["nisar_date"]))


def match_dates(nisar_dates: list[date]) -> None:
    """Find, save and record the best Sentinel-2 scene for each NISAR date.

    Skipped dates are recorded with an empty s2_date and the cloud/coverage of the best scene seen.
    """
    for nisar_date in nisar_dates:
        print(f"NISAR {nisar_date}:", flush=True)
        best = best_scene(nisar_date)
        row = dict(nisar_date=nisar_date, s2_date="", gap_days="", cloud_pct="", lake_coverage_pct="")
        if best:
            row.update(cloud_pct=f"{best['cloud_pct']:.1f}", lake_coverage_pct=f"{best['coverage_pct']:.0f}")
        if best is None or best["cloud_pct"] > MAX_CLOUD_PCT:
            print(f"  -> skipped (best scene: cloud {row['cloud_pct'] or 'n/a'} %)")
        else:
            gap = (best["day"] - nisar_date).days
            print(f"  -> {best['day']} (gap {gap:+d} d)", flush=True)
            save_scene(nisar_date, best["items"])
            row.update(s2_date=best["day"], gap_days=gap)
        update_matches({k: str(v) for k, v in row.items()})


# ---------------------------------------------------------------- validation points
# Files are named by the Sentinel-2 day (what labellers see). Points go on the team's
# data/lake.geojson + LAKE_BUFFER_M. The SCL cloud mask is NOT used to drop points: Sen2Cor
# flags white salt surfaces as cloud, and the confirmed dates have a clear sky over land.
def ensure_scene(day: date) -> None:
    """Download a Sentinel-2 day's bands, SCL and true colour unless they are already saved."""
    if not (SCENE_DIR / f"{day}_B03_B08_B11.tif").exists():
        save_scene(day, scenes_on(day, day)[day])


def true_colour(day: date) -> np.ndarray:
    """True colour of a Sentinel-2 day (floats 0-1); downloads only the visual asset if missing."""
    path = SCENE_DIR / f"{day}_truecolour.png"
    if not path.exists():
        SCENE_DIR.mkdir(parents=True, exist_ok=True)
        plt.imsave(path, np.moveaxis(mosaic(scenes_on(day, day)[day], "visual"), 0, -1))
    return plt.imread(path)[..., :3]


def read_bands(day: date) -> np.ndarray:
    """Saved B03/B08/B11 as surface reflectance (NaN = no data)."""
    with rasterio.open(SCENE_DIR / f"{day}_B03_B08_B11.tif") as src:
        dn = src.read().astype(np.float32)
    dn[dn == 0] = np.nan
    return (dn + BOA_OFFSET) / 10000


def mndwi(b03: np.ndarray, b11: np.ndarray) -> np.ndarray:
    """Modified NDWI (green vs SWIR). Positive often means water, BUT bright salt crust can score
    positive too, so this is only a second opinion, never ground truth."""
    with np.errstate(invalid="ignore", divide="ignore"):
        return (b03 - b11) / (b03 + b11)


def sampling_area(day: date) -> np.ndarray:
    """Pixels where points may go: team lake + LAKE_BUFFER_M, where the scene has data."""
    near_lake = ndimage.distance_transform_edt(~team_lake()) * RES_M <= LAKE_BUFFER_M
    with rasterio.open(SCENE_DIR / f"{day}_SCL.tif") as src:
        scl = src.read(1)
    return near_lake & ~np.isin(scl, NO_DATA_CLASSES)


def make_points(day: date) -> None:
    """Draw random points over lake + buffer, write the CSVs and the numbered helper image(s)."""
    ensure_scene(day)
    rng = np.random.default_rng([RANDOM_SEED, day.toordinal()])  # reproducible per date
    b03, _, b11 = read_bands(day)
    index = mndwi(b03, b11)
    rows, cols = np.nonzero(sampling_area(day))
    pick = rng.choice(rows.size, N_POINTS, replace=False)
    # Random position inside each chosen pixel, so points are continuous, not on a lattice.
    r = rows[pick] + rng.random(N_POINTS)
    c = cols[pick] + rng.random(N_POINTS)
    xs, ys = rasterio.transform.xy(transform_of(GRID), r, c, offset="ul")
    lons, lats = Transformer.from_crs(f"EPSG:{EPSG}", "EPSG:4326", always_xy=True).transform(xs, ys)

    stem = OUT_DIR / f"points_{day}"
    with open(f"{stem}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "lon", "lat", "date", "label"])
        w.writerows([i + 1, f"{lon:.6f}", f"{lat:.6f}", day, ""]
                    for i, (lon, lat) in enumerate(zip(lons, lats)))
    with open(f"{stem}_mndwi.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "mndwi"])
        w.writerows([i + 1, f"{index[rows[p], cols[p]]:.3f}"] for i, p in enumerate(pick))
    numbered_image([day], r, c, f"{stem}_numbered.png", zoom=2)
    print(f"{day}: {N_POINTS} points -> {stem}.csv, {stem}_numbered.png")
    if str(day) in NEIGHBOUR_DAYS:
        before, after = (date.fromisoformat(d) for d in NEIGHBOUR_DAYS[str(day)])
        numbered_image([before, day, after], r, c, f"{stem}_neighbours.png", zoom=1)
        print(f"  side-by-side {before} | {day} | {after} -> {stem}_neighbours.png")


def numbered_image(days: list[date], rows, cols, path: str, zoom: int) -> None:
    """Each day's true colour side by side, lake outline in yellow, every point circled and numbered.

    Cropped to the points plus a margin, and drawn at `zoom`x so the numbers stay legible.
    """
    margin = 40
    r0, r1 = max(int(rows.min()) - margin, 0), min(int(rows.max()) + margin, GRID.shape[0])
    c0, c1 = max(int(cols.min()) - margin, 0), min(int(cols.max()) + margin, GRID.shape[1])
    lake = team_lake()
    outline = lake & ~ndimage.binary_erosion(lake, iterations=2)
    h, w = r1 - r0, c1 - c0
    fig, axes = plt.subplots(1, len(days), figsize=(len(days) * w * zoom / 100, h * zoom / 100),
                             dpi=100, squeeze=False)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0.01)
    x, y = cols - c0 - 0.5, rows - r0 - 0.5  # imshow puts pixel edges at -0.5
    for ax, day in zip(axes[0], days):
        rgb = true_colour(day).copy()
        rgb[outline] = (1, 1, 0)
        ax.imshow(rgb[r0:r1, c0:c1], interpolation="nearest")
        ax.scatter(x, y, s=100 * zoom, facecolors="none", edgecolors="red", linewidths=1.5)
        for i, (xi, yi) in enumerate(zip(x, y)):
            ax.text(xi + 3 * zoom, yi - 3 * zoom, str(i + 1), color="yellow", fontsize=6.5 * zoom,
                    weight="bold", bbox=dict(facecolor="black", alpha=0.6, pad=1, linewidth=0))
        ax.text(5, 5, f"Sentinel-2 {day}   labels: {LABEL_CLASSES}   (see LOG.md)",
                color="white", fontsize=9 * zoom, va="top", bbox=dict(facecolor="black", alpha=0.7))
        ax.axis("off")
    fig.savefig(path, dpi=100)
    plt.close(fig)


# ---------------------------------------------------------------- season check by eye
# Sen2Cor flags bright salt crust over the lake as cloud (seen on 2026-05-11), so here sky
# cloudiness is measured over land only: outside the hand-drawn lake + LAKE_BUFFER_M.
def team_lake() -> np.ndarray:
    """Lake pixels on GRID from the team's hand-drawn data/lake.geojson."""
    return pans_mask(LAKE_GEOJSON, GRID)


def scenes_on(start: date, end: date) -> dict[date, list]:
    """All Sentinel-2 L2A tiles over the box between two dates, grouped by acquisition day."""
    items = pystac_client.Client.open(STAC_URL).search(
        collections=[COLLECTION], bbox=SAMBHAR_BBOX, datetime=f"{start}/{end}").items()
    by_day: dict[date, list] = {}
    for item in items:
        by_day.setdefault(item.datetime.date(), []).append(item)
    return dict(sorted(by_day.items()))


def scan(start: date, end: date) -> None:
    """Print each day's land cloud % (true sky state) and % of the lake imaged, clearest first."""
    lake = team_lake()
    land = ndimage.distance_transform_edt(~lake) * RES_M > LAKE_BUFFER_M
    days = scenes_on(start, end)

    def stats(items):
        scl = mosaic(items, "SCL")[0]
        land_valid = land & ~np.isin(scl, NO_DATA_CLASSES)
        land_cloud = 100 * np.isin(scl[land_valid], CLOUD_CLASSES).mean() if land_valid.any() else 100
        return land_cloud, 100 * (~np.isin(scl[lake], NO_DATA_CLASSES)).mean()

    rows = zip(days, ThreadPoolExecutor(len(days) or 1).map(stats, days.values()))
    for day, (land_cloud, lake_imaged) in sorted(rows, key=lambda r: (r[1][1] < 99, r[1][0])):
        print(f"  {day}  land cloud {land_cloud:5.1f} %  lake imaged {lake_imaged:3.0f} %")


def look(day: date) -> None:
    """Save the true-colour image of one Sentinel-2 day with the team's lake outline drawn on it."""
    rgb = true_colour(day).copy()
    lake = team_lake()
    rgb[lake & ~ndimage.binary_erosion(lake, iterations=3)] = (1, 1, 0)
    SCENE_DIR.mkdir(parents=True, exist_ok=True)
    path = SCENE_DIR / f"look_{day}.png"
    plt.imsave(path, rgb)
    print(f"saved {path}")


# ---------------------------------------------------------------- main
def main(args: list[str]) -> None:
    if args and args[0] == "scan":
        scan(date.fromisoformat(args[1]), date.fromisoformat(args[2]))
        return
    if args and args[0] == "look":
        for d in args[1:]:
            look(date.fromisoformat(d))
        return
    if args and args[0] == "points":
        for d in args[1:]:
            make_points(date.fromisoformat(d))
        return
    if args == ["all"]:
        dates = [date.fromisoformat(g.date) for g in load_granules()]
    else:
        dates = [date.fromisoformat(d) for d in args]
    if not dates:
        raise SystemExit(__doc__)
    match_dates(dates)


if __name__ == "__main__":
    main(sys.argv[1:])
