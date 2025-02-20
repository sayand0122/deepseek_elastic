from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from backend.ollama_client import generate_query,execute_query
from backend.csv_loader import load_csv_to_elastic
from backend.summarization import summarize_results
from pathlib import Path
from backend.properties import index_name

app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Serve frontend
@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    return frontend_path.read_text()

# API Endpoint for querying Titanic dataset
@app.get("/query/")
def search_csv(question: str = Query(..., description="Ask a question about the Titanic dataset")):
    summary_keywords = ["summary", "summarize", "conclusion", "insight", "key takeaways", "explanation"]
    if any(keyword in question.lower() for keyword in summary_keywords):
        return summarize_results()
    else: 
        return execute_query(question)

# Load Titanic CSV into Elasticsearch at startup
load_csv_to_elastic("data/titanic.csv", index_name)
