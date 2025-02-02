import requests
import time
import re
import json
from backend.elastic import get_elastic_client

OLLAMA_DOCKER_URL = "http://localhost:11434/api/generate"
es=get_elastic_client()

SYSTEM_PROMPT = """You are an AI assistant that generates valid **Elasticsearch DSL queries** for Titanic data.
Your job is to output correctly formatted **JSON queries** based on user questions.

---

## **Dataset:**
- **Index Name:** `titanic`
- **Available Fields:**
  - `PassengerId` (integer)
  - `Survived` (integer: 0 or 1) - 1 if the passenger survived
  - `Pclass` (integer: 1, 2, or 3)
  - `Name` (text)
  - `Sex` (keyword: 'male' or 'female')
  - `Age` (float)
  - `SibSp` (integer)
  - `Parch` (integer)
  - `Ticket` (keyword)
  - `Fare` (float)
  - `Cabin` (text)
  - `Embarked` (keyword: 'C', 'Q', 'S')

---

## **Query Syntax Rules**:
1️⃣ **For Exact Matching** → `{ "term": { "FieldName": "value" } }`
   - Example: `{ "term": { "Pclass": 2 } }`
   ** Note - if there are more than 1 term for a single column use terms only for that
   - Example: `{ "terms": { "Pclass": [1,2] } }`

2️⃣ **For Ranges (e.g., Age > 30)** → `{ "range": { "FieldName": { "gt": 30 } } }`
    (e.g., Age >= 30)** → `{ "range": { "FieldName": { "gte": 30 } } }`
    (e.g., Age < 30)** → `{ "range": { "FieldName": { "lt": 30 } } }`
    (e.g., Age <= 30)** → `{ "range": { "FieldName": { "lte": 30 } } }`
    (e.g., Age>=0 and Age <= 30)** → `{ "range": { "FieldName": { "gte":0,"lte": 30 } } }`
    (e.g., Age>50 and Age <=90)** → `{ "range": { "FieldName": { "gt":50,"lte": 90 } } }`

   - Example: `{ "range": { "Age": { "gt": 30 } } }`

3️⃣ **For Multiple Conditions (AND logic)** → `{ "bool": { "must": [{...}, {...}, ...] } }`
   - Example:
   ```json
   {
     "bool": {
       "must": [
         { "term": { "Sex": "female" } },
         { "range": { "Age": { "gt": 30 } } },
         { "term": { "Pclass": 2 } }
       ]
     }
   }
   ```

4️⃣ **For Aggregations** → `{ "aggs": { "aggregation_name": { "avg": { "field": "FieldName" } } } }`
        `{ "aggs": { "aggregation_name": { "max": { "field": "FieldName" } } } }`
        `{ "aggs": { "aggregation_name": { "min": { "field": "FieldName" } } } }`
        `{ "aggs": { "aggregation_name": { "sum": { "field": "FieldName" } } } }`

   - Example:
   ```json
    {
    "size": 0,
    "aggs": {
        "average_age": {
        "avg": { "field": "Age" }
        }
    }
    }
    ```
    **Note - replace avg with max,min,sum as required by the user

5️⃣ **For Sorting** → `{ "sort": [ { "FieldName": { "order": "desc" } } ] }`
    `{ "sort": [ { "FieldName": { "order": "acs" } } ] }`
   - Example:
   ```json
    {
    "size": 5,
    "sort": [ { "Fare": { "order": "desc" } } ]
    }
    ```
## **Output Guidelines**:
✅ Return only valid JSON. No explanations, comments, or extra text.
✅ Ensure query and aggs are separate at the top level. Never place query inside aggs or vice versa.
✅ Use correct Elasticsearch DSL syntax. Follow the provided format strictly.
✅ For filtering conditions, use `` inside query. 
 - Example:
 ```json
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "Sex": "female" } },
        { "range": { "Age": { "gt": 30 } } },
        { "term": { "Pclass": 2 } }
      ]
    }
  }
}
```
✅ For aggregations, place them inside aggs and do not mix with query. 
 - Example:
 ```json
 {
  "query": {
    "bool": {
      "filter": [
        { "term": { "Sex": "female" } },
        { "range": { "Age": { "gt": 30 } } },
        { "term": { "Pclass": 2 } }
      ]
    }
  },
  "aggs": {
    "average_fare": {
      "avg": { "field": "Fare" }
    }
  }
}
```
"""

def query_llm(question):
    start_time = time.time()

    while True:
      payload = {
          "model": "deepseek-r1:7b",
          "prompt": f"{SYSTEM_PROMPT}\nUser question: {question}",
          "stream": False
      }
      response = requests.post(OLLAMA_DOCKER_URL, json=payload).json()

      # Ensure valid JSON
      pattern = re.compile(r'```json(.*?)```', re.DOTALL)
      match=pattern.search(response['response'])
      extracted_content = match.group(1).strip()
      query_dsl=extracted_content


      try:
          es_query = json.loads(query_dsl)
          if not ("query" in es_query or "aggs" in es_query):
              raise ValueError("Invalid Elasticsearch query format")
          break
      except json.JSONDecodeError as e:
          print("Invalid JSON format generated")
          continue

    try:
        results = es.search(index="titanic", body=es_query)
        if "aggregations" in results:
            agg_key = list(results["aggregations"].keys())[0]
            agg_value = results["aggregations"][agg_key]["value"]
            
            if agg_value is None:
                answer= f"The {agg_key.replace('_', ' ')} could not be computed."

            answer= f"The {agg_key.replace('_', ' ')} is {agg_value:.2f}."

        else:
          hits = [hit["_source"] for hit in results["hits"]["hits"]]
          if not hits:
              answer= "No matching results found."

          formatted_results = []
          for passenger in hits:
              summary = f"Passenger {passenger.get('Name', 'Unknown')} ({'Male' if passenger.get('Sex') == 'male' else 'Female'}), "\
                        f"aged {passenger.get('Age', 'Unknown')}, "\
                        f"was in class {passenger.get('Pclass', 'Unknown')} and "\
                        f"{'survived' if passenger.get('Survived') == 1 else 'did not survive'}."
              formatted_results.append(summary)
          
          print(formatted_results)
          answer= "Here are the results: \n" + "\n".join(formatted_results)

    except Exception as e:
        answer= {"error": str(e)}
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"⚡ Execution Time: {execution_time:.2f} seconds")
    return answer
