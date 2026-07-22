from unittest.mock import patch

from scripts.run_ingest import run_ingest


def test_run_ingest_orchestrates_pipeline_and_returns_ids():
    with (
        patch("scripts.run_ingest.clean_pdf", return_value="1. Do X.\n\n2. Do Y.") as mock_clean,
        patch("scripts.run_ingest.embed_texts", return_value=[[0.1], [0.2]]) as mock_embed,
        patch("scripts.run_ingest.get_client", return_value="fake-client"),
        patch("scripts.run_ingest.ensure_collection") as mock_ensure,
        patch("scripts.run_ingest.upsert_chunks", return_value=["id-1", "id-2"]) as mock_upsert,
    ):
        result = run_ingest("data/raw_pdfs/demo.pdf")

    mock_clean.assert_called_once_with("data/raw_pdfs/demo.pdf")
    mock_embed.assert_called_once_with(["1. Do X.", "2. Do Y."])
    mock_ensure.assert_called_once_with("fake-client", vector_size=1)
    mock_upsert.assert_called_once()
    assert result == ["id-1", "id-2"]


def test_run_ingest_returns_empty_list_when_no_clauses_found():
    with patch("scripts.run_ingest.clean_pdf", return_value="   "):
        assert run_ingest("data/raw_pdfs/empty.pdf") == []
