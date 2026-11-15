# Lab notebook: Terminal 2 (website, demo data, validation)

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

### 18:17 IST - Log moved from terminal-1 to terminal-2
- What: Moved my 18:12 entries from docs/log/terminal-1.md and decisions-terminal-1.md into terminal-2.md and decisions-terminal-2.md, and left a one-line pointer in each terminal-1 file. Commits b9e2b1f (old position) and this one.
- Why: Two sessions had both been told they were "Terminal 1". The docs session (commit fc1d2c3) wrote first. The user confirmed this session is Terminal 2.
- Result: The docs terminal's entries are unchanged; only this terminal's text moved.
  Also seen in their decision log: on real data, dry (May) and monsoon (Aug) lake bed are both about -22 dB HH, so the team is adding NISAR GUNW coherence. The website currently shows HH-threshold water only.
- Next: Keep the website ready for real results; adapt it if the team adopts a coherence-based water rule.

### 18:17 IST - Stop tracking .venv and outputs (no history rewrite)
- What: Created .gitignore (.venv/, outputs/, __pycache__/, .pytest_cache/, *.h5, .netrc). Ran `git rm -r --cached .venv outputs`.
  Commits 12af318 (failed attempt, see below) and d0928ea (the removal).
- Why: The starting commit e2ec1ed (another terminal) tracked the virtualenv and generated outputs, including FAKE demo data. Team asked to stop tracking them without rewriting history.
- Result:
  - FAILED first attempt: I committed with `git commit -- .gitignore .venv outputs`. Naming paths makes git commit them from the
    working tree, which re-added every file that git rm --cached had just removed. 12af318 therefore contains only .gitignore plus the
    current outputs/crop_all.log (the other terminal's crop log, picked up by accident). Its message wrongly says it stopped tracking them.
    Left as it is (no amend, no history rewrite).
  - Second attempt: repeated git rm --cached, checked that nothing outside .venv/ and outputs/ was staged, then committed the index with
    no paths. d0928ea: 12,788 files removed from tracking. `git ls-files .venv outputs` now returns 0. Files are still on disk
    (outputs/crops/*.npz present; .venv/bin/python imports numpy).
  - Still tracked, not touched because the task didn't ask: sambhar/__pycache__/*.pyc and scripts/__pycache__ (now in .gitignore, but files
    that are already tracked stay tracked), and .DS_Store. The old commits still contain .venv and outputs, so clones stay large until history is rewritten.
- Lesson: to commit only some staged changes, check `git diff --cached --name-only` and run plain `git commit`. Don't use `git commit -- <paths>` after git rm --cached.
- Next: Optional: `git rm -r --cached sambhar/__pycache__ scripts/__pycache__ tests/__pycache__ .DS_Store` (team's call).
