from langgraph.checkpoint.memory import MemorySaver

from app.graph.build_graph import build_graph, route_after_diff, route_after_evidence


def test_build_graph_compiles_with_injected_checkpointer():
    graph = build_graph(checkpointer=MemorySaver())
    node_names = set(graph.get_graph().nodes.keys())
    assert {
        "chunker", "embedder", "extractor", "differ", "human_review",
        "mapper", "evidence_check", "gap_engine", "finalize",
    } <= node_names


def test_route_after_diff_sends_amended_and_superseded_to_human_review():
    assert route_after_diff({"diff_status": "amended"}) == "human_review"
    assert route_after_diff({"diff_status": "superseded"}) == "human_review"


def test_route_after_diff_sends_unchanged_to_finalize():
    assert route_after_diff({"diff_status": "unchanged"}) == "finalize"


def test_route_after_diff_sends_new_to_mapper():
    assert route_after_diff({"diff_status": "new"}) == "mapper"


def test_route_after_evidence_routing():
    assert route_after_evidence({"evidence_status": "missing"}) == "gap_engine"
    assert route_after_evidence({"evidence_status": "invalid"}) == "human_review"
    assert route_after_evidence({"evidence_status": "present"}) == "finalize"
