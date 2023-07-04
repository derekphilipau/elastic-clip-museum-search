# export ELASTICSEARCH_API_KEY=RUW3aWxZWUJIDwNOUzYwU1ZKaUg6dEllY3JjQkVTX3lURlU3RTdLUm5mQQ==
from elasticsearch import Elasticsearch, helpers
import os
import json

# Retrieve the API key from an environment variable
api_key = os.getenv('ELASTICSEARCH_API_KEY')

if not api_key:
    raise ValueError("Missing environment variable: 'ELASTICSEARCH_API_KEY'")

es = Elasticsearch(
    "https://localhost:9200",
    ca_certs="./secrets/http_ca.crt",
    api_key=api_key
)

# Open and load the embeddings JSON file
with open('data/elasticsearch_embeddings.json', 'r') as f:
    data = json.load(f)

# For each embedding, update the corresponding document in the collections index
for item in data:
    es.update(
        index='collections',
        id=item['id'],
        body={
            'doc': {
                'image_embeddings': item['embedding']
            }
        }
    )

print('Update completed')