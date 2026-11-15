# Sambhar Watch: slide outline

**This deck is our main deliverable. The video is optional, only if time allows.**

**Hard limit: 7 slides in total, title and intro included. Do not add any.**

Placeholders in `[BRACKETS]` still need filling. Keep the words on each slide short; the notes under each slide are for us, not for the slide.

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
4. **Check:** 177 points labelled on Sentinel-2 images

**Bottom line (large):** Every number has an uncertainty band.

**Footer (small):** Data: NISAR GCOV + GUNW (NASA ASF) · Lake 152 km², pans inside 49.1 km² (outlines drawn by hand on satellite imagery)

**Visual:** brightness-only vs brightness + coherence for the same date [IMAGE: outputs/results/rule_comparison.png]

**Notes:**
- Coherence measures how much the ground changes between two passes 12 days apart. Water and wet brine change; stable dry ground and dry crust don't.
- Rule (provisional): HH below −18 dB **and** coherence below 0.3.
- Stress test: HH threshold −17 to −20 dB, coherence threshold 0.25 to 0.35. One date's area can shift by 40–72 km², so the small April–August changes (~10 km²) are within uncertainty. The August → October drop holds in all 12 of 12 settings (16.9–38.7 km²) (slide 5).
- [COHERENCE REMOVED km²] was "25–40 km² on every date", but 14 Oct (115 → 55.7 km²) implies ~59 km². Confirm the range before filling it in.
- Each date uses the 12-day pair that starts on that date.
- The two radar modes (DHDH, QPDH) are separate lines; only April–October is one consistent series.
- Validation: 177 labelled points inside the lake (203 in total), labelled by eye on 20 m Sentinel-2.

---

## Slide 5: Results

**Headline:** Sambhar dries out after the monsoon. Brightness alone missed it; coherence caught it.

**On slide**
- The drop holds under every threshold setting we tested

| Checked on 177 Sentinel-2 points | Brightness only | + Coherence |
|---|---|---|
| **Balanced accuracy** | 58% | **68%** |
| Water found | 89% | 60% |
| Non-water found (crust, land) | 28% | 77% |
| Accuracy, late Aug (crust spreading) | 62% | 73% |
| Accuracy, 11 Jan (lake full) | 86% | 44% |

- Plain accuracy: 74% vs 64%, but always saying "water" scores 76%.
- A trade-off: brightness over-counts, coherence under-counts. Together they bracket the true area.

**Visual:** August vs October side by side, with Sentinel-2 on top and the radar map below. Under them: brightness only about 125 → 115 km², + coherence about 91 → 56 km² [IMAGE: Aug vs Oct, S2 + radar]

**Caption (small):** Water detected on these dates, inside the 152 km² lake outline. Sentinel-2: 29 Aug and 13 Oct. Both radar dates use mixed-mode coherence pairs, so they're treated alike; our mode check found coherence consistent between modes; separate QPDH dates in Sep–Oct (56–60 km²) agree with the October value.

**Notes:**
- **Lead with balanced accuracy, and don't hide the 64%.** Say: "76% of validation points were water, so plain accuracy rewards over-counting; a model that always says 'water' scores 76%. Weighting water and non-water equally, coherence is better (68% vs 58%), while brightness still finds more water." Counts: n = 177 (134 water, 43 non-water = 37 crust + 6 land). Brightness only: water 119/134 (88.8%), non-water 12/43 (27.9%), balanced 58.4%, plain 74.0%. + Coherence: water 80/134 (59.7%), non-water 33/43 (76.7%), balanced 68.2%, plain 63.8%. Always "water": plain 75.7%, balanced 50%.
- The headline is about the post-monsoon drying, which is a crust-spreading period, and that is exactly where coherence validated better (73% vs 62%).
- Labels: an MNDWI audit flagged 5 of 203 blind labels as mixed-edge or white-film pixels; all labels were kept unchanged to avoid post-hoc bias.
- Areas are approximate: say "about", or give the range across settings.
- The framing: "It's a trade-off. Brightness alone over-counts (it calls most salt crust water); coherence under-counts (it misses some real water, especially in January). The right method depends on the lake's state: when crust is spreading, as in the post-monsoon drying, coherence is more accurate; when the lake is full, brightness is. Together they bracket the true water area."
- Full numbers:
  - Brightness + coherence 91.4 → 55.7 km² (range across settings 51–110 → 34–72).
  - The drop holds in all 12 of 12 settings (16.9–38.7 km²); 14 Oct is the lowest date in 10 of 12.
  - QPDH dates in Sep–Oct agree (56–60 km²).
  - Precision: brightness 79%, + coherence 89%.
  - 11 May accuracy: 78% vs 74%.
  - The August validation uses 27/29 Aug images.
- Sentinel-2: 29 Aug ~55–60% water with a crust band at the edges. 13 Oct ~55–60% white crust across most of the basin, ~20–25% water; 10 Oct looks the same.
- Honest limits (say them if asked):
  - Radar overestimates in October: 56 vs ~30–40 km² optical, likely the reservoir and wet edges.
  - Coherence misses winter water: in January (QPDH) radar detects ~50–55% of the lake vs ~85–90% water in Sentinel-2. Unresolved. Hypotheses: calm, stable shallow water or thin brine films; stable sub-pixel features (salt rafts, mud ridges); coherence estimates biased upward at low signal.
  - April–August changes are within uncertainty.
  - Processing: 20 m nearest-neighbour resampling (no multilooking); 3×3 smoothing done in dB, not linear power; GUNW coherence estimated over a coarser window than the 10 m GCOV.
  - Strength: all dates share one track and geometry, so the incidence angle is constant through the year.
  - Small samples: 37 crust, 20 white, 6 land points. Labels are by eye from 20 m Sentinel-2.
  - Wet salt crust can look like water; we tested this.
- Supporting points, if time:
  - The 11 May optical trap: a white lake on 11 May only, with water on 6 and 16 May. One optical image can mislead.
  - JRC's long-term record says the lake is rarely wet, which clashes with January 2026. Our hypothesis is that optical misses shallow brine; this is not tested.

---

## Slide 6: The app

**On slide**
- Pick a date → see where water was detected
- Every area shown with its range
- Salt pans outlined
- https://lokesh09s.github.io/sambhar-watch

**Visual:** app screenshot with a date being picked [IMAGE: app screenshot]

**Notes:** This slide covers the user experience. Name a few users: wetland managers, researchers, bird-watch groups.

---

## Slide 7: Recommendation and future

**On slide**
- **Use brightness when the lake is full, add coherence when crust is present, and report both as upper and lower bounds.**
- Next: a continuous monitor for Sambhar and other salt lakes
- Gets better as NISAR's record grows
- Combined with optical data
- Ground truth from the wetland authority

**Footer:** Thank you · https://github.com/lokesh09s/sambhar-watch · Data: NASA/ASF NISAR (GCOV, GUNW), ESA Sentinel-2
