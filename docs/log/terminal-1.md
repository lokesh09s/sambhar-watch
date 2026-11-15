# Terminal 1 lab notebook

Role: NISAR data processing. Only Terminal 1 writes to this file. Entries are append-only.

- 18:12 IST: Terminal 2's entries were appended here by mistake (both sessions had been told they were Terminal 1). They were moved to docs/log/terminal-2.md.
- 18:17 IST: Terminal 4's entries were logged here by mistake (that session was wrongly told it was Terminal 1). They were moved to docs/log/terminal-4.md.

### 18:21 IST - Summary of this session so far (17:49-18:21)
- What:
  - 17:49 Read README and all code. System Python is 3.9.6; code uses `str | None` hints (needs 3.10+). Created `.venv` with Homebrew Python 3.12 and installed requirements.txt. README "Run it" now says Python 3.10+ and shows the venv command.
  - 17:51 `python tests/test_pipeline.py` and `pytest tests/`: 2/2 passed (synthetic 113 km2 lake recovered within 3%).
  - 17:52 No Earthdata login on this machine; the user saved one to ~/.netrc (interactive, done by the user).
  - 17:55 `python scripts/crop_lake.py 2026-05-11 --show-structure` worked first time on the real file (2.6 min, no code fixes). Layout saved to outputs/structure_2026-05-11.log.
  - 17:58 Read calibration metadata from the file (one-off script in scratchpad, not in repo).
  - 18:00 `python scripts/crop_lake.py 2026-08-15` (monsoon) worked. Compared quick-looks and region medians.
  - 18:05 Added the GCOV `mask` layer to cropping (sambhar/config.py INVALID_MASK_VALUES, scripts/crop_lake.py), extended the synthetic test with a masked strip. Deleted the 2 unmasked crops and re-cropped.
  - 18:06 First bulk crop launch was wrong: `crop_lake.py 2026-05-11 2026-08-15 all` treats "all" as a date, so only 2 dates would run. Stopped it and relaunched as two runs (priority dates, then `all`), log in outputs/crop_all.log.
  - 18:07 Searched NASA CMR with earthaccess (no new dependency) for NISAR GUNW. Wrote data/gunw_pairs.csv (19 twelve-day pairs, track 34 D, frame 75).
  - 18:08 Dumped GUNW layout (outputs/structure_gunw_2026-05-11.log), read coherence/mask attributes.
  - 18:10 Added sambhar/coherence.py, scripts/check_coherence.py, grid.box_mask(), plots.coherence_check(), granules.GunwPair/load_gunw_pairs(), config CHECK_REGIONS/GUNW_PAIRS_CSV/COHERENCE_DIR, a GUNW mask-decoding test. README: GUNW data row, noise-floor note, new files.
  - 18:11 Ran the dry-season coherence check; moved the "central lake" box east (it included bright land) and re-ran.
  - 18:13 Read the GCOV noise-equivalent backscatter layer over the lake.
  - 18:16 Ran the monsoon coherence check.
- Why: plan steps 1-3, then the user's decision to add coherence because brightness alone cannot separate water from smooth crust.
- Result:
  - GCOV: group science/LSAR/GCOV/grids/frequencyA (HHHH, HVHV, mask, xCoordinates, yCoordinates, projection; coarser frequencyB ignored). EPSG 32643, 10 m spacing, 33912 x 34560 px. Fill: NaN in images; mask 255 = outside swath, 0 = invalid sample. HHHH is gamma0, linear power, RTC applied. Noise correction, Faraday rotation and RFI mitigation NOT applied. productVersion 1.0.11, software 0.25.16.
  - Study grid 1442 x 1889 px at 20 m; bbox covers the whole lake plus nearby ponds. Both crops 100% valid after the mask.
  - HH alone: lake bed dark in both seasons (median -22.7 dB May, -21.2 dB Aug); farmland 3 dB brighter in monsoon. At -18 dB, 36% of the May box vs 19% of the Aug box is "dark".
  - Noise-equivalent backscatter at the lake about -26.8 dB HH (convention unclear, +/-3 dB). Lake HV (-25.8 dB) is at the noise floor: HV is not useful over water.
  - GUNW: wrappedInterferogram/HH/coherenceMagnitude at 20 m, EPSG 32643. No validated GUNW yet. Three non-12-day pairs left out (2025-11-12->2026-01-11, 2026-03-12->04-05, 2026-07-22->08-15).
  - Coherence medians (lake / pans / farmland): May pair 0.19 / 0.32 / 0.59; Aug pair 0.23 / 0.28 / 0.51. Lake low coherence is below what noise alone would cause (~0.5-0.8 for a stable surface at -23 dB), so the lake surface really changed between passes.
  - Dark (HH < -18) area split by coherence <0.3 / 0.3-0.5 / >=0.5: May 144 / 82 / 47 km2 (total 273); Aug 111 / 50 / 11 km2 (total 172).
  - Correction to an earlier statement: at the step-3 checkpoint I said the dark May lake bed was "very likely wet or smooth crust". Coherence does not support that; it looks unstable like water/brine. Sentinel-2 still needed.
  - Tests: 3/3 pass.
