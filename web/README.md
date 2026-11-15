# Sambhar Watch website

A static page (plain HTML, CSS and JavaScript, no build step) that shows the
pipeline results: a map with a date slider, a water-area chart, and short
explanations. Leaflet and Chart.js load from cdnjs; the basemap is Esri World Imagery.

```
web/
  index.html    page and all text (sections: how radar sees water, what we found, limitations, data and code)
  style.css     layout; one accent colour (teal #0f5c6e)
  app.js        loads data/, draws the map, slider, chart and click popups
  data/         made by scripts/export_web.py, do not edit by hand
```

## Update the data

```bash
python scripts/map_water.py            # writes outputs/results/
python scripts/export_web.py           # copies results into web/data/
```

`export_web.py` copies `water_area.csv`, `map_info.json`, `frequency.png` and
`overlays/<date>.png`, and makes two new files from `frequency.npz`:

- `frequency_overlay.png`: water-detection frequency as a transparent map layer
- `frequency_lookup.json`: frequency and valid-observation count on a coarser grid
  (at most 400 cells on the long side), used when you click the map

The salt pans and lake outline are shown if `data/pans.geojson` and `data/lake.geojson` exist
(or the files given with `--pans` / `--lake`). The map opens zoomed to the lake outline.

### What the site expects from the coherence rule (provisional: HH < T AND coherence < C)

The page works with the plain HH-only results too; these extras switch on the coherence parts.

| In `outputs/results/` | Meaning | Used for |
|---|---|---|
| `overlays/<date>.png` | final rule, HH < T AND coherence < C | "Dark unstable surface (water or wet brine)" layer |
| `overlays_hh_only/<date>.png` | HH < T only, same PNG format, same dates | orange "Dark but stable" comparison layer (`export_web.py` makes `comparison/<date>.png` = HH-only minus final) |
| `water_area.csv` columns `water_km2_min`, `water_km2_max` | range of `water_km2` over reasonable thresholds | shaded band around the total line, range in the tooltip and next to the slider |
| `water_area.csv` column `mode` | DHDH (dual-pol) or QPDH (quad-pol) | each mode its own total line and band; QPDH points are triangles (see `SPLIT_MODES` in `app.js`) |
| `map_info.json` key `coherence_threshold` | the value of C | shown in the explainer next to T (`threshold_db`) |
| `map_info.json` keys `area_scope`, `pans_label` | e.g. "inside lake outline", "salt works and mapped pans" | chart series names, pans layer and legend |
| `map_info.json` key `class_name` | what is mapped, e.g. "dark unstable surface (water or wet brine)" | layer name, legend, chart title and axis, popups (falls back to "water") |
| `rule_comparison.png` | HH only vs HH + coherence area per date | linked under the chart |

`water_area.csv` columns stay `water_*`. Other columns (`hh_only_water_*`, `*_study_box_km2`,
`coherence_pair_end`) are ignored by the page. Blank or missing min/max values just leave the band out.

Robust changes: `ROBUST_DATES` at the top of `app.js` lists dates whose change holds up across threshold
choices (currently 14 Oct, from Terminal 1's sensitivity check); they get a star on the chart and a note.

Radar modes: the mode check found QPDH about 0.9 dB brighter in HH, so the main results are DHDH only. `SPLIT_MODES = true`
at the top of `app.js` draws one total line per mode and never joins points from different modes. If the check
shows the modes agree, set it to `false` to draw a single line.

`make_demo_data.py` makes fake crops and fake coherence, then runs the real `map_water.py`,
so the demo always uses exactly the team's current rule.

### Optical vs radar section

`export_web.py` also turns every `validation_data/sentinel2/<date>_truecolour.png` (from
`scripts/fetch_sentinel2.py`) into `data/optical/<date>.jpg`, and pairs it with the nearest radar
date in the results, if one is within 6 days (`data/optical/index.json`). The Sentinel-2 images are on
the same 20 m grid as the radar, so the page lays the radar layers straight on top, with a swipe slider.
Images with no radar date close enough are shown alone, with a note. The 11 May headline sentence and the
"What this means" box are in `index.html`. Fill in the `[result to be added]` placeholder by hand.

## Demo data (FAKE)

To test the page before real results exist:

```bash
python scripts/make_demo_data.py
python scripts/export_web.py --results outputs/demo/results
```

Demo data lives in `outputs/demo/`, never in `outputs/crops` or `outputs/results`.
Its `map_info.json` has `"demo": true`, which makes the page show a "Demo data" banner.
**Run `export_web.py` on the real results before publishing**, and check the banner is gone.

## View it locally

The page loads files with `fetch`, so it needs a web server (opening `index.html`
directly from disk will not work):

```bash
python -m http.server -d web
```

Then open http://localhost:8000.

## Publish on GitHub Pages

GitHub Pages can serve a branch only from the repository root or from `docs/`, not
from `web/`. Either:

- **Settings → Pages → Source: GitHub Actions**, and use the "Static HTML" workflow
  with `path: web`; or
- copy the folder before pushing: `rm -rf docs && cp -r web docs`, then
  **Settings → Pages → Deploy from branch → /docs**.

Before publishing, replace the placeholder GitHub link in the "Data and code" section
of `index.html` (marked `TODO`), and fill in "What we found".

## Known simplifications

- Overlays are PNGs on the UTM grid, stretched over a latitude/longitude box. Across
  this ~40 km area the misplacement is small. Click lookups use the same box, so
  popups match what is drawn.
- Click lookups use one pixel from each 5 x 5 block (about 100 m), not every 20 m pixel.
