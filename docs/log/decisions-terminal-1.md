# Terminal 1 decisions

Format: HH:MM IST | decision | reason | evidence

- 18:12 IST (recorded; decided earlier) | Brightness-only water threshold dropped as the sole classifier; adding NISAR GUNW coherence (12-day pairs) as a hypothesis to test against Sentinel-2 | On real NISAR data the May (dry) and August (monsoon) lake bed are both about −22 dB HH, so HH cannot separate water from smooth salt crust | Team update message; docs/slides_outline.md slides 4–5; docs/project_page.md "How it works"
- 18:12 IST (recorded; decided earlier) | The 7-slide deck is the main deliverable; the 30 s video is optional | Deadline tonight 23:59 IST; limited time | Team update message; docs/slides_outline.md header
- 18:12 IST (recorded; decided earlier) | Ramsar figure kept at 24,000 ha designated, sourced to the Ramsar Sites Information Service | Needed a citable source | docs/project_page.md "Space Agency Partner and Other Data"
# Decisions: Terminal 1

- 18:01 IST | Demo data goes in outputs/demo/, not outputs/crops or outputs/results | crop_lake.py skips any date that is already cropped, so fake crops in outputs/crops would silently replace real NISAR dates | outputs/crops already had the real 2026-05-11.npz
- 18:04 IST | Image overlays and click lookups are placed in the lat/lon bounding box from map_info.json (no reprojection) | uses the existing map_water output format with no extra JS library; popups match what is drawn | grid 1442 x 1889 at 20 m, ~40 km across
- 18:04 IST | Click lookup uses every 5th pixel (longest side at most 400 cells) | keeps frequency_lookup.json small enough to load on a phone | 562 KB, 288 x 378 cells (~100 m)
- 18:04 IST | Frequency layer is transparent where frequency is 0 or there is no data; colours run over 30-100% of Blues | satellite image stays visible; low frequencies stay visibly blue | web/data/frequency_overlay.png
- 18:08 IST | validate.py skips points with no NISAR date within 6 days (--max-days) | half the 12-day repeat; the lake changes between dates | demo test: point 22 days away reported as too_far_in_time
- 18:08 IST | validate.py reports water vs not-water scores, plus salt crust and land false-water rates separately | wet salt crust is the main known confusion | demo: crust called water 50% (1/2)
