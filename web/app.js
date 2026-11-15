// Sambhar Watch website. Reads the files that scripts/export_web.py puts in data/.

const DATA = "data/";
const ACCENT = "#0f5c6e";

let current = 0;   // index of the date shown on the map
let rows = [];     // rows of water_area.csv
let waterLayer, comparisonLayer, chart;
let className = "water";   // replaced by map_info.json class_name

async function main() {
  try {
    const info = await getJSON("map_info.json");
    rows = parseCSV(await getText("water_area.csv"));
    const lookup = await getJSON("frequency_lookup.json");
    const pans = await getJSON("pans.geojson").catch(() => null);   // optional

    const hasComparison = await fileExists("comparison/" + rows[0].date + ".png");

    // Name of what is mapped, from map_info.json; older HH-only results have none and mean water.
    className = info.class_name || "water";
    document.querySelectorAll(".class-name").forEach(el => { el.textContent = className; });
    document.querySelectorAll(".class-name-cap").forEach(el => { el.textContent = capitalise(className); });
    document.getElementById("rule-figure").hidden = !(await fileExists("rule_comparison.png"));

    document.getElementById("demo-banner").hidden = !info.demo;
    document.getElementById("legend-stable").hidden = !hasComparison;
    if (info.coherence_threshold !== undefined) {
      document.getElementById("rule-values").textContent =
        " (here: HH below " + info.threshold_db + " dB and coherence below " + info.coherence_threshold + ")";
    }
    makeMap(info, lookup, pans, hasComparison);
    makeChart();
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

function makeMap(info, lookup, pans, hasComparison) {
  const bounds = info.bounds_latlon;   // [[south, west], [north, east]]
  const map = L.map("map", { scrollWheelZoom: false }).fitBounds(bounds);

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
    layers["Dark but stable (HH only vs HH + coherence)"] = comparisonLayer;
  }
  layers["Detection frequency"] = frequencyLayer;
  if (pans) {
    layers["Mapped salt pans"] = L.geoJSON(pans, {
      style: { color: "#ffffff", weight: 2, dashArray: "6 4", fill: false },
      interactive: false,
    }).addTo(map);
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

/** Dates with fewer than two coherence pairs are less certain. Files without the column are never flagged. */
function fewPairs(row) {
  return row.coherence_pairs !== undefined && Number(row.coherence_pairs) < 2;
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

function makeChart() {
  const series = (label, key, color, dash) => ({
    label,
    data: rows.map(r => ({ x: Date.parse(r.date), y: Number(r[key]) })),
    borderColor: color,
    backgroundColor: color,
    borderDash: dash,
    borderWidth: 2,
    pointRadius: ctx => (ctx.dataIndex === current ? 6 : 3),
    pointBackgroundColor: ctx => (fewPairs(rows[ctx.dataIndex]) ? "#ffffff" : color),   // hollow = only 1 pair
    pointHoverRadius: 7,
  });

  chart = new Chart(document.getElementById("area-chart"), {
    type: "line",
    data: {
      datasets: [
        series("Total", "water_km2", "#1d2327", []),
        series("Inside mapped pans", "water_inside_mapped_pans_km2", ACCENT, []),
        series("Outside mapped pans", "water_outside_mapped_pans_km2", "#8a959b", [6, 4]),
      ],
    },
    options: {
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: { type: "linear", ticks: { callback: value => shortDate(value), maxTicksLimit: 8 } },
        y: { beginAtZero: true, title: { display: true, text: capitalise(className) + " (km²)" } },
      },
      plugins: {
        tooltip: {
          callbacks: {
            title: items => shortDate(items[0].parsed.x),
            label: item => item.dataset.label + ": " + item.parsed.y.toFixed(1) + " km²",
            footer: items => (fewPairs(rows[items[0].dataIndex]) ? "Only 1 coherence pair: less certain" : ""),
          },
        },
      },
      onClick: (event, elements) => {
        if (elements.length) showDate(elements[0].index);
      },
    },
  });
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
    (fewPairs(r) ? " · only 1 coherence pair" : "");
  chart.update("none");
}

main();
