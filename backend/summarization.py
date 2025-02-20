import requests
import json
from backend.elastic import get_elastic_client
from backend.properties import index_name
import re

OLLAMA_DOCKER_URL = "http://localhost:11434/api/generate"
es=get_elastic_client()

SYSTEM_PROMPT = """
You are a data analysis assistant. Given a dataset, generate a **concise 2-3 sentence summary** in plain English.
Focus on key insights such as:
- Trends and patterns in the data.
- Important comparisons (e.g., survival rates, price variations).
- Statistical insights (e.g., average, highest, lowest values).

🚨 Do NOT return structured JSON, lists, or key-value pairs.
🚨 ONLY return a human-readable summary.
🚨 Keep it precise and avoid redundant information.

Example Output:
 "All passengers in this dataset were female from second class, with an average fare of $17.88. They were between 36-50 years old, and all survived."
"""


def extract_relevant_data(query_results):
    """Dynamically extracts relevant fields from Elasticsearch results."""
    extracted_data = []

    if "hits" in query_results and "hits" in query_results["hits"]:
        for hit in query_results["hits"]["hits"]:
            source = hit["_source"]
            relevant_fields = {key: value for key, value in source.items() if not isinstance(value, (dict, list))}
            extracted_data.append(relevant_fields)
    
    return extracted_data

# def summarize_results(query):
#     """Summarizes Elasticsearch query results using Ollama."""
#     results = es.search(index=index_name, body=query)

#     meaningful_data=extract_relevant_data(results)

#     if not meaningful_data:
#         return {"summary": "No relevant data found to summarize."}
#     results_json2=json.dumps(meaningful_data, indent=2)

    
#     payload = {
#         "model": "deepseek-r1:7b",
#         "prompt": f"{SYSTEM_PROMPT}\n\nData:\n{results_json2}\n\nSummary:",
#         "stream": False
#     }

#     response = requests.post(OLLAMA_DOCKER_URL, json=payload).json()

#     cleaned_text = re.sub(r"<think>.*?</think>", "", response['response'], flags=re.DOTALL).strip()

#     return cleaned_text

def summarize_results():
    """Fetches all data from Elasticsearch and generates a summary."""
    try:
        # Fetch all records (pagination handled by scroll API)
        results = es.search(index=index_name, body={"size": 10000, "query": {"match_all": {}}}, scroll="2m")
        
        all_hits = results["hits"]["hits"]
        scroll_id = results["_scroll_id"]

        while len(results["hits"]["hits"]) > 0:
            results = es.scroll(scroll_id=scroll_id, scroll="2m")
            all_hits.extend(results["hits"]["hits"])
        
        es.clear_scroll(scroll_id=scroll_id)  # Clear scroll context

        # Extract relevant fields
        meaningful_data = extract_relevant_data({"hits": {"hits": all_hits}})

        if not meaningful_data:
            return {"summary": "No relevant data found to summarize."}
        
        results_json = json.dumps(meaningful_data, indent=2)

        # Send full dataset to Ollama for summarization
        payload = {
            "model": "deepseek-r1:7b",
            "prompt": f"{SYSTEM_PROMPT}\n\nData:\n{results_json}\n\nSummary:",
            "stream": False
        }

        response = requests.post(OLLAMA_DOCKER_URL, json=payload).json()
        cleaned_text = re.sub(r"<think>.*?</think>", "", response['response'], flags=re.DOTALL).strip()
        # print(cleaned_text)

        return cleaned_text
    
    except Exception as e:
        return {"summary": f"Error retrieving data: {str(e)}"}
