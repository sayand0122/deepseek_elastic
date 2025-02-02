import pandas as pd
from backend.elastic import get_elastic_client

def load_csv_to_elastic(csv_file, index_name):
    es = get_elastic_client()
    if es.ping():
        print("✅ Elasticsearch is up and running")
    else:
        print("❌ Elasticsearch is not running")

    df = pd.read_csv(csv_file).fillna("") 

    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, ignore=400)
        for i, row in df.iterrows():
            es.index(index=index_name, id=i, body=row.to_dict())
    
        print(f"✅ {csv_file} loaded into {index_name}")
    else:
        print(f"⚠️ {index_name} already exists in Elasticsearch")
