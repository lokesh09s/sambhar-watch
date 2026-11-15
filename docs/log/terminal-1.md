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
