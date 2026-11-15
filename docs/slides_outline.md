# Sambhar Watch: slide outline

**This deck is our main deliverable. The video is optional, only if time allows.**

**Hard limit: 7 slides in total, title and intro included. Do not add any.** **FINAL: Slide 5D** (decided 19:34 IST). 5A, 5B and 5C are superseded and will be deleted when the validation numbers arrive. Only 5D goes in the deck.

Placeholders in `[BRACKETS]` get filled in once results exist. Keep the words on each slide short; the notes under each slide are for us, not for the slide.

Required items, and where each one appears:
- Image of the project: slides 4, 5 and 6
- The user experience: slide 6
- How NASA/space-agency data make it possible: slides 3 and 4

Wording rules: never "first"; nothing "illegal"; say "detected on these dates"; mention that wet salt crust can look like water and that we tested it.

---

## Slide 1: Title

**On slide**
- Sambhar Watch
- Tracking Sambhar Lake's water through clouds, with NISAR radar
- Team [TEAM NAME]: [MEMBER NAMES]
- NASA Space Apps 2026 · Challenge: Dancing with the SARs

**Visual:** NISAR radar image of Sambhar Lake, full-bleed [IMAGE: outputs quicklook]

---

## Slide 2: The problem

**On slide**
- India's largest inland saline lake
- Ramsar wetland (24,000 ha)
- Natural water: 131 → 117 km² (2022 → 2023)
- Salt pans: 49.5 → 51.5 km²
- 18,000+ bird deaths in 2019 (avian botulism)

**Footer (small):** Sources: Ramsar Sites Information Service; NRSC-ISRO / VIT-AP study (2026); IVRI report (2019)

**Visual:** map pin, about 70 km west of Jaipur

**Notes:** The 2026 study's authors say salt pans need to be told apart from natural wetland. That is the gap we work on. Do not suggest anything is illegal.

---

## Slide 3: Why radar

**On slide**
- The lake changes most in the monsoon
- Monsoon = clouds = optical satellites can't see
- NISAR's L-band radar sees through clouds
- But can radar tell water from salt crust? We tested it.

**Visual:** two panels for the same date: cloudy Sentinel-2 | clear NISAR [IMAGE: side-by-side, DATE]

**Notes:** NISAR is a NASA–ISRO mission. Its data is free from NASA's ASF archive through Earthdata.

---

## Slide 4: How we tested it

**On slide**
1. **Brightness only fails:** dry May and monsoon August lake bed are both about −22 dB
2. **Add 12-day coherence:** removes [COHERENCE REMOVED km²] of false "water" per date (stable dry fields and dry crust)
3. **Stress test:** 12 fair settings. Only changes that hold across them count.

**Bottom line (large):** Every number has an uncertainty band.

**Footer (small):** Data: NISAR GCOV + GUNW (NASA ASF) · Lake 152 km², pans inside 49.1 km² (outlines drawn by hand on satellite imagery)

**Visual:** brightness-only vs brightness + coherence for the same date [IMAGE: outputs/results/rule_comparison.png]

**Notes:**
- Coherence measures how much the ground changes between two passes 12 days apart. Water and wet brine change; stable dry ground doesn't.
- Rule (provisional, until Sentinel-2): HH below −18 dB **and** coherence below 0.3.
- Stress test: HH threshold −17 to −20 dB, coherence threshold 0.25 to 0.35. One date's area can shift by 40–72 km², so the small April–August changes (~10 km²) are within uncertainty. The August → October drop holds in all 12 of 12 settings (16.9–38.7 km²) (slide 5).
- [COHERENCE REMOVED km²] was "25–40 km² on every date", but 14 Oct (115 → 55.7 km²) implies ~59 km². Confirm the range before filling it in.
- Each date uses the 12-day pair that starts on that date.
- The two radar modes (DHDH, QPDH) are separate lines until a consistency check shows they agree.

---

## Slide 5D: Results (FINAL)

**Headline:** Sambhar dries out after the monsoon, and NISAR radar sees it, but only with coherence.

**On slide** (water inside the 152 km² lake outline, 15 Aug → 14 Oct)

| | 15 Aug | 14 Oct |
|---|---|---|
| Radar, brightness only | 125 km² | 115 km² |
| Radar + coherence | 91 km² | 56 km² |
| Sentinel-2 | ~55–60% water | ~55–60% white crust |

- Dry crust looks as dark as water, but stays stable. Coherence spots it.
- The drop holds under every threshold setting we tested
- Validation points: [VALIDATION ACCURACY %] agree ([N POINTS] points)

**Visual:** August vs October side by side, with Sentinel-2 on top and the radar map below, and the brightness-only vs brightness + coherence numbers under each [IMAGE: Aug vs Oct, S2 + radar]

**Footer (small):** Water detected on these dates. Sentinel-2: 29 Aug and 13 Oct. Radar: DHDH mode.

**Notes:**
- Full numbers: brightness + coherence 91.4 → 55.7 km² (range across settings 51–110 → 34–72). The Aug → Oct drop holds in all 12 of 12 threshold settings, by 16.9–38.7 km². 14 Oct is the lowest date in 10 of 12 settings. QPDH dates in Sep–Oct agree (56–60 km²).
- Sentinel-2: 29 Aug ~55–60% water with a crust band at the edges. 13 Oct ~55–60% white crust spread across most of the basin, ~20–25% water; 10 Oct looks the same, so the crust persists.
- Honest limits (say them if asked):
  - Radar overestimates in October: 56 vs ~30–40 km² optical. This is likely the reservoir and wet edges.
  - April–August changes are within uncertainty.
  - Only April–October is one consistent radar series (radar-mode check).
  - Radar misses a lot of winter water: in January (QPDH mode) it detects ~50–55% of the lake vs ~85–90% water in Sentinel-2. Possibly the brighter QPDH mode; unconfirmed, so don't state a cause.
  - Wet salt crust can still look like water; we tested this.
