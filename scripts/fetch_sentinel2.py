"""Find and save Sentinel-2 L2A scenes that match each NISAR date (independent optical validation).

Data come from Microsoft Planetary Computer's free STAC API (no account needed).
Every scene is mosaicked from its MGRS tiles onto the same 20 m UTM grid as the NISAR crops,
so radar and optical pixels line up exactly.

    python scripts/fetch_sentinel2.py 2026-05-11 2026-08-15   # match and save these NISAR dates
    python scripts/fetch_sentinel2.py all                     # every date in data/granules.csv
    python scripts/fetch_sentinel2.py points 2026-05-11 2026-08-15   # random points to label by eye

Outputs (in validation_data/):
    sentinel2/<nisar_date>_truecolour.png    10 m true colour (Sentinel-2 "visual" product)
    sentinel2/<nisar_date>_B03_B08_B11.tif   20 m bands, raw L2A digital numbers (see BOA_OFFSET)
    sentinel2_matches.csv                    nisar_date, s2_date, gap_days, cloud_pct
    points_<nisar_date>.csv                  id, lon, lat, date, label (label left empty for humans)
    points_<nisar_date>_numbered.png         true colour with numbered points, for labelling
    points_<nisar_date>_mndwi.csv            id, mndwi: optical second opinion, kept out of the
                                             labelling file so it cannot bias the labellers
"""
import csv
import sys
from datetime import date, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import planetary_computer
import pystac_client
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sambhar.config import ROOT, SAMBHAR_BBOX, GRID_RESOLUTION_M  # noqa: E402
from sambhar.granules import load_granules  # noqa: E402
from sambhar.grid import Grid, make_grid  # noqa: E402

# ---------------------------------------------------------------- settings
STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "sentinel-2-l2a"
EPSG = 32643                     # UTM 43N: same projection as the NISAR crops
BANDS_RES_M = GRID_RESOLUTION_M  # GeoTIFF on the NISAR grid (20 m)
TRUE_COLOUR_RES_M = 10.0         # native Sentinel-2 resolution, sharper for labelling by eye
MAX_GAP_DAYS = 5                 # search window: NISAR date +/- this many days
MAX_CLOUD_PCT = 20.0             # skip the date if the best scene is cloudier than this
MIN_COVERAGE = 0.95              # a scene must cover this fraction of the box (orbit edges)
CLOUD_TIE_PCT = 1.0              # scenes within 1 % cloud count as equal; then the closest date wins
# Scene Classification (SCL) classes counted as cloud: 3 shadow, 8/9 cloud, 10 cirrus.
CLOUD_CLASSES = [3, 8, 9, 10]
BANDS = ["B03", "B08", "B11"]
BOA_OFFSET = -1000               # processing baseline >= 04.00: reflectance = (DN + offset) / 10000

N_POINTS = 150
LAKE_BUFFER_M = 2000
RANDOM_SEED = 2026

OUT_DIR = ROOT / "validation_data"
SCENE_DIR = OUT_DIR / "sentinel2"
MATCHES_CSV = OUT_DIR / "sentinel2_matches.csv"
MATCH_FIELDS = ["nisar_date", "s2_date", "gap_days", "cloud_pct"]


# ---------------------------------------------------------------- reading
def transform_of(grid: Grid):
    """Affine transform (top-left corner, pixel size) for a project grid."""
    r = grid.resolution_m
    return from_origin(grid.x[0] - r / 2, grid.y[0] + r / 2, r, r)


def mosaic(items, asset: str, grid: Grid, resampling=Resampling.nearest) -> np.ndarray:
    """Read one asset from every tile of a scene onto the grid; 0 where no tile has data.

    Only the blocks under the grid are downloaded (GDAL warped VRT over a cloud-optimised GeoTIFF).
    """
    out = None
    for item in items:
        href = planetary_computer.sign(item).assets[asset].href  # fresh signature: links expire
        with rasterio.open(href) as src, WarpedVRT(
                src, crs=f"EPSG:{grid.epsg}", transform=transform_of(grid),
                width=grid.shape[1], height=grid.shape[0], resampling=resampling, nodata=0) as vrt:
            data = vrt.read()
        if out is None:
            out = data
        else:
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


def cloud_over_box(items, grid: Grid) -> tuple[float, float]:
    """(cloud %, coverage fraction) over the study box, from the Scene Classification layer."""
    scl = mosaic(items, "SCL", grid)[0]
    valid = scl > 0
    coverage = valid.mean()
    cloud_pct = 100 * np.isin(scl[valid], CLOUD_CLASSES).mean() if valid.any() else 100.0
    return float(cloud_pct), float(coverage)


