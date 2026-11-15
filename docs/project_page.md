# Sambhar Watch: project page text

Copy each section into the matching field on the project page. Placeholders in `[BRACKETS]` still need filling.

---

## Project Name

Sambhar Watch

---

## High-Level Summary

Sambhar Watch uses NASA–ISRO NISAR radar to track surface water at Sambhar Salt Lake, India's largest inland saline lake and a Ramsar wetland, through the cloudy monsoon and after it. Our finding: Sambhar dries out after the monsoon; brightness alone missed it, coherence caught it. Between 15 August and 14 October, radar brightness alone barely changes (125 → 115 km²), because dry, smooth salt crust looks as dark as water. Crust stays stable between passes 12 days apart while water doesn't, so adding interferometric coherence separates them. With coherence, the detected water falls from about 91 to about 56 km², and the drop holds under every threshold setting we tested. Sentinel-2 shows the same drying, from about 55–60% water to about 55–60% white crust. Checked on 177 labelled points, it is a trade-off. Brightness alone over-counts: it calls 81% of salt crust water. Coherence under-counts: it finds 60% of real water. Because 76% of the points were water, plain accuracy rewards over-counting, and a model that always says "water" would score 76%. Weighting water and non-water equally, coherence is better (68% vs 58%), while brightness still finds more water. Coherence does better while crust is spreading, brightness when the lake is full. The methods give different estimates with different error trade-offs; they are not proven limits on the true area. A simple web app lets anyone pick a date and see where water was detected, with an uncertainty band on every number.

---

## Detailed Description

### What it does

Sambhar Watch shows, for each NISAR date over one year, where Sambhar's lake bed was detected as water or wet brine, and how large that area was. Every area comes with an uncertainty band. For each date it reports:

- the detected area inside the lake outline (152 km²), split into inside and outside mapped salt pans (49.1 km² of pans inside the lake)
- a water-detection frequency map: for each spot, the share of dates on which it was detected

### Why it matters

Sambhar is a Ramsar site with 24,000 ha designated. A 2026 study by NRSC-ISRO and VIT-AP found that natural water area fell from 131 km² to 117 km² between 2022 and 2023, while salt-pan area grew from 49.5 km² to 51.5 km². The authors note that industrial salt pans need to be distinguished from natural wetland. The lake is also important for birds: IVRI reported more than 18,000 bird deaths from avian botulism in 2019. The lake changes most in the monsoon, when clouds often block optical satellites. Radar can see through clouds, but it is only useful if we know how far to trust it. That is what we tested.

### How it works

1. **Get the data.** We stream only the Sambhar area from each NISAR GCOV file (L-band backscatter, HH and HV) and the matching NISAR GUNW interferogram pairs through NASA's ASF archive, using an Earthdata login. Every date is resampled onto the same 20 m map grid.
2. **Draw the outlines.** We drew the lake outline (152 km²) and the salt-works and pan outlines by hand on satellite imagery. All areas are counted inside the lake outline only.
3. **Test the usual method.** Calm water reflects the radar pulse away from the satellite, so it usually looks dark. The standard approach labels dark pixels as water.
4. **It failed here.** On real NISAR data, the lake bed in the dry season (May) and in the monsoon (August) are both about −22 dB in HH. Dark-but-dry surfaces look the same as water in brightness alone.
5. **Add coherence.** Coherence compares the radar signal from two passes 12 days apart; open water usually has low coherence, stable dry surfaces usually stay coherent (including dry, smooth salt crust that is as dark as water). This follows Festa, D., Roth, F., Hassaan, M., Wagner, W. (2026). Improving Backscatter-Based Surface Water Classification in Arid Environments Through Interferometric Coherence. *Remote Sensing* 18(17), 2966. https://www.mdpi.com/2072-4292/18/17/2966. We apply and test this approach at a salt lake with NISAR. Each date uses the 12-day pair that starts on that date. Our provisional rule: a pixel is detected when HH is below −18 dB **and** coherence is below 0.3. This removes [COHERENCE REMOVED km²] of false "water" inside the lake per date, from dark but stable dry fields and dry crust.
6. **Stress-test the settings.** We re-ran the rule over 12 reasonable settings: HH threshold −17 to −20 dB, coherence threshold 0.25 to 0.35. On a single date, the lake area can change by 40–72 km². That is more than the small changes between April and August (about 10 km²), so we don't claim those. A change only counts if it holds across settings: the drop from 15 August to 14 October holds in all 12 of 12 settings (by 16.9–38.7 km²). Every result is shown with this uncertainty band.
7. **Keep radar modes apart.** NISAR alternates two modes over Sambhar (DHDH and QPDH). Only April–October forms one consistent series; outside that window the modes are shown separately.
8. **Validate with Sentinel-2.** We labelled 203 points by eye on cloud-free 20 m Sentinel-2 images (177 inside the lake) as water, salt crust, white surface or land. We scored both methods against them, overall and by date. Because most points are water, we lead with balanced accuracy, which weights water and non-water equally. Wet salt crust can look like water to radar, so we also report how often each method calls crust water. An MNDWI audit flagged 5 of 203 blind labels as mixed-edge or white-film pixels; all labels were kept unchanged to avoid post-hoc bias.
9. **Compare with the long-term record.** JRC Global Surface Water's long-term record says the lake is rarely wet, which clashes with what we see in January 2026. Our hypothesis, not yet tested: optical records miss shallow brine.

