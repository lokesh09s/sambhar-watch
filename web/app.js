// Sambhar Watch website. Reads the files that scripts/export_web.py puts in data/.

const DATA = "data/";
const ACCENT = "#0f5c6e";
const INK = "#1d2327";

// Draw each radar mode (DHDH dual-pol, QPDH quad-pol) as its own "Total" line and never join the
// two modes with a line. Set to false once the team has checked that the two modes agree.
const SPLIT_MODES = true;
const MODE_NAMES = { DHDH: "dual-pol DHDH", QPDH: "quad-pol QPDH" };

let current = 0;   // index of the date shown on the map
let rows = [];     // rows of water_area.csv
let waterLayer, comparisonLayer, chart;
let className = "water";   // replaced by map_info.json class_name
let pansLabel = "mapped pans";   // replaced by map_info.json pans_label

async function main() {
  try {
    const info = await getJSON("map_info.json");
    rows = parseCSV(await getText("water_area.csv"));
    const lookup = await getJSON("frequency_lookup.json");
    const pans = await getJSON("pans.geojson").catch(() => null);   // optional
    const lake = await getJSON("lake.geojson").catch(() => null);   // optional

    const hasComparison = await fileExists("comparison/" + rows[0].date + ".png");

    // Name of what is mapped, from map_info.json; older HH-only results have none and mean water.
    className = info.class_name || "water";
    document.querySelectorAll(".class-name").forEach(el => { el.textContent = className; });
    document.querySelectorAll(".class-name-cap").forEach(el => { el.textContent = capitalise(className); });
    pansLabel = info.pans_label || pansLabel;
    document.querySelectorAll(".pans-label-cap").forEach(el => { el.textContent = capitalise(pansLabel); });
    document.getElementById("rule-figure").hidden = !(await fileExists("rule_comparison.png"));

    document.getElementById("demo-banner").hidden = !info.demo;
    document.getElementById("legend-stable").hidden = !hasComparison;
    if (info.coherence_threshold !== undefined) {
      document.getElementById("rule-values").textContent =
        " (here: HH below " + info.threshold_db + " dB and coherence below " + info.coherence_threshold + ")";
    }
    document.getElementById("legend-lake").hidden = !lake;
    makeMap(info, lookup, pans, lake, hasComparison);
    makeChart(info.area_scope);
    makeSlider();
    showDate(0);
  } catch (error) {
    const box = document.getElementById("load-error");
    box.hidden = false;
    box.textContent = "Could not load the data (" + error.message + "). " +
      "Run scripts/export_web.py, and open the page through a web server, e.g. python -m http.server -d web";
  }
}

// ---------- loading ----------

async function getText(name) {
  const response = await fetch(DATA + name);
  if (!response.ok) throw new Error(name + " not found");
  return response.text();
}

async function fileExists(name) {
  const response = await fetch(DATA + name, { method: "HEAD" });
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
    layers[capitalise(pansLabel)] = L.geoJSON(pans, {
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
    pointStyle: ctx => (rows[ctx.dataIndex].mode === "QPDH" ? "triangle" : "circle"),
    pointRadius: ctx => (ctx.dataIndex === current ? 6 : 3),
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
    datasets.push(line("Total" + (areaScope ? " " + areaScope : "") + which, "water_km2", INK,
                       mode === "QPDH" ? [2, 3] : [], mode));
  }
  datasets.push(line("Inside " + pansLabel, "water_inside_mapped_pans_km2", ACCENT, []));
  datasets.push(line("Outside " + pansLabel, "water_outside_mapped_pans_km2", "#8a959b", [6, 4]));

  chart = new Chart(document.getElementById("area-chart"), {
    type: "line",
    data: { datasets },
    options: {
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: { type: "linear", ticks: { callback: value => shortDate(value), maxTicksLimit: 8 } },
        y: { beginAtZero: true, title: { display: true, text: capitalise(className) + " (km²)" } },
      },
      plugins: {
        legend: { labels: { filter: item => item.text !== "band" } },
        tooltip: {
          filter: item => item.dataset.label !== "band" && item.parsed.y !== null,
          callbacks: {
            title: items => shortDate(items[0].parsed.x) + " · " + rows[items[0].dataIndex].mode,
            label: item => item.dataset.label + ": " + item.parsed.y.toFixed(1) + " km²",
            footer: items => rangeText(rows[items[0].dataIndex]),
          },
        },
      },
      onClick: (event, elements) => {
        if (elements.length) showDate(elements[0].index);
      },
    },
  });

  document.getElementById("band-note").hidden = !rows.some(hasRange);
  document.getElementById("mode-note").hidden = modes.length < 2;
}

/** "Range 26.5-27.9 km² with other thresholds", or "" when the CSV has no range. */
function rangeText(row) {
  if (!hasRange(row)) return "";
  return "Range " + number(row, "water_km2_min").toFixed(1) + "–" + number(row, "water_km2_max").toFixed(1) +
    " km² with other thresholds";
}

function capitalise(text) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function shortDate(ms) {
  return new Date(ms).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
}

// ---------- date slider ----------

function makeSlider() {
  const slider = document.getElementById("date-slider");
  slider.max = rows.length - 1;
  slider.addEventListener("input", () => showDate(Number(slider.value)));
}

/** Show one date: water layer on the map, slider position, label and chart highlight. */
function showDate(index) {
  current = index;
  const r = rows[index];
  waterLayer.setUrl(overlayUrl(index));
  if (comparisonLayer) comparisonLayer.setUrl(comparisonUrl(index));
  document.getElementById("date-slider").value = index;
  document.getElementById("date-label").textContent =
    shortDate(Date.parse(r.date)) + " · " + Number(r.water_km2).toFixed(1) + " km²" +
    (hasRange(r) ? " (" + number(r, "water_km2_min").toFixed(1) + "–" + number(r, "water_km2_max").toFixed(1) + ")" : "") +
    " · " + r.mode;
  chart.update("none");
}

main();
