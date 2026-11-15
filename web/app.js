// Sambhar Watch website. Reads the files that scripts/export_web.py puts in data/.

const DATA = "data/";

// The landing page and the app page each hold only some of the parts. A missing element is replaced by a
// detached one, so writing to it does nothing; whole parts are skipped in main() when their element is absent.
const has = id => document.getElementById(id) !== null;
const byId = id => document.getElementById(id) || document.createElement("div");
const ACCENT = "#0f5c6e";
const INK = "#1d2327";

// Draw each radar mode (DHDH dual-pol, QPDH quad-pol) as its own "Total" line and never join the
// two modes with a line. Set to false once the team has checked that the two modes agree.
const SPLIT_MODES = true;
const MODE_NAMES = { DHDH: "dual-pol DHDH", QPDH: "quad-pol QPDH" };

// Dates whose change holds up across threshold choices, with the reason shown on the page.
// Source: Terminal 1 sensitivity check, 19:20 IST (docs/log/terminal-1.md): 14 Oct is the lowest
// date in 10 of 12 threshold pairs. Its coherence pair is mixed-mode (QPDH to DHDH).
// The headline comparison at the top: optical and radar dates for "before" and "after".
const HERO = {
  before: { optical: "2026-08-29", radar: "2026-08-15" },
  after: { optical: "2026-10-13", radar: "2026-10-14" },
};

const ROBUST_DATES = {
  "2026-10-14": "the lowest date for 10 of 12 threshold choices (coherence from a QPDH-to-DHDH pair; provisional)",
};

let current = 0;   // index of the date shown on the map
let rows = [];     // rows of water_area.csv
let waterLayer, comparisonLayer, chart;
let className = "water";   // replaced by map_info.json class_name
let pansLabel = "mapped pans";   // replaced by map_info.json pans_label
// Name of the hand-drawn outlines in the map legend and layer box: they are rough zones, not surveyed pans.
const PANS_LAYER_NAME = "Salt-works zones (approximate, hand-drawn)";

async function main() {
  try {
    // Ask for all the start-up files at once: waiting for them one after another made the app slow to appear.
    const [info, areaText, lookup, pans, lake] = await Promise.all([
      getJSON("map_info.json"),
      getText("water_area.csv"),
      has("map") ? getJSON("frequency_lookup.json") : null,   // only the map needs it
      getJSON("pans.geojson").catch(() => null),    // optional
      getJSON("lake.geojson").catch(() => null),    // optional
    ]);
    rows = parseCSV(areaText);

    const hasComparison = await fileExists("comparison/" + rows[0].date + ".png");

    // Name of what is mapped, from map_info.json; older HH-only results have none and mean water.
    className = info.class_name || "water";
    document.querySelectorAll(".class-name").forEach(el => { el.textContent = className; });
    document.querySelectorAll(".class-name-cap").forEach(el => { el.textContent = capitalise(className); });
    pansLabel = info.pans_label || pansLabel;
    document.querySelectorAll(".pans-label-cap").forEach(el => { el.textContent = capitalise(pansLabel); });
    byId("rule-figure").hidden = !(await fileExists("rule_comparison.png"));

    byId("demo-banner").hidden = !info.demo;
    byId("legend-stable").hidden = !hasComparison;
    if (info.coherence_threshold !== undefined) {
      byId("rule-values").textContent =
        " (here: HH below " + info.threshold_db + " dB and coherence below " + info.coherence_threshold + ")";
    }
    byId("legend-lake").hidden = !lake;
    if (has("map")) makeMap(info, lookup, pans, lake, hasComparison);
    if (has("area-chart")) makeChart(info.area_scope);
    if (has("date-slider")) makeSlider();
    if (has("map")) showDate(0);
    byId("loading").classList.add("done");   // map and chart are up: lift the loading screen
    if (has("hero")) await makeHero(info.demo);
    if (has("optical-section")) await makeOptical(info.demo);
  } catch (error) {
    byId("loading").classList.add("done");
    const box = byId("load-error");
    box.hidden = false;
    box.textContent = "Could not load the data (" + error.message + "). " +
      "Run scripts/export_web.py, and open the page through a web server, e.g. python -m http.server -d web";
  }
}

