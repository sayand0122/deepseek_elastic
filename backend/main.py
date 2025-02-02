from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from backend.ollama_client import query_llm
from backend.csv_loader import load_csv_to_elastic
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
    answer = query_llm(question)  # Generate Elasticsearch DSL query
    return {"answer": answer}

# Load Titanic CSV into Elasticsearch at startup
load_csv_to_elastic("data/titanic.csv", index_name)
