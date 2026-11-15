"""Download the JRC Global Surface Water "occurrence" layer over Sambhar (long-term context).

Occurrence = % of valid Landsat observations, 1984-2021, in which a pixel was water
(Pekel et al. 2016, Nature; dataset v1.4). It shows how often each place has historically had
water: it is context, not ground truth for any single NISAR date.

    python scripts/fetch_jrc.py

Outputs (in validation_data/):
    jrc_occurrence.tif   occurrence %, 0-100 (255 = no data), cropped to the study box, native ~30 m
    jrc_occurrence.png   the same as a map
    jrc_lake_occurrence.png   occurrence inside data/lake.geojson with the 50 % and 90 % contours
    (and printed: share of the lake outline that had water in >50 % and >90 % of observations)
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.windows import from_bounds

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sambhar.config import ROOT, SAMBHAR_BBOX  # noqa: E402
from sambhar.grid import make_grid  # noqa: E402
from sambhar.pans import pans_mask  # noqa: E402

# ---------------------------------------------------------------- settings
# 10x10 degree tiles named by their north-west corner; 70E_30N covers 70-80 E, 20-30 N.
JRC_URL = ("https://storage.googleapis.com/global-surface-water/downloads2021/occurrence/"
           "occurrence_70E_30Nv1_4_2021.tif")
NODATA = 255
OUT_DIR = ROOT / "validation_data"
OUT_TIF = OUT_DIR / "jrc_occurrence.tif"
OUT_PNG = OUT_DIR / "jrc_occurrence.png"
LAKE_GEOJSON = ROOT / "data" / "lake.geojson"
LAKE_PNG = OUT_DIR / "jrc_lake_occurrence.png"
THRESHOLDS = [50, 90]            # report the share of the lake wet more often than these %
JRC_PIXEL_DEG = 0.00025          # JRC grid spacing (~25 x 28 m here)


def download_crop() -> None:
    """Read only the study-box window of the remote tile (no full 54 MB download) and save it."""
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY=4):
        with rasterio.open(f"/vsicurl/{JRC_URL}") as src:
            window = from_bounds(*SAMBHAR_BBOX, src.transform).round_offsets().round_lengths()
            data = src.read(1, window=window)
            profile = src.profile | dict(width=data.shape[1], height=data.shape[0],
                                         transform=src.window_transform(window), nodata=NODATA,
                                         compress="deflate", tiled=False)
    profile.pop("blockxsize", None), profile.pop("blockysize", None)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with rasterio.open(OUT_TIF, "w", **profile) as dst:
        dst.write(data, 1)
        dst.update_tags(source=JRC_URL, units="percent of observations with water, 1984-2021")
    print(f"saved {OUT_TIF} {data.shape}, max occurrence {data[data != NODATA].max()} %")


def plot() -> None:
    """Map of occurrence: never-water pixels grey, then light to dark blue from rare to permanent."""
    with rasterio.open(OUT_TIF) as src:
        data = src.read(1).astype(float)
        b = src.bounds
    data[data == NODATA] = np.nan
    shown = np.where(data > 0, data, np.nan)
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.imshow(np.where(data == 0, 1, np.nan), cmap="Greys", vmin=0, vmax=5,
              extent=(b.left, b.right, b.bottom, b.top))
    im = ax.imshow(shown, cmap="Blues", vmin=0, vmax=100, extent=(b.left, b.right, b.bottom, b.top))
    fig.colorbar(im, ax=ax, shrink=0.7, label="water occurrence 1984-2021 (% of observations)")
    ax.set_title("JRC Global Surface Water occurrence, Sambhar Salt Lake")
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {OUT_PNG}")


def lake_stats() -> None:
    """Print how much of the team's lake outline had water in >50 % and >90 % of observations,
    and save a map of occurrence inside the outline with those two contours."""
    with rasterio.open(OUT_TIF) as src:
        occ = src.read(1).astype(float)
        b = src.bounds
    # The JRC crop is a lon/lat grid; the project grid helper gives the same pixel centres.
    grid = make_grid(SAMBHAR_BBOX, 4326, JRC_PIXEL_DEG)
    assert grid.shape == occ.shape, (grid.shape, occ.shape)
    lake = pans_mask(LAKE_GEOJSON, grid)
    valid = lake & (occ != NODATA)
    km2_per_px = (JRC_PIXEL_DEG * 111.32) ** 2 * np.cos(np.radians(grid.y.mean()))
    print(f"lake outline: {lake.sum() * km2_per_px:.0f} km2, {valid.mean() / lake.mean():.1%} with JRC data")
    print(f"  ever water (>0 %): {(occ[valid] > 0).mean():.1%}   median occurrence {np.median(occ[valid]):.0f} %"
          f"   max {occ[valid].max():.0f} %")
    for t in THRESHOLDS:
        share = (occ[valid] > t).mean()
        print(f"  water in >{t} % of observations: {share:.1%} of the lake ({share * valid.sum() * km2_per_px:.1f} km2)")

    occ[~valid] = np.nan
    extent = (b.left, b.right, b.bottom, b.top)
    fig, ax = plt.subplots(figsize=(11, 7))
    im = ax.imshow(occ, cmap="Blues", vmin=0, vmax=100, extent=extent)
    ax.contour(lake, levels=[0.5], colors="black", linewidths=1, extent=extent, origin="upper")
    contours = ax.contour(np.nan_to_num(occ), levels=THRESHOLDS, colors=["orange", "red"],
                          linewidths=1.2, extent=extent, origin="upper")
    ax.clabel(contours, fmt="%d %%", fontsize=8)
    fig.colorbar(im, ax=ax, shrink=0.7, label="water occurrence 1984-2021 (% of observations)")
    ax.set_title("JRC water occurrence inside the lake outline (black); 50 % and 90 % contours")
    ax.set_xlim(*np.array(grid.x)[np.nonzero(lake.any(0))[0][[0, -1]]] + [-0.01, 0.01])
    ax.set_ylim(*np.array(grid.y)[np.nonzero(lake.any(1))[0][[-1, 0]]] + [-0.01, 0.01])
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    fig.savefig(LAKE_PNG, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {LAKE_PNG}")


if __name__ == "__main__":
    if not OUT_TIF.exists():
        download_crop()
        plot()
    lake_stats()
