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
