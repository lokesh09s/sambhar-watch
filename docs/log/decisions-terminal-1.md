# Terminal 1 decisions

Format: HH:MM IST | decision | reason | evidence

- 18:12 IST: Terminal 2's decisions were appended here by mistake. They were moved to docs/log/decisions-terminal-2.md.
- 18:17 IST: Terminal 4's decisions were logged here by mistake. They were moved to docs/log/decisions-terminal-4.md.
- 17:50 IST | Run with Python 3.12 in .venv, not system Python 3.9 | code uses `str | None` type hints (3.10+) | README "Run it"
- 18:05 IST | Treat GCOV mask values 0 and 255 as no observation | 0 = partially focused/invalid samples, 255 = outside swath (file's own mask description) | sambhar/config.py INVALID_MASK_VALUES
- 18:05 IST | Add 12-day interferometric coherence (NISAR GUNW) to the method | HH brightness alone cannot separate water from smooth crust; dry-season farmland also darkens | outputs/crops/2026-05-11.png, 2026-08-15.png; lake -22.7/-21.2 dB, farmland -15.5/-12.4 dB
- 18:07 IST | Use only 12-day GUNW pairs | longer gaps lose coherence for reasons unrelated to water | data/gunw_pairs.csv (19 pairs; 60/24/24-day pairs excluded)
- 18:19 IST | Provisional rule: "dark unstable surface (water or wet brine)" = HH < -18 dB AND coherence < 0.3, until Sentinel-2 confirms | coherence medians lake 0.19/0.23 vs farmland 0.59/0.51; HH-only -18 dB flags 273 km2 in May of which 129 km2 has coherence >= 0.3 | outputs/coherence/*.png, docs/log/terminal-1.md 18:21
- 18:19 IST | Per-date coherence = pixel-wise HIGHER of the two adjacent 12-day pairs; dates with one pair use it and are flagged (coherence_pairs = 1) | pixel must be unstable in both pairs to count | team decision
- 18:19 IST | Keep an HH-only result next to the combined rule | to show how much false water coherence removes (key slide result) | team decision
- 18:19 IST | Report areas inside the lake outline (data/lake.geojson) as well as inside/outside mapped pans, once the outline arrives | the study box also contains other ponds and channels | outputs/crops/*.png
- 18:50 IST | Report all areas inside the lake outline only; pan-related areas = lake & pans | pan shapes outside the lake are rough rectangles (99.7 km2 of them outside the lake) | data/lake.geojson, data/pans.geojson; lake 152.1, pans in lake 49.1, outside pans 103.0 km2
- 18:50 IST | Name the pan class "salt works and mapped pans" in outputs | pans.geojson shape 1 covers the whole eastern salt-works section (reservoirs + pans) | team instruction; config.PANS_LABEL
- 18:57 IST | Per-date coherence = the 12-day pair STARTING on the date; dates with no starting pair dropped (replaces 18:19 "higher of both pairs") | with "higher of both", one-pair dates were 10-15 km2 (11-14%) wetter in the lake than two-pair dates, as large as the between-date difference | docs/log/terminal-1.md 18:53 entry; single pair 102.5-110.6 vs higher-of-both 92.2-99.5 km2 on 04-17..05-23
- 18:57 IST | Output water_km2_min / water_km2_max per date = range over T in {-17,-18,-19,-20} dB x C in {0.25,0.30,0.35} | threshold-induced range (median ~50 km2) exceeds the between-date difference (7-46 km2) | outputs/results/sensitivity_DHDH.csv
- 18:57 IST | If QPDH and DHDH disagree on stable ground, DHDH dates are the main series and QPDH dates are shown separately | science rule: don't mix modes before checking consistency | consistency check pending
- 18:57 IST | Method freeze at 20:00 IST; afterwards only reruns, validation and results | deadline 23:59 IST, team target 23:00 | team decision
- 19:11 IST | If no 12-day pair starts on a date, use the pair ending on it (still one pair per date); record pair_direction and pair_modes | recovers 2026-07-22 and 2026-10-14 (the only post-monsoon DHDH date) without mixing one- and two-pair dates | outputs/results/water_area.csv
- 19:11 IST | The QPDH vs DHDH consistency check decides the series: full year (Jan-Oct) if the modes agree on stable ground, else Apr-Aug DHDH only (QPDH separately) | science rule: check modes before mixing | scripts/check_modes.py
