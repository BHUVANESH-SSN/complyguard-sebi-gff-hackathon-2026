"""CLI: run the LangGraph extraction/diff pipeline over a single clause.
Usage: python -m scripts.run_diff <circular_id> <clause_id> '<raw clause text>'
"""
import sys

from app.graph.build_graph import build_graph


def run_diff(circular_id: str, clause_id: str, raw_clause: str, heading: str | None = None) -> dict:
    graph = build_graph()
    return graph.invoke(
        {
            "circular_id": circular_id,
            "clause_id": clause_id,
            "raw_clause": raw_clause,
            "heading": heading,
        },
        config={"configurable": {"thread_id": f"{circular_id}:{clause_id}"}},
    )


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python -m scripts.run_diff <circular_id> <clause_id> '<raw clause text>'")
        sys.exit(1)
    result = run_diff(sys.argv[1], sys.argv[2], sys.argv[3])
    print(result)
