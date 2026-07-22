"""Placeholder for individual LangGraph pipeline nodes (extraction, diffing,
human-review interrupt routing).

Real implementation is pasted in separately — this file intentionally defines
no functions yet, since the exact node signatures depend on the graph state
schema in app.graph.state. Once pasted in, app.graph.build_graph imports and
wires these nodes into the compiled graph.
"""
