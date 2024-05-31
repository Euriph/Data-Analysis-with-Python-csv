document
  .getElementById("singleDataForm")
  .addEventListener("submit", function (event) {
    event.preventDefault();

    const data = {
      date: document.getElementById("date").value,
      value: document.getElementById("value").value,
      username: document.getElementById("username").value,
    };

    fetch("http://localhost:5000/submit_single_data", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    })
      .then((response) => response.json())
      .then((data) => alert("Data submitted: " + JSON.stringify(data)))
      .catch((error) => {
        console.error("Error:", error);
      });
  });

document
  .getElementById("csvUploadForm")
  .addEventListener("submit", function (event) {
    event.preventDefault();

    const formData = new FormData();
    const fileField = document.getElementById("csvFile");

    formData.append("file", fileField.files[0]);

    fetch("http://localhost:5000/upload_csv", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => alert("CSV uploaded: " + JSON.stringify(data)))
      .catch((error) => {
        console.error("Error:", error);
      });
  });

document
  .getElementById("generateInsightsButton")
  .addEventListener("click", function () {
    fetch("http://localhost:5000/get_data_summary")
      .then((response) => response.json())
      .then((summary) => {
        const summaryData = {
          coefficients: summary.coefficients,
          mse: summary.mse,
          data_points: summary.data_points.slice(-100),
        };
        console.log("Summary Data:", summaryData);
        fetch("http://localhost:5000/generate_insights", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ summary: JSON.stringify(summaryData) }),
        })
          .then((response) => response.json())
          .then((data) => {
            const insightsResult = document.getElementById("insightsResult");
            insightsResult.innerHTML = `
                      <p>Generated Insights:</p>
                      <pre>${data.insight}</pre>
                      <p>Token Used: ${data.token_count}</p>
                  `;
          })
          .catch((error) => console.error("Error generating insights:", error));
      })
      .catch((error) => console.error("Error fetching data summary:", error));
  });

function fetchDataPlot() {
  fetch("http://localhost:5000/get_data_plot")
    .then((response) => response.json())
    .then((data) => {
      const img = document.getElementById("dataPlot");
      const mseReport = document.getElementById("mseReport");

      img.src = "data:image/png;base64," + data.image;
      mseReport.textContent = "Mean Squared Error: " + data.mse;
    })
    .catch((error) => console.error("Error fetching data plot:", error));
}

fetchDataPlot();
