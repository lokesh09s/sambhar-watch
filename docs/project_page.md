# Sambhar Watch: project page text

Copy each section into the matching field on the project page. Placeholders in `[BRACKETS]` get filled in once results exist. Delete any line marked *(if used)* that doesn't apply.

**Two versions are drafted where the Sentinel-2 check decides the story: (A) Sentinel-2 confirms dry-season water, (B) Sentinel-2 shows dry crust. Keep one and delete the other before submitting.** **Current lean: (A)** (early Sentinel-2 look, 19:05 IST). Keep (B) as the fallback until validation confirms.

---

## Project Name

Sambhar Watch

---

## High-Level Summary

*Pick (A) or (B).*

**(A) If Sentinel-2 confirms dry-season water (current lean)**

Sambhar Watch uses NASA–ISRO NISAR radar to track surface water at Sambhar Salt Lake, India's largest inland saline lake and a Ramsar wetland, through a full year, including the cloudy monsoon. Radar brightness alone failed: the dry-season and monsoon lake bed look equally dark. Adding 12-day interferometric coherence fixed most of this. Sambhar appears to keep shallow water or brine through the dry season: NISAR tracks about [X ± Y] km² of water or brine at Sambhar through the year, and coherence removes [Z] km² of false detections. We stress-tested our settings and found the uncertainty is larger than the change between dates, so we show every result with an uncertainty band and don't claim a seasonal trend from radar alone. A simple web app lets anyone pick a date and see where water was detected.

**(B) If Sentinel-2 shows dry crust in the dry season (fallback)**

Sambhar Watch uses NASA–ISRO NISAR radar to study surface water at Sambhar Salt Lake, India's largest inland saline lake and a Ramsar wetland, through a full year, including the cloudy monsoon. We found that at Sambhar, L-band radar maps the active wet lake bed, not open water: wet salt crust and water look alike, even after adding 12-day interferometric coherence. A stress test showed that the method's uncertainty is larger than the seasonal signal, so we don't claim a seasonal trend. We show what the radar can and can't see, with an uncertainty band on every number, and what would fix it: more dates, fusion with optical data, and field measurements. A simple web app lets anyone pick a date and see where wet lake bed was detected.

---

## Detailed Description

### What it does

Sambhar Watch shows, for each NISAR date over one year, where Sambhar's lake bed was detected as water or wet brine, and how large that area was. Every area comes with an uncertainty band. For each date it reports:

- the detected area inside the lake outline (152 km²), split into inside and outside mapped salt pans (49.1 km² of pans inside the lake)
- a water-detection frequency map: for each spot, the share of dates on which it was detected

### Why it matters

Sambhar is a Ramsar site with 24,000 ha designated. A 2026 study by NRSC-ISRO and VIT-AP found that natural water area fell from 131 km² to 117 km² between 2022 and 2023, while salt-pan area grew from 49.5 km² to 51.5 km². The authors note that industrial salt pans need to be distinguished from natural wetland. The lake is also important for birds: IVRI reported more than 18,000 bird deaths from avian botulism in 2019. The lake changes most in the monsoon, when clouds often block optical satellites. Radar can see through clouds, but it is only useful if we know how far to trust it. That is what we tested.

### How it works: test, failure, fix, stress test, check

1. **Get the data.** We stream only the Sambhar area from each NISAR GCOV file (L-band backscatter, HH and HV) and the matching NISAR GUNW interferogram pairs through NASA's ASF archive, using an Earthdata login. Every date is resampled onto the same 20 m map grid.
2. **Draw the outlines.** We drew the lake outline (152 km²) and the salt-works and pan outlines by hand on satellite imagery. All areas are counted inside the lake outline only.
3. **Test the usual method.** Calm water reflects the radar pulse away from the satellite, so it usually looks dark. The standard approach labels dark pixels as water.
4. **It failed here.** On real NISAR data, the lake bed in the dry season (May) and in the monsoon (August) are both about −22 dB in HH. Dark-but-dry surfaces look the same as water in brightness alone.
5. **Add coherence.** Coherence measures how much the surface changes between two radar passes 12 days apart. Water and wet brine change, so their coherence is low; stable ground stays coherent. Each date uses the 12-day pair that starts on that date. Our provisional rule: a pixel is detected when HH is below −18 dB **and** coherence is below 0.3. This removes 25–40 km² of false "water" inside the lake on every date, mostly dark but stable dry fields.
6. **Stress-test the settings.** We re-ran the rule over a range of reasonable settings: HH threshold −17 to −20 dB, coherence threshold 0.25 to 0.35. On a single date, the lake area changes by 40–72 km². That is more than the difference between dates (about 10 km²). So we don't claim a seasonal trend from radar alone, and every result is shown with this uncertainty band.
7. **Keep radar modes apart.** NISAR alternates two modes over Sambhar (DHDH and QPDH). We show them as separate series until a consistency check shows they agree.
8. **Check against Sentinel-2.** We compare the maps with labelled points from cloud-free Sentinel-2 images, reporting water and salt crust separately. Wet salt crust can look like water to radar, so this is the key test. *(Running now. Early look: in May the main basin appears mostly shallow water on 6 and 16 May, with a short-lived white surface on 11 May.)*

