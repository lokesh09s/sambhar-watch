# Sambhar Watch: slide outline

**This deck is our main deliverable. The video is optional, only if time allows.**

**Hard limit: 7 slides in total, title and intro included. Do not add any.**

Placeholders in `[BRACKETS]` get filled in once results exist. Keep the words on each slide short; the notes under each slide are for us, not for the slide.

Required items, and where each one appears:
- Image of the project: slides 5 and 6
- The user experience: slide 6
- How NASA/space-agency data make it possible: slides 3 and 4

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

## Slide 4: Method: test, fail, fix

**On slide** (three steps, left to right)
1. **Test:** does "dark = water" work?
2. **It fails:** dry May and monsoon August lake bed are both about −22 dB
3. **Fix:** add coherence from pairs of images 12 days apart
   - Water changes → low coherence
   - Salt crust stays put → high coherence

**Footer (small):** Data: 24 NISAR GCOV dates + NISAR GUNW pairs (NASA ASF)

**Visual:** bar chart showing May and August HH almost equal [IMAGE: HH dB May vs Aug] next to a coherence map [IMAGE: coherence map]

**Notes:** Plain words: radar brightness alone can't separate water from smooth salt crust. Coherence measures how much the ground changes between two passes. That it separates water from crust is a hypothesis we are testing, not a known result. Salt-pan outlines were drawn by hand in geojson.io.

---

## Slide 5: Results: did coherence work?

**On slide**
- Coherence on water: [COHERENCE WATER]
- Coherence on salt crust: [COHERENCE CRUST]
- Our rule: [RULE]
- Agreement with Sentinel-2: [ACCURACY %]
- Peak water detected: [WATER AREA PEAK km²] on [PEAK DATE]
- Inside mapped pans: [PAN SHARE %]

**Visual:** water-area chart through the year, pans vs natural [IMAGE: area chart] plus the water-frequency map [IMAGE: frequency map]

**Notes:** Say "water detected on these dates". If coherence did not separate water and crust well, say so on this slide. Showing a method that failed is still a result.

---

## Slide 6: The app

**On slide**
- Pick a date → see where water was detected
- Frequency map: how often each spot was wet
- Salt pans outlined
- [APP URL]

**Visual:** app screenshot with a date being picked [IMAGE: app screenshot]

**Notes:** This slide covers the user experience. Name a few users: wetland managers, researchers, bird-watch groups.

---

## Slide 7: Future

**On slide**
- Update automatically with each new NISAR pass
- Add more lakes and wetlands
- Test coherence on more dates and other salt lakes
- Alerts when the lake shrinks quickly

**Footer:** Thank you · [REPO URL] · Data: NASA/ASF NISAR (GCOV, GUNW), ESA Sentinel-2
