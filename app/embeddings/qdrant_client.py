"""Thin wrapper around the Qdrant client for storing and querying circular chunks."""
import os
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

DEFAULT_COLLECTION = "circular_clauses"


def get_client(url: str | None = None) -> QdrantClient:
    return QdrantClient(url=url or os.environ.get("QDRANT_URL", "http://localhost:6333"))


def ensure_collection(
    client: QdrantClient,
    collection_name: str = DEFAULT_COLLECTION,
    vector_size: int = 768,
) -> None:
    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def upsert_chunks(
    client: QdrantClient,
    chunks: list[str],
    vectors: list[list[float]],
    metadatas: list[dict],
    collection_name: str = DEFAULT_COLLECTION,
) -> list[str]:
    ids = [str(uuid.uuid4()) for _ in chunks]
    points = [
        PointStruct(id=ids[i], vector=vectors[i], payload={**metadatas[i], "text": chunks[i]})
        for i in range(len(chunks))
    ]
    client.upsert(collection_name=collection_name, points=points)
    return ids


def search(
    client: QdrantClient,
    query_vector: list[float],
    limit: int = 3,
    collection_name: str = DEFAULT_COLLECTION,
) -> list[dict]:
    response = client.query_points(
        collection_name=collection_name, query=query_vector, limit=limit
    )
    return [
        {"text": p.payload.get("text"), "score": p.score, "payload": p.payload}
        for p in response.points
    ]
