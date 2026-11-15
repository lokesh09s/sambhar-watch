# Terminal 1 lab notebook

Role: NISAR data processing. Only Terminal 1 writes to this file. Entries are append-only.

### 18:12 IST - Summary of this session so far (docs only)
- What: This session has only written project docs; no NISAR processing has been run from this terminal yet. Exact times of the earlier steps were not recorded.
  1. Read `README.md`. `sambhar_watch_brief.md` was not found. Checked `requirements.txt`, `data/` and `sambhar/config.py` (bbox, 20 m grid, −18 dB threshold) for facts.
  2. Created `docs/slides_outline.md` (7 slides), `docs/video_script.md` (30 s, on-screen text + music, no people) and `docs/project_page.md` (all page fields), with `[PLACEHOLDERS]` for results.
  3. After the real-data update: rewrote slides 4–5 as test → brightness fails → add coherence → validate, with `[COHERENCE WATER]`, `[COHERENCE CRUST]` and `[RULE]`. Rewrote the project page the same way, added NISAR GUNW to NASA Data, sourced Ramsar 24,000 ha to the Ramsar Sites Information Service, and marked the video as optional.
- Why: The team asked for submission text while other terminals code; the instructions were to write only in `docs/`.
- Result: All three docs exist. Checked `git show HEAD:docs/project_page.md`: the latest versions (with GUNW) are already in commit e2ec1ed ("Starting point…", 18:11 IST, made by someone else). Open items: results placeholders, team names and URLs, video timing not checked, and one unsourced limitation line ("wind, rain or crust changes can also lower coherence") waiting for a team decision.
- Next: Create the decision log, commit only the two log files, then continue with NISAR processing tasks as assigned.
# Lab notebook: Terminal 1

Note: this terminal's work so far has been the website, demo data and validation script.
NISAR processing (crop_lake.py / map_water.py on real data) runs in another terminal.

### 18:12 IST - Summary of session so far (17:59 to 18:12)
- What:
  - Read README.md, sambhar/, scripts/, tests/test_pipeline.py. Did not edit sambhar/, crop_lake.py, map_water.py or config.py.
  - Created scripts/make_demo_data.py: 23 FAKE dates (the provisional dates in granules.csv) made with make_fake_gcov,
    then run through the real crop_lake.process (same as --local) and map_water.main. Paints a lake that changes size
    with the season, example pans (data/pans_example.geojson) holding brine Nov-Jun, a wet-salt-crust ring Oct-Jan
    (about -19 dB) and a data gap in the east on 2026-02-16. Tags map_info.json with "demo": true, writes outputs/demo/README.txt.
  - Created scripts/export_web.py: copies water_area.csv, map_info.json, frequency.png, overlays/ into web/data/;
    makes frequency_overlay.png (Blues, transparent where 0 or no data) and frequency_lookup.json (every 5th pixel).
  - Created web/index.html, style.css, app.js, README.md: Leaflet + Chart.js from cdnjs, Esri imagery basemap,
    date slider, 3 toggle layers, 3-line area chart (click a point to set the date), click popup with frequency and
    valid-observation count, demo banner, text sections (how radar sees water, what we found placeholder,
    limitations, data and code).
  - Created scripts/validate.py and data/validation_points_TEMPLATE.csv.
- Why: give the team a working website and validation step before real results are ready.
- Result:
  - make_demo_data.py ran in 40 s. Demo water area: 148.5 km2 (2025-11-12) down to 40.7 km2 (Jul) and back up to 145.9 km2 (Oct).
    The gap date has 591 km2 valid area, versus 1089.6 km2 on the other dates. Grid is 1442 x 1889, the same as the real crops.
  - Checked that outputs/crops/2026-08-15.npz is real, not demo: created before my run, HH median -12.7 dB vs -10.7 dB for the fake.
  - export_web.py: web/data is 1.1 MB in total; lookup grid 288 x 378, step 5.
  - Click lookup checked with node on known spots: lake centre 100% (23/23), pans 64% (14/22, as designed:
    15 brine dates minus the gap date), land 0% (0/23), outside the box "Outside the study area".
  - Screenshots (headless Chrome) at 1200 px and 500 px look right. A 390 px screenshot was clipped, but that was
    headless Chrome's minimum window width (about 500 px), not the page. Fixed: an empty Leaflet base-layer box
    (hidden with CSS); map height on phones changed from 62vh to 55vh.
  - validate.py on 9 hand-placed demo points with known answers: confusion matrix as expected,
    accuracy 85.7% (6/7), water precision 75% (3/4), recall 100% (3/3), salt crust called water 50% (1/2:
    wet crust in Nov wrongly called water, dry crust in Apr correctly not water), 1 no_data (gap date),
    1 too_far_in_time (22 days). An invalid label ('flood') is rejected with its line number.
  - pytest tests/: 2 passed.
  - Found: the 18:11 "Starting point" commit (not made by this terminal) includes .venv/ (12,707 files),
    outputs/ and outputs/demo/. Left it as it is: rewriting shared history while other terminals are working is risky.
- Next: run export_web.py on real outputs/results when the other terminal finishes; replace the GitHub link TODO
  in index.html; fill in "What we found"; label Sentinel-2 points for validate.py.
