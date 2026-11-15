"""A fixed map grid over Sambhar, so every date lines up pixel for pixel."""
from dataclasses import dataclass

import h5py
import numpy as np
from pyproj import Transformer


@dataclass
class Grid:
    """Pixel-centre coordinates (metres) of the study-area grid in a given projection."""
    x: np.ndarray        # west -> east
    y: np.ndarray        # north -> south
    epsg: int
    resolution_m: float

    @property
    def shape(self) -> tuple[int, int]:
        return (self.y.size, self.x.size)

    @property
    def pixel_area_km2(self) -> float:
        return self.resolution_m ** 2 / 1e6

    def bounds_latlon(self) -> list[list[float]]:
        """[[south, west], [north, east]] corners, the format Leaflet uses for image overlays."""
        to_latlon = Transformer.from_crs(f"EPSG:{self.epsg}", "EPSG:4326", always_xy=True)
        half = self.resolution_m / 2
        xs = [self.x[0] - half, self.x[-1] + half] * 2
        ys = [self.y[0] + half] * 2 + [self.y[-1] - half] * 2
        lons, lats = to_latlon.transform(xs, ys)
        return [[min(lats), min(lons)], [max(lats), max(lons)]]


def make_grid(bbox_lonlat: tuple, epsg: int, resolution_m: float) -> Grid:
    """Build a grid covering a lon/lat box, in the same projection as the NISAR file."""
    to_map = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    lon_min, lat_min, lon_max, lat_max = bbox_lonlat
    xs, ys = to_map.transform([lon_min, lon_max, lon_min, lon_max], [lat_min, lat_min, lat_max, lat_max])

    snap = lambda v, rounding: rounding(v / resolution_m) * resolution_m
    x_min, x_max = snap(min(xs), np.floor), snap(max(xs), np.ceil)
    y_min, y_max = snap(min(ys), np.floor), snap(max(ys), np.ceil)

    x = np.arange(x_min + resolution_m / 2, x_max, resolution_m)
    y = np.arange(y_max - resolution_m / 2, y_min, -resolution_m)
    return Grid(x=x, y=y, epsg=epsg, resolution_m=resolution_m)


def box_mask(grid: Grid, bbox_lonlat: tuple) -> np.ndarray:
    """Boolean map: True for pixels inside a lon/lat box (lon_min, lat_min, lon_max, lat_max)."""
    to_map = Transformer.from_crs("EPSG:4326", f"EPSG:{grid.epsg}", always_xy=True)
    lon_min, lat_min, lon_max, lat_max = bbox_lonlat
    xs, ys = to_map.transform([lon_min, lon_max, lon_min, lon_max], [lat_min, lat_min, lat_max, lat_max])
    in_x = (grid.x >= min(xs)) & (grid.x <= max(xs))
    in_y = (grid.y >= min(ys)) & (grid.y <= max(ys))
    return np.outer(in_y, in_x)


def _nearest_index(source: np.ndarray, targets: np.ndarray) -> np.ndarray:
    """For each target coordinate, the index of the nearest source pixel (-1 if outside)."""
    step = source[1] - source[0]
    index = np.rint((targets - source[0]) / step).astype(np.int64)
    index[(index < 0) | (index >= source.size)] = -1
    return index


def sample_onto_grid(image: h5py.Dataset, image_x: np.ndarray, image_y: np.ndarray,
                     grid: Grid) -> np.ndarray:
    """Read only the part of `image` under the grid and resample it (nearest neighbour).

    Pixels outside the image are NaN.
    """
    cols = _nearest_index(image_x, grid.x)
    rows = _nearest_index(image_y, grid.y)
    has_col, has_row = cols >= 0, rows >= 0
    result = np.full(grid.shape, np.nan, dtype=np.float32)
    if not (has_col.any() and has_row.any()):
        return result

    # Read one rectangular window: this is the only large read from the file.
    r0, r1 = rows[has_row].min(), rows[has_row].max() + 1
    c0, c1 = cols[has_col].min(), cols[has_col].max() + 1
    window = image[r0:r1, c0:c1].astype(np.float32)

    result[np.ix_(has_row, has_col)] = window[np.ix_(rows[has_row] - r0, cols[has_col] - c0)]
    return result
