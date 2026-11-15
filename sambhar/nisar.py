"""Reading NISAR GCOV (geocoded backscatter) files.

A GCOV file stores backscatter on a map grid. We need four things from it:
the HH and HV images, the x/y map coordinates of the grid, and the map
projection (EPSG code). Dataset paths are searched for rather than hard-coded,
so small differences between product versions do not break the code.
"""
import h5py
import numpy as np


def print_structure(h5: h5py.File, limit: int = 400) -> None:
    """Print every group and dataset in the file (useful the first time)."""
    lines = []

    def visit(name, obj):
        if len(lines) < limit:
            if isinstance(obj, h5py.Dataset):
                lines.append(f"  {name}  shape={obj.shape}  dtype={obj.dtype}")
            else:
                lines.append(f"[{name}]")

    h5.visititems(visit)
    print("\n".join(lines))


def find_datasets(h5: h5py.File, name_ending: str) -> list[str]:
    """Paths of all datasets whose path ends with `name_ending`."""
    found = []
    h5.visititems(lambda path, obj: found.append(path)
                  if isinstance(obj, h5py.Dataset) and path.endswith(name_ending) else None)
    return found


def backscatter_group(h5: h5py.File) -> h5py.Group:
    """The group holding the main-band images (expected: .../GCOV/grids/frequencyA)."""
    hh_paths = find_datasets(h5, "HHHH")
    main_band = [p for p in hh_paths if "frequencyA" in p] or hh_paths
    if not main_band:
        raise RuntimeError("No HHHH image found. Run with --show-structure to inspect the file.")
    return h5[main_band[0].rsplit("/", 1)[0]]


def epsg_code(group: h5py.Group) -> int:
    """EPSG code of the map projection, read from the 'projection' dataset."""
    for obj in (group.get("projection"), group):
        if obj is None:
            continue
        for key, value in obj.attrs.items():
            if "epsg" in key.lower():
                return int(np.ravel(value)[0])
    raise RuntimeError("No EPSG code found. Run with --show-structure and look for 'projection'.")


def describe(group: h5py.Group) -> dict:
    """Short summary for the log: projection, pixel spacing, grid size, image attributes."""
    x, y = group["xCoordinates"], group["yCoordinates"]
    attrs = {k: (v.decode() if isinstance(v, bytes) else v) for k, v in group["HHHH"].attrs.items()}
    return {
        "epsg": epsg_code(group),
        "pixel_spacing_m": (float(x[1] - x[0]), float(y[1] - y[0])),
        "grid_size": (y.shape[0], x.shape[0]),
        "HHHH_attributes": attrs,
    }
