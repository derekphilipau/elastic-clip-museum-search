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

# create field if not exists
es.indices.put_mapping(
    index='collections',
    body={
        'properties': {
            'image': {  
                'type': 'object',
                'properties': {
                    'embedding': {  
                        'type': 'dense_vector',
                        'dims': 512,
                        'index': True,
                        'similarity': 'cosine'
                    }
                }
            }
        }
    }
)

i = 0
while True:
    try:
        # Open and load the embeddings JSON file
        with open(f'data/elasticsearch_embeddings_{i}.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        break

    # For each embedding, update the corresponding document in the collections index
    for item in data:
        es.update(
            index='collections',
            id=item['id'],
            body={
                'doc': {
                    'image': {
                        'embedding': item['embedding']
                    }
                }
            }
        )

    i += 1

print('Update completed')