- Next: apply the provisional combined rule (HH < -18 dB AND coherence < 0.3), per-date coherence from adjacent pairs, process all 19 pairs after the bulk crop, mixed-mode check, lake-outline areas.

### 18:24 IST - Combined rule (HH + coherence) in map_water.py; bulk coherence started
- What:
  - sambhar/config.py: WATER_THRESHOLD_DB = -18, COHERENCE_THRESHOLD = 0.3, CLASS_NAME = "dark unstable surface (water or wet brine)", with the evidence in a comment; LAKE_GEOJSON = data/lake.geojson.
  - sambhar/coherence.py: pair_file(), coherence_for_date() (pixel-wise HIGHER of the adjacent 12-day pairs via np.fmax, so one missing pair falls back to the other).
  - sambhar/water.py: classify_dark_unstable(). sambhar/plots.py: rule_comparison() (HH-only vs combined area chart).
  - scripts/map_water.py: applies the combined rule; keeps HH-only result on the same valid pixels; new columns coherence_threshold, coherence_pairs, water_in_lake_*, hh_only_water_*; overlays_hh_only/; rule_comparison.png; map_info.json gains coherence_threshold and class_name. Dates with no pair are left out.
  - scripts/check_coherence.py: accepts `all`, prints radar modes of each pair, keeps going after a failure.
  - tests/test_pipeline.py: 2 new tests (higher-pair coherence, dark-but-stable not detected). 5/5 pass.
  - README: method, data table (lake outline), run commands.
  - Background: coherence for all 19 pairs, each started once its first date is cropped (outputs/coherence_all.log).
- Why: team decisions at 18:19 (see decisions log). Kept the existing water_area.csv column names (water_km2, water_inside_mapped_pans_km2, ...) and folder names because web/app.js, scripts/export_web.py and scripts/make_demo_data.py (other terminals) already read them; only added columns. Did not rename pans.pans_mask because make_demo_data.py imports it.
- Result: smoke test on the 3 DHDH dates cropped so far: 2025-11-12 left out (no 12-day pair); 2026-05-11 HH only 272.9 -> combined 144.3 km2; 2026-08-15 171.8 -> 110.6 km2 (1 pair each so far), matching the 18:16 hand calculation.
  - Found: scripts/make_demo_data.py (not mine) averages the two adjacent pairs; the team decision is the higher of the two. Reported to the user, not changed.
- Next: wait for bulk crop (~6/24 done at 18:23) and coherence; run map_water.py --mode DHDH on everything; mixed-mode coherence check.