### Results

**Sambhar dries out after the monsoon; brightness alone missed it, coherence caught it.**

Water inside the 152 km² lake outline, radar in DHDH mode. Radar areas are water detected on these dates.

| | 15 August | 14 October |
|---|---|---|
| Radar, brightness only | about 125 km² | about 115 km² |
| Radar, brightness + coherence | about 91 km² (51–110 across settings) | about 56 km² (34–72 across settings) |
| Sentinel-2 | 29 Aug: ~55–60% water, crust band at the edges | 13 Oct: ~55–60% white crust, ~20–25% water |

Both radar dates use mixed-mode coherence pairs, so they're treated alike. Our mode check found coherence consistent between modes, and separate QPDH dates in September–October (56–60 km²) agree with the October value.

- **Brightness alone misses the change.** Dry, smooth salt crust is as dark as water to radar, so brightness drops by only 10 km².
- **Coherence finds it.** Crust is stable between passes; water isn't. With coherence, the detected area falls by about 35 km².
- **The drop holds under every threshold setting we tested.** Across all 12 settings, the detected area falls from 15 August to 14 October by 16.9–38.7 km². 14 October is the lowest date in 10 of 12 settings. QPDH-mode dates in September–October agree (56–60 km²).
- **Sentinel-2 shows the same drying.** White crust covers most of the basin by 13 October; 10 October looks the same, so it persists.

**Validation against Sentinel-2 (177 labelled points inside the lake: 134 water, 43 non-water = 37 salt crust + 6 land)**

| | Always "water" (baseline) | Brightness only | Brightness + coherence |
|---|---|---|---|
| **Balanced accuracy** | 50% | 58.4% | **68.2%** |
| Water found (water recall) | 100% | 88.8% (119/134) | 59.7% (80/134) |
| Non-water found (non-water recall) | 0% | 27.9% (12/43) | 76.7% (33/43) |
| Plain accuracy | 75.7% | 74.0% | 63.8% |
| Detections that are real water (precision) | | 79% | 89% |
| Salt crust called water | | 81% | 24% |
| Accuracy, 11 January (lake full) | | 86% | 44% |
| Accuracy, 11 May | | 78% | 74% |
| Accuracy, 27/29 August (crust spreading) | | 62% | 73% |

**Why balanced accuracy.** 76% of validation points were water, so plain accuracy rewards over-counting; a model that always says "water" scores 76%. Weighting water and non-water equally, coherence is better (68% vs 58%), while brightness still finds more water.

