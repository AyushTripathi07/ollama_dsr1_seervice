# Weaviate Integration for Vector Embeddings

## Overview
This module provides integration with Weaviate, a vector search engine, to store and retrieve vector embeddings of text. It includes functionalities for:
- Connecting to a Weaviate instance
- Creating a schema for storing text embeddings
- Storing text and its corresponding vector representation
- Querying for similar text based on vector similarity

## Requirements
Ensure you have the following installed before using this module:
- Python 3.7+
- `weaviate-client` package
- A running instance of Weaviate (local or cloud-based)

### Install Dependencies
```sh
pip install weaviate-client
```

## Configuration
Update the `WEAVIATE_INSTANCE_URL` in the `connect_weaviate` function to match your Weaviate instance:
```python
client = weaviate.Client("http://localhost:8080")
```
If using a cloud instance, replace `localhost:8080` with your Weaviate cloud URL.

## Usage

### 1. Connect to Weaviate
```python
from weaviate_integration import connect_weaviate
client = connect_weaviate()
```

### 2. Create Schema
Before storing embeddings, define a schema for Weaviate.
```python
from weaviate_integration import create_schema
create_schema(client)
```
> **Note:** Run this only once unless you need to redefine the schema.

### 3. Store Text Embeddings
To store a text with its vector representation:
```python
from weaviate_integration import store_embedding

test_text = "This is an example sentence."
test_embedding = [0.1, 0.2, 0.3, 0.4]  # Example vector representation
store_embedding(client, test_text, test_embedding)
```

### 4. Query Similar Texts
To retrieve the most similar texts from Weaviate:
```python
from weaviate_integration import query_similar_text

query_vector = [0.1, 0.2, 0.3, 0.4]
results = query_similar_text(client, query_vector, top_k=3)
print(results)
```

## Schema Details
This module uses the `TextEmbedding` class with the following structure:
- **text (string)**: Stores the original input text.
- **embedding (number[])**: Stores the vector representation of the text.

## Troubleshooting
- Ensure Weaviate is running before executing the script.
- If connection issues arise, verify the Weaviate URL is correct.
- If schema conflicts occur, delete the existing schema before re-running `create_schema(client)`.

## License
This module is open-source and available for modification and distribution under the MIT License.