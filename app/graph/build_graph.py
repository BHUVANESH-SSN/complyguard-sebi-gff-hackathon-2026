from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import interrupt
from .state import ComplianceState
from . import nodes

PG_CONN = "postgresql://regops:regops@localhost:5432/regops_db"

def route_after_diff(state: ComplianceState) -> str:
    if state["diff_status"] in ("amended", "superseded"):
        return "human_review"
    return "mapper"

def route_after_evidence(state: ComplianceState) -> str:
    if state["evidence_status"] == "missing":
        return "gap_engine"
    if state["evidence_status"] == "invalid":
        return "human_review"
    return "finalize"

def build_graph():
    g = StateGraph(ComplianceState)
    g.add_node("chunker", nodes.chunker_node)
    g.add_node("embedder", nodes.embedder_node)
    g.add_node("extractor", nodes.extractor_node)
    g.add_node("differ", nodes.differ_node)
    g.add_node("human_review", nodes.human_review_node)
    g.add_node("mapper", nodes.mapper_node)
    g.add_node("evidence_check", nodes.evidence_node)
    g.add_node("gap_engine", nodes.gap_engine_node)
    g.add_node("finalize", nodes.finalize_node)

    g.set_entry_point("chunker")
    g.add_edge("chunker", "embedder")
    g.add_edge("embedder", "extractor")
    g.add_edge("extractor", "differ")
    g.add_conditional_edges("differ", route_after_diff,
        {"human_review": "human_review", "mapper": "mapper"})
    g.add_edge("human_review", "mapper")
    g.add_edge("mapper", "evidence_check")
    g.add_conditional_edges("evidence_check", route_after_evidence,
        {"gap_engine": "gap_engine", "human_review": "human_review", "finalize": "finalize"})
    g.add_edge("gap_engine", "finalize")
    g.add_edge("finalize", END)

    checkpointer = PostgresSaver.from_conn_string(PG_CONN)
    return g.compile(checkpointer=checkpointer, interrupt_before=["human_review"])