**It's a trade-off.** Brightness alone over-counts: it calls most salt crust water. Coherence under-counts: it misses some real water, especially in January. The right method depends on the lake's state. When crust is spreading, as in the post-monsoon drying, coherence is more accurate; when the lake is full, brightness is. The methods give different estimates with different error trade-offs; they are not proven limits on the true area. Our headline is about the post-monsoon drying, a crust-spreading period, which is exactly where coherence validated better.

**Recommendation:** Use brightness when the lake is full, add coherence when crust is present, and report both estimates ("Brightness only" and "Brightness + coherence").

**Supporting findings**
- *The 11 May optical trap:* Sentinel-2 shows a white lake on 11 May but water on 6 and 16 May. A single optical image can mislead.
- *JRC long-term record:* says the lake is rarely wet, which clashes with January 2026. Hypothesis: optical misses shallow brine.

### Benefits

- **Works through clouds:** radar covers the monsoon months that optical satellites often miss.
- **Pans kept apart:** natural lake bed is reported separately from mapped salt pans.
- **Honest numbers:** every area has an uncertainty band, and we report both methods' scores, including where each one fails.
- **Consistent geometry:** all dates share one orbit track and viewing geometry, so the incidence angle is constant through the year.
- **A clear rule for users:** which method to trust depends on the lake's state, and both estimates are reported side by side.
- **Open and repeatable:** free data and open code. The same steps can be run on new NISAR passes or other salt lakes.

### Limitations

- Coherence misses real water (water recall 60%), especially in January (44% accuracy), so on plain accuracy it scores lower than brightness alone (64% vs 74%). Why it missed January water is unresolved. Hypotheses: calm, stable shallow water or thin brine films; stable sub-pixel features such as salt rafts or mud ridges; coherence estimates biased upward at low signal.
- In January (QPDH mode) radar detects about 50–55% of the lake vs about 85–90% water in Sentinel-2.
- Radar overestimates in October (56 vs about 30–40 km² optical), likely because of the reservoir and wet edges.
- The validation samples are small for some classes: 37 crust, 20 white-surface and 6 land points.
- The validation labels were made by eye from 20 m Sentinel-2 images. An MNDWI audit flagged 5 of 203 blind labels as mixed-edge or white-film pixels; all labels were kept unchanged to avoid post-hoc bias.
- Processing simplifications: 20 m nearest-neighbour resampling (no multilooking); 3×3 smoothing done in dB, not linear power; GUNW coherence is estimated over a coarser window than the 10 m GCOV pixels.
- Wet salt crust can look like water in radar. This is the main source of error, and we tested it explicitly.
- Settings can change one date's area by 40–72 km², so we only report changes that hold across settings (the August → October drop holds in all 12 of 12). April–August changes are within the uncertainty.
- Only April–October forms one consistent radar series. The two radar modes stay as separate series outside that window.
- The rule (HH below −18 dB and coherence below 0.3) is provisional.
- The NISAR products are provisional (calibrated, partly validated). One date comes from a later release and is analysed separately.
- Observations are about 12 days apart, with some gaps, and a date needs a 12-day pair starting or ending on it. The results mean "detected on these dates", not continuous presence. We don't measure depth.
- The lake and pan outlines are hand-drawn. Unmapped pans, channels or roads may remain.
- The lake outline was hand-drawn from optical imagery and misses part of the western lake bed (about 10 km², visible in the radar). Reported areas are inside the outline only, so they understate the full lake bed. Including it does not change the August → October drop (about 91 → 56 km² inside the outline; about 98 → 59 km² with the western arm added).
- The maps show surface changes only. They say nothing about whether any use of the lake is permitted.

### How we are different from what already exists

- **Optical water maps** (e.g. JRC Global Surface Water) can't see through monsoon clouds and can confuse white salt crust with water; the JRC record we used ends in 2021.
- **Radar flood tools** usually use brightness only. At a salt lake that fails: flat crust looks as dark as water. With brightness alone, the post-monsoon drying is much smaller (about 10 km² vs 35 km²): about 125 → 115 km² vs 91 → 56 km² with coherence.
- **Published Sambhar studies** we found give yearly figures; we update every 12 days, through clouds.

