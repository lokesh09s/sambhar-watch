"""Figures: quick-looks for checking data, and images for the web app."""
import matplotlib
matplotlib.use("Agg")  # draw to files, no window needed
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm


def quicklook(hh_db, hv_db, title, path):
    """HH image, HV image and HH histogram side by side, for a visual sanity check."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    _image(axes[0], hh_db, f"HH (dB)  {title}", vmin=-30, vmax=0)
    _image(axes[1], hv_db, "HV (dB)", vmin=-35, vmax=-5)

    values = hh_db[np.isfinite(hh_db)]
    axes[2].hist(values, bins=150, range=(-40, 5), color="#0f5c6e")
    axes[2].set_title("HH histogram: water should form a dark peak on the left")
    axes[2].set_xlabel("HH backscatter (dB)")
    _save(fig, path)


def frequency_map(frequency, n_valid, path):
    """Water-detection frequency next to the number of valid observations per pixel."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    _image(axes[0], frequency, "Water-detection frequency\n(detections / valid observations)",
           cmap="Blues", vmin=0, vmax=1)
    _image(axes[1], n_valid, "Valid observations per pixel", cmap="viridis")
    _save(fig, path)


REGION_COLOURS = ["#e8a33d", "#d1495b", "#66a182", "#2e86ab"]


def coherence_check(hh_db, coherence, regions, title, path):
    """HH image, coherence image, and HH vs coherence for every pixel, with test regions marked.

    `regions` maps a name to a boolean pixel map. Each region's median is a dot on the scatter.
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    _image(axes[0], hh_db, f"HH (dB)  {title}", vmin=-30, vmax=0)
    _image(axes[1], coherence, "12-day coherence", cmap="magma", vmin=0, vmax=1)

    both = np.isfinite(hh_db) & np.isfinite(coherence)
    axes[2].hist2d(hh_db[both], coherence[both], bins=150, range=[[-35, 5], [0, 1]],
                   cmap="Greys", norm=LogNorm())
    for (name, region), colour in zip(regions.items(), REGION_COLOURS):
        for ax in axes[:2]:
            ax.contour(region, levels=[0.5], colors=colour, linewidths=1.2)
        inside = region & both
        axes[2].plot(np.median(hh_db[inside]), np.median(coherence[inside]), "o", color=colour,
                     markersize=10, markeredgecolor="white", label=f"{name} (median)")
    axes[2].set_xlabel("HH backscatter (dB)")
    axes[2].set_ylabel("coherence")
    axes[2].set_title("Every pixel: brightness vs coherence")
    axes[2].legend(loc="upper left")
    _save(fig, path)


def water_overlay(water, path, rgba=(30, 120, 200, 200)):
    """Transparent PNG with water pixels coloured, to lay over a web map."""
    image = np.zeros(water.shape + (4,), dtype=np.uint8)
    image[water] = rgba
    plt.imsave(path, image)


def _image(ax, data, title, cmap="gray", vmin=None, vmax=None):
    shown = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_title(title)
    ax.set_xticks([]); ax.set_yticks([])
    plt.colorbar(shown, ax=ax, fraction=0.035)


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
