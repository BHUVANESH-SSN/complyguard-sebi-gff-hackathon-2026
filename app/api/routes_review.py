# app/api/routes_review.py
from fastapi import APIRouter
from langgraph.types import Command
from app.graph.build_graph import build_graph

router = APIRouter()
app_graph = build_graph()

@router.post("/review/{thread_id}/decision")
def submit_decision(thread_id: str, decision: str):
    result = app_graph.invoke(
        Command(resume=decision),
        config={"configurable": {"thread_id": thread_id}}
    )
    return {"status": "resumed", "state": result}