### Results

*Pick (A) or (B).*

**Both versions**
- Brightness alone: dry-season and monsoon lake bed both about −22 dB in HH.
- Coherence removes 25–40 km² of false detections inside the lake on every date.
- Method uncertainty on one date: 40–72 km². Difference between dates: about 10 km².

**(A) Sentinel-2 confirms dry-season water (current lean)**
- Sambhar appears to keep shallow water or brine through the dry season.
- NISAR tracks about [X ± Y] km² of water or brine at Sambhar through the year.
- Coherence removes [Z] km² of false detections.
- Agreement with Sentinel-2: [ACCURACY %]
- Detected inside mapped pans: [PAN WATER km²] of 49.1 km²
- *(Placeholder until validation confirms; delete if not supported.)* On 11 May an optical image shows a white lake; [NISAR RESULT ON 11 MAY].

**(B) Sentinel-2 shows dry crust in the dry season (fallback)**
- At Sambhar, L-band radar maps the active wet lake bed, not open water. Wet salt crust and water look alike, even with coherence.
- Method uncertainty is larger than the seasonal signal.
- Sentinel-2 points labelled crust but detected by radar: [CRUST ERROR %]
- What would fix it: more NISAR dates, fusion with optical data such as Sentinel-2, and field measurements.

### Benefits

- **Works through clouds:** radar covers the monsoon months that optical satellites often miss.
- **Pans kept apart:** natural lake bed is reported separately from mapped salt pans.
- **Honest numbers:** every area has an uncertainty band, and we say when the band is bigger than the change.
- **Tested, not assumed:** we checked the standard method on real data, showed where it breaks, and measured how much the fix helps.
- **Open and repeatable:** free data and open code. The same steps can be run on new NISAR passes or other salt lakes.

### Limitations

- The rule (HH below −18 dB and coherence below 0.3) is provisional until the Sentinel-2 check is done.
- Wet salt crust can look like water in radar. This is the main source of error, and we test it explicitly.
- Settings change the result more than the seasons do, so we don't report a seasonal trend from radar alone.
- The two radar modes are not yet shown to agree, so they stay as separate series.
- The NISAR products are provisional (calibrated, partly validated). One date comes from a later release and is analysed separately.
- Observations are about 12 days apart, with some gaps, and a date needs a 12-day pair starting on it. The results mean "detected on these dates", not continuous presence. We don't measure depth.
- The lake and pan outlines are hand-drawn. Unmapped pans, channels or roads may remain.
- The maps show surface changes only. They say nothing about whether any use of the lake is permitted.

### Tools and languages

- **Python:** earthaccess (NASA Earthdata access), h5py (reading NISAR HDF5), NumPy, pyproj, fsspec/aiohttp (remote streaming), Matplotlib (figures), pytest (tests)
- **Web app:** [APP STACK, e.g. HTML/JavaScript + Leaflet]
- **geojson.io:** drawing the lake and salt-pan outlines
- Code: [REPO URL] · App: [APP URL]

---

## Use of Super Intelligence

We used Claude (an AI assistant from Anthropic) as a helper throughout the project:

- **Research:** background on Sambhar Lake, SAR water mapping and the NISAR product formats
- **Data discovery:** finding which NISAR files cover the lake and how to access them
- **Code drafting:** first drafts of the processing scripts, tests and web app
- **Review:** checking our reasoning, methods and wording

The team ran every step, checked the outputs against Sentinel-2 images, and chose and interpreted all results. Every figure and number in this project comes from code we ran on the data ourselves.

---

## NASA Data

- **NISAR Level-2 GCOV (Geocoded Polarimetric Covariance)**: L-band radar backscatter (HH and HV), from the NASA–ISRO NISAR mission. Dates from November 2025 to November 2026, one descending track over Sambhar Lake, in both DHDH and QPDH modes. Accessed from the **Alaska Satellite Facility (ASF) DAAC**. This is our main dataset.
- **NISAR GUNW (interferograms, coherence)**: 12-day pairs of passes, accessed from ASF. Each date uses the coherence of the pair that starts on that date, to separate changing surfaces (water, wet brine) from stable ground.
- **NASA Earthdata / earthaccess**: used to log in, search for granules and stream only the part of each file that covers the lake.

---

## Space Agency Partner and Other Data

- **Sentinel-2 (ESA, Copernicus)**: cloud-free optical images used to validate the radar maps, including water vs salt crust.
- **ISRO** (partner in NISAR): NISAR is a joint NASA–ISRO mission.
- **NRSC-ISRO / VIT-AP study (2026)**: background figures on natural water area (131 → 117 km²) and salt-pan area (49.5 → 51.5 km²), 2022 → 2023.
- **IVRI report (2019)**: background on bird deaths from avian botulism at Sambhar (more than 18,000 birds).
- **Ramsar Sites Information Service**: Sambhar's Ramsar site record (24,000 ha designated).
- **JRC Global Surface Water (European Commission)** *(if used)*: long-term water occurrence, used for comparison.
- **geojson.io**: tool used to hand-draw the lake and salt-pan outlines (`data/lake.geojson`, `data/pans.geojson`).