- Supporting points, if time:
  - The 11 May optical trap: a white lake on 11 May only, with water on 6 and 16 May. One optical image can mislead.
  - JRC's long-term record says the lake is rarely wet, which clashes with January 2026. Our hypothesis is that optical misses shallow brine; this is not tested.
- Water vs crust from validation points: [WATER POINTS CORRECT %] water correct, [CRUST POINTS CORRECT %] crust correct.

---

## Slide 5A (SUPERSEDED by 5D): Results, IF Sentinel-2 confirms dry-season water

*Superseded. Delete when validation numbers arrive.*

**Headline:** Sambhar appears to keep shallow water or brine through the dry season.

**On slide**
- NISAR tracks about [X ± Y] km² of water or brine through the year
- Coherence removes [Z] km² of false detections
- Sentinel-2 agrees: [ACCURACY %]
- **Highlight (placeholder until validation confirms):** On 11 May an optical image shows a white lake; [NISAR RESULT ON 11 MAY]
- Detected inside mapped pans: [PAN WATER km²] of 49.1 km²
- Water detected on these dates; band = method uncertainty

**Visual:** in-lake area through the year, uncertainty band, DHDH and QPDH as separate lines [IMAGE: area chart with band] plus the frequency map [IMAGE: outputs/results/frequency.png]

**Optional visual for the highlight:** 11 May Sentinel-2 (white lake) next to the 11 May NISAR map [IMAGE: Sentinel-2 vs NISAR, 11 May]

**Notes:**
- Don't say "the lake shrank" or "grew": the band is wider than the change between dates.
- Keep "appears to". The early Sentinel-2 look: the main basin is mostly shallow water (green) on 6 and 16 May, with a short-lived white surface on 11 May. Not yet a finished validation.
- Drop the highlight if validation doesn't support it. Don't say what the white surface is until we know.

---

## Slide 5B (SUPERSEDED by 5D): Results, IF Sentinel-2 shows dry crust in the dry season

*Superseded. Delete when validation numbers arrive.*

**Headline:** At Sambhar, L-band radar maps the active wet lake bed, not open water.

**On slide**
- Wet salt crust and water look alike, even with coherence
- Method uncertainty (40–72 km²) > seasonal change (~10 km²)
- What would fix it: more dates · fusion with optical data · field measurements

**Visual:** the same date as radar map vs Sentinel-2 image, crust marked [IMAGE: radar vs Sentinel-2, DATE] plus the area chart with its band [IMAGE: area chart with band]

**Notes:** This is still a result. We tested the obvious method, showed where it breaks, and measured by how much.

---

## Slide 5C (SUPERSEDED by 5D): Results, radar agrees in some seasons, not others

*Superseded. Delete when validation numbers arrive.*

**Headline:** Sentinel-2 shows Sambhar changes a lot through the year. NISAR roughly agrees in some seasons and underestimates in others.

**On slide** (water inside the 152 km² lake outline)

| | Sentinel-2 (optical) | NISAR radar |
|---|---|---|
| Jan | ~130 km² | ~80 km² |
| May | mostly shallow water | ~94 km² |
| Aug | ~85–90 km² | ~91 km² |

- Radar uncertainty is large
- Fix: more dates · optical + radar together · field data
- Validation points: [VALIDATION ACCURACY %] agree ([N POINTS] points)

**Visual:** Sentinel-2 on 6, 11 and 16 May (white lake on 11 May only) next to the NISAR result for 11 May [IMAGE: S2 6/11/16 May + NISAR 11 May]

**Footer (small):** Optical areas by eye, to be confirmed by validation points. Radar: water or brine detected on these dates.

**Notes:**
- Dates and modes: Jan is 11 Jan for both (radar in QPDH mode). May radar is 11 May (DHDH); the optical image that day shows a short-lived white film over mostly shallow water, with water on 6 and 16 May. Aug optical is 29 Aug, but radar is 15 Aug (DHDH), two weeks earlier.
- January looks too low in radar. This may be a radar-mode effect (QPDH vs DHDH), which is being checked: [JAN MODE CHECK RESULT]. Don't explain it until the check is done.
- August optical also shows a band of real salt crust (~30% of the lake). Wet salt crust can look like water, and this is where we tested it.
- Water vs crust from validation points: [WATER POINTS CORRECT %] water correct, [CRUST POINTS CORRECT %] crust correct.
- Say "roughly agrees" and "underestimates". Don't put a single accuracy figure on the whole year.

---

## Slide 6: The app

**On slide**
- Pick a date → see where water was detected
- Every area shown with its range
- Salt pans outlined
- [APP URL]

**Visual:** app screenshot with a date being picked [IMAGE: app screenshot]

**Notes:** This slide covers the user experience. Name a few users: wetland managers, researchers, bird-watch groups.

---

## Slide 7: Future

**On slide**
- A continuous monitor for Sambhar and other salt lakes
- Uncertainty shown on every number
- Gets better as NISAR's record grows
- Combined with optical data
- Ground truth from the wetland authority

**Footer:** Thank you · [REPO URL] · Data: NASA/ASF NISAR (GCOV, GUNW), ESA Sentinel-2
