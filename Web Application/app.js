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

// Call the function to fetch data when the page loads or based on some user action
fetchDataPlot();
