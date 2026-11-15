"""Turning radar backscatter into water maps and summary numbers.

Physics in one line: calm water reflects the radar pulse away from the
satellite (like a mirror), so it looks very dark in HH. We therefore call a
pixel "water" when its HH backscatter is below a threshold.

Caveat: smooth salt crust and dry fields can also look dark, so darkness is
combined with 12-day coherence (see coherence.py): water is dark AND unstable.
Both thresholds must be checked against independent evidence (Sentinel-2)
at Sambhar itself.
"""
import numpy as np


def to_decibels(power: np.ndarray) -> np.ndarray:
    """Convert linear backscatter power to dB. Missing or non-positive values become NaN."""
    valid = np.isfinite(power) & (power > 0)
    return np.where(valid, 10.0 * np.log10(np.where(valid, power, 1.0)), np.nan)


def reduce_speckle(image: np.ndarray, window: int = 3) -> np.ndarray:
    """Average each pixel with its neighbours (window x window), ignoring NaNs.

    Radar images are grainy ("speckle"); light averaging makes the water/land
    boundary less noisy. Pixels that were NaN stay NaN.
    """
    if window <= 1:
        return image
    pad = window // 2
    values = np.pad(np.nan_to_num(image), pad)
    counts = np.pad(np.isfinite(image).astype(float), pad)
    total, n = np.zeros(image.shape), np.zeros(image.shape)
    for dy in range(window):
        for dx in range(window):
            total += values[dy:dy + image.shape[0], dx:dx + image.shape[1]]
            n += counts[dy:dy + image.shape[0], dx:dx + image.shape[1]]
    smoothed = np.where(n > 0, total / np.maximum(n, 1), np.nan)
    smoothed[~np.isfinite(image)] = np.nan
    return smoothed


def otsu_threshold(values_db: np.ndarray, bins: int = 256) -> float:
    """Threshold that best splits the histogram into two groups (Otsu's method).

    Only a starting suggestion: on a scene with no water it still splits
    something (e.g. land into two halves). Always check it visually.
    """
    v = values_db[np.isfinite(values_db)]
    hist, edges = np.histogram(v, bins=bins)
    p = hist / hist.sum()
    centres = (edges[:-1] + edges[1:]) / 2
    weight_low = np.cumsum(p)
    weight_high = 1 - weight_low
    mean_low = np.cumsum(p * centres) / np.maximum(weight_low, 1e-12)
    mean_high = ((p * centres).sum() - np.cumsum(p * centres)) / np.maximum(weight_high, 1e-12)
    separation = weight_low * weight_high * (mean_low - mean_high) ** 2
    return float(centres[np.argmax(separation)])


def classify_water(hh_db: np.ndarray, threshold_db: float) -> tuple[np.ndarray, np.ndarray]:
    """Return (water, valid) boolean maps. Water = valid pixel darker than the threshold."""
    valid = np.isfinite(hh_db)
    water = valid & (hh_db < threshold_db)
    return water, valid


def classify_dark_unstable(hh_db: np.ndarray, coherence: np.ndarray, threshold_db: float,
                           coherence_threshold: float) -> tuple[np.ndarray, np.ndarray]:
    """Return (detected, valid) maps for the combined rule: dark in HH AND unstable over 12 days.

    Low coherence means the surface changed between passes, as water and wet brine do.
    Dark but stable surfaces (smooth dry crust, dry fields) keep high coherence and are left out.
    A pixel is valid only where both HH and coherence exist.
    """
    valid = np.isfinite(hh_db) & np.isfinite(coherence)
    detected = valid & (hh_db < threshold_db) & (coherence < coherence_threshold)
    return detected, valid


def detection_frequency(water_stack: np.ndarray, valid_stack: np.ndarray):
    """Fraction of VALID observations in which each pixel was classified as water.

    Dividing by the number of valid observations (not the number of dates)
    matters: 2 detections out of 2 observations is weaker evidence than
    12 out of 12, so the observation count is returned as well.
    """
    n_valid = valid_stack.sum(axis=0)
    n_water = (water_stack & valid_stack).sum(axis=0)
    frequency = np.where(n_valid > 0, n_water / np.maximum(n_valid, 1), np.nan)
    return frequency, n_valid
