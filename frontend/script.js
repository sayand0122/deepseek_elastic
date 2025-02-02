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
        document.getElementById("result").textContent = JSON.stringify(data.answer, null, 2);
    } catch (error) {
        console.error("Error:", error);
        document.getElementById("result").textContent = "Error fetching data.";
    }
});
