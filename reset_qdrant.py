from qdrant_client import QdrantClient
import os

client = QdrantClient("http://localhost:6333")
col_name = "apex_patents_v1"
if client.collection_exists(col_name):
    print(f"Deleting collection {col_name}...")
    client.delete_collection(col_name)
    print("Deleted.")
else:
    print("Collection does not exist.")
