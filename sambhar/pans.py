"""Salt-pan polygons drawn by hand (e.g. on geojson.io) turned into a pixel mask.

The pan / non-pan split comes from these polygons, not from the radar.
Pixels outside them are labelled "outside mapped pans": they may still
contain unmapped pans, channels or roads.
"""
import json

import numpy as np
from matplotlib.path import Path
from pyproj import Transformer

from sambhar.grid import Grid


def _polygons(geojson: dict):
    """Yield each polygon (list of rings, lon/lat) from a GeoJSON object."""
    features = geojson["features"] if geojson.get("type") == "FeatureCollection" else [geojson]
    for feature in features:
        geometry = feature.get("geometry", feature)
        if geometry["type"] == "Polygon":
            yield geometry["coordinates"]
        elif geometry["type"] == "MultiPolygon":
            yield from geometry["coordinates"]


def pans_mask(geojson_path, grid: Grid) -> np.ndarray:
    """Boolean map: True where the pixel centre lies inside a mapped salt pan."""
    with open(geojson_path) as f:
        geojson = json.load(f)

    to_map = Transformer.from_crs("EPSG:4326", f"EPSG:{grid.epsg}", always_xy=True)
    gx, gy = np.meshgrid(grid.x, grid.y)
    pixel_centres = np.column_stack([gx.ravel(), gy.ravel()])
    inside_any = np.zeros(gx.size, dtype=bool)

    for outer_ring, *holes in _polygons(geojson):
        inside = _contains(outer_ring, to_map, pixel_centres)
        for hole in holes:
            inside &= ~_contains(hole, to_map, pixel_centres)
        inside_any |= inside
    return inside_any.reshape(grid.shape)


def _contains(ring_lonlat, to_map, points):
    ring = np.asarray(ring_lonlat)
    x, y = to_map.transform(ring[:, 0], ring[:, 1])
    return Path(np.column_stack([x, y])).contains_points(points)
