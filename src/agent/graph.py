"""
LangGraph workflow construction for research agent.
Defines the consecutive search loop with conditional edges.
"""

from langgraph.graph import StateGraph,START,END
from typing import Literal
import logging

from src.agent.state import ResearchState
from src.agent.nodes import ResearchNodes

logger = logging.getLogger(__name__)


def should_continue_research(state: ResearchState) -> Literal["continue", "report"]:
    """
    Decide whether to continue research or move to reporting.
    
    Args:
        state: Current research state
        
    Returns:
        "continue" to loop back or "report" to end
    """
    if state['should_continue']:
        logger.info(f"Continuing research (iteration {state['iteration_count']}/{state['max_depth']})")
        return "continue"
    else:
        logger.info("Research complete, generating report")
        return "report"


def build_research_graph() -> StateGraph:
    """
    Build the LangGraph workflow for research agent.
    
    Workflow:
    1. Plan → Search → Extract → Analyze → Validate → Refine
    2. Refine decides: continue (back to Search) or report
    3. Report generates final output
    
    Returns:
        Compiled StateGraph
    """
    nodes = ResearchNodes()
    
    # Create graph
    graph_workflow = StateGraph(ResearchState)
    
    # Add nodes
    graph_workflow.add_node("plan", nodes.plan_node)
    graph_workflow.add_node("search", nodes.search_node)
    graph_workflow.add_node("extract", nodes.extract_node)
    graph_workflow.add_node("analyze", nodes.analyze_node)
    graph_workflow.add_node("validate", nodes.validate_node)
    graph_workflow.add_node("refine", nodes.refine_node)
    graph_workflow.add_node("report", nodes.report_node)
    # Linear flow for initial research
    # Entry point
    # graph_workflow.set_entry_point("plan")
    graph_workflow.add_edge(START, "plan")
    graph_workflow.add_edge("plan","search")
    graph_workflow.add_edge("search", "extract")
    graph_workflow.add_edge("extract", "analyze")
    graph_workflow.add_edge("analyze", "validate")
    graph_workflow.add_edge("validate", "refine")
    
    # Conditional edge: continue loop or generate report
    graph_workflow.add_conditional_edges(
        "refine",
        should_continue_research,
        {
            "continue": "search",  # Loop back for another iteration
            "report": "report"     # Move to final report
        }
    )

    # End after report
    graph_workflow.add_edge("report",END)
    
    return graph_workflow.compile()


# Convenience function
_compiled_graph = None

def get_research_graph():
    """Get or build the compiled research graph."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_research_graph()
    return _compiled_graph