// ---------- loading ----------

async function getText(name) {
  const response = await fetch(DATA + name, { cache: "no-cache" });   // always check for a newer file
  if (!response.ok) throw new Error(name + " not found");
  return response.text();
}

async function fileExists(name) {
  const response = await fetch(DATA + name, { method: "HEAD", cache: "no-cache" });
  return response.ok;
}

async function getJSON(name) {
  return JSON.parse(await getText(name));
}

/** Simple CSV reader for our own files (no quoted commas). Returns a list of objects. */
function parseCSV(text) {
  const lines = text.trim().split(/\r?\n/);
  const header = lines[0].split(",");
  return lines.slice(1).map(line => {
    const values = line.split(",");
    return Object.fromEntries(header.map((key, i) => [key, values[i]]));
  });
}

// ---------- map ----------

function makeMap(info, lookup, pans, lake, hasComparison) {
  const bounds = info.bounds_latlon;   // [[south, west], [north, east]]
  const map = L.map("map", { scrollWheelZoom: false }).fitBounds(bounds);

  if (info.demo) {   // keep the warning on the map itself, so screenshots of the map carry it too
    const label = L.control({ position: "bottomleft" });
    label.onAdd = () => L.DomUtil.create("div", "map-demo-label");
    label.addTo(map).getContainer().textContent = "DEMO DATA: synthetic, not NISAR results";
  }

  L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
    maxZoom: 18,
    attribution: "Imagery &copy; Esri, Maxar, Earthstar Geographics",
  }).addTo(map);

  // shortcut: overlays are stretched over a lat/lon box although the grid is UTM (tiny skew at this size);
  // reproject the PNGs to EPSG:3857 if pixel-exact placement is ever needed.
  waterLayer = L.imageOverlay(overlayUrl(0), bounds, { className: "pixelated" }).addTo(map);
  const frequencyLayer = L.imageOverlay(DATA + "frequency_overlay.png", bounds, { className: "pixelated" });

  const layers = { [capitalise(className)]: waterLayer };
  if (hasComparison) {
    // Orange: dark in HH alone, removed by the coherence rule. Never overlaps the blue layer.
    comparisonLayer = L.imageOverlay(comparisonUrl(0), bounds, { className: "pixelated" }).addTo(map);
    layers["Removed by coherence check"] = comparisonLayer;
  }
  layers["Detection frequency"] = frequencyLayer;
  if (pans) {
    layers[PANS_LAYER_NAME] = L.geoJSON(pans, {
      style: { color: "#ffffff", weight: 2, dashArray: "6 4", fill: false },
      interactive: false,
    }).addTo(map);
  }
  if (lake) {
    const lakeLayer = L.geoJSON(lake, {
      style: { color: "#ffd84d", weight: 2.5, fill: false },
      interactive: false,
    }).addTo(map);
    layers["Lake outline"] = lakeLayer;
    map.fitBounds(lakeLayer.getBounds(), { padding: [12, 12] });
  }
  L.control.layers(null, layers, { collapsed: window.innerWidth < 600 }).addTo(map);

  map.on("click", event => {
    L.popup().setLatLng(event.latlng).setContent(describeSpot(event.latlng, bounds, lookup)).openOn(map);
  });
}

function overlayUrl(index) {
  return DATA + "overlays/" + rows[index].date + ".png";
}

function comparisonUrl(index) {
  return DATA + "comparison/" + rows[index].date + ".png";
}