# ---------------------------------------------------------------- matching
def best_scene(nisar_date: date, grid: Grid):
    """Pick the least-cloudy full-coverage day near a NISAR date.

    Returns (s2_date, items, cloud_pct), or (None, None, best_cloud_pct) if nothing usable.
    """
    candidates = []
    for day, items in sorted(scenes_near(nisar_date).items()):
        cloud_pct, coverage = cloud_over_box(items, grid)
        gap = abs((day - nisar_date).days)
        print(f"    {day}  gap {gap} d  cloud {cloud_pct:5.1f} %  coverage {coverage:.0%}  ({len(items)} tiles)")
        if coverage >= MIN_COVERAGE:
            candidates.append((round(cloud_pct / CLOUD_TIE_PCT), gap, day, items, cloud_pct))
    if not candidates:
        return None, None, None
    _, _, day, items, cloud_pct = min(candidates, key=lambda c: c[:2])
    if cloud_pct > MAX_CLOUD_PCT:
        return None, None, cloud_pct
    return day, items, cloud_pct


def save_scene(nisar_date: date, items) -> None:
    """Write the true-colour PNG (10 m) and the B03/B08/B11 GeoTIFF (20 m) for one match."""
    SCENE_DIR.mkdir(parents=True, exist_ok=True)
    rgb_grid = make_grid(SAMBHAR_BBOX, EPSG, TRUE_COLOUR_RES_M)
    rgb = mosaic(items, "visual", rgb_grid)
    plt.imsave(SCENE_DIR / f"{nisar_date}_truecolour.png", np.moveaxis(rgb, 0, -1))

    grid = make_grid(SAMBHAR_BBOX, EPSG, BANDS_RES_M)
    # B03/B08 are 10 m: average them down to 20 m; B11 is already 20 m.
    stack = np.concatenate([mosaic(items, b, grid, Resampling.average) for b in BANDS])
    profile = dict(driver="GTiff", dtype="uint16", count=len(BANDS), width=grid.shape[1],
                   height=grid.shape[0], crs=f"EPSG:{EPSG}", transform=transform_of(grid),
                   nodata=0, compress="deflate")
    with rasterio.open(SCENE_DIR / f"{nisar_date}_B03_B08_B11.tif", "w", **profile) as dst:
        dst.write(stack)
        dst.descriptions = tuple(BANDS)
        dst.update_tags(s2_items=" ".join(i.id for i in items), nisar_date=str(nisar_date),
                        reflectance=f"(DN + {BOA_OFFSET}) / 10000")


def update_matches(rows: list[dict]) -> None:
    """Merge rows into sentinel2_matches.csv (one row per NISAR date, re-runs overwrite)."""
    existing = {}
    if MATCHES_CSV.exists():
        with open(MATCHES_CSV) as f:
            existing = {r["nisar_date"]: r for r in csv.DictReader(f)}
    existing.update({r["nisar_date"]: r for r in rows})
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(MATCHES_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MATCH_FIELDS)
        writer.writeheader()
        writer.writerows(sorted(existing.values(), key=lambda r: r["nisar_date"]))


def match_dates(nisar_dates: list[date]) -> None:
    """Find, save and record the best Sentinel-2 scene for each NISAR date.

    Skipped dates are recorded with an empty s2_date and the best cloud % found (if any).
    """
    grid = make_grid(SAMBHAR_BBOX, EPSG, BANDS_RES_M)
    for nisar_date in nisar_dates:
        print(f"NISAR {nisar_date}:")
        s2_date, items, cloud_pct = best_scene(nisar_date, grid)
        cloud = "" if cloud_pct is None else f"{cloud_pct:.1f}"
        if s2_date is None:
            print(f"  -> skipped (best cloud {cloud or 'n/a'} %)")
            row = dict(nisar_date=nisar_date, s2_date="", gap_days="", cloud_pct=cloud)
        else:
            gap = (s2_date - nisar_date).days
            print(f"  -> {s2_date} (gap {gap:+d} d, cloud {cloud} %)")
            save_scene(nisar_date, items)
            row = dict(nisar_date=nisar_date, s2_date=s2_date, gap_days=gap, cloud_pct=cloud)
        update_matches([{k: str(v) for k, v in row.items()}])


# ---------------------------------------------------------------- validation points
def read_bands(nisar_date: date):
    """Saved B03/B08/B11 as surface reflectance (NaN = no data), plus the grid transform."""
    with rasterio.open(SCENE_DIR / f"{nisar_date}_B03_B08_B11.tif") as src:
        dn = src.read().astype(np.float32)
        transform = src.transform
    dn[dn == 0] = np.nan
    return (dn + BOA_OFFSET) / 10000, transform