### 18:50 IST - Lake and pan outlines in; areas now counted inside the lake only
- What:
  - The outlines were saved in the project root (and ~/Downloads), not in data/. Root copies matched the latest Downloads copies (md5); ~/Documents/lake.geojson is an older, different draft (18:42) and was ignored. Moved root lake.geojson and pans.geojson into data/.
  - Sanity check on our 20 m grid: lake 152.1 km2, mapped pans inside lake 49.1 km2, lake outside pans 103.0 km2 (matches the teammate's numbers exactly). Pan shapes outside the lake cover 99.7 km2 (rough rectangles, not used).
  - scripts/map_water.py: all areas now inside the lake outline (whole study box only if no outline). Existing columns keep their names but now mean "inside lake": water_km2 = total in lake, water_inside_mapped_pans_km2 = lake & pans, water_outside_mapped_pans_km2 = lake & not pans; valid_area_km2 also within the lake. Added *_study_box_km2 for context. Removed the water_in_lake_* columns from 18:24 (now redundant). Per-date print shows in/out pans for both rules.
  - config.py: PANS_LABEL = "salt works and mapped pans"; map_info.json gains pans_label and area_scope.
  - README method step 3 updated.
- Why: team instruction: shape 1 covers the eastern salt works (reservoirs + pans); pan shapes outside the lake are rough, so only report pan areas inside the lake. Kept the old column names so web/app.js "Total / Inside / Outside" series stay consistent (total = inside + outside).
- Result: partial run (7 DHDH dates cropped so far), inside lake, km2, HH only -> HH + coherence: 2026-04-05 119.6 -> 101.6; 04-17 132.7 -> 99.5; 04-29 126.7 -> 96.3; 05-11 131.8 -> 93.6; 05-23 130.3 -> 92.2; 08-15 125.3 -> 91.4. Tests 5/5.
  - Note for other terminals: water_km2 changed meaning from "whole study box" to "inside lake outline".
- Next: bulk crop at 12/24 (18:49), slower than estimated (~3 min/date with mask + parallel coherence); full rerun expected ~19:30.

### 19:00 IST - Threshold sensitivity check (scripts/sensitivity.py)
- What: new scripts/sensitivity.py (reuses map_water.select_crops/region_masks/areas); config SENSITIVITY_THRESHOLDS_DB = (-17,-18,-19,-20), SENSITIVITY_COHERENCE = (0.25,0.30,0.35). Ran `--mode DHDH` (7 dates with coherence so far) and `--mode QPDH` (Jan-Mar, reported separately, not mixed). Output outputs/results/sensitivity_<mode>.csv. First version wrote sensitivity.csv for every mode (would overwrite); renamed per mode and deleted the old file.
- Why: team asked whether the seasonal signal survives reasonable threshold choices.
- Result (in-lake km2, DHDH, chosen T=-18/C=0.3 then min-max over 12 threshold pairs):
  04-05 101.6 (45.8-118.1); 04-17 99.5 (65.5-114.4); 04-29 96.3 (61.0-111.3); 05-11 93.6 (66.8-107.5); 05-23 92.2 (65.0-106.4); 06-04 95.7 (62.5-112.2); 08-15 91.3 (51.0-110.5).
  - Threshold-induced range on one date: 41-72 km2 (median 49.7). Difference between dates: 7.3-46.3 km2 depending on thresholds (10.3 at the chosen pair). => The seasonal difference is SMALLER than the threshold-induced range.
  - The order of dates flips: 2026-04-05 is the largest at T=-17/-18 and the smallest at T=-19/-20. The monsoon date 2026-08-15 is never larger than the dry-season dates (rank 1-3 of 7 from the bottom in all 12 pairs).
  - One-pair bias: on 2-pair dates, using a single pair gives 102.5-110.6 km2 vs 92.2-99.5 with the higher of both, i.e. +10-15 km2 (11-14%). One-pair dates (04-05, 08-15, 01-11, 03-12) are biased upward by about the size of the whole between-date difference.
  - QPDH Jan-Mar (separate, consistency with DHDH not yet checked): 01-11 80.5, 01-23 52.7, 02-04 49.4, 02-16 51.7, 02-28 59.9, 03-12 83.7 km2. The two highest (01-11, 03-12) are exactly the one-pair dates. Jan-Mar values are lower than Apr-Aug DHDH, the opposite of "extra water after the monsoon" - could be real, a mode (QPDH vs DHDH) difference, or the method; cannot tell yet.
  - Coverage: with --mode DHDH, 2025-11-12 (no 12-day pair) and all Jan-Mar 2026 (QPDH) are absent; after the monsoon only 2026-10-14 is DHDH.
- Next: report to the team; decision needed on one-pair bias; QPDH vs DHDH consistency check; Sentinel-2 to choose thresholds.

### 18:59 IST - Per-date coherence = pair starting on the date; uncertainty columns
- Correction: the previous entry's heading "19:00 IST" was an estimate; the system clock read 18:55 shortly after, so that work finished at about 18:53.
- What:
  - sambhar/coherence.py: coherence_for_date() now returns the 12-day pair STARTING on the date (coherence, pair), or (None, None). Removed the "higher of both pairs" logic.
  - scripts/map_water.py: column coherence_pairs removed, coherence_pair_end added (second date of the pair used); new columns water_km2_min / water_km2_max = range of in-lake water_km2 over the 12 threshold pairs of config.SENSITIVITY_*; new helper area_range().
  - scripts/sensitivity.py: same pair rule.
  - config.py comment, README method, tests updated (test_date_coherence_uses_pair_starting_on_date). Tests 5/5.
- Why: team decision (option a) after the one-pair bias found at ~18:53; min/max columns so the website and slides can show an uncertainty band.
  - Dropped coherence_pairs (rather than writing a constant 1) because web/app.js draws hollow points when coherence_pairs < 2; without the column it draws normal points.
- Result (partial, DHDH, inside lake, km2, chosen [min-max]): 04-05 101.6 [45.8-118.1]; 04-17 110.3 [83.5-121.0]; 04-29 106.3 [77.3-117.1]; 05-11 102.9 [84.5-112.7]; 05-23 107.8 [84.5-119.1]; 06-04 110.4 [82.6-122.2]; 08-15 91.4 [51.0-110.5].
  - Dates with no starting 12-day pair, now dropped: 2025-11-12, 2026-03-12, 2026-07-22, 2026-10-14, 2026-11-07. So 2026-10-14, the only post-monsoon DHDH date, is lost; after 2026-08-15 the DHDH series has no dates.
- Next: QPDH vs DHDH consistency check (max 20 min).

### 19:08 IST - Radar-mode consistency check, part 1 (scripts/check_modes.py)
- Correction: the previous entry's heading "18:59" was also an estimate; the clock read 18:57 when it was committed. Headings are now stamped from the system clock.
- What: new scripts/check_modes.py; config MODE_CHECK_PAIRS (3 mixed-mode and 4 same-mode neighbouring date pairs) and STABLE_COHERENCE = 0.7. Stable ground = coherence >= 0.7 in every cropped 12-day pair touching either date. Compares median HH and HV change on stable ground, and farmland coherence per pair (mixed vs same mode). To fit the 20-minute limit, started a second crop process for 2026-10-14, 10-02, 09-20 (reverse order, so it does not work on the same date as the bulk run at the same time), then their coherence.
- Why: team decision: check whether QPDH and DHDH agree before mixing; if not, DHDH is the main series.
- Result so far (dB change first->second date, median (25-75%)):
  - MIXED QPDH->DHDH 03-12->04-05 (24 d, stable 98.9 km2): HH -0.43 (-1.4 to +0.5), HV -0.10.
  - same QPDH 02-28->03-12 (12 d, 227.7 km2): HH -0.41, HV -0.87. same DHDH 04-05->04-17 (12 d, 55.0 km2): HH -0.72, HV -0.26. same DHDH 04-05->04-29 (24 d, 36.2 km2): HH -0.30, HV -0.69.
  - => the first mixed pair's HH change (-0.43 dB) is inside the same-mode range (-0.30 to -0.72 dB): no sign of a mode offset there.
  - Farmland coherence: QPDH-QPDH Jan-Mar 0.56-0.71; DHDH-DHDH Apr-May 0.50-0.59, Jun 0.33-0.38; MIXED 08-15->08-27 0.51 (not lower than same-mode pairs in Apr-May; needs 08-27->09-08 for a seasonal neighbour).
- Next: 08-15/08-27 and 10-02/10-14 once 08-27, 10-02, 10-14 are cropped.

### 19:11 IST - Backward-pair fallback; pair_direction and pair_modes columns
- What: sambhar/coherence.py coherence_for_date() returns (coherence, pair, direction): the pair starting on the date ("forward"), else the pair ending on it ("backward"). scripts/map_water.py and scripts/sensitivity.py: column coherence_pair_end replaced by coherence_pair ("<ref> to <sec>"; for backward pairs the end date would just repeat the date), plus pair_direction and pair_modes (e.g. DHDH-QPDH). config.py comment, README, test updated (test now also checks the backward case). Tests 5/5.
- Why: team decision: keep exactly one pair per date but recover dates with no starting pair.
- Result: DHDH dates with results rise from 10 to 12: 2026-07-22 (backward, 07-10 to 07-22, DHDH-DHDH) and 2026-10-14 (backward, 10-02 to 10-14, QPDH-DHDH). 2025-11-12 still has none (its only pair is 60 days). Mixed-mode pairs used by DHDH dates: 08-15 (DHDH-QPDH) and 10-14 (QPDH-DHDH).
  - Note: 07-10 (forward) and 07-22 (backward) use the same pair, so their coherence is identical; only their HH differs.
  - In-lake areas (chosen [range]): 07-22 115.6 [76.9-126.3]; 10-14 55.7 [34.1-71.8], about half of every other DHDH date and based on a mixed-mode pair, so it waits for the mode check.
- Next: finish the mode check once 08-27->09-08 and 09-08->09-20 are cropped.

### 19:12 IST - Speeding up the last crops and pairs (parallel workers)
- What: measured the bottleneck: worker CPU 0-4% while en0 received ~4.2 MB/s across 2 streaming processes => network/latency-bound per connection, not CPU. Remaining: crops 08-27 (bulk run was ~2 min into it), 09-08, 11-07; pairs 08-27->09-08, 09-08->09-20 (09-20->10-02 finished in the earlier parallel job).
  - Stopped the sequential coherence loop (bkrnli6ab; it was only waiting, nothing lost) so it could not take the same pairs as the new workers.
  - Worker 1 (outputs/worker1.log): waits for the bulk run to save 08-27, then kills the bulk run (before it can save anything for 09-08) and runs check_coherence.py 2026-08-27.
  - Worker 2 (outputs/worker2.log): crop_lake.py 2026-09-08, then check_coherence.py 2026-09-08.
  - Worker 3 (outputs/worker3.log): crop_lake.py 2026-11-07.
  - Explicit date lists only (no 'all'), at most 4 streaming processes at once. No code changes.
- Why: user request to speed up; 'all' would have collided with explicit workers on 09-08 and 11-07.
- Result: pending.
- Next: mode check on all mixed pairs once 08-27/09-08 are in.

### 19:13 IST - FAILURE: my worker 1 truncated the 08-27 crop; re-cropping
- What: worker 1 waited for outputs/crops/2026-08-27.npz to exist and then killed the bulk run. np.savez_compressed creates the file when it STARTS writing, so the kill landed mid-save: 08-27.npz was a 436-byte truncated zip ("File is not a zip file"); worker 1's coherence step then failed on it. Deleted the file and started worker 1b (outputs/worker1b.log): crop_lake.py 2026-08-27, then check_coherence.py 2026-08-27.
- Why it matters: crop_lake.py skips dates whose .npz exists, so a truncated file would have been skipped silently on every later run. Should have waited for the "[date] saved" log line, which is printed after the save.
- Risk noted (code not changed, per instruction): any crop interrupted mid-save leaves a file that later runs skip. Before the final run, every crop is test-loaded.
- Result: bulk run ended (exit 143 = killed, as intended). Lost ~3 min for 08-27.

### 19:20 IST - All crops and pairs done; mode check complete; final DHDH run
- What: workers 1b/2/3 finished at 19:18 with no errors: 24/24 crops, 19/19 coherence pairs; every .npz test-loaded OK. config MODE_CHECK_PAIRS gained 09-20 -> 10-02 (same-mode QPDH, post-monsoon yardstick for 10-02 -> 10-14); check_modes.py now also prints each date's median dB on the stable pixels. Ran check_modes.py, map_water.py --mode DHDH, sensitivity.py --mode DHDH and --mode QPDH.
- Why: team decision: the mode check decides between a full-year series and DHDH only.
- Result, mode check (stable ground = coherence >= 0.7; median dB per date, per-pixel change):
  - same mode (5 date pairs): HH change -0.41, -0.72, -0.30, +0.14, -0.10 dB => |change| 0.10-0.72 dB.
  - MIXED: 03-12 -> 04-05 QP->DH HH -11.8 -> -12.3 (-0.43); 08-15 -> 08-27 DH->QP -10.8 -> -9.9 (+0.89); 10-02 -> 10-14 QP->DH -11.1 -> -12.6 (-1.39).
  - All three mixed changes have the sign expected if QPDH HH is brighter than DHDH (mean ~0.9 dB), in three different seasons; two of three exceed the largest same-mode change. => Modes DISAGREE in HH (likely offset ~0.4-1.4 dB, QPDH brighter). HV signs inconsistent (not used).
  - Coherence: farmland coherence of mixed pairs 0.51 (08-15 -> 08-27) and 0.47 (10-02 -> 10-14) is inside the range of neighbouring same-mode pairs (0.39-0.55) => mixed-mode COHERENCE looks fine.
  - Consequence (team rule): DHDH dates are the main series (12 dates, 2026-04-05 .. 2026-10-14); QPDH dates (Jan-Mar, 08-27 .. 10-02) shown separately. DHDH dates 08-15 and 10-14 keep their mixed-mode coherence pairs (HH comes from the DHDH date itself).
- Result, final DHDH in-lake areas (HH+coherence, km2, chosen [min-max]; HH-only in brackets after):
  04-05 101.6 [45.8-118.1] (119.6); 04-17 110.3 [83.5-121.0] (132.7); 04-29 106.3 [77.3-117.1] (126.7); 05-11 102.9 [84.5-112.7] (131.8); 05-23 107.8 [84.5-119.1] (130.3); 06-04 110.4 [82.6-122.2] (129.3); 06-16 88.0 [38.6-111.0] (103.9); 06-28 104.7 [78.9-117.4] (130.4); 07-10 109.9 [64.7-124.2] (122.0); 07-22 115.6 [76.9-126.3] (129.0); 08-15 91.4 [51.0-110.5] (125.3); 10-14 55.7 [34.1-71.8] (115.4).
  - Coherence removes 12-60 km2 per date inside the lake (largest on 10-14: 115.4 -> 55.7).
  - 10-14 is the lowest date in 10 of 12 threshold pairs (30-40 km2 below the next at T=-17/-18). Without 10-14, the Apr-Aug spread is 16-58 km2 and the order of dates changes with the thresholds.
  - Threshold range on one date: median 39.7, max 72.4 km2. Between dates (incl. 10-14): 50-61 km2.
  - QPDH separately (km2, chosen [range]): Jan-Mar 71.9-83.9; 08-27 73.0; 09-08 55.9; 09-20 60.3; 10-02 58.1. Sep-Oct QPDH are also low, like 10-14 DHDH.
- Next: report; method freeze at 20:00.

### 19:24 IST - Atomic .npz saves (bug fix); METHOD FREEZE
- What: sambhar/storage.py save_npz(): writes <name>.npz.partial in the same folder, then os.replace() onto the real name (atomic on one file system). Used by save_crop(), scripts/check_coherence.py (coherence per pair) and scripts/map_water.py (frequency.npz). New test test_interrupted_save_leaves_no_file: a save that fails mid-way (object that cannot be pickled) must leave no file; a normal save loads and leaves no .partial. Tests 6/6.
  - Checked the test is meaningful: the old direct np.savez_compressed() with the same failing object leaves a 425-byte file (like the real 436-byte 08-27 file at ~19:13).
  - Leftover *.npz.partial files after a crash are harmless: load_all_crops() reads only *.npz.
  - Not changed: scripts/make_demo_data.py (another terminal's file) still calls np.savez_compressed directly; it writes only to outputs/demo/. Reported to the user.
- Why: team request after my worker-1 incident; judges read the code.
- Result: no change to any result (existing files were all test-loaded at 19:18).
- Method freeze: from now on only reruns, validation and results. Next: README Results section once validation numbers arrive.

### 19:30 IST - Results section, slide figures, and the prepared (NOT run) history cleanup
- What:
  - scripts/make_figures.py (new) + plotting functions slide_area_over_time / slide_comparison / slide_frequency_map in sambhar/plots.py; config FIGURES_DIR, FIGURE_COMPARISON_DATE, FIGURE_GAP_DAYS. Writes docs/figures/area_over_time.png, comparison_2026-05-11.png, frequency_map.png. Looked at each figure; fixed two problems on the first try (14 Oct HH-only value invisible as an isolated point on a dashed line without markers; frequency-map title cut off).
  - README: Results section (table of 12 DHDH dates with range, pans/outside, HH-only, removed by coherence, pair modes; 5 findings; Sentinel-2 by-eye comparison; placeholders for validation and the October Sentinel-2 check); make_figures.py in the layout.
- Why: team request (slides + README); no method changes.
- Result / found while making figures:
  - The hand-drawn lake outline leaves out part of the dark lake bed in the south-west: 14.5 km2 just outside the outline (within the lake window) is detected on >= 50% of dates (4.1 km2 on >= 80%), vs 118.5 km2 (74.2) inside. Not changed (method frozen; teammate's outline); stated in README Results.
  - By-eye Sentinel-2 vs radar, % of the 152.1 km2 lake: Jan S2 ~85-90% water vs radar QPDH 01-11/01-23 50-53% (radar misses much January water); May radar 68% (S2: water under white film); Aug S2 ~55-60% water + ~30% crust band vs radar 60%.

#### Git history cleanup - PREPARED, NOT RUN (planned ~22:00 with the other terminals paused)
Problem: commit e2ec1ed ("Starting point") added .venv/ and outputs/; later commits untracked them, but they stay in history: pack = 561 MiB. Also tracked by mistake: */__pycache__/*.pyc and .DS_Store.
No secrets found in history (`git log --all --name-only | grep -i netrc|token|credential` only hits library files inside .venv; ~/.netrc was never in the repo).
git-filter-repo is not installed, so this uses git's built-in filter-branch.
Dry run at 19:27 on a throwaway clone (scratchpad/histtest): exit 0, pack 561.40 MiB -> 13.80 MiB, 0 removed paths left, 29 commits kept, all source/docs/data/web files still present.

Commands (run from the repo folder, with every other terminal paused and nothing uncommitted):

    cd ~/spaceapp
    git status --short                       # must show nothing staged/modified (untracked is OK)
    git bundle create ../spaceapp-before-cleanup.bundle --all     # full backup of the history
    FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --force \
      --index-filter 'git rm -r --cached --ignore-unmatch --quiet -- .venv outputs "*__pycache__*" .DS_Store' \
      --prune-empty -- --all
    git for-each-ref --format='%(refname)' refs/original/ | xargs -n1 git update-ref -d   # drop the backup refs filter-branch leaves
    git reflog expire --expire=now --all
    git gc --prune=now --aggressive
    # checks
    git count-objects -vH | grep size-pack                          # expect ~14 MiB
    git log --all --name-only --format= | grep -cE '^(\.venv|outputs)/|__pycache__|\.DS_Store'   # expect 0
    git status --short                                              # .DS_Store and __pycache__ now show as untracked: expected
    .venv/bin/python -m pytest -q tests                             # expect all pass
    echo ".DS_Store" >> .gitignore && git add .gitignore && git commit -m "Ignore .DS_Store"   # .gitignore is shared: whoever runs this

Notes:
- Every commit hash changes, so hashes quoted in docs/log/*.md will no longer match. The order and messages stay the same.
- Files on disk (.venv, outputs, pycache) are not touched; only history changes. Other terminals share this folder, so nobody needs to re-clone.
- If anything looks wrong: `git clone ../spaceapp-before-cleanup.bundle restored` gives back the old history.
- Push to GitHub only after the checks pass (no remote is configured yet).

### 20:11 IST - README validation section from Terminal 2's results
- What: README Results: replaced the validation placeholder with the inside-lake table for both methods (recall, precision, crust/land/white called water, accuracy), a per-date table (accuracy; recall; crust called water), the upper/lower-bound reading, the recommendation (method depends on lake state), the 11 May white-film result and the sample-size limits. Source: outputs/results/validation_plain_english.txt and validation_summary.txt (Terminal 2, 20:06-20:07; copy of the text in docs/log/terminal-2.md).
- Correction of my own earlier README text (19:30): finding 5 said the brighter QPDH mode is "a likely part of the reason" radar misses January water. The validation contradicts that: HH alone finds 89% (49/55) of January water points, so the misses come from the coherence step (42%, 23/55). Rewritten accordingly; cause still unexplained.
- Result: inside the lake, HH+coherence recall 60% / precision 89% / crust called water 24%; HH only 89% / 79% / 81%. Per date accuracy HH+coh vs HH: 11 Jan 44% vs 86%, 11 May 74% vs 78%, 27 Aug 73% vs 62%. Small samples: 37 crust (2 in January), 20 white, 6 land inside the lake; only 11 May is a main-series (DHDH) date.
