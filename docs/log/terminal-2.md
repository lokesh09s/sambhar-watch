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

### 18:23 IST - Website and demo data prepared for the provisional coherence rule
- What:
  - scripts/make_demo_data.py: new fake surface "smooth dry crust" on the exposed lake bed in Mar-Jun (about -21 dB: dark but stable).
    Fake 12-day coherence for each of the 19 pairs in data/gunw_pairs.csv (0.15 +- 0.06 where water, brine or wet crust on either date,
    0.7 +- 0.1 elsewhere), saved as outputs/demo/coherence/<ref>_<sec>.npz in the same format as outputs/coherence/.
    It then applies HH < T AND coherence < C (demo C = 0.35) itself, because map_water.py has no coherence rule yet (marked "shortcut").
    Writes overlays/ (final rule), overlays_hh_only/ (map_water.py output), water_area.csv with coherence_pairs, map_info.json with coherence_threshold.
  - scripts/export_web.py: makes comparison/<date>.png (orange = dark in HH only, removed by coherence) when results has overlays_hh_only/.
  - web/: layer renamed "Dark unstable surface (water or wet brine)"; new layer "Dark but stable (HH only vs HH + coherence)";
    chart and popup wording changed; dates with 1 pair get hollow chart points, a tooltip line and a note by the slider;
    coherence explainer and rule (T and C shown from map_info.json); two limitation bullets updated or added. web/README.md documents the expected files.
- Why: The team set the provisional water rule to HH < T AND coherence < C. HH alone cannot separate water from smooth crust
  (real data: dry May and monsoon August lake bed both about -22 dB HH, see decisions-terminal-1.md).
- Result:
  - Pairs per date (from gunw_pairs.csv): 2025-11-12 has 0 (left out, so 22 dates instead of 23); 2026-01-11, 03-12, 04-05, 07-22, 08-15 and 10-14 have 1; the rest have 2.
  - Demo, Mar-Jun: HH only about 144 km2 versus HH + coherence 49-86 km2. Other months change by less than 0.1 km2. 2026-05-11 comparison layer:
    91.0 km2 orange, which equals 144.2 - 53.2. 2026-03-12 keeps 86 km2 (not 73) because its only pair is with 02-28, when the lake was larger:
    a surface that changed between passes counts as unstable.
  - Failure: the first app.js edit stopped on an assertion. The Write tool had stored "\u00b2" as a literal ² in app.js, so the text did not match.
    No partial write happened (the file is written only at the end). Redone with literal characters; node --check passes.
  - Screenshot at 1200 px checked: new layers, 1-pair label, hollow points, rule text "(here: HH below -18 dB and coherence below 0.35)".
    The orange layer can't be seen on the first date (01-11, 0.1 km2); it was checked through the PNG numbers above.
- Open questions for the processing terminal: how to combine two pairs (demo uses the mean); what to do with 0-pair dates (demo leaves them out);
  map_water.py output names should match the table in web/README.md.
  validate.py still classifies with HH only from the crops, so it does not yet test the new rule.
- Next: once the real rule is in map_water.py, run export_web.py on outputs/results. Update validate.py to the HH + coherence rule.

### 18:23 IST - Checked the website format against the other terminal's new map_water.py (uncommitted)
- What: Read `git diff scripts/map_water.py` and sambhar/config.py (read only, not edited).
- Why: The website must work on real output without changes.
- Result: Their output matches web/README.md: overlays/ (combined rule), overlays_hh_only/, water_area.csv with water_km2,
  water_inside/outside_mapped_pans_km2 and coherence_pairs, map_info.json with threshold_db and coherence_threshold. Dates with no pair are left out, as in the demo.
  Their extra columns (hh_only_water_*, *_in_lake*) and map_info class_name are ignored by the site, which is harmless.
  Real C in config.py is COHERENCE_THRESHOLD = 0.3 (the demo uses 0.35). They added sambhar.coherence.coherence_for_date.
- Next: once their map_water.py is committed, make_demo_data.py can call it directly and drop its own apply_coherence_rule (the "shortcut").
  Not done yet: their code is still changing.

