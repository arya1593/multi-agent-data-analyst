"""LangGraph state machine: wires router → sql → (viz ‖ stats) → synthesizer."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from typing import Annotated, TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

load_dotenv()

from agents.router import router_node, route_decision
from agents.sql_agent import sql_node
from agents.viz_agent import viz_node
from agents.stats_agent import stats_node
from agents.synthesizer import synthesizer_node


class AgentState(TypedDict):
    messages:    Annotated[list, add_messages]
    query:       str
    intent:      str
    sql:         str
    sql_results: list
    chart_spec:  dict
    stats:       dict
    answer:      str
    error:       str


def _build_graph() -> StateGraph:
    # Constructs the LangGraph StateGraph with all nodes and edges
    builder = StateGraph(AgentState)

    builder.add_node("router", router_node)
    builder.add_node("sql", sql_node)
    builder.add_node("viz", viz_node)
    builder.add_node("stats", stats_node)
    builder.add_node("synthesizer", synthesizer_node)

    builder.set_entry_point("router")

    # All intents go through SQL first (viz/stats need data)
    builder.add_conditional_edges(
        "router",
        route_decision,
        {
            "sql":    "sql",
            "viz":    "sql",
            "stats":  "sql",
            "hybrid": "sql",
        },
    )

    # After SQL, run viz and stats in parallel
    builder.add_edge("sql", "viz")
    builder.add_edge("sql", "stats")

    # Both feed into synthesizer
    builder.add_edge("viz", "synthesizer")
    builder.add_edge("stats", "synthesizer")

    builder.add_edge("synthesizer", END)
    return builder


graph = _build_graph().compile()


def run_query(question: str) -> dict:
    # Convenience wrapper: invokes the full graph and returns the final state dict
    return graph.invoke({
        "query":       question,
        "messages":    [{"role": "user", "content": question}],
        "intent":      "",
        "sql":         "",
        "sql_results": [],
        "chart_spec":  {},
        "stats":       {},
        "answer":      "",
        "error":       "",
    })
