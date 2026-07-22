from datetime import date, datetime
from unittest.mock import patch

from app.graph.nodes import (
    chunker_node,
    compute_audit_hash,
    embedder_node,
    resolve_due_date,
)


def test_chunker_node_strips_whitespace_and_derives_heading():
    state = {"raw_clause": "  1. Appoint a compliance officer.\nDetails here.  "}
    result = chunker_node(state)
    assert result["raw_clause"] == "1. Appoint a compliance officer.\nDetails here."
    assert result["heading"] == "1. Appoint a compliance officer."


def test_chunker_node_keeps_existing_heading():
    state = {"raw_clause": "1. Do X.", "heading": "Custom Heading"}
    result = chunker_node(state)
    assert result["heading"] == "Custom Heading"


def test_embedder_node_calls_embed_texts_with_raw_clause():
    with patch("app.graph.nodes.embed_texts", return_value=[[0.1, 0.2]]) as mock_embed:
        result = embedder_node({"raw_clause": "1. Do X."})
    mock_embed.assert_called_once_with(["1. Do X."])
    assert result == {"embedding": [0.1, 0.2]}


def test_resolve_due_date_parses_iso_date():
    assert resolve_due_date("2026-12-31", date(2026, 1, 1)) == date(2026, 12, 31)


def test_resolve_due_date_maps_quarterly_keyword():
    assert resolve_due_date("quarterly", date(2026, 1, 1)) == date(2026, 4, 1)


def test_resolve_due_date_maps_annual_keyword():
    assert resolve_due_date("annual", date(2026, 1, 1)) == date(2027, 1, 1)


def test_resolve_due_date_returns_none_for_unrecognized_or_missing():
    assert resolve_due_date(None, date(2026, 1, 1)) is None
    assert resolve_due_date("", date(2026, 1, 1)) is None
    assert resolve_due_date("whenever", date(2026, 1, 1)) is None


def test_compute_audit_hash_is_deterministic_and_chains_on_prev_hash():
    ts = datetime(2026, 1, 1, 12, 0, 0)
    action = {"obligation_id": "obl-1"}
    h1 = compute_audit_hash("", action, ts)
    h2 = compute_audit_hash("", action, ts)
    h3 = compute_audit_hash("some-prev-hash", action, ts)
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64
