import numpy as np
import pytest
from unittest.mock import MagicMock

from app.embeddings.embedder import _model_cache, embed_texts


@pytest.fixture(autouse=True)
def clear_model_cache():
    yield
    _model_cache.clear()


def test_embed_texts_returns_empty_list_for_no_input():
    assert embed_texts([]) == []


def test_embed_texts_uses_model_encode_and_returns_lists():
    fake_model = MagicMock()
    fake_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
    _model_cache["fake-model"] = fake_model

    result = embed_texts(["a", "b"], model_name="fake-model")

    fake_model.encode.assert_called_once_with(["a", "b"])
    assert result == [[0.1, 0.2], [0.3, 0.4]]
