# Sambhar Watch: project page text

Copy each section into the matching field on the project page. Placeholders in `[BRACKETS]` get filled in once results exist. Delete any line marked *(if used)* that doesn't apply.

---

## Project Name

Sambhar Watch

---

## High-Level Summary

Sambhar Watch uses NASA–ISRO NISAR radar to track surface water at Sambhar Salt Lake, India's largest inland saline lake and a Ramsar wetland, through a full year. Clouds often block optical satellites during the monsoon, when the lake changes most, but radar sees through them. We first tested the usual method, "dark in radar = water", on 24 NISAR dates from November 2025 to November 2026. It failed: the dry-season and monsoon lake bed look equally dark. So we added interferometric coherence, which measures how much the surface changes between two radar passes 12 days apart, and checked the result against Sentinel-2 images. The maps keep water inside mapped salt pans separate from natural wetland, and a simple web app lets anyone pick a date and see where water was detected. [ONE-SENTENCE COHERENCE OUTCOME]

---

## Detailed Description

### What it does

Sambhar Watch shows how much of Sambhar Salt Lake held water on each NISAR date over one year, and where that water was. For each date it reports:

- the area where water was detected, inside and outside mapped salt pans
- a water-detection frequency map: for each spot, the share of dates on which water was detected

### Why it matters

Sambhar is a Ramsar site with 24,000 ha designated. A 2026 study by NRSC-ISRO and VIT-AP found that natural water area fell from 131 km² to 117 km² between 2022 and 2023, while salt-pan area grew from 49.5 km² to 51.5 km². The authors note that industrial salt pans need to be distinguished from natural wetland. The lake is also important for birds: IVRI reported more than 18,000 bird deaths from avian botulism in 2019. Year-round water maps that keep salt pans separate from natural wetland help people follow how the lake changes, including through the cloudy monsoon months.

### How it works: test, failure, fix, check

1. **Get the data.** We stream only the Sambhar area from each NISAR GCOV file (L-band backscatter, HH and HV) through NASA's ASF archive with an Earthdata login: 24 dates on one orbit track, all resampled onto the same 20 m map grid.
2. **Test the usual method.** Calm water reflects the radar pulse away from the satellite, so it usually looks dark. The standard approach labels dark pixels as water.
3. **It failed here.** On real NISAR data, the lake bed in the dry season (May) and in the monsoon (August) are both about −22 dB in HH. Smooth salt crust is as dark as water, so brightness alone cannot tell them apart at Sambhar. We report this as a finding, not a footnote.
4. **Add coherence.** NISAR GUNW products include interferometric coherence between two passes 12 days apart. Our hypothesis: open water changes between passes, so its coherence is low, while stable salt crust stays coherent. We measured coherence on water ([COHERENCE WATER]) and on salt crust ([COHERENCE CRUST]) and built a combined rule: [RULE].
5. **Separate pans from natural water.** We drew the salt-pan outlines by hand in geojson.io and split every result into inside and outside the mapped pans.
6. **Check it.** We compared the maps with labelled points from cloud-free Sentinel-2 images, reporting water and salt crust separately. Agreement with Sentinel-2: [ACCURACY %]. Salt crust labelled as water: [CRUST ERROR %].

### Results

- Coherence, water vs salt crust: [COHERENCE WATER] vs [COHERENCE CRUST]
- Rule used: [RULE]
- Agreement with Sentinel-2: [ACCURACY %]
- Peak detected water: [WATER AREA PEAK km²] on [PEAK DATE]
- Lowest detected water: [WATER AREA MIN km²] on [MIN DATE]
- Share of detected water inside mapped pans: [PAN SHARE %]
- [ONE-SENTENCE KEY FINDING]

### Benefits

- **Works through clouds:** radar covers the monsoon months that optical satellites often miss.
- **Pans kept apart:** natural wetland is reported separately from industrial salt pans.
- **Tested, not assumed:** we checked the standard method on real data, showed where it breaks, and report how well the fix works.
- **Open and repeatable:** free data and open code. The same steps can be run on new NISAR passes or other salt lakes.

### Limitations

- Coherence as a water/crust separator is a hypothesis we tested on this lake and these dates. It may not hold elsewhere or in every season. Wind, rain or crust changes can also lower coherence.
- The NISAR products are provisional (calibrated, partly validated). One date comes from a later release and is analysed separately.
- Observations are about 12 days apart, with some gaps. The results mean "water detected on these dates", not continuous presence. We don't measure depth.
- "Outside mapped pans" may still include pans, channels or roads that we didn't map.
- The maps show surface changes only. They say nothing about whether any use of the lake is permitted.

### Tools and languages

- **Python:** earthaccess (NASA Earthdata access), h5py (reading NISAR HDF5), NumPy, pyproj, fsspec/aiohttp (remote streaming), Matplotlib (figures), pytest (tests)
- **Web app:** [APP STACK, e.g. HTML/JavaScript + Leaflet]
- **geojson.io:** drawing the salt-pan outlines
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

- **NISAR Level-2 GCOV (Geocoded Polarimetric Covariance)**: L-band radar backscatter (HH and HV), from the NASA–ISRO NISAR mission. 24 dates from November 2025 to November 2026, one descending track over Sambhar Lake, both DHDH and QPDH modes. Accessed from the **Alaska Satellite Facility (ASF) DAAC**. This is our main dataset.
- **NISAR GUNW (interferograms, coherence)**: pairs of passes 12 days apart, accessed from ASF. We use the coherence layer to separate water from salt crust.
- **NASA Earthdata / earthaccess**: used to log in, search for granules and stream only the part of each file that covers the lake.

---

## Space Agency Partner and Other Data

- **Sentinel-2 (ESA, Copernicus)**: cloud-free optical images used to validate the radar water maps, including water vs salt crust.
- **ISRO** (partner in NISAR): NISAR is a joint NASA–ISRO mission.
- **NRSC-ISRO / VIT-AP study (2026)**: background figures on natural water area (131 → 117 km²) and salt-pan area (49.5 → 51.5 km²), 2022 → 2023.
- **IVRI report (2019)**: background on bird deaths from avian botulism at Sambhar (more than 18,000 birds).
- **Ramsar Sites Information Service**: Sambhar's Ramsar site record (24,000 ha designated).
- **JRC Global Surface Water (European Commission)** *(if used)*: long-term water occurrence, used for comparison.
- **geojson.io**: tool used to hand-draw the salt-pan outlines (`data/pans.geojson`).
