async function loadDashboardCharts() {
  try {
    const res = await fetch("/api/mood-data");
    if (!res.ok) return;
    const data = await res.json();

    const trendCtx = document.getElementById("trendChart");
    if (trendCtx) {
      new Chart(trendCtx, {
        type: "line",
        data: {
          labels: data.trend.map((d) => d.date),
          datasets: [
            {
              label: "Mood score",
              data: data.trend.map((d) => d.score),
              borderColor: "#4f8ea8",
              backgroundColor: "rgba(79, 142, 168, 0.15)",
              tension: 0.3,
              fill: true,
            },
          ],
        },
        options: {
          scales: {
            y: { min: 1, max: 5, ticks: { stepSize: 1 } },
          },
          plugins: { legend: { display: false } },
        },
      });
    }

    const distCtx = document.getElementById("distributionChart");
    if (distCtx) {
      const labels = Object.keys(data.distribution);
      const values = Object.values(data.distribution);
      new Chart(distCtx, {
        type: "doughnut",
        data: {
          labels,
          datasets: [
            {
              data: values,
              backgroundColor: ["#8fc1a9", "#f2d38a", "#e0938a"],
            },
          ],
        },
      });
    }
  } catch (err) {
    console.error("Failed to load mood data:", err);
  }
}

document.addEventListener("DOMContentLoaded", loadDashboardCharts);