### 18:28 IST - Demo now uses the real map_water.py coherence rule; site uses class_name and rule_comparison.png
- What:
  - scripts/make_demo_data.py: removed my own copy of the rule (apply_coherence_rule, coherence_for_date, demo C = 0.35). It now makes fake crops
    and fake coherence (saved with sambhar.coherence.pair_file), then calls the real map_water.main() once, with thresholds from config.py.
  - scripts/export_web.py: copies rule_comparison.png when present (and removes a stale copy).
  - web/: the label comes from map_info.json class_name (falls back to "water" for old HH-only results). Used in the layer name, legend,
    chart title and axis, popup and hint. Added a link to rule_comparison.png under the chart. web/README.md table updated.
- Why: Terminal 1 said the team rule takes the HIGHER coherence of the two pairs (unstable in both), while my demo averaged them.
  map_water.py now applies the rule itself (commit bc5809b) and writes class_name, overlays_hh_only/ and rule_comparison.png.
- Result: Demo through the real map_water.py: 22 dates (2025-11-12 has no pair and is left out), C = 0.3. Mar-Jun HH only about 144 km2
  versus HH + coherence 48-86 km2; other months 0.3-1.7 km2 lower than HH only (the max rule with noisy fake coherence leaves small specks).
  water_in_lake_* columns are blank (no data/lake.geojson); the page ignores them. Screenshot checked: class_name everywhere, hollow
  1-pair points, rule figure link. node --check OK; pytest tests: 5 passed in 1.49s.
- Next: update validate.py to the HH + coherence rule (it still tests HH only). Run export_web.py on real outputs/results when ready.

### 19:00 IST - Area chart: uncertainty band, radar modes kept apart, labels from map_info.json
- What:
  - web/app.js chart rewritten: shaded min-max band (water_km2_min / water_km2_max) behind each total line; one total line per radar mode
    (SPLIT_MODES = true at the top of app.js); QPDH points are triangles; no line ever joins a DHDH and a QPDH date (also for the pans lines).
    The tooltip shows the mode and range, and the slider label shows "km2 (min-max) · mode". Series names use map_info area_scope and pans_label.
    Removed all one-coherence-pair code (fewPairs, hollow points, notes).
  - web/index.html: your band note text (shown only when the CSV has a range), a radar-mode note, the explainer now says "the pass 12 days later",
    limitations updated (thresholds/band, radar modes), pans legend label from map_info. web/README.md table updated.
  - scripts/make_demo_data.py: briefly added water_km2_min/max from sensitivity.py (add_uncertainty_range), then REMOVED it on finding that
    map_water.py (commit af45043) already writes both columns. Demo again just calls map_water.py.
- Why: Team asked for an uncertainty band and the note. The 18:57 decisions: range over T {-17..-20} x C {0.25..0.35}; the 12-day pair starting
  on each date (coherence_pairs column gone); don't mix QPDH and DHDH until checked.
- Result: Dead end: my sensitivity-based min/max step duplicated map_water.py's new columns and would have overwritten them; it was removed before committing.
  Demo now 19 dates (4 dates with no starting pair left out), areas inside the real data/lake.geojson outline. Demo band is narrow (median about 2 km2)
  because the fake data is clean; the real median range is about 50 km2 (decisions-terminal-1.md 18:57). Screenshot checked: band, 2 mode lines with a gap,
  triangles, notes, legend. node --check OK.
- Next: when the QPDH/DHDH consistency check is done, set SPLIT_MODES as decided. Update validate.py to the HH + coherence rule.

### 19:02 IST - validate.py now tests the current rule (HH + coherence) with HH only next to it
- What: Rewrote scripts/validate.py. For each NISAR date: HH (dB) from the crop, coherence from sambhar.coherence.coherence_for_date
  (the pair STARTING on the date), then classify_dark_unstable(T, C) and classify_water(T) on the same valid pixels, as in map_water.py.
  T, C and dates are read from map_info.json. New --coherence option. validation.csv has hh_db, coherence, result_hh_coherence, result_hh_only.
  The summary has one block per rule, each with the salt-crust and land false-water rates kept separate.
  Rows with an empty label are now skipped and counted, not an error.
