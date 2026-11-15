# Terminal 4 lab notebook

Role: slides and project-page text. Only Terminal 4 writes to this file. Entries are append-only.

### 18:12 IST - Summary of this session so far (docs only)
- What: This session has only written project docs; no NISAR processing has been run from this terminal yet. Exact times of the earlier steps were not recorded.
  1. Read `README.md`. `sambhar_watch_brief.md` was not found. Checked `requirements.txt`, `data/` and `sambhar/config.py` (bbox, 20 m grid, −18 dB threshold) for facts.
  2. Created `docs/slides_outline.md` (7 slides), `docs/video_script.md` (30 s, on-screen text + music, no people) and `docs/project_page.md` (all page fields), with `[PLACEHOLDERS]` for results.
  3. After the real-data update: rewrote slides 4–5 as test → brightness fails → add coherence → validate, with `[COHERENCE WATER]`, `[COHERENCE CRUST]` and `[RULE]`. Rewrote the project page the same way, added NISAR GUNW to NASA Data, sourced Ramsar 24,000 ha to the Ramsar Sites Information Service, and marked the video as optional.
- Why: The team asked for submission text while other terminals code; the instructions were to write only in `docs/`.
- Result: All three docs exist. Checked `git show HEAD:docs/project_page.md`: the latest versions (with GUNW) are already in commit e2ec1ed ("Starting point…", 18:11 IST, made by someone else). Open items: results placeholders, team names and URLs, video timing not checked, and one unsourced limitation line ("wind, rain or crust changes can also lower coherence") waiting for a team decision.
- Next: Create the decision log, commit only the two log files, then continue with NISAR processing tasks as assigned.

### 18:17 IST - Moved log entries from Terminal 1 files to Terminal 4 files
- What: Moved my 18:12 entry from `docs/log/terminal-1.md` and my three decisions from `docs/log/decisions-terminal-1.md` into `terminal-4.md` and `decisions-terminal-4.md`, unchanged. Left a one-line pointer in each Terminal 1 file. Committed only these four files with `git commit -- <paths>`, so Terminal 2's staged `.gitignore`/`.venv` changes were left alone.
- Why: The team corrected my role. I am Terminal 4 (slides and project-page text), not Terminal 1. The 18:12 entry's "Next: continue with NISAR processing" line is out of date; my work is the docs.
- Result: The Terminal 1 files now hold only their header and the pointer lines from Terminal 2 and me. First attempt wrote the pointers without a time (shell variable not passed to Python); fixed with sed to 18:17. Did not create `.gitignore`; Terminal 2 owns it.
- Next: Fill the results placeholders in `docs/slides_outline.md` and `docs/project_page.md` once numbers arrive. Logging only to the -4 files from now on.

### 19:03 IST - Slides and project page rewritten for the new results (coherence, sensitivity, two Sentinel-2 outcomes)
- What: Rewrote `docs/slides_outline.md` and `docs/project_page.md`, and changed one line in `docs/video_script.md`. Checked first that no other terminal had edited these files (`git log` showed only e2ec1ed). Read `sambhar/config.py` for the rule and `ls outputs/results` for figure names.
  - Slide 4 is now "How we tested it": brightness fails (both seasons about −22 dB HH) → 12-day coherence removes 25–40 km² of false water per date → stress test 40–72 km² vs ~10 km² between dates → no trend claimed, every number has a band.
  - Slide 5 has two clearly labelled drafts: 5A (Sentinel-2 confirms dry-season water) and 5B (Sentinel-2 shows dry crust). Only one goes in, so the deck stays at 7 slides.
  - Slide 6 now says every area is shown with its range. Slide 7 is the continuous, uncertainty-aware monitor, optical fusion and wetland-authority ground truth.
  - Project page: summary and results in (A)/(B) versions; "How it works" is 8 steps (data, outlines 152 km² / pans 49.1 km², usual method, failure, coherence, stress test, separate modes, Sentinel-2); new limitations; GUNW pair-starting-on-date wording.
  - Video: the 0:18 "Peak: [WATER AREA PEAK km²]" text became "Every number with its uncertainty", since a peak number implies a trend we no longer claim.
- Why: New results from other terminals changed the story (team message 19:02 IST). Used the rule from `sambhar/config.py` (HH < −18 dB AND coherence < 0.3, marked PROVISIONAL), which replaces the `[RULE]` placeholder. Dropped `[COHERENCE WATER]` and `[COHERENCE CRUST]`: whether coherence separates water from crust is now exactly what 5A vs 5B decides.
- Result: Grep for "first", "illegal", "shrank" and "grew" found only the wording-rule notes, the cited NRSC fact and "first drafts" of code, which is fine. 8 slide headings = 7 slides + one alternate. Open items: `[X ± Y]`, `[Z]`, `[ACCURACY %]`, `[PAN WATER km²]`, `[CRUST ERROR %]`, team names and URLs, choosing A or B. Not verified: that geojson.io was the tool used for `lake.geojson` (the team said only "hand-drawn on satellite imagery"); the area-chart image filename (it isn't in `outputs/results`, so left as `[IMAGE: area chart with band]`).
- Next: When the Sentinel-2 check finishes, delete 5A or 5B and the matching (A)/(B) text, then fill the numbers.
