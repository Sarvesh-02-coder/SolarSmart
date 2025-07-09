function generateLastMonthLabels() {
  let labels = [];
  let today = new Date();
  for (let i = 29; i >= 0; i--) {
    let d = new Date(today);
    d.setDate(d.getDate() - i);
    labels.push(d.toLocaleDateString('en-US', { day: 'numeric', month: 'short' }));
  }
  return labels;
}

function generateNext10DaysLabels() {
  let labels = [];
  let today = new Date();
  for (let i = 1; i <= 10; i++) {
    let d = new Date(today);
    d.setDate(d.getDate() + i);
    labels.push(d.toLocaleDateString('en-US', { day: 'numeric', month: 'short' }));
  }
  return labels;
}

let lastMonthChartInstance = null;
let forecastChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
  const result = JSON.parse(localStorage.getItem("solarPrediction"));
  console.log(" LocalStorage result:", result);

  if (!result) {
    alert("No prediction data found. Please return to the homepage and try again.");
    window.location.href = "index.html";
    return;
  }

  // Show message if all values are zero
  if (
    result.current_power === 0 &&
    result.daily_avg === 0 &&
    result.monthly_avg === 0 &&
    result.yearly_avg === 0
  ) {
    alert("No sunlight or solar data available for the selected location and time.");
  }

  document.getElementById("currentPower").textContent = `${result.current_power} kWh`;
  document.getElementById("electricitySaved").textContent = `Rs ${result.money_saved}`;
  document.getElementById("dailyAvg").textContent = `${result.daily_avg} kWh`;
  

  

  const lastMonthLabels = generateLastMonthLabels();
  const forecastLabels = generateNext10DaysLabels();

  const lastMonthCtx = document.getElementById("lastMonthChart").getContext("2d");
  const forecastCtx = document.getElementById("forecastChart").getContext("2d");

  // Destroy previous charts if they exist
  if (lastMonthChartInstance) lastMonthChartInstance.destroy();
  if (forecastChartInstance) forecastChartInstance.destroy();

  // Last Month Chart
  lastMonthChartInstance = new Chart(lastMonthCtx, {
    type: "line",
    data: {
      labels: lastMonthLabels,
      datasets: [{
        label: "Power (kWh)",
        data: result.last_month_kwh,
        borderColor: "#f97316",
        backgroundColor: "rgba(249, 115, 22, 0.3)",
        fill: true,
        tension: 0.3,
        pointRadius: 3,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: "#f97316" } }
      },
      scales: {
        x: { ticks: { color: "#f97316" } },
        y: {
          beginAtZero: true,
          ticks: { color: "#f97316" }
        }
      }
    }
  });

  // Forecast Chart
  forecastChartInstance = new Chart(forecastCtx, {
    type: "bar",
    data: {
      labels: forecastLabels,
      datasets: [{
        label: "Forecast Power (kWh)",
        data: result.forecast_10_days_kwh,
        backgroundColor: "#ec4899",
        borderRadius: 5,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: "#ec4899" } }
      },
      scales: {
        x: { ticks: { color: "#ec4899" } },
        y: {
          beginAtZero: true,
          ticks: { color: "#ec4899" }
        }
      }
    }
  });

  // Optional: clear localStorage
  //localStorage.removeItem("solarPrediction");
});
