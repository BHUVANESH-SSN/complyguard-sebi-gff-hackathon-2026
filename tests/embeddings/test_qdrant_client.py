from unittest.mock import MagicMock

from app.embeddings.qdrant_client import (
    DEFAULT_COLLECTION,
    ensure_collection,
    search,
    upsert_chunks,
)


def test_ensure_collection_creates_when_missing():
    client = MagicMock()
    client.get_collections.return_value = MagicMock(collections=[])

    ensure_collection(client, vector_size=768)

    client.create_collection.assert_called_once()
    _, kwargs = client.create_collection.call_args
    assert kwargs["collection_name"] == DEFAULT_COLLECTION
    assert kwargs["vectors_config"].size == 768


def test_ensure_collection_skips_when_present():
    client = MagicMock()
    existing = MagicMock()
    existing.name = DEFAULT_COLLECTION
    client.get_collections.return_value = MagicMock(collections=[existing])

    ensure_collection(client)

    client.create_collection.assert_not_called()


def test_upsert_chunks_sends_one_point_per_chunk():
    client = MagicMock()
    ids = upsert_chunks(
        client,
        chunks=["clause one", "clause two"],
        vectors=[[0.1, 0.2], [0.3, 0.4]],
        metadatas=[{"source": "a.pdf"}, {"source": "a.pdf"}],
    )

    assert len(ids) == 2
    _, kwargs = client.upsert.call_args
    assert len(kwargs["points"]) == 2
    assert kwargs["points"][0].payload["text"] == "clause one"


def test_search_maps_results_to_text_and_score():
    client = MagicMock()
    hit = MagicMock(payload={"text": "clause one"}, score=0.9)
    client.search.return_value = [hit]

    results = search(client, query_vector=[0.1, 0.2])

    assert results == [{"text": "clause one", "score": 0.9}]