/** Popup text for a clicked spot: water-detection frequency and number of valid observations. */
function describeSpot(latlng, bounds, lookup) {
  const [[south, west], [north, east]] = bounds;
  const fy = (north - latlng.lat) / (north - south);
  const fx = (latlng.lng - west) / (east - west);
  if (fx < 0 || fx >= 1 || fy < 0 || fy >= 1) return "Outside the study area.";

  // Same lat/lon box as the image overlays, so the value matches what is drawn.
  const row = Math.min(lookup.rows - 1, Math.floor(Math.floor(fy * lookup.full_rows) / lookup.step));
  const col = Math.min(lookup.cols - 1, Math.floor(Math.floor(fx * lookup.full_cols) / lookup.step));
  const pct = lookup.frequency_pct[row * lookup.cols + col];
  const n = lookup.n_valid[row * lookup.cols + col];

  if (n === 0 || pct < 0) return "No valid radar observations here.";
  return "<strong>Detection frequency: " + pct + "%</strong><br>" +
    capitalise(className) + " on about " + Math.round(pct * n / 100) + " of " + n + " valid observations.";
}

// ---------- chart ----------

/** A number from the CSV, or null when the column is missing or blank (the chart leaves a gap). */
function number(row, key) {
  return row[key] === undefined || row[key] === "" ? null : Number(row[key]);
}

function hasRange(row) {
  return number(row, "water_km2_min") !== null && number(row, "water_km2_max") !== null;
}

/** True where the line from one date to the next would join two different radar modes. */
function joinsModes(ctx) {
  return SPLIT_MODES && rows[ctx.p0DataIndex].mode !== rows[ctx.p1DataIndex].mode;
}

function makeChart(areaScope) {
  const modes = SPLIT_MODES ? [...new Set(rows.map(r => r.mode))].sort() : [null];   // DHDH (main series) first
  const points = (key, mode) => rows.map(r => ({ x: Date.parse(r.date), y: !mode || r.mode === mode ? number(r, key) : null }));

  const line = (label, key, color, dash, mode = null) => ({
    label,
    data: points(key, mode),
    borderColor: color,
    backgroundColor: color,
    borderDash: dash,
    borderWidth: 2,
    segment: { borderColor: ctx => (joinsModes(ctx) ? "transparent" : undefined) },
    pointStyle: ctx => (ROBUST_DATES[rows[ctx.dataIndex].date] ? "star"
      : rows[ctx.dataIndex].mode === "QPDH" ? "triangle" : "circle"),
    pointRadius: ctx => (ROBUST_DATES[rows[ctx.dataIndex].date] ? 9 : ctx.dataIndex === current ? 6 : 3),
    pointHoverRadius: 7,
  });

  // Uncertainty band: an invisible "min" line, and a "max" line filled down to it ("-1" = previous dataset).
  const band = mode => [
    { label: "band", data: points("water_km2_min", mode), borderWidth: 0, pointRadius: 0, pointHitRadius: 0, fill: false },
    { label: "band", data: points("water_km2_max", mode), borderWidth: 0, pointRadius: 0, pointHitRadius: 0,
      fill: "-1", backgroundColor: "rgba(29, 35, 39, 0.13)" },
  ];

  const datasets = [];
  for (const mode of modes) {
    const which = mode && modes.length > 1 ? ", " + (MODE_NAMES[mode] || mode) : "";
    if (rows.some(hasRange)) datasets.push(...band(mode));
    datasets.push(line("Brightness + coherence" + which, "water_km2", INK, mode === "QPDH" ? [2, 3] : [], mode));
  }
  if (rows.some(r => number(r, "hh_only_water_km2") !== null)) {   // same orange as "removed by coherence" on the map
    datasets.push(line("Brightness only", "hh_only_water_km2", "rgb(240, 140, 0)", [5, 3]));
  }
  datasets.push(line("Inside " + pansLabel, "water_inside_mapped_pans_km2", ACCENT, []));
  datasets.push(line("Outside " + pansLabel, "water_outside_mapped_pans_km2", "#8a959b", [6, 4]));

  Chart.defaults.animation = false;   // draw the chart in its final state straight away
  if (window.innerWidth < 600) {      // phone: smaller text and legend marks, so the plot keeps its room
    Chart.defaults.font.size = 10;
    Chart.defaults.plugins.legend.labels.boxWidth = 16;
  }
  chart = new Chart(byId("area-chart"), {
    type: "line",
    data: { datasets },
    options: {
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: { type: "linear", ticks: { callback: value => shortDate(value), maxTicksLimit: 8 } },
        y: { beginAtZero: true, title: { display: true, text: "Detected area" + (areaScope ? " " + areaScope : "") + " (km²)" } },
      },
      plugins: {
        legend: { labels: { filter: item => item.text !== "band" } },
        tooltip: {
          filter: item => item.dataset.label !== "band" && item.parsed.y !== null,
          callbacks: {
            title: items => shortDate(items[0].parsed.x) + " · " + rows[items[0].dataIndex].mode,
            label: item => item.dataset.label + ": " + item.parsed.y.toFixed(1) + " km²",
            footer: items => [rangeText(rows[items[0].dataIndex]), robustText(rows[items[0].dataIndex])],
          },
        },
      },
      onClick: (event, elements) => {
        if (elements.length) showDate(elements[0].index);
      },
    },
  });

  byId("band-note").hidden = !rows.some(hasRange);
  const robust = rows.filter(r => ROBUST_DATES[r.date]);
  byId("robust-note").hidden = robust.length === 0;
  byId("robust-note-text").textContent =
    robust.map(r => shortDate(Date.parse(r.date)) + ": " + ROBUST_DATES[r.date]).join("; ");
  byId("mode-note").hidden = modes.length < 2;
}

