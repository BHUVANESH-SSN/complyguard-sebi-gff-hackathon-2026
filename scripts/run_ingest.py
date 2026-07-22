"""CLI: ingest a SEBI circular PDF into Qdrant. Usage: python -m scripts.run_ingest <pdf_path>"""
import sys

from app.embeddings.embedder import embed_texts
from app.embeddings.qdrant_client import ensure_collection, get_client, upsert_chunks
from app.ingestion.clause_splitter import split_into_clauses
from app.ingestion.pdf_cleaner import extract_and_clean


def run_ingest(pdf_path: str) -> list[str]:
    cleaned_text = extract_and_clean(pdf_path)
    clauses = split_into_clauses(cleaned_text)
    if not clauses:
        print(f"No clauses found in {pdf_path}")
        return []

    vectors = embed_texts(clauses)
    client = get_client()
    ensure_collection(client, vector_size=len(vectors[0]))
    ids = upsert_chunks(
        client,
        chunks=clauses,
        vectors=vectors,
        metadatas=[{"source": pdf_path, "clause_index": i} for i in range(len(clauses))],
    )
    print(f"Ingested {len(ids)} clauses from {pdf_path}")
    return ids


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.run_ingest <pdf_path>")
        sys.exit(1)
    run_ingest(sys.argv[1])
