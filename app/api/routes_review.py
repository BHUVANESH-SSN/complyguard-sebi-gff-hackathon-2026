"""Human-review API routes: resume a paused compliance-pipeline run with a decision."""
from fastapi import APIRouter
from langgraph.types import Command

from app.graph.build_graph import build_graph

router = APIRouter()

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


@router.post("/review/{thread_id}/decision")
def submit_decision(thread_id: str, decision: str, actor: str = "reviewer"):
    graph = _get_graph()
    result = graph.invoke(
        Command(resume={"decision": decision, "actor": actor}),
        config={"configurable": {"thread_id": thread_id}},
    )
    return {"status": "resumed", "state": result}