/** "Robust change: ..." for the dates in ROBUST_DATES, otherwise "". */
function robustText(row) {
  return ROBUST_DATES[row.date] ? "Robust change: " + ROBUST_DATES[row.date] : "";
}

/** "Range 26.5-27.9 km² with other thresholds", or "" when the CSV has no range. */
function rangeText(row) {
  return hasRange(row) ? "Range " + rangeKm2(row) + " with other thresholds" : "";
}

/** "51.0–110.5 km²" from water_km2_min / water_km2_max. */
function rangeKm2(row) {
  return number(row, "water_km2_min").toFixed(1) + "–" + number(row, "water_km2_max").toFixed(1) + " km²";
}

function capitalise(text) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function shortDate(ms) {
  return new Date(ms).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
}

// ---------- hero: August vs October ----------

/** Fill the August vs October comparison, if both radar dates and both optical images are available. */
async function makeHero(demo) {
  const before = rows.find(r => r.date === HERO.before.radar);
  const after = rows.find(r => r.date === HERO.after.radar);
  const imagesThere = await fileExists("optical/" + HERO.before.optical + ".jpg") &&
    await fileExists("optical/" + HERO.after.optical + ".jpg");
  if (!before || !after || !imagesThere) return;
  byId("hero").hidden = false;

  for (const [side, row] of [["before", before], ["after", after]]) {
    const optical = DATA + "optical/" + HERO[side].optical + ".jpg";
    byId("hero-optical-" + side).src = optical;
    byId("hero-radar-" + side + "-base").src = optical;
    byId("hero-radar-" + side + "-removed").src = DATA + "comparison/" + row.date + ".png";
    byId("hero-radar-" + side + "-detected").src = DATA + "overlays/" + row.date + ".png";
    byId("hero-optical-" + side + "-text").textContent =
      "Sentinel-2 optical, " + shortDate(Date.parse(HERO[side].optical));
    byId("hero-radar-" + side + "-text").textContent =
      "NISAR radar, " + shortDate(Date.parse(row.date)) + (demo ? " (DEMO data)" : " (provisional)");
    byId("hero-col-" + side).textContent = shortDate(Date.parse(row.date));
  }

  // withRange: also show the water_km2 threshold range, e.g. "91 (51–110)"
  const cellText = (row, key, withRange) => "about " + Math.round(number(row, key)) + (withRange && hasRange(row)
    ? " (" + Math.round(number(row, "water_km2_min")) + "–" + Math.round(number(row, "water_km2_max")) + ")" : "");
  const tableRow = (label, key, strong) => {
    const change = Math.round(number(after, key)) - Math.round(number(before, key));
    return "<tr" + (strong ? ' class="strong"' : "") + "><td>" + label + "</td><td>" + cellText(before, key, strong) +
      "</td><td>" + cellText(after, key, strong) + "</td><td>" + (change > 0 ? "+" : "") + change + "</td></tr>";
  };
  byId("hero-table-body").innerHTML =
    tableRow("HH only (brightness)", "hh_only_water_km2", false) +
    tableRow("HH + coherence", "water_km2", true);

  const days = (a, b) => Math.abs(Date.parse(a) - Date.parse(b)) / 86400000;
  const paired = await pairedComparison(before, after);
  byId("hero-note").textContent =
    (paired ? paired + " " : "") +
    "Radar dates are the nearest DHDH dates: the August optical image is " + days(HERO.before.optical, before.date) +
    " days after its radar date, the October one " + days(HERO.after.optical, after.date) + " day before. " +
    (demo ? "Radar values are DEMO data." : "Results are provisional.");
}

