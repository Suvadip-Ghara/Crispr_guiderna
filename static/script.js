document.getElementById("analyze-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    const response = await fetch("/analyze", {
        method: "POST",
        body: formData,
    });
    const data = await response.json();
    const resultsDiv = document.getElementById("results");
    const downloadLink = document.getElementById("download-link");

    if (data.results) {
        resultsDiv.innerHTML = data.results;
        downloadLink.style.display = "block";
        downloadLink.href = "/download/results";
    } else {
        resultsDiv.innerHTML = `<p>Error: ${data.error}</p>`;
        downloadLink.style.display = "none";
    }
});
