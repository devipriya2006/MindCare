async function loadDashboardCharts() {
  try {
    const res = await fetch("/api/mood-data");

    if (!res.ok) {
      console.error("Failed to load dashboard data.");
      return;
    }

    const data = await res.json();

    // 1. Mood trend chart
    const trendCtx = document.getElementById("trendChart");

    if (trendCtx && data.trend) {
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
          responsive: true,
          maintainAspectRatio: false,
        },
      });
    }

    // 2. Sentiment distribution chart
    const distCtx = document.getElementById("distributionChart");

    if (distCtx && data.distribution) {
      new Chart(distCtx, {
        type: "doughnut",
        data: {
          labels: Object.keys(data.distribution),
          datasets: [
            {
              data: Object.values(data.distribution),
              backgroundColor: ["#8fc1a9", "#f2d38a", "#e0938a"],
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
        },
      });
    }

    // 3. AI facial-expression distribution chart
    const faceCtx = document.getElementById("faceDistributionChart");

    if (faceCtx && data.face_distribution) {
      const labels = Object.keys(data.face_distribution);
      const values = Object.values(data.face_distribution);

      new Chart(faceCtx, {
        type: "doughnut",
        data: {
          labels,
          datasets: [
            {
              data: values,
              backgroundColor: [
                "#8fc1a9",
                "#f2d38a",
                "#e0938a",
                "#9c91c7",
                "#86b8d8",
                "#e8a7c0",
                "#b7b7b7",
              ],
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "bottom",
            },
            title: {
              display: true,
              text: "AI-Detected Facial Expressions",
            },
          },
        },
      });
    }
  } catch (err) {
    console.error("Failed to load mood data:", err);
  }
}

document.addEventListener("DOMContentLoaded", loadDashboardCharts);