- Why: Team request. Validation must test the rule we publish. Also, validation_data/points_*.csv (made by another terminal) have empty labels until they are labelled by hand.
- Result: Demo test, 7 points with known answers: dry smooth crust in May: HH -21.2 dB, coherence 0.775 -> HH only "water" (wrong), HH + coherence "not water" (right).
  Wet crust in Oct: coherence 0.196 -> both "water" (expected: wet brine is counted by the rule). Lake centre and land right in both.
  1 no_data (gap date), 1 too_far_in_time (60 days), 1 unlabelled. Salt crust called water: HH only 100% (2/2), HH + coherence 50% (1/2).
  On the real validation_data/points_2026-05-11.csv: "No labelled points (150 rows without a label)". The file is not labelled yet, so no real result.
  validation_data columns (id, lon, lat, date, label) are compatible; date there is the NISAR date (S2 is 4-5 days earlier, within --max-days 6).
- Next: run on real outputs once the points are labelled: python scripts/validate.py validation_data/points_2026-05-11.csv (and 08-15). Then the website feedback.

### 19:04 IST - Website feedback: on-map demo label, lake outline, real pans, zoom to lake, renamed comparison layer, compact layer box
- What:
  - web/app.js: a "DEMO DATA: synthetic, not NISAR results" label on the map (bottom left, only when map_info demo is true); "Lake outline"
    layer from data/lake.geojson, on by default (yellow #ffd84d); the map zooms to the lake outline (study-box bounds if there is no outline);
    the comparison layer is renamed "Removed by coherence check".
  - web/index.html: legend "Removed by coherence check: dark in HH but stable (likely dry fields or dry crust)"; lake legend item.
  - web/style.css: compact layer box; demo label style; the page-wide 'section { margin }' rule is now 'main > section'.
  - scripts/export_web.py: new --lake option (default data/lake.geojson); copy_outline() handles both pans and lake.
  - scripts/make_demo_data.py: the demo now uses the real data/pans.geojson (7 shapes), not pans_example.geojson; --pans is no longer needed in the commands.
- Why: Team website feedback (the earlier message did not reach this terminal; done from the list in the latest request).
- Result: Screenshot checked: the map opens on the lake outline; real pans dashed; demo label visible on the map; legend wording right.
  Dead end: the first compact-box CSS did nothing. The empty space came from my own 'section { margin: 36px 0 }', which also applied to
  Leaflet's <section class="leaflet-control-layers-list">. Scoping it to 'main > section' fixed it.
  Demo 2026-05-11 with real pans: HH only 114.0 -> HH + coherence 62.5 km2 inside the lake outline (range 59.9-62.9).
- Next: the layer name "Removed by coherence check" was my choice (the feedback did not give one); rename it if the team prefers another.

### 19:17 IST - "Optical vs radar" swipe section and "What this means" box
- What:
  - scripts/export_web.py: export_optical() converts validation_data/sentinel2/*_truecolour.png to web/data/optical/<s2_date>.jpg (quality 80)
    and writes optical/index.json, pairing each with the nearest radar date in map_info dates (null if more than 6 days apart).
  - web/: new section after the chart with date buttons (11 Jan, 6, 11, 16 May, 29 Aug). Swipe: Sentinel-2 true colour on the left;
    on the right the same image in grey with the radar layers (blue = class_name, orange = removed by the coherence check). The caption gives the dates,
    days apart, and DEMO/provisional status. The 11 May headline uses the team's wording, with a "[result to be added]" placeholder and a Provisional tag.
    New "What this means" box (4 provisional recommendations) under "What we found".
- Why: Team request: a feature for judges that shows radar against optical images.
- Result:
  - Alignment checked with real data: the real outputs/results overlays_hh_only/2026-05-11.png laid on the Sentinel-2 2026-05-06 true colour
    (both 1889 x 1442, same 20 m grid). Lake shore, pan dykes and small ponds match pixel for pixel. HH only also flags many dry fields, as known.
  - Contact sheet of the 5 true-colour images confirms the headline: 11 May the lake is white; 6 and 16 May it is green (water).
  - With the current REAL results (DHDH only: 2026-04-05 to 10-14), only the May images have a radar date within 6 days: 11 Jan has none,
    and 29 Aug's nearest is 08-15 (14 days). The page then shows the optical image alone, with a note. With the demo, all 5 have a date.
  - Real 2026-05-11 (for the headline, NOT filled in): water_km2 = 102.9 km2 inside the lake outline (HH only 144.3).
  - web/data/optical is 4.5 MB; web/data total 6.4 MB. Screenshot of the section checked. node --check OK.
- Next: the team fills in the 11 May result sentence; switch web/data to real results (python scripts/export_web.py) when the team says so.
