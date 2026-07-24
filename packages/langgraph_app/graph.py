# packages/langgraph_app/graph.py
from packages.langgraph_app.supervisor import create_supervisor_graph

_graph_instance = None
def get_compiled_graph():
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = create_supervisor_graph()
    return _graph_instance