/**
 * "At the same threshold settings, 14 Oct is lower than 15 Aug in N of 12 combinations (drop of a-b km²)."
 * Read from sensitivity_<mode>.csv, which has the area of every date for every threshold pair. "" if missing.
 */
async function pairedComparison(before, after) {
  const table = await getText("sensitivity_" + before.mode + ".csv").catch(() => null);
  if (!table) return "";
  const settings = row => row.threshold_db + "/" + row.coherence_threshold;
  const areaBefore = {};
  const all = parseCSV(table);
  all.filter(r => r.date === before.date).forEach(r => { areaBefore[settings(r)] = Number(r.water_km2); });
  const drops = all.filter(r => r.date === after.date && settings(r) in areaBefore)
    .map(r => areaBefore[settings(r)] - Number(r.water_km2));
  if (!drops.length) return "";
  const lower = drops.filter(d => d > 0);
  const name = date => new Date(Date.parse(date)).toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
  const mixedPairs = [before, after].every(r => (r.pair_modes || "").split("-").some(m => m !== r.mode));
  return "At the same threshold settings, " + name(after.date) + " is lower than " + name(before.date) + " in " +
    (lower.length === drops.length ? "all " : "") + lower.length + " of " + drops.length + " combinations" +
    (lower.length ? " (drop of about " + Math.round(Math.min(...lower)) + "–" + Math.round(Math.max(...lower)) + " km²)." : ".") +
    (before.mode === after.mode && mixedPairs
      ? " Both dates use mixed-mode coherence pairs, so they're treated alike; our mode check found coherence consistent" +
        " between modes; separate QPDH dates in Sep–Oct (56–60 km²) agree with the October value."
      : "");
}

// ---------- optical vs radar ----------

/** Fill the "Optical vs radar" section from data/optical/index.json (made by export_web.py), if present. */
async function makeOptical(demo) {
  const images = await getJSON("optical/index.json").catch(() => null);
  if (!images || !images.length) return;
  byId("optical-section").hidden = false;

  const tabs = byId("optical-tabs");
  const buttons = images.map(entry => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = new Date(Date.parse(entry.s2_date))
      .toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
    button.addEventListener("click", () => {
      buttons.forEach(b => b.setAttribute("aria-pressed", String(b === button)));
      showOptical(entry, demo);
    });
    tabs.appendChild(button);
    return button;
  });

  const start = Math.max(0, images.findIndex(e => e.s2_date === "2026-05-11"));   // the headline date
  buttons[start].click();
}

/** Show one Sentinel-2 date in the left panel and the radar result of its nearest NISAR date in the right panel.
    Both panels are the whole study area on the same grid, so they show exactly the same extent. */
