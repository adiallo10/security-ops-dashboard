/* Security Ops Mini-Dashboard front-end.
 * Fetches aggregated data from the Flask backend, renders charts with Chart.js,
 * and asks the backend to explain the currently selected trend. */

const SEVERITY_COLORS = {
  low: "#3fb950",
  medium: "#d29922",
  high: "#f85149",
  critical: "#da3633",
};
const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

let dashboardData = null;
let trendChart = null;

async function init() {
  const res = await fetch("/api/alerts");
  dashboardData = await res.json();

  renderStats(dashboardData);
  populateSeriesSelect(dashboardData);
  renderTrendChart(currentSeries());
  renderCategoryChart(dashboardData);
  renderHeatmap(dashboardData);

  document.getElementById("series").addEventListener("change", () => {
    hideExplanation();
    renderTrendChart(currentSeries());
  });
  document.getElementById("explainBtn").addEventListener("click", explainTrend);
}

function renderStats(data) {
  const stats = document.getElementById("stats");
  const counts = data.severity_counts;
  const tiles = [
    { l: "Total", n: data.total, cls: "" },
    { l: "Low", n: counts.low, cls: "low" },
    { l: "Medium", n: counts.medium, cls: "medium" },
    { l: "High", n: counts.high, cls: "high" },
    { l: "Critical", n: counts.critical, cls: "critical" },
  ];
  stats.innerHTML = tiles
    .map((t) => `<div class="tile ${t.cls}"><div class="n">${t.n}</div><div class="l">${t.l}</div></div>`)
    .join("");
}

function populateSeriesSelect(data) {
  const select = document.getElementById("series");
  const options = ["total", ...Object.keys(data.trend.by_category)];
  select.innerHTML = options
    .map((o) => `<option value="${o}">${o === "total" ? "All alerts" : o}</option>`)
    .join("");
}

function currentSeries() {
  return document.getElementById("series").value || "total";
}

function seriesValues(series) {
  return series === "total"
    ? dashboardData.trend.total
    : dashboardData.trend.by_category[series];
}

function renderTrendChart(series) {
  const labels = dashboardData.trend.labels;
  const values = seriesValues(series);
  const ctx = document.getElementById("trendChart");

  if (trendChart) trendChart.destroy();
  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: series === "total" ? "All alerts" : series,
          data: values,
          borderColor: "#58a6ff",
          backgroundColor: "rgba(88,166,255,0.15)",
          fill: true,
          tension: 0.3,
          pointRadius: 2,
        },
      ],
    },
    options: baseChartOptions(),
  });
}

function renderCategoryChart(data) {
  const ctx = document.getElementById("categoryChart");
  const cats = data.top_categories;
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: cats.map((c) => c.category),
      datasets: [
        {
          label: "Alerts",
          data: cats.map((c) => c.count),
          backgroundColor: "#58a6ff",
          borderRadius: 4,
        },
      ],
    },
    options: baseChartOptions(),
  });
}

function renderHeatmap(data) {
  const container = document.getElementById("heatmap");
  const max = Math.max(...data.heatmap.map((c) => c.count), 1);
  const byKey = {};
  data.heatmap.forEach((c) => (byKey[`${c.weekday}-${c.hour}`] = c.count));

  let html = "";
  for (let wd = 0; wd < 7; wd++) {
    html += `<div class="h-label">${WEEKDAYS[wd]}</div>`;
    for (let hr = 0; hr < 24; hr++) {
      const count = byKey[`${wd}-${hr}`] || 0;
      const alpha = count === 0 ? 0 : 0.15 + 0.85 * (count / max);
      const bg = count === 0 ? "#1f2733" : `rgba(88,166,255,${alpha.toFixed(2)})`;
      html += `<div class="cell" style="background:${bg}" title="${WEEKDAYS[wd]} ${hr}:00 — ${count} alerts"></div>`;
    }
  }
  container.innerHTML = html;
}

function baseChartOptions() {
  return {
    responsive: true,
    plugins: { legend: { labels: { color: "#8b949e" } } },
    scales: {
      x: { ticks: { color: "#8b949e", maxRotation: 0, autoSkip: true }, grid: { color: "#21262d" } },
      y: { ticks: { color: "#8b949e" }, grid: { color: "#21262d" }, beginAtZero: true },
    },
  };
}

async function explainTrend() {
  const btn = document.getElementById("explainBtn");
  const box = document.getElementById("explanation");
  const series = currentSeries();

  btn.disabled = true;
  btn.textContent = "Analyzing…";
  box.hidden = false;
  box.textContent = "Analyzing the trend…";

  try {
    const res = await fetch("/api/explain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        series,
        labels: dashboardData.trend.labels,
        values: seriesValues(series),
      }),
    });
    const data = await res.json();
    box.innerHTML = `${escapeHtml(data.explanation)}<span class="prov">Explanation source: ${data.provider}</span>`;
  } catch (err) {
    box.textContent = "Sorry — could not generate an explanation.";
  } finally {
    btn.disabled = false;
    btn.textContent = "Explain this trend";
  }
}

function hideExplanation() {
  const box = document.getElementById("explanation");
  box.hidden = true;
  box.textContent = "";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

init();
