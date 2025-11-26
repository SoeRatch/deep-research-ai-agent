# src/main.py
"""
Main CLI entry point for the Research Agent.

Usage:
    python src/main.py --entity "Sam Altman" --depth 5 --output-dir reports
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from src.config import load_config
from src.agent.state import create_initial_state
from src.agent.graph import get_research_graph
from src.reporting.generator import ReportGenerator
from src.reporting.audit import AuditLogger

import json
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('research_agent.log')
    ]
)

logger = logging.getLogger(__name__)


async def run_research(
    entity: str,
    entity_type: str = "individual",
    max_depth: int = 5,
    output_dir: Path = Path("reports")
):
    """
    Run the research agent on an entity.
    
    Args:
        entity: Target entity name
        entity_type: Type of entity
        max_depth: Maximum research depth
        output_dir: Output directory for reports
    """
    logger.info(f"Starting research on: {entity}")
    logger.info(f"Max depth: {max_depth}")
    
    try:
        # Load and validate configuration
        config = load_config(validate=True)
        logger.info("Configuration validated successfully")
        
        # Create initial state
        initial_state = create_initial_state(
            entity=entity,
            entity_type=entity_type,
            max_depth=max_depth
        )
        
        # Get compiled graph
        graph = get_research_graph()
        
        # Run the agent
        logger.info("Starting agent workflow...")
        # Increase recursion limit to allow for deep research (depth * nodes_per_iteration)
        # 5 iterations * 5 nodes = 25 steps + 1(planning step) = 26 steps, so default 25 is too low.
        final_state = await graph.ainvoke(initial_state, {"recursion_limit": 100})
        
        logger.info("Research workflow completed")
        logger.info(f"Total facts discovered: {len(final_state['facts_discovered'])}")
        logger.info(f"Total connections: {len(final_state['connections'])}")
        logger.info(f"Total risks: {len(final_state['risks_identified'])}")
        logger.info(f"Overall confidence: {final_state['overall_confidence']:.2%}")
        
        # Generate reports
        report_gen = ReportGenerator(output_dir)
        report_path = report_gen.save_report(final_state)
        logger.info(f"Report saved to: {report_path}")
        
        # Save audit trail
        audit_logger = AuditLogger(output_dir)
        audit_path = audit_logger.save_audit_trail(
            final_state['audit_trail'],
            entity
        )
        logger.info(f"Audit trail saved to: {audit_path}")
        
        summary_path = audit_logger.save_audit_summary(
            final_state['audit_trail'],
            entity
        )
        logger.info(f"Audit summary saved to: {summary_path}")


        # Save full state snapshot for debugging/analysis
        entity_clean = entity.replace(' ', '_').lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        state_path = output_dir / f"{entity_clean}_state_{timestamp}.json"
        
        # Create a JSON-serializable version of state
        state_snapshot = {
            'entity': final_state['entity'],
            'entity_type': final_state['entity_type'],
            'generated_at': datetime.now().isoformat(),
            'metadata': {
                'iteration_count': final_state['iteration_count'],
                'research_depth': final_state['research_depth'],
                'max_depth': final_state['max_depth'],
                'overall_confidence': final_state['overall_confidence'],
                'should_continue': final_state['should_continue']
            },
            'queries': {
                'executed': final_state['queries_executed'],
                'next': final_state['next_queries']
            },
            'entities': {
                'to_investigate': final_state['entities_to_investigate'],
                'investigated': final_state['investigated_entities']
            },
            'data': {
                'facts_discovered': final_state['facts_discovered'],
                'connections': final_state['connections'],
                'risks_identified': final_state['risks_identified'],
                'sources': final_state['sources'],
                'information_gaps': final_state['information_gaps']
            },
            'counts': {
                'total_facts': len(final_state['facts_discovered']),
                'total_connections': len(final_state['connections']),
                'total_risks': len(final_state['risks_identified']),
                'total_sources': len(set(final_state['sources'])),
                'total_queries': len(final_state['queries_executed']),
                'entities_discovered': len(final_state['entities_to_investigate']),
                'entities_investigated': len(final_state['investigated_entities'])
            }
        }
        
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state_snapshot, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Full state snapshot saved to: {state_path}")
        
        print("\n" + "="*60)
        print("RESEARCH COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Entity: {entity}")
        print(f"Facts discovered: {len(final_state['facts_discovered'])}")
        print(f"Connections mapped: {len(final_state['connections'])}")
        print(f"Risks identified: {len(final_state['risks_identified'])}")
        print(f"Overall confidence: {final_state['overall_confidence']:.0%}")
        print(f"\nReport: {report_path}")
        print(f"Audit Trail: {audit_path}")
        print("="*60 + "\n")
        
        return final_state
        
    except Exception as e:
        logger.error(f"Research failed: {e}", exc_info=True)
        raise


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Research Agent - Deep investigation tool"
    )
    
    parser.add_argument(
        "--entity",
        type=str,
        required=True,
        help="Name of entity to research (person, organization, etc.)"
    )
    
    parser.add_argument(
        "--entity-type",
        type=str,
        default="",
        choices=["individual", "organization", "company"],
        help="Type of entity (default: individual)"
    )
    
    parser.add_argument(
        "--depth",
        type=int,
        default=5,
        help="Maximum research depth (iterations) (default: 5)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports",
        help="Output directory for reports (default: reports)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to .env config file (default: .env)"
    )
    
    args = parser.parse_args()
    
    # Override config path if provided
    if args.config:
        import os
        os.environ['ENV_FILE'] = args.config
    
    # Run research
    try:
        asyncio.run(run_research(
            entity=args.entity,
            entity_type=args.entity_type,
            max_depth=args.depth,
            output_dir=Path(args.output_dir)
        ))
    except KeyboardInterrupt:
        logger.info("Research interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


# For example, Run like this - 
# python -m src.main --entity "Sam Altman" --depth 5 --output-dir test_results/sam_altman