function showOptical(entry, demo) {
  const optical = DATA + "optical/" + entry.s2_date + ".jpg";
  byId("swipe-optical").src = optical;
  byId("swipe-radar-base").src = optical;

  const radar = byId("swipe-radar");
  const caption = byId("optical-caption");
  const s2Text = "Sentinel-2 image " + shortDate(Date.parse(entry.s2_date));
  byId("swipe-optical-text").textContent = "Sentinel-2 optical, " + shortDate(Date.parse(entry.s2_date));
  if (entry.nisar_date) {
    radar.hidden = false;
    byId("swipe-radar-detected").src = DATA + "overlays/" + entry.nisar_date + ".png";
    const removed = byId("swipe-radar-removed");
    removed.hidden = byId("legend-stable").hidden;   // hidden when there is no comparison layer
    removed.src = DATA + "comparison/" + entry.nisar_date + ".png";
    caption.textContent = s2Text + " vs NISAR radar " + shortDate(Date.parse(entry.nisar_date)) +
      (entry.days_apart === 0 ? " (same day)" : " (" + entry.days_apart + " days apart)") +
      ". Blue: " + className + ". Orange: removed by the coherence check. Grey background: the same optical" +
      " image in grey, for orientation. Both panels show exactly the same area." +
      (entry.mode === "QPDH" ? " This radar date is quad-pol (QPDH): outside the main series, about 0.9 dB brighter in HH." : "") +
      (demo ? " Radar side: DEMO data, not NISAR results." : " Radar results are provisional.");
  } else {
    radar.hidden = true;
    caption.textContent = s2Text + ". No NISAR radar result within 6 days of this image, so only the optical image is shown.";
  }
  // The label names the actual radar date and mode; without a radar result there is no radar half at all.
  const tag = byId("swipe-tag-right");
  tag.hidden = !entry.nisar_date;
  if (entry.nisar_date) {
    const radarDay = new Date(Date.parse(entry.nisar_date))
      .toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
    tag.textContent = demo ? "NISAR radar (DEMO)" : "NISAR radar, " + radarDay + (entry.mode ? " (" + entry.mode + ")" : "");
  }
  byId("optical-headline").hidden = entry.s2_date !== "2026-05-11";
  byId("may-result").textContent = mayResult();
}

/** The radar result on 11 May, with the radar dates just before and after it, read from water_area.csv. */
function mayResult() {
  const i = rows.findIndex(r => r.date === "2026-05-11");
  if (i < 0) return "[no radar result for 11 May]";
  const r = rows[i];
  const around = [rows[i - 1], rows[i + 1]].filter(Boolean)
    .map(n => Math.round(number(n, "water_km2")) + " km² on " + shortDate(Date.parse(n.date)));
  return "about " + Math.round(number(r, "water_km2")) + " km² of " + className + " inside the lake outline" +
    (hasRange(r) ? " (range " + Math.round(number(r, "water_km2_min")) + "–" + Math.round(number(r, "water_km2_max")) + ")" : "") +
    (around.length ? ", similar to the radar dates before and after (" + around.join(" and ") + ")" : "");
}

// ---------- date slider ----------

function makeSlider() {
  const slider = byId("date-slider");
  slider.max = rows.length - 1;
  slider.addEventListener("input", () => showDate(Number(slider.value)));
}

/** Show one date: water layer on the map, slider position, label and chart highlight. */
function showDate(index) {
  current = index;
  const r = rows[index];
  waterLayer.setUrl(overlayUrl(index));
  if (comparisonLayer) comparisonLayer.setUrl(comparisonUrl(index));
  byId("date-slider").value = index;
  byId("date-label").textContent =
    shortDate(Date.parse(r.date)) + " · " + Number(r.water_km2).toFixed(1) + " km²" +
    (hasRange(r) ? " (" + number(r, "water_km2_min").toFixed(1) + "–" + number(r, "water_km2_max").toFixed(1) + ")" : "") +
    " · " + r.mode + (ROBUST_DATES[r.date] ? " · robust change" : "");
  if (chart) chart.update("none");
}

main();
