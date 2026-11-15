# Optical validation log (Sentinel-2 + JRC)

Scripts: `scripts/fetch_sentinel2.py`, `scripts/fetch_jrc.py`. Extra packages: `requirements-validation.txt`.

## Confirmed comparison dates

| Season | Sentinel-2 date | NISAR date | Gap | Sky cloud over land |
|---|---|---|---|---|
| Winter | 2026-01-11 | 2026-01-11 (QPDH) | 0 d | 0 % |
| Pre-monsoon | 2026-05-11 | 2026-05-11 (DHDH) | 0 d | 0.7 % |
| Late monsoon | 2026-08-29 | 2026-08-27 (QPDH) | +2 d | 1.4 % |

August 2026 is almost entirely clouded. The other August days are cloudy over at least 60 % of
the land away from the lake, or don't image the whole lake.

## By-eye reading of the lake (inside `data/lake.geojson`)

| Date | Open green water | White surface | Pans + bare shore |
|---|---|---|---|
| 2026-01-11 | ~85-90 % | ~3-5 % | ~5-10 % |
| 2026-05-11 | ~25 % | ~55-60 % (probably not dry crust, see below) | ~15-20 % |
| 2026-08-29 | ~55-60 % | ~30 % (looks like crust or a wet salt flat) | ~10 % |

On **6 and 16 May** the main basin is green water. On **11 May** it is white. A dry crust
doesn't appear and vanish within 10 rainless days, so the 11 May white is probably a short-lived
bright surface on shallow water (salt film, whiting, foam or glint). See
`points_2026-05-11_neighbours.png`.

## Known issues and decisions

- **The lake outline's western arm may cut across water near 75.00 E.** On 2026-01-11, open water
  clearly extends south of the `data/lake.geojson` boundary between about 74.95 E and 75.05 E.
  Lake statistics will undercount there. We are not redrawing it tonight.
- **The Sen2Cor cloud mask (SCL) flags white salt surfaces as cloud.** On 2026-05-11 it marked about
  35 % of the lake as cloud under a clear sky. So:
  - sky cloud is measured over land only, more than 2 km from the lake (`scan` mode);
  - validation points are **not** filtered by the cloud mask.
- **The older matching mode** (`fetch_sentinel2.py <nisar_date>` / `all`) still uses the cloud
  mask over the lake, so it wrongly rejects bright-lake days. We didn't use it for the final dates
  and skipped the 22-date run.
- **Planetary Computer storage is slow from here** (about 30 kB/s per connection). The script reads
  tiles in parallel and uses the 20 m overviews, so everything is on the NISAR 20 m grid
  (EPSG:32643). True colour is 20 m too, not 10 m.
- **GeoTIFF bands are raw L2A digital numbers.** Reflectance = (DN - 1000) / 10000.

## Labelling the validation points

Files per date (`2026-01-11`, `2026-05-11`, `2026-08-29`):

- `points_<date>.csv`: fill in the `label` column. The `date` column is the Sentinel-2 date.
- `points_<date>_numbered.png`: true colour with the lake outline (yellow) and numbered points.
- `points_2026-05-11_neighbours.png`: the same points on 6 May, 11 May and 16 May, side by side.
- `points_<date>_mndwi.csv`: MNDWI at each point. **Don't open this until labelling is done.**
  MNDWI also scores salt crust as water, so it is a second opinion, not ground truth.

The points are random within `data/lake.geojson` plus a 2 km buffer, 150 per date, with a fixed
seed for each date.

| Label | Use when |
|---|---|
| `water` | Clearly open water: green, blue or dark, with no white surface. |
| `white_uncertain` | A white surface that could be crust **or** a thin bright layer on water. **This is the default for white areas.** |
| `salt_crust` | Clearly dry crust: white on this date **and** white on the neighbouring dates too (for 11 May, check 6 and 16 May). |
| `land` | Soil, fields, vegetation, roads, buildings, embankments. Also the pans' dry walls. |

For 11 May, label a white point `water` only if the neighbouring dates clearly show water there.
Label it `salt_crust` only if they clearly show crust. Otherwise use `white_uncertain`.
Leave the label empty if you can't tell (cloud, a boundary pixel).

