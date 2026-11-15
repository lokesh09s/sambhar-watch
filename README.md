# Sambhar Watch

**Tracking surface water at Sambhar Salt Lake through a full year with NASA–ISRO NISAR radar.**

Built for the NASA Space Apps Challenge 2026, challenge *Dancing with the SARs*.

## The question

Sambhar Salt Lake, about 70 km west of Jaipur, is India's largest inland saline lake and a Ramsar wetland. Industrial salt pans operate inside and around it. A 2026 study by NRSC-ISRO and VIT-AP found that natural water area fell from 131 km² (2022) to 117 km² (2023) while salt-pan area grew from 49.5 to 51.5 km². The authors note the need to distinguish industrial salt pans from natural wetland area.

The lake changes most during the monsoon, when clouds often block optical satellites. NISAR's L-band radar sees through cloud. We ask:

> **How does detected surface water change through the year, inside and outside mapped salt pans, and how reliably can radar tell that water apart from wet salt crust?**

## Data

| Source | What | Use |
|---|---|---|
| NISAR GCOV (NASA/ASF) | L-band HH and HV backscatter, descending track 34, frame 75, 24 dates (Nov 2025 – Nov 2026) | Main measurements |
| NISAR GUNW (NASA/ASF) | 12-day interferometric coherence, same track and frame, 19 pairs | Telling water apart from smooth salt crust |
| Sentinel-2 (ESA) | Cloud-free optical images | Independent validation |
| Hand-drawn polygons | Salt-pan boundaries, `data/pans.geojson` | Inside/outside comparison |

`data/granules.csv` lists every NISAR file used. Two radar modes alternate (`DHDH` dual-pol, `QPDH` quad-pol); both contain HH and HV. One date (7 Nov 2026) comes from the later validated release and is analysed separately.

GCOV values are gamma-zero backscatter in linear power, terrain-corrected (RTC), on a 10 m UTM grid (EPSG:32643). Pixels flagged invalid by the file's own `mask` layer are treated as "no observation". **Thermal noise correction is not applied in these products**, so the darkest pixels (calm water, very smooth crust) may be close to the radar's noise floor, where their brightness no longer tells them apart.

`data/gunw_pairs.csv` lists the 12-day GUNW pairs for the same track (found by searching NASA CMR for `NISAR_L2_GUNW_PROVISIONAL_V1` over Sambhar). Three longer gaps (60, 24 and 24 days) are left out.

## Method

1. **Crop**: stream only the Sambhar area from each NISAR file and resample every date onto one fixed 20 m grid (`scripts/crop_lake.py`).
2. **Classify**: convert to decibels, lightly reduce speckle, and label pixels darker than an HH threshold as water. Calm water reflects the radar pulse away from the satellite, so it appears dark.
3. **Measure**: water area per date, inside and outside mapped pans, and the **water-detection frequency** of each pixel (detections ÷ valid observations) (`scripts/map_water.py`).
4. **Validate**: compare against labelled Sentinel-2 points, reporting water vs salt crust separately. *(in progress)*

## Repository layout

```
sambhar/            reusable code
  config.py         all settings (study area, grid size, threshold)
  granules.py       list of NISAR files and remote access
  nisar.py          reading GCOV HDF5 files
  coherence.py      reading 12-day coherence from GUNW HDF5 files
  grid.py           common map grid and resampling
  water.py          dB conversion, speckle filter, water classification, frequency
  pans.py           salt-pan polygons to pixel mask
  plots.py          figures
  storage.py        saving/loading cropped dates
scripts/            the steps you run
  crop_lake.py      step 1
  map_water.py      step 2
  check_coherence.py  water vs salt crust: brightness and coherence of test regions
tests/              synthetic end-to-end test (lake of known area)
data/               granule and interferogram-pair lists, salt-pan polygons
outputs/            generated files (not committed)
```

## Run it

Needs Python 3.10 or newer (macOS's built-in Python 3.9 is too old).

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python tests/test_pipeline.py                        # check everything works offline
python scripts/crop_lake.py 2026-05-11 --show-structure
python scripts/crop_lake.py all
python scripts/check_coherence.py 2026-05-11 2026-08-15   # dry season and monsoon pairs
python scripts/map_water.py --suggest-threshold      # look, then choose a threshold
python scripts/map_water.py --threshold -18
```

A free [NASA Earthdata](https://urs.earthdata.nasa.gov) account is needed to stream NISAR data.

## Results

*To be added: water-area chart, frequency map, validation table.*

## Limitations

- NISAR products used are provisional (calibrated, partially validated); one date is from a later release.
- Thermal noise correction is not applied in these products, so the darkest pixels may sit near the noise floor.
- Wet salt crust can look as dark as water in radar. This is the main source of error and is tested explicitly.
- Observations are 12 days apart (with some gaps): results mean "water detected on these dates", not continuous presence. Depth is not measured.
- The pan / non-pan split comes from our hand-drawn polygons. "Outside mapped pans" may still contain unmapped pans, channels or roads.
- Mapped changes are surface observations only and say nothing about legality.

## Use of AI

AI assistants (Claude) were used to research the topic, check data availability, draft code and review our reasoning. All results were run, checked and interpreted by the team.

## License

MIT. Data: NASA/ASF (NISAR), ESA Copernicus (Sentinel-2), under their respective terms.
