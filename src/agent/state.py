"""
Agent state schema for the research workflow.
Defines the TypedDict state that flows through the LangGraph.
"""

from typing_extensions import TypedDict
from typing import List, Dict, Any, Optional, Annotated
from operator import add
# from langgraph.graph.message import add_messages


class ResearchState(TypedDict):
    """State that flows through the research agent graph."""
    
    # Input
    entity: str  # Target entity name
    entity_type: str  # individual, organization, etc.
    
    # Research progress
    research_depth: int  # Current iteration depth
    max_depth: int  # Maximum allowed depth
    
    # Query management
    queries_executed: Annotated[List[str], add]  # All queries run so far
    next_queries: List[str]  # Queries planned for next steps
    
    # Data collected
    search_results: Annotated[List[Dict[str, Any]], add]  # All search results
    scraped_content: Annotated[List[Dict[str, Any]], add]  # All scraped pages
    
    # Extracted information
    facts_discovered: Annotated[List[Dict[str, Any]], add]  # All extracted facts
    connections: Annotated[List[Dict[str, Any]], add]  # All identified relationships
    risks_identified: Annotated[List[Dict[str, Any]], add]  # All detected risks

    # Entity tracking for second-order investigation
    entities_to_investigate: Annotated[List[Dict[str, Any]], add]  # Queue of discovered entities
    investigated_entities: Annotated[List[str], add]  # Names of entities already investigated
    
    # Metadata
    sources: Annotated[List[str], add]  # All source URLs used
    information_gaps: List[str]  # # Missing or unclear areas. What's still missing
    overall_confidence: float  # Aggregate confidence score
    
    # Control flow
    should_continue: bool  # Whether to continue research
    iteration_count: int  # Number of completed cycles
    
    # Final output
    final_report: Optional[str]  # Generated markdown report
    audit_trail: Annotated[List[Dict[str, Any]], add]  # Log of decisions taken


def create_initial_state(
    entity: str,
    entity_type: str = "individual",
    max_depth: int = 5
) -> ResearchState:
    """
    Create initial state for research agent.
    
    Args:
        entity: Target entity name
        entity_type: Type of entity
        max_depth: Maximum research depth
        
    Returns:
        Initial state dictionary
    """
    return {
        'entity': entity,
        'entity_type': entity_type,
        'research_depth': 0,
        'max_depth': max_depth,
        'queries_executed': [],
        'next_queries': [],
        'search_results': [],
        'scraped_content': [],
        'facts_discovered': [],
        'connections': [],
        'risks_identified': [],
        'entities_to_investigate': [],
        'investigated_entities': [],
        'sources': [],
        'information_gaps': [],
        'overall_confidence': 0.0,
        'should_continue': True,
        'iteration_count': 0,
        'final_report': None,
        'audit_trail': []
    }
