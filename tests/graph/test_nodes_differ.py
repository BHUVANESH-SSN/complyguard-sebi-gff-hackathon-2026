from unittest.mock import patch

from app.graph.nodes import differ_node


def test_differ_node_returns_new_when_no_match():
    with (
        patch("app.graph.nodes.get_client", return_value="fake-client"),
        patch("app.graph.nodes.ensure_collection") as mock_ensure,
        patch("app.graph.nodes.search", return_value=[]) as mock_search,
    ):
        result = differ_node({"raw_clause": "1. Do X.", "embedding": [0.1] * 768})

    assert result == {"diff_status": "new", "similarity_match": None}
    mock_ensure.assert_called_once_with("fake-client", vector_size=768)
    mock_search.assert_called_once()


def test_differ_node_returns_unchanged_when_match_is_identical_text():
    hit = {"text": "1. Do X.", "score": 0.99, "payload": {"obligation_id": "obl-1"}}
    with (
        patch("app.graph.nodes.get_client", return_value="fake-client"),
        patch("app.graph.nodes.ensure_collection"),
        patch("app.graph.nodes.search", return_value=[hit]),
    ):
        result = differ_node({"raw_clause": "1.  Do X.  ", "embedding": [0.1] * 768})

    assert result == {"diff_status": "unchanged", "similarity_match": hit}


def test_differ_node_returns_amended_when_match_has_different_text():
    hit = {"text": "1. Do X annually.", "score": 0.9, "payload": {"obligation_id": "obl-1"}}
    with (
        patch("app.graph.nodes.get_client", return_value="fake-client"),
        patch("app.graph.nodes.ensure_collection"),
        patch("app.graph.nodes.search", return_value=[hit]),
    ):
        result = differ_node({"raw_clause": "1. Do X quarterly.", "embedding": [0.1] * 768})

    assert result == {"diff_status": "amended", "similarity_match": hit}


def test_differ_node_returns_new_when_score_below_threshold():
    hit = {"text": "unrelated clause", "score": 0.5, "payload": {}}
    with (
        patch("app.graph.nodes.get_client", return_value="fake-client"),
        patch("app.graph.nodes.ensure_collection"),
        patch("app.graph.nodes.search", return_value=[hit]),
    ):
        result = differ_node({"raw_clause": "1. Do X.", "embedding": [0.1] * 768})

    assert result == {"diff_status": "new", "similarity_match": None}
