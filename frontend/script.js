document.getElementById("queryBtn").addEventListener("click", async () => {
    let question = document.getElementById("question").value;

    if (!question) {
        alert("Please enter a question!");
        return;
    }

    document.getElementById("result").textContent = "Processing...";

    try {
        const response = await fetch(`/query?question=${encodeURIComponent(question)}`);
        const data = await response.json();

        let outputHtml = "";
        outputHtml+=`<div>${data}</div>`;
        document.getElementById("result").innerHTML = outputHtml;

    } catch (error) {
        console.error("❌ Error:", error);
        document.getElementById("result").textContent = "Error fetching data.";
    }
});