def mndwi(b03: np.ndarray, b11: np.ndarray) -> np.ndarray:
    """Modified NDWI (green vs SWIR). Positive often means water, BUT bright salt crust can score
    positive too, so this is only a second opinion, never ground truth."""
    with np.errstate(invalid="ignore", divide="ignore"):
        return (b03 - b11) / (b03 + b11)


def sampling_area(index: np.ndarray, pixel_m: float) -> np.ndarray:
    """Lake bed + LAKE_BUFFER_M: the largest MNDWI>0 blob, filled, then grown by the buffer.

    MNDWI flags both water and salt crust, which is exactly the lake bed we want to sample.
    This only decides *where* points go; it never labels them.
    """
    blobs, n = ndimage.label(index > 0)
    if n == 0:
        raise SystemExit("No MNDWI>0 area found: cannot outline the lake on this scene.")
    sizes = ndimage.sum(np.ones_like(blobs), blobs, range(1, n + 1))
    lake = ndimage.binary_fill_holes(blobs == 1 + int(np.argmax(sizes)))
    return ndimage.distance_transform_edt(~lake) * pixel_m <= LAKE_BUFFER_M


def make_points(nisar_date: date, rng: np.random.Generator) -> None:
    """Draw random points over lake + buffer, write the CSVs and the numbered helper image."""
    (b03, _, b11), transform = read_bands(nisar_date)
    index = mndwi(b03, b11)
    area = sampling_area(np.nan_to_num(index, nan=-1), BANDS_RES_M) & np.isfinite(index)

    rows, cols = np.nonzero(area)
    pick = rng.choice(rows.size, N_POINTS, replace=False)
    # Random position inside each chosen 20 m pixel, so points are continuous, not on a lattice.
    r = rows[pick] + rng.random(N_POINTS)
    c = cols[pick] + rng.random(N_POINTS)
    xs, ys = rasterio.transform.xy(transform, r, c, offset="ul")
    lons, lats = Transformer.from_crs(f"EPSG:{EPSG}", "EPSG:4326", always_xy=True).transform(xs, ys)

    stem = OUT_DIR / f"points_{nisar_date}"
    with open(f"{stem}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "lon", "lat", "date", "label"])
        w.writerows([i + 1, f"{lon:.6f}", f"{lat:.6f}", nisar_date, ""]
                    for i, (lon, lat) in enumerate(zip(lons, lats)))
    with open(f"{stem}_mndwi.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "mndwi"])
        w.writerows([i + 1, f"{index[int(ri), int(ci)]:.3f}"] for i, (ri, ci) in enumerate(zip(r, c)))
    numbered_image(nisar_date, xs, ys, f"{stem}_numbered.png")
    print(f"{nisar_date}: {N_POINTS} points -> {stem}.csv")


def numbered_image(nisar_date: date, xs, ys, path: str) -> None:
    """True colour at native 10 m with each point circled and numbered (zoom in to label)."""
    rgb = plt.imread(SCENE_DIR / f"{nisar_date}_truecolour.png")
    g = make_grid(SAMBHAR_BBOX, EPSG, TRUE_COLOUR_RES_M)
    col = (np.asarray(xs) - (g.x[0] - g.resolution_m / 2)) / g.resolution_m
    row = ((g.y[0] + g.resolution_m / 2) - np.asarray(ys)) / g.resolution_m
    h, w = rgb.shape[:2]
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(rgb)
    ax.scatter(col, row, s=160, facecolors="none", edgecolors="red", linewidths=1.5)
    for i, (cx, ry) in enumerate(zip(col, row)):
        ax.text(cx + 10, ry - 10, str(i + 1), color="yellow", fontsize=14, weight="bold",
                bbox=dict(facecolor="black", alpha=0.6, pad=1, linewidth=0))
    ax.set_title(f"Validation points, NISAR {nisar_date}: label water / salt_crust / land", fontsize=20)
    ax.axis("off")
    fig.savefig(path, dpi=100)
    plt.close(fig)


# ---------------------------------------------------------------- main
def main(args: list[str]) -> None:
    if args and args[0] == "points":
        rng = np.random.default_rng(RANDOM_SEED)
        for d in args[1:]:
            make_points(date.fromisoformat(d), rng)
        return
    if args == ["all"]:
        dates = [date.fromisoformat(str(g.date)) for g in load_granules()]
    else:
        dates = [date.fromisoformat(d) for d in args]
    if not dates:
        raise SystemExit(__doc__)
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY=4,
                      GDAL_HTTP_RETRY_DELAY=2):
        match_dates(dates)


if __name__ == "__main__":
    main(sys.argv[1:])
