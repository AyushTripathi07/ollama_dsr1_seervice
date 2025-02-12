import weaviate
import json

def connect_weaviate():
    """
    Establishes a connection to the Weaviate instance.
    """
    client = weaviate.Client("http://localhost:8080")  
    return client

def create_schema(client):
    """
    Defines and creates a schema in Weaviate.
    """
    schema = {
        "classes": [
            {
                "class": "TextEmbedding",
                "description": "Store vector embeddings of texts",
                "vectorizer": "text2vec-openai",
                "properties": [
                    {
                        "name": "text",
                        "dataType": ["string"],
                        "description": "Original text data"
                    },
                    {
                        "name": "embedding",
                        "dataType": ["number[]"],
                        "description": "Vector representation of text"
                    }
                ]
            }
        ]
    }
    client.schema.create(schema)

def store_embedding(client, text, embedding):
    """
    Stores a text and its vector embedding in Weaviate.
    """
    data_object = {
        "text": text,
        "embedding": embedding
    }
    client.data_object.create(data_object, "TextEmbedding")

def query_similar_text(client, query_vector, top_k=5):
    """
    Queries Weaviate for the most similar texts based on a given vector.
    """
    result = client.query.get("TextEmbedding", ["text"])\
        .with_near_vector({"vector": query_vector})\
        .with_limit(top_k)\
        .do()
    return result

if __name__ == "__main__":
    client = connect_weaviate()
    create_schema(client)
    print("Weaviate connected and schema initialized.")
