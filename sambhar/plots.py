"""Figures: quick-looks for checking data, and images for the web app."""
import matplotlib
matplotlib.use("Agg")  # draw to files, no window needed
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm
from matplotlib.patches import Patch


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


def rule_comparison(dates, hh_only_km2, combined_km2, area_label, path):
    """Detected area per date with HH alone vs HH + coherence. The gap is what coherence removed."""
    fig, ax = plt.subplots(figsize=(10, 4.5))
    days = np.array(dates, dtype="datetime64[D]")
    ax.plot(days, hh_only_km2, "o--", color="#8a959b", label="HH only: dark")
    ax.plot(days, combined_km2, "o-", color="#1f6fb2", label="HH + coherence: dark and unstable")
    ax.fill_between(days, combined_km2, hh_only_km2, color="#e8a33d", alpha=0.3,
                    label="removed by coherence (dark but stable)")
    ax.set_ylabel(f"area {area_label} (km²)")
    ax.set_ylim(bottom=0)
    ax.set_title("How much 'dark' area coherence removes")
    ax.legend(loc="upper left")
    fig.autofmt_xdate()
    _save(fig, path)


# Slide figures: large text, no top/right frame, few colours.
SLIDE_STYLE = {"font.size": 17, "axes.titlesize": 21, "axes.labelsize": 18, "legend.fontsize": 14,
               "axes.spines.top": False, "axes.spines.right": False}
DETECTED_COLOUR = "#1f6fb2"
REMOVED_COLOUR = "#e8a33d"
OTHER_MODE_COLOUR = "#7a7a7a"


def slide_area_over_time(main, other_mode, path):
    """Area per date: main series with its threshold range, HH-only dashed, other-mode dates as points.

    `main` has lists dates, km2, km2_min, km2_max, hh_only_km2 (NaN breaks the line at long gaps);
    `other_mode` has lists dates, km2, km2_min, km2_max.
    """
    with plt.rc_context(SLIDE_STYLE):
        fig, ax = plt.subplots(figsize=(13, 6.5))
        days = np.array(main["dates"], dtype="datetime64[D]")
        ax.fill_between(days, main["km2_min"], main["km2_max"], color=DETECTED_COLOUR, alpha=0.18,
                        label="range over 12 threshold choices")
        ax.plot(days, main["hh_only_km2"], "o--", color=REMOVED_COLOUR, linewidth=2.5, markersize=5,
                label="radar brightness only (HH)")
        main_km2 = np.array(main["km2"])
        ax.errorbar(days, main_km2, yerr=[main_km2 - np.array(main["km2_min"]), np.array(main["km2_max"]) - main_km2],
                    fmt="none", ecolor=DETECTED_COLOUR, alpha=0.5, linewidth=1.5)
        ax.plot(days, main["km2"], "o-", color=DETECTED_COLOUR, linewidth=3, markersize=8,
                label="brightness + coherence (dual-pol dates)")
        other_days = np.array(other_mode["dates"], dtype="datetime64[D]")
        other = np.array(other_mode["km2"])
        ax.errorbar(other_days, other, yerr=[other - np.array(other_mode["km2_min"]),
                                             np.array(other_mode["km2_max"]) - other],
                    fmt="s", color=OTHER_MODE_COLOUR, markerfacecolor="white", markersize=8, capsize=4,
                    label="quad-pol dates (not comparable: ~0.9 dB brighter)")
        last_day, last_km2 = days[-1], main["km2"][-1]
        ax.annotate("14 Oct: lowest in\n10 of 12 threshold choices", xy=(last_day, last_km2),
                    xytext=(last_day - np.timedelta64(75, "D"), 25), fontsize=15,
                    arrowprops={"arrowstyle": "->", "color": "black"})
        ax.set_ylim(0, 150)
        ax.set_ylabel("km² inside lake outline")
        ax.set_title("Dark unstable surface (water or wet brine), Sambhar Lake")
        ax.legend(loc="lower left", frameon=False)
        fig.autofmt_xdate()
        _save(fig, path)


def slide_comparison(hh_db, coherence, detected, hh_dark, lake, title, path):
    """HH image, coherence image and the result side by side, with the lake outline.

    In the result, blue = dark and unstable (detected); orange = dark but stable (removed by coherence).
    """
    with plt.rc_context(SLIDE_STYLE):
        fig, axes = plt.subplots(1, 3, figsize=(19, 6.5))
        panels = [(hh_db, "gray", -30, 0, "1. Radar brightness (HH, dB)\ndark = smooth surface"),
                  (coherence, "magma", 0, 1, "2. 12-day coherence\ndark = surface changed")]
        for ax, (data, cmap, vmin, vmax, panel_title) in zip(axes, panels):
            shown = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax)
            plt.colorbar(shown, ax=ax, fraction=0.035)
            ax.set_title(panel_title)

        result = np.full(hh_db.shape + (3,), 0.93)
        result[hh_dark & ~detected] = matplotlib.colors.to_rgb(REMOVED_COLOUR)
        result[detected] = matplotlib.colors.to_rgb(DETECTED_COLOUR)
        axes[2].imshow(result)
        axes[2].set_title("3. Result\ndark AND changed = detected")
        axes[2].legend(handles=[Patch(color=DETECTED_COLOUR, label="detected: water or wet brine"),
                                Patch(color=REMOVED_COLOUR, label="dark but stable: removed")],
                       loc="lower left", fontsize=13, framealpha=0.9)
        for ax in axes:
            ax.contour(lake, levels=[0.5], colors="#2bb3c0", linewidths=1.5)
            ax.set_xticks([]); ax.set_yticks([])
        fig.suptitle(title, fontsize=23)
        _save(fig, path)


def slide_frequency_map(frequency, lake, n_dates_text, path):
    """Water-detection frequency with the lake outline."""
    with plt.rc_context(SLIDE_STYLE):
        fig, ax = plt.subplots(figsize=(12, 7.5))
        shown = ax.imshow(frequency, cmap="Blues", vmin=0, vmax=1)
        ax.contour(lake, levels=[0.5], colors="#d1495b", linewidths=2)
        colour_bar = plt.colorbar(shown, ax=ax, fraction=0.035)
        colour_bar.set_label("detections ÷ valid observations")
        ax.set_title(f"Water-detection frequency\n{n_dates_text}")
        ax.text(0.01, 0.02, "red line: lake outline", transform=ax.transAxes, fontsize=14, color="#d1495b")
        ax.set_xticks([]); ax.set_yticks([])
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
