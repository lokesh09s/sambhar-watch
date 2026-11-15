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

Salt pans are shown if `data/pans.geojson` exists (or the file given with `--pans`).

## Demo data (FAKE)

To test the page before real results exist:

```bash
python scripts/make_demo_data.py
python scripts/export_web.py --results outputs/demo/results --pans data/pans_example.geojson
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