**What we add:** NISAR (launched 2025); a test for water vs salt crust using coherence; open reliability (177 check points, 12 threshold settings, stated limits); salt works separated from the natural lake; built for non-experts.

### Why does the lake change? (hypothesis, not proven)

- **Monsoon (roughly July–September):** rain and seasonal streams flow into the shallow lake.
- **After the rains stop:** strong evaporation shrinks the water, leaving wet brine and then salt crust.
- **Human driver:** the salt works pump brine into the mapped pans to evaporate it, so the pans follow a managed cycle, not only the weather.
- **What we did NOT see:** no clear monsoon rise in radar water area. The per-date uncertainty (40–72 km²) is larger than the April–August changes, and shallow water vs wet crust is hard to separate.

### Which polarization?

- We used **HH backscatter plus 12-day coherence**. Coherence is not a polarization: it compares the radar signal from two passes 12 days apart; open water usually has low coherence, stable dry surfaces usually stay coherent.
- **We did not test HV.** This is a reason, not a result: over the lake HV is likely close to the noise floor (about −26.8 dB), and HH usually gives better water/land contrast at L-band.
- **Mode check we did do:** quad-pol (QPDH) HH is about 0.9 dB brighter than dual-pol (DHDH); coherence agrees between the modes.

### Tools and languages

- **Python:** earthaccess (NASA Earthdata access), h5py (reading NISAR HDF5), NumPy, pyproj, fsspec/aiohttp (remote streaming), Matplotlib (figures), pytest (tests)
- **Web app:** plain HTML, CSS and JavaScript with Leaflet (map) and Chart.js (chart); no build step
- **geojson.io:** drawing the lake and salt-pan outlines
- Code: https://github.com/lokesh09s/sambhar-watch · App: https://lokesh09s.github.io/sambhar-watch

---

## Use of Super Intelligence

We used Claude (an AI assistant from Anthropic) as a helper throughout the project:

- **Research:** background on Sambhar Lake, SAR water mapping and the NISAR product formats
- **Data discovery:** finding which NISAR files cover the lake and how to access them
- **Code drafting:** first drafts of the processing scripts, tests and web app
- **Review:** checking our reasoning, methods and wording

The team ran every step, checked the outputs against Sentinel-2 validation points, and chose and interpreted all results. Every figure and number in this project comes from code we ran on the data ourselves.

---

## NASA Data

- **NISAR Level-2 GCOV (Geocoded Polarimetric Covariance)**: L-band radar backscatter (HH and HV), from the NASA–ISRO NISAR mission. Dates from November 2025 to November 2026, one descending track over Sambhar Lake, in both DHDH and QPDH modes. Accessed from the **Alaska Satellite Facility (ASF) DAAC**. This is our main dataset.
- **NISAR GUNW (interferograms, coherence)**: 12-day pairs of passes, accessed from ASF. Each date uses the coherence of the pair that starts on that date, to separate changing surfaces (water, wet brine) from stable ground and dry crust.
- **NASA Earthdata / earthaccess**: used to log in, search for granules and stream only the part of each file that covers the lake.

---

## Space Agency Partner and Other Data

- **Sentinel-2 (ESA, Copernicus)**: cloud-free optical images used to label 203 validation points (water, salt crust, white surface, land) and to compare seasonal water cover.
- **ISRO** (partner in NISAR): NISAR is a joint NASA–ISRO mission.
- **NRSC-ISRO / VIT-AP study (2026)**: background figures on natural water area (131 → 117 km²) and salt-pan area (49.5 → 51.5 km²), 2022 → 2023.
- **IVRI report (2019)**: background on bird deaths from avian botulism at Sambhar (more than 18,000 birds).
- **Ramsar Sites Information Service**: Sambhar's Ramsar site record (24,000 ha designated).
- **JRC Global Surface Water (European Commission)**: long-term water occurrence. It says the lake is rarely wet, which clashes with January 2026 (our hypothesis: optical misses shallow brine).
- **geojson.io**: tool used to hand-draw the lake and salt-pan outlines (`data/lake.geojson`, `data/pans.geojson`).
