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

### 19:06 IST - Leaning to version A after the early Sentinel-2 look; 11 May highlight added as a placeholder
- What: Edited `docs/slides_outline.md` and `docs/project_page.md`. Marked 5A / (A) "current lean" and 5B / (B) "fallback". Made "Sambhar appears to keep shallow water or brine through the dry season" the 5A headline and the first line of the (A) summary and results. Added the highlight "On 11 May an optical image shows a white lake; [NISAR RESULT ON 11 MAY]" to slide 5A and to the (A) results, marked as a placeholder until validation confirms, with an optional side-by-side image. Added the early Sentinel-2 observations to step 8 of "How it works".
- Why: Team message 19:05 IST: Sentinel-2 shows the May main basin mostly shallow water (green) on 6 and 16 May, with a short-lived white surface on 11 May. Kept "appears to" and kept B because the validation isn't finished. The docs don't say what the white surface is.
- Result: Still 7 slides (5A/5B are alternates). New placeholder: [NISAR RESULT ON 11 MAY].
- Next: Once validation confirms, delete 5B / (B), fill [X ± Y], [Z], [ACCURACY %], [PAN WATER km²] and the 11 May result, or drop the highlight.

### 19:08 IST - Added results version C (radar agrees in some seasons, underestimates in others) as likely final
- What: Edited `docs/slides_outline.md` and `docs/project_page.md`.
  - Added slide 5C: the team's headline, a 3-row table (Sentinel-2 by eye vs NISAR: Jan ~130 vs ~80 km², May mostly shallow water vs ~94 km², Aug ~85–90 vs ~91 km²), the fixes, and a validation placeholder. Visual: Sentinel-2 on 6/11/16 May next to NISAR on 11 May. Notes give the date and mode details (Aug optical 29 Aug vs radar 15 Aug; Jan radar in QPDH) and the August salt-crust band.
  - Project page: (C) summary and (C) results table; step 8 now gives the by-eye numbers; two new limitations (possible January mode effect, optical areas are by eye).
  - Relabelled: C "likely final"; A and B kept with no lean labels. Header says validation at ~21:00 IST decides.
  - New placeholders: [VALIDATION ACCURACY %], [N POINTS], [WATER POINTS CORRECT %], [CRUST POINTS CORRECT %], [JAN MODE CHECK RESULT].
- Why: Team message 19:07 IST. Optical shows a real seasonal change while radar stays fairly flat; radar roughly agrees in August and looks low in January. Kept "roughly agrees" / "underestimates" wording, and said nothing about the cause of the January gap until the mode check is done.
- Result: 7 slides in the deck (5A/5B/5C are alternates). The wording grep found one "A first by-eye comparison"; changed it to "An initial" to keep "first" out entirely.
- Next: After validation (~21:00 IST), delete two of the three versions and fill the validation numbers.

### 19:36 IST - Final story (version D) written into slides and project page; A/B/C marked superseded
- What: Edited `docs/slides_outline.md` and `docs/project_page.md`.
  - Added slide 5D (FINAL): headline "Sambhar dries out after the monsoon, and NISAR radar sees it, but only with coherence". A table for 15 Aug vs 14 Oct (brightness only 125/115, + coherence 91/56, Sentinel-2 water vs white crust), the "why" line, "lowest date in 10 of 12 settings", and a validation placeholder. Visual: Aug vs Oct, Sentinel-2 + radar, with both sets of numbers. The notes hold the full numbers, the honest limits (Oct overestimate 56 vs ~30–40 km², Apr–Aug within uncertainty, only Apr–Oct consistent) and the supporting points (11 May trap, JRC clash).
  - Slide 4: the bottom line is now "Every number has an uncertainty band", replacing "No seasonal trend claimed"; the stress test is now "only changes that hold across settings count".
  - Project page: (D) summary and (D) results with a table, honest limits and supporting findings; steps 5, 6 and 8 updated; new step 9 (JRC comparison); limitations rewritten; JRC moved from "(if used)" to used.
  - Marked 5A/5B/5C and (A)/(B)/(C) "SUPERSEDED by D" and kept them, because the team said to replace them after the validation numbers arrive.
