"""CLI: run the LangGraph extraction/diff pipeline over a clause.
Usage: python -m scripts.run_diff '<clause text>'
"""
import sys

from app.graph.build_graph import build_graph


def run_diff(clause_text: str) -> dict:
    graph = build_graph()
    return graph.invoke({"clause_text": clause_text})


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.run_diff '<clause text>'")
        sys.exit(1)
    result = run_diff(sys.argv[1])
    print(result)
