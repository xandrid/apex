from qdrant_client import QdrantClient
import inspect

client = QdrantClient("http://localhost:6333")
print(f"Client Type: {type(client)}")
print(f"Has search: {hasattr(client, 'search')}")
print(f"Has query_points: {hasattr(client, 'query_points')}")
print(f"Has search_points: {hasattr(client, 'search_points')}") # Deprecated?

try:
    print(inspect.signature(client.search))
except Exception as e:
    print(f"Error inspecting search: {e}")
