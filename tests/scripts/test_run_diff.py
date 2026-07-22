from unittest.mock import MagicMock, patch

from scripts.run_diff import run_diff


def test_run_diff_invokes_graph_with_real_state_shape_and_thread_id():
    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {"diff_status": "new"}

    with patch("scripts.run_diff.build_graph", return_value=fake_graph) as mock_build:
        result = run_diff("circular-1", "clause-1", "1. Appoint a compliance officer.")

    mock_build.assert_called_once()
    fake_graph.invoke.assert_called_once_with(
        {
            "circular_id": "circular-1",
            "clause_id": "clause-1",
            "raw_clause": "1. Appoint a compliance officer.",
            "heading": None,
        },
        config={"configurable": {"thread_id": "circular-1:clause-1"}},
    )
    assert result == {"diff_status": "new"}
