"""Wraps a local sentence-transformers model for embedding text into vectors."""
from sentence_transformers import SentenceTransformer

DEFAULT_MODEL_NAME = "BAAI/bge-base-en-v1.5"

_model_cache: dict[str, SentenceTransformer] = {}


def get_model(model_name: str = DEFAULT_MODEL_NAME) -> SentenceTransformer:
    if model_name not in _model_cache:
        _model_cache[model_name] = SentenceTransformer(model_name)
    return _model_cache[model_name]


def embed_texts(
    texts: list[str], model_name: str = DEFAULT_MODEL_NAME
) -> list[list[float]]:
    if not texts:
        return []
    model = get_model(model_name)
    return model.encode(texts).tolist()