- Why: Team message 19:34 IST decided the final story.
- Result: The deck is exactly 7 slides when superseded ones are excluded (grep count = 7). The wording grep is clean.
  - Two of my own overstatements were caught and fixed before committing: "the drop holds in 10 of 12 settings" (the team said "14 Oct is the lowest date in 10 of 12") and "radar isn't fooled" by the 11 May film (not shown).
  - **Inconsistency found:** the earlier "coherence removes 25–40 km² on every date" clashes with 14 Oct (115 → 55.7 = ~59 km² removed). Replaced it in slide 4 and step 5 with [COHERENCE REMOVED km²]; the team needs to confirm the range. The shared lines under the superseded versions still say 25–40 and go when those versions are deleted.
- Next: When the validation numbers arrive, fill [VALIDATION ACCURACY %], [N POINTS], [WATER POINTS CORRECT %] and [CRUST POINTS CORRECT %], confirm [COHERENCE REMOVED km²], delete A/B/C, recheck 7 slides, and commit.

### 19:48 IST - Story D: Aug→Oct drop holds in 12 of 12 settings; January underestimate added as an honest limit
- What: Edited `docs/slides_outline.md` and `docs/project_page.md`. The slide 5D bullet now reads "The drop holds under every threshold setting we tested", replacing "14 Oct is the lowest date in 10 of 12 settings". The notes, slide 4 notes, project-page summary, step 6, (D) results and limitations now give 12 of 12 (16.9–38.7 km²); "lowest date in 10 of 12" is kept as a secondary detail. Added the January limit (QPDH radar ~50–55% of lake vs ~85–90% Sentinel-2 water; possibly the brighter QPDH mode, unconfirmed) to the slide 5D notes, (D) honest limits, (D) summary and Limitations.
- Why: Team message 19:48 IST. The stronger 12-of-12 statement is now supported, which resolves my 19:34 caution about the overlapping ranges.
- Result: The wording grep is clean; 7 slides in the deck. The January cause is worded as unconfirmed everywhere.
- Next: Same as before: validation numbers, [COHERENCE REMOVED km²], delete A/B/C.

### 20:11 IST - Validation results added; superseded versions A/B/C deleted; deck is final at 7 slides
- What: Rewrote `docs/slides_outline.md` and `docs/project_page.md` in full (checked first that no other terminal had touched them since 8bdc5d5).
  - Deleted 5A/5B/5C and (A)/(B)/(C), as planned for when the validation numbers arrived.
  - Slide 5 headline: "Sambhar dries out after the monsoon. Brightness alone missed it; coherence caught it." A 5-row validation table (water found 89/60%, crust called water 81/24%, late Aug 62/73%, 11 Jan 86/44%, all dates 74/64%) and the trade-off line. The Aug/Oct km² moved into the visual caption to keep words down.
  - Slide 4 adds the validation step (177 points). Slide 7 is renamed "Recommendation and future" and leads with the recommendation line.
  - Project page: new summary with the trade-off and the 64%; step 8 describes the validation; a full validation table (including precision 79/89% and 11 May 78/74%); the trade-off paragraph and recommendation; new limitations (January miss unexplained; small samples of 37 crust, 20 white and 6 land points; by-eye labels from 20 m Sentinel-2; coherence less accurate overall).
- Why: Team message ~20:10 IST with validation results and the framing to use ("don't hide the 64%").
- Result: `grep '^## Slide'` = 7. No version labels remain. Wording grep is clean. Filled [VALIDATION ACCURACY %], [N POINTS], [WATER POINTS CORRECT %] and [CRUST POINTS CORRECT %] (as "crust called water"). Remaining: [COHERENCE REMOVED km²] (still unconfirmed; 14 Oct implies ~59 km², not 25–40), [TEAM NAME], [MEMBER NAMES], [APP URL], [REPO URL], [APP STACK] and the [IMAGE: …] slots. In the AI-use section I wrote "checked the outputs against Sentinel-2 validation points", not "labelled", because I don't know who labelled them. The validation class list "water, salt crust, white surface, land" is inferred from the counts given; check it.
- Next: Fill team names, URLs and the coherence-removed range when the team sends them. `docs/video_script.md` was left unchanged; it doesn't contradict the final story.
