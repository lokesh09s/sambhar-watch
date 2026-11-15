"""Build docs/slides/Sambhar_Watch.pptx (7 slides, 16:9) from docs/slides_outline.md content.

Run from the repo root:  python docs/slides/build_deck.py
Needs python-pptx and Pillow. Reads figures from docs/figures, validation_data/sentinel2,
outputs/results/overlays and web/data/comparison; the app screenshot is docs/slides/assets/app_map.jpg.
"""
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "Sambhar_Watch.pptx"

TEAL = RGBColor(0x0F, 0x5C, 0x6E)      # same accent as the web app
INK = RGBColor(0x17, 0x25, 0x2B)
MUTED = RGBColor(0x5B, 0x6B, 0x70)
TINT = RGBColor(0xE7, 0xF1, 0xF3)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Calibri"

# Sentinel-2 and radar layers share one 1889 x 1442 grid; this box frames the lake.
LAKE_BOX = (60, 330, 1640, 1150)
S2 = ROOT / "validation_data/sentinel2"
CREDIT_S2 = "Images: ESA Copernicus Sentinel-2"
CREDIT_NISAR = "NASA/ASF NISAR"


def picture(slide, img, x, y, w=None, h=None):
    """Add a PIL image (saved as JPEG) at inches x, y with width or height in inches."""
    buf = BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=88)
    buf.seek(0)
    kw = {}
    if w is not None:
        kw["width"] = Inches(w)
    if h is not None:
        kw["height"] = Inches(h)
    return slide.shapes.add_picture(buf, Inches(x), Inches(y), **kw)


def trim(img):
    """Cut the white margins off a figure."""
    white = Image.new("RGB", img.size, (255, 255, 255))
    return img.crop(ImageChops.difference(img, white).getbbox())


def lake(path, max_w=1400):
    im = Image.open(path).convert("RGB").crop(LAKE_BOX)
    im.thumbnail((max_w, max_w))
    return im


def radar_panel(date):
    """Radar result on light grey: blue = detected, orange = dark but removed by coherence."""
    base = Image.new("RGBA", (1889, 1442), (233, 237, 238, 255))
    for layer in (ROOT / f"web/data/comparison/{date}.png", ROOT / f"outputs/results/overlays/{date}.png"):
        base.alpha_composite(Image.open(layer).convert("RGBA"))
    im = base.convert("RGB").crop(LAKE_BOX)
    im.thumbnail((1400, 1400))
    return im


