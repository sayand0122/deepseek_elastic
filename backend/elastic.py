from elasticsearch import Elasticsearch

def get_elastic_client():
    return Elasticsearch("http://localhost:9200")

