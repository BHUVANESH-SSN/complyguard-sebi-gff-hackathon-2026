import pytest

from scripts.run_diff import run_diff


def test_run_diff_propagates_not_implemented_until_graph_is_pasted_in():
    with pytest.raises(NotImplementedError):
        run_diff("1. Appoint a compliance officer.")
