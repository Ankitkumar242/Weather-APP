/**
 * SkyPulse Chart Renderer using pinned local Chart.js
 * Implements 15-Day Temperature Band + Rain Bars, 48h Hourly Scrubbing, and State Aggregates.
 */

import { cToF } from "./units.js";

let timelineChartInstance = null;
let hourlyChartInstance = null;
let stateTrendChartInstance = null;

export function render15DayChart(canvasId, dailyItems, unit = "C") {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof Chart === "undefined" || !dailyItems || !dailyItems.length) return;

  if (timelineChartInstance) {
    timelineChartInstance.destroy();
  }

  const isF = unit === "F";
  const labels = dailyItems.map((d) => {
    const parts = d.date.split("-");
    const m = parts[1];
    const day = parts[2];
    return `${day}/${m}`;
  });

  const maxTemps = dailyItems.map((d) => (isF ? cToF(d.temp_max) : d.temp_max));
  const minTemps = dailyItems.map((d) => (isF ? cToF(d.temp_min) : d.temp_min));
  const rainSums = dailyItems.map((d) => d.precipitation_sum || 0);

  // Find index of Today
  const todayIdx = dailyItems.findIndex((d) => d.kind === "today");

  const pointColors = dailyItems.map((d) => {
    if (d.kind === "today") return "#2563EB";
    if (d.kind === "past") return "#94A3B8";
    return "#38BDF8";
  });

  const ctx = canvas.getContext("2d");

  // Vertical today marker plugin
  const todayLinePlugin = {
    id: "todayLine",
    afterDraw(chart) {
      if (todayIdx < 0) return;
      const meta = chart.getDatasetMeta(0);
      if (!meta.data[todayIdx]) return;
      const x = meta.data[todayIdx].x;
      const chartCtx = chart.ctx;
      chartCtx.save();
      chartCtx.beginPath();
      chartCtx.moveTo(x, chart.chartArea.top);
      chartCtx.lineTo(x, chart.chartArea.bottom);
      chartCtx.lineWidth = 1.5;
      chartCtx.strokeStyle = "rgba(37, 99, 235, 0.7)";
      chartCtx.setLineDash([4, 4]);
      chartCtx.stroke();

      // Label "Today"
      chartCtx.fillStyle = "#2563EB";
      chartCtx.font = "bold 10px sans-serif";
      chartCtx.fillText("Today", x - 14, chart.chartArea.top + 12);
      chartCtx.restore();
    },
  };

  timelineChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: `Max Temp (°${unit})`,
          data: maxTemps,
          borderColor: "#F97316",
          backgroundColor: "rgba(249, 115, 22, 0.15)",
          pointBackgroundColor: pointColors,
          pointBorderColor: "#FFFFFF",
          pointRadius: 4,
          tension: 0.35,
          yAxisID: "yTemp",
          fill: "+1", // Fill band down to min temp
        },
        {
          label: `Min Temp (°${unit})`,
          data: minTemps,
          borderColor: "#38BDF8",
          backgroundColor: "transparent",
          pointBackgroundColor: pointColors,
          pointBorderColor: "#FFFFFF",
          pointRadius: 4,
          tension: 0.35,
          yAxisID: "yTemp",
          fill: false,
        },
        {
          label: "Precipitation (mm)",
          type: "bar",
          data: rainSums,
          backgroundColor: "rgba(59, 130, 246, 0.45)",
          borderRadius: 4,
          yAxisID: "yRain",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
          labels: {
            boxWidth: 12,
            font: { size: 11 },
          },
        },
        tooltip: {
          callbacks: {
            label(context) {
              const val = context.parsed.y;
              if (context.datasetIndex === 2) {
                return ` Rain: ${val.toFixed(1)} mm`;
              }
              return ` ${context.dataset.label}: ${Math.round(val)}°${unit}`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { size: 10 } },
        },
        yTemp: {
          position: "left",
          grid: { color: "rgba(255, 255, 255, 0.08)" },
          ticks: {
            callback(val) {
              return `${Math.round(val)}°`;
            },
            font: { size: 10 },
          },
        },
        yRain: {
          position: "right",
          grid: { display: false },
          min: 0,
          suggestedMax: 15,
          ticks: {
            callback(val) {
              return `${val}mm`;
            },
            font: { size: 9 },
          },
        },
      },
    },
    plugins: [todayLinePlugin],
  });
}

export function renderHourlyChart(canvasId, hourlyItems, unit = "C") {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof Chart === "undefined" || !hourlyItems || !hourlyItems.length) return;

  if (hourlyChartInstance) {
    hourlyChartInstance.destroy();
  }

  const isF = unit === "F";
  const labels = hourlyItems.map((h) => {
    const timeStr = h.time.split("T")[1];
    return timeStr ? timeStr.slice(0, 5) : "";
  });

  const temps = hourlyItems.map((h) => (isF ? cToF(h.temperature) : h.temperature));
  const rainProb = hourlyItems.map((h) => h.precipitation_probability || 0);

  const ctx = canvas.getContext("2d");

  hourlyChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: `Temperature (°${unit})`,
          data: temps,
          borderColor: "#2563EB",
          backgroundColor: "rgba(37, 99, 235, 0.12)",
          borderWidth: 2.5,
          pointRadius: 2,
          pointHoverRadius: 5,
          tension: 0.35,
          fill: true,
          yAxisID: "yTemp",
        },
        {
          label: "Rain Chance (%)",
          type: "bar",
          data: rainProb,
          backgroundColor: "rgba(56, 189, 248, 0.4)",
          borderRadius: 3,
          yAxisID: "yRain",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
          labels: { boxWidth: 10, font: { size: 10 } },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            maxTicksLimit: 12,
            font: { size: 10 },
          },
        },
        yTemp: {
          position: "left",
          grid: { color: "rgba(255, 255, 255, 0.08)" },
          ticks: {
            callback(val) {
              return `${Math.round(val)}°`;
            },
            font: { size: 10 },
          },
        },
        yRain: {
          position: "right",
          min: 0,
          max: 100,
          grid: { display: false },
          ticks: {
            callback(val) {
              return `${val}%`;
            },
            font: { size: 9 },
          },
        },
      },
    },
  });
}

export function renderStateTrendChart(canvasId, trendPoints, unit = "C") {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof Chart === "undefined" || !trendPoints || !trendPoints.length) return;

  if (stateTrendChartInstance) {
    stateTrendChartInstance.destroy();
  }

  const isF = unit === "F";
  const labels = trendPoints.map((p) => {
    const parts = p.date.split("-");
    return `${parts[2]}/${parts[1]}`;
  });

  const maxTemps = trendPoints.map((p) => (isF ? cToF(p.avg_temp_max) : p.avg_temp_max));
  const minTemps = trendPoints.map((p) => (isF ? cToF(p.avg_temp_min) : p.avg_temp_min));

  const ctx = canvas.getContext("2d");

  stateTrendChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: `Avg State High (°${unit})`,
          data: maxTemps,
          borderColor: "#F97316",
          backgroundColor: "rgba(249, 115, 22, 0.12)",
          tension: 0.3,
          fill: "+1",
        },
        {
          label: `Avg State Low (°${unit})`,
          data: minTemps,
          borderColor: "#0284C7",
          backgroundColor: "transparent",
          tension: 0.3,
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top", labels: { font: { size: 10 } } },
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10 } } },
        y: {
          grid: { color: "rgba(255, 255, 255, 0.08)" },
          ticks: {
            callback(val) {
              return `${Math.round(val)}°`;
            },
            font: { size: 10 },
          },
        },
      },
    },
  });
}