def text(slide, x, y, w, h, paras, size=18, color=INK, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, space_after=0):
    """paras: list of str or list of runs [(text, {bold, color, size, italic})]."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        runs = [(para, {})] if isinstance(para, str) else para
        for t, o in runs:
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = FONT
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.italic = o.get("italic", False)
            f.color.rgb = o.get("color", color)
    return box


def card(slide, x, y, w, h, fill=TINT):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.adjustments[0] = 0.08
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def title(slide, t, size=34, h=0.9):
    text(slide, 0.6, 0.35, 12.1, h, [t], size=size, bold=True, color=INK, anchor=MSO_ANCHOR.TOP)


def credit(slide, t, y=7.05):
    text(slide, 0.6, y, 12.1, 0.3, [t], size=11, color=MUTED)


def notes(slide, t):
    slide.notes_slide.notes_text_frame.text = t


prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]

# 1. Title ------------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
text(s, 0.6, 1.5, 5.9, 1.1, ["Sambhar Watch"], size=54, bold=True, color=TEAL)
text(s, 0.6, 2.6, 5.9, 1.3, ["Watching India's largest saline lake through clouds, with NISAR radar"], size=24)
text(s, 0.6, 4.2, 5.9, 0.5, ["Team [TEAM NAME]"], size=22, bold=True)
text(s, 0.6, 4.7, 5.9, 0.9, ["[MEMBERS]"], size=20)
text(s, 0.6, 5.7, 5.9, 0.8, ["NASA Space Apps Challenge 2026", "Dancing with the SARs"], size=18, color=MUTED)
freq = Image.open(ROOT / "docs/figures/frequency_map.png").convert("RGB").crop((36, 125, 1105, 672))
picture(s, freq, 6.75, 1.75, w=6.0)
text(s, 6.75, 1.75 + 6.0 * freq.height / freq.width + 0.1, 6.0, 0.6,
     ["How often each spot was detected as water, Apr–Oct 2026. Red line: lake outline."], size=14, color=MUTED)
credit(s, f"Image: our water-detection frequency map from {CREDIT_NISAR} radar data")
notes(s, "Team name and members go here. Challenge: Dancing with the SARs. The image is our own product: "
         "how often each spot of Sambhar Lake was detected as water across 12 NISAR dates.")

# 2. Problem ----------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
title(s, "A lake that is hard to watch")
jan = lake(S2 / "2026-01-11_truecolour.png")
picture(s, jan, 0.6, 1.45, w=6.2)
text(s, 0.6, 1.45 + 6.2 * jan.height / jan.width + 0.1, 6.2, 0.9,
     ["India's largest inland saline lake", "Ramsar wetland: 24,000 ha"], size=18)
stats = [("131 → 117 km²", "natural water, 2022 → 2023"),
         ("49.5 → 51.5 km²", "salt pans, same years"),
         ("18,000+", "bird deaths, avian botulism, 2019")]
for i, (big, small) in enumerate(stats):
    y = 1.45 + i * 1.45
    card(s, 7.2, y, 5.5, 1.25)
    text(s, 7.45, y + 0.1, 5.1, 0.65, [big], size=34, bold=True, color=TEAL)
    text(s, 7.45, y + 0.72, 5.1, 0.45, [small], size=18)
text(s, 7.2, 5.85, 5.5, 0.9, ["Salt pans need to be told apart from natural wetland."], size=20, bold=True)
credit(s, "Sources: Ramsar Sites Information Service; NRSC-ISRO / VIT-AP study (2026); IVRI report (2019). "
          f"{CREDIT_S2}, 11 Jan 2026. About 70 km west of Jaipur.")
notes(s, "The 2026 NRSC-ISRO / VIT-AP study found natural water fell from 131 to 117 square km while salt pans "
         "grew from 49.5 to 51.5 (2022 to 2023), and its authors say salt pans need to be told apart from natural "
         "wetland. IVRI reported over 18,000 bird deaths from avian botulism in 2019.")

# 3. Why radar --------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
title(s, "Why radar: clouds, and optical traps")
text(s, 0.6, 1.3, 12.1, 0.9,
     ["Monsoon clouds hide the lake from optical satellites. NISAR's L-band radar sees through them."], size=20)
w, gap, y0 = 3.9, 0.2, 2.35
for i, (d, lab) in enumerate([("2026-05-06", "6 May: water"), ("2026-05-11", "11 May: white"),
                              ("2026-05-16", "16 May: water")]):
    x = 0.6 + i * (w + gap)
    im = lake(S2 / f"{d}_truecolour.png", 1000)
    if d == "2026-05-11":
        card(s, x - 0.07, y0 - 0.07, w + 0.14, w * im.height / im.width + 0.14, fill=TEAL)
    picture(s, im, x, y0, w=w)
    text(s, x, y0 + w * im.height / im.width + 0.15, w, 0.5, [lab], size=20, bold=True,
         color=TEAL if d == "2026-05-11" else INK, align=PP_ALIGN.CENTER)
card(s, 0.6, 5.5, 12.15, 1.1)
text(s, 0.85, 5.5, 11.7, 1.1,
     [[("One optical image can mislead. ", {"bold": True, "color": TEAL}),
       ("Can radar tell water from salt crust? We tested it.", {})]], size=24, anchor=MSO_ANCHOR.MIDDLE)
credit(s, f"{CREDIT_S2}, 6, 11 and 16 May 2026. NISAR is a NASA–ISRO mission; data free from NASA's ASF archive.")
notes(s, "Sentinel-2 shows the main basin as green water on 6 and 16 May, but white on 11 May. "
         "A single optical image can mislead. We don't yet know what the white surface is.")

# 4. Method -----------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
title(s, "How we tested it")
text(s, 0.6, 1.15, 12.1, 0.45, ["11 May 2026. Rule: HH below −18 dB and 12-day coherence below 0.3."], size=18)
cmp_ = Image.open(ROOT / "docs/figures/comparison_2026-05-11.png").convert("RGB")
cmp_ = trim(cmp_.crop((0, int(0.19 * cmp_.height), cmp_.width, cmp_.height)))   # drop the figure's own title
cmp_w = min(12.1, 2.95 * cmp_.width / cmp_.height)   # as wide as fits above the polarization line
picture(s, cmp_, 0.6 + (12.1 - cmp_w) / 2, 1.7, w=cmp_w)
text(s, 0.6, 4.78, 12.1, 0.6,
     [[("Polarization: ", {"bold": True, "color": TEAL}),
       ("HH brightness + 12-day coherence (coherence measures stability, it is not a polarization). "
        "HV not tested: over the lake it is likely near the noise floor (about −26.8 dB). "
        "Quad-pol HH is about 0.9 dB brighter than dual-pol; coherence agrees between modes.", {})]], size=16)
steps = [("1", "Brightness only", "fails: May ≈ Aug ≈ −22 dB"),
         ("2", "Add coherence", "water changes, crust doesn't"),
         ("3", "Stress test", "12 threshold settings"),
         ("4", "Check", "177 Sentinel-2 points")]
cw = (12.1 - 3 * 0.25) / 4
for i, (n, head, sub) in enumerate(steps):
    x = 0.6 + i * (cw + 0.25)
    card(s, x, 5.6, cw, 1.35)
    text(s, x + 0.15, 5.65, cw - 0.3, 0.45, [[(n + "  ", {"color": TEAL}), (head, {})]], size=20, bold=True)
    text(s, x + 0.15, 6.1, cw - 0.3, 0.8, [sub], size=18)
credit(s, f"Radar: {CREDIT_NISAR}, 11 May 2026. Hand-drawn outline: lake 152 km², pans 49.1 km². "
          "It misses about 10 km² of western lake bed; adding it does not change the Aug → Oct drop.")
notes(s, "Rule: HH below -18 dB AND 12-day coherence below 0.3 (provisional). Stress test: HH -17 to -20 dB, "
         "coherence 0.25 to 0.35. One date's area can shift 40-72 km2, so small April-August changes are within "
         "uncertainty. Each date uses the 12-day pair starting on that date (else the one ending on it). Modes DHDH and "
         "QPDH kept separate. Polarization: we used HH plus coherence; HV was not tested (likely near the noise "
         "floor over the lake, and HH usually gives better water/land contrast at L-band).")

# 5. Results (hero) ---------------------------------------------------------
s = prs.slides.add_slide(BLANK)
title(s, "Sambhar dries out after the monsoon. Brightness alone missed it; coherence caught it.",
      size=32, h=1.15)
gw, gg, gx, gy = 2.7, 0.15, 0.6, 1.92
text(s, gx, 1.55, gw, 0.4, ["August"], size=18, bold=True, align=PP_ALIGN.CENTER)
text(s, gx + gw + gg, 1.55, gw, 0.4, ["October"], size=18, bold=True, align=PP_ALIGN.CENTER)
row_h = None
for col, (s2d, rd) in enumerate([("2026-08-29", "2026-08-15"), ("2026-10-13", "2026-10-14")]):
    x = gx + col * (gw + gg)
    top = lake(S2 / f"{s2d}_truecolour.png", 900)
    row_h = gw * top.height / top.width
    picture(s, top, x, gy, w=gw)
    picture(s, radar_panel(rd), x, gy + row_h + gg, w=gw)
sy = gy + 2 * row_h + gg + 0.12
text(s, gx, sy, 6.2, 1.0,
     [[("Brightness only: ", {}), ("about 125 → 115 km²", {"bold": True})],
      [("+ Coherence: ", {"color": TEAL, "bold": True}), ("about 91 → 56 km²", {"color": TEAL, "bold": True})],
      [("The drop holds under every threshold setting we tested.", {"bold": True})]],
     size=18)

# Lead with balanced accuracy: 76% of points are water, so plain accuracy rewards over-counting.
rows = [("Checked on\n177 Sentinel-2 points", "Brightness only", "+ Coherence", None),
        ("Balanced accuracy", "58%", "68%", 2),
        ("Water found", "89%", "60%", 1),
        ("Non-water found\n(crust, land)", "28%", "77%", 2),
        ("Accuracy, late Aug\n(crust spreading)", "62%", "73%", 2),
        ("Accuracy, 11 Jan\n(lake full)", "86%", "44%", 1)]
tx, ty, tw = 6.9, 1.55, 5.85
heights = [0.8, 0.45, 0.45, 0.75, 0.75, 0.75]
tbl = s.shapes.add_table(len(rows), 3, Inches(tx), Inches(ty), Inches(tw), Inches(sum(heights))).table
tbl.columns[0].width, tbl.columns[1].width, tbl.columns[2].width = Inches(2.95), Inches(1.45), Inches(1.45)
tbl.first_row = True
for r, (lab, a, b, win) in enumerate(rows):
    tbl.rows[r].height = Inches(heights[r])
    for c, val in enumerate((lab, a, b)):
        cell = tbl.cell(r, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = TEAL if r == 0 else (TINT if r % 2 == 0 else WHITE)
        cell.margin_left = cell.margin_right = Inches(0.08)
        cell.margin_top = cell.margin_bottom = Inches(0.03)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.word_wrap = True
        tf.paragraphs[0].text = ""
        for i, line in enumerate(val.split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
            run = p.add_run()
            run.text = line
            f = run.font
            f.name = FONT
            f.size = Pt(18)
            f.bold = r <= 1 or (win == c)
            f.color.rgb = WHITE if r == 0 else (TEAL if win == c else INK)
text(s, tx, ty + sum(heights) + 0.1, tw, 0.7,
     ["Plain accuracy: 74% vs 64%, but always saying “water” scores 76%."], size=18)
card(s, 0.6, 6.27, 12.15, 0.58)
text(s, 0.75, 6.27, 11.9, 0.58,
     [[("A trade-off: ", {"bold": True, "color": TEAL}),
       ("brightness over-counts, coherence under-counts. Together they bracket the true area.", {})]],
     size=20, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.6, 6.9, 12.1, 0.5,
     [f"Top: ESA Copernicus Sentinel-2, 29 Aug, 13 Oct. Bottom: {CREDIT_NISAR}, 15 Aug, 14 Oct; blue = water "
      "detected on these dates, orange = removed by coherence; inside the 152 km² lake. "
      "Both dates use mixed-mode coherence pairs, so they're treated alike; our mode check found coherence "
      "consistent between modes; separate QPDH dates in Sep–Oct (56–60 km²) agree with the October value."],
     size=10, color=MUTED)
notes(s, "76% of validation points were water, so plain accuracy rewards over-counting; a model that always says "
         "'water' scores 76%. Weighting water and non-water equally, coherence is better (68% vs 58%), while "
         "brightness still finds more water. Counts: n=177 (134 water, 43 non-water = 37 crust + 6 land); "
         "brightness water 119/134, non-water 12/43; coherence water 80/134, non-water 33/43. Don't hide the 64% "
         "plain accuracy. The headline is about the post-monsoon drying, a crust-spreading period, where coherence "
         "validated better (73% vs 62%). Areas are approximate: about 91 to about 56 km2 (51-110 to 34-72 across "
         "settings); the drop holds in 12 of 12 settings (16.9-38.7 km2). Labels: an MNDWI audit flagged 5 of 203 "
         "blind labels as mixed-edge or white-film pixels; all were kept unchanged to avoid post-hoc bias. Limits: "
         "radar overestimates in October (56 vs ~30-40 km2 optical, likely reservoir and wet edges); January misses "
         "are unresolved (hypotheses: calm stable shallow water or thin brine films; stable sub-pixel features such "
         "as salt rafts or mud ridges; coherence biased upward at low signal); 20 m nearest-neighbour resampling, "
         "3x3 smoothing in dB, GUNW coherence on a coarser window. Strength: one track, constant incidence angle. "
         "Wet salt crust can look like water; we tested this.")

# 6. The app ----------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
title(s, "The app: pick a date, see the water")
# The app's own legend is too small for a projector, so crop it off and restate it at 18 pt.
app = Image.open(Path(__file__).resolve().parent / "assets/app_map.jpg").crop((0, 0, 928, 575))
aw = 6.2
picture(s, app, 0.6, 1.4, w=aw)
BLUE, ORANGE, GOLD = RGBColor(0x1F, 0x77, 0xB4), RGBColor(0xE0, 0x8A, 0x10), RGBColor(0xC9, 0x9A, 0x06)
text(s, 0.6, 1.4 + aw * app.height / app.width + 0.15, aw, 1.0,
     [[("Blue: ", {"bold": True, "color": BLUE}), ("water detected   ", {}),
       ("Orange: ", {"bold": True, "color": ORANGE}), ("removed by coherence", {})],
      [("Yellow: ", {"bold": True, "color": GOLD}), ("lake outline   ", {}),
       ("Dashed: ", {"bold": True}), ("salt works and pans", {})]], size=18)
area = Image.open(ROOT / "docs/figures/area_over_time.png").convert("RGB")
area = area.crop((0, 60, area.width, int(0.83 * area.height)))   # drop the figure's title and small legend
cx, cwid = 7.1, 5.65
picture(s, area, cx, 1.4, w=cwid)
ky = 1.4 + cwid * area.height / area.width + 0.15
text(s, cx, ky, cwid, 1.25,
     [[("Orange: ", {"bold": True, "color": ORANGE}), ("brightness only (upper bound)", {})],
      [("Blue: ", {"bold": True, "color": BLUE}), ("+ coherence (lower bound)", {})],
      [("Band: ", {"bold": True, "color": BLUE}), ("range over 12 threshold settings", {})],
      [("Grey squares: ", {"bold": True, "color": MUTED}), ("quad-pol dates, not comparable", {})]], size=18)
text(s, cx, ky + 1.6, cwid, 1.1,
     ["Drag the slider: see each radar date",
      [("[APP URL]", {"bold": True, "color": TEAL})]], size=18, space_after=6)
credit(s, f"Screenshot of our web app (map imagery © Esri, Maxar, Earthstar Geographics). Radar: {CREDIT_NISAR}.")
notes(s, "This is the user experience. Who would use it: wetland managers, researchers, bird-watch groups.")

# 7. Recommendation and proposed use -----------------------------------------
s = prs.slides.add_slide(BLANK)
title(s, "Recommendation and proposed use")
card(s, 0.6, 1.2, 12.15, 0.9, fill=TEAL)
text(s, 0.85, 1.2, 11.7, 0.9,
     ["Use brightness when the lake is full, add coherence when crust is present, "
      "and report both as upper and lower bounds."], size=20, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.6, 2.2, 12.1, 0.45, ["Why does the lake change? (hypothesis, not proven)"], size=20, bold=True, color=TEAL)
drivers = [("Monsoon (Jul–Sep)", "Rain and seasonal streams flow into the shallow lake"),
           ("After the rains", "Evaporation shrinks the water: wet brine, then salt crust"),
           ("Salt works", "Brine pumped into the pans: a managed cycle, not only weather")]
dw = (12.15 - 2 * 0.25) / 3
for i, (head, body) in enumerate(drivers):
    x = 0.6 + i * (dw + 0.25)
    card(s, x, 2.68, dw, 1.2)
    text(s, x + 0.15, 2.73, dw - 0.3, 0.4, [head], size=18, bold=True, color=TEAL)
    text(s, x + 0.15, 3.1, dw - 0.3, 0.75, [body], size=16)
text(s, 0.6, 3.95, 12.1, 0.6,
     [[("Not seen: ", {"bold": True}),
       ("no clear monsoon rise in radar water area. Per-date uncertainty (40–72 km²) is larger than the "
        "April–August changes, and shallow water vs wet crust is hard to separate.", {})]], size=16)
text(s, 0.6, 4.65, 12.1, 0.45, ["How this would be used (proposed)"], size=20, bold=True, color=TEAL)
uses = [("Who", "Wetland managers, researchers, bird-watch groups"),
        ("Every 12 days", "Each new NISAR pass updates the map"),
        ("Early warning", "Flag when the lake dries fast"),
        ("Free and open", "Free NASA data, open code; scales to other salt lakes")]
cw = (12.15 - 3 * 0.25) / 4
for i, (head, body) in enumerate(uses):
    x = 0.6 + i * (cw + 0.25)
    card(s, x, 5.12, cw, 1.35)
    text(s, x + 0.15, 5.17, cw - 0.3, 0.4, [head], size=18, bold=True, color=TEAL)
    text(s, x + 0.15, 5.55, cw - 0.3, 0.9, [body], size=16)
text(s, 0.6, 6.55, 12.1, 0.45,
     [[("Next: ", {"bold": True}),
       ("grows with NISAR's record · combine with optical data · ground truth from the wetland authority", {})]],
     size=16)
credit(s, "Thank you · [REPO URL] · Data: NASA/ASF NISAR (GCOV, GUNW), ESA Copernicus Sentinel-2")
notes(s, "Everything on this slide is a proposed use, not something already running. The three drivers are a "
         "hypothesis, not proven: monsoon inflow, evaporation after the rains, and the salt works pumping brine "
         "into the mapped pans. We did not see a clear monsoon rise in radar water area. Limitation: the lake outline "
         "was hand-drawn from optical imagery and misses part of the western lake bed (about 10 km2, visible in the "
         "radar). Reported areas are inside the outline only, so they understate the full lake bed. Including it "
         "does not change the August to October drop (about 91 to 56 km2 inside; about 98 to 59 km2 with the arm).")

for number, slide in enumerate(prs.slides, start=1):
    if number > 1:
        text(slide, 11.9, 7.05, 0.85, 0.3, [f"{number} / {len(prs.slides)}"], size=11, color=MUTED, align=PP_ALIGN.RIGHT)

prs.save(OUT)
print(f"wrote {OUT} ({len(prs.slides)} slides)")
assert len(prs.slides) == 7