## JRC long-term context (1984-2021)

Figure: `jrc_lake_occurrence.png`.

JRC occurrence is the share of valid Landsat observations, 1984-2021, that saw water at a pixel.
Of the 153 km² inside `data/lake.geojson`, 84 % had water at least once. The median pixel had
water in only 14 % of observations, and the maximum is 74 %. Only **0.7 % of the outline (about
1 km²) had water in more than 50 % of observations**, and that is almost entirely the salt-works
brine pans. **No pixel had water in more than 90 %.**

So by Landsat's record, the open lake bed is wet only occasionally, never permanently. This
disagrees with the January 2026 Sentinel-2 scene, where about 85-90 % of the outline is green
water. There are two possible explanations, and we haven't checked which: 2025-26 may be
wetter than the 1984-2021 average, or JRC's Landsat classifier may miss shallow, turbid or saline
water. Use these numbers as long-term context only, not as a reference for single dates.

## October check (radar 2026-10-14)

Clearest Sentinel-2 day within 5 days of the 14 Oct NISAR pass: **2026-10-13** (0.2 % cloud over
land, whole lake imaged), file `sentinel2/look_2026-10-13.png`. 10 Oct (0.3 % cloud, 90 % of the
lake imaged) shows the same pattern (`sentinel2/look_2026-10-10.png`). 15 and 18 Oct are cloudier.

By eye, inside `data/lake.geojson` on 13 Oct:

| Class | Share | Where |
|---|---|---|
| White crust | ~55-60 % (~85-90 km²) | The whole western arm, the centre of the main basin and the southern lobe margins. Unchanged between 10 and 13 Oct, so it counts as `salt_crust` under our rule. |
| Open green water | ~20-25 % (~30-40 km²) | One pool in the south-east of the main basin, a small pool by the north-west pans, and the reservoir behind the dam (shallow and mottled) |
| Other | ~15-20 % | Salt-works pans, grey/purple mudflats in the east, bare shore |

**Answer:** in October most of the lake bed is drying crust, not water. Water has pulled back to
the deepest part of the main basin and the reservoir behind the dam. On 29 Aug the crust was
only a band on the southern and western margins. By 13 Oct it covers most of the basin.

This fits the radar result. Smooth, dry crust can look dark to L-band, like calm water. But it is
stable, so coherence stays high, while water decorrelates. The October drop to ~56 km² matches
the coherence rule removing crust that only looks like water. The radar's 56 km² is above the
~30-40 km² of open water seen by eye. The gap may be the shallow, mottled reservoir and wet
margins. We haven't checked this pixel by pixel.

## Label sanity check against MNDWI (labels unchanged)

The labels are in `points_<date>_labelled.csv` in the project root, identical to the copies in
~/Downloads. Strong disagreement means `water` with MNDWI < 0, or `salt_crust`/`land` with
MNDWI > +0.2. Five points are strong disagreements, all labelled `water`:
May #112, #93; Aug #25, #53, #117. No crust or land label has MNDWI above +0.2. Thirteen more are
borderline. Chips: `label_check_disagreements.png`.

Looking at the chips, most disagreements are **mixed pixels**: pan walls, the dam or a shoreline
edge (Aug #53, #117; Jan #38, #39; May #124). Two are **white surfaces labelled `water`**: May #93 and
Aug #25. Under our rules, May #93 should probably be `white_uncertain`, and Aug #25
`white_uncertain` or `salt_crust`. One is a **pink salt-works pan** (May #112), which none of our
classes covers well. Rechecking these by eye is up to the team.

## 20:23 IST: labels moved to `validation_data/labels/` (contents unchanged)

The three `points_<date>_labelled.csv` files moved from the project root to `validation_data/labels/`
with no edits (byte-identical). Labelled points: 11 Jan 59, 11 May 68, 29 Aug 76 (203 in total;
the other rows in each 150-row file have no label). Any by-eye corrections after the MNDWI check
will be committed separately and listed here with their reasons.
