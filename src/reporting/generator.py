"""
Report generator for research findings.

Outputs markdown reports with Mermaid diagrams for connection visualization.
"""

from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import logging

from src.agent.state import ResearchState

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates comprehensive markdown reports."""
    
    def __init__(self, output_dir: Path = Path("reports")):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_connection_diagram(self, connections: List[Dict]) -> str:
        """
        Generate Mermaid diagram for connections.
        
        Args:
            connections: List of connection dictionaries
            
        Returns:
            Mermaid diagram code
        """
        if not connections:
            return ""
        
        lines = ["```mermaid", "graph TD"]
        
        # Use first 15 connections to avoid overcrowding
        for i, conn in enumerate(connections[:15]):
            source = "TARGET"
            target = conn.get('target_entity', 'Unknown').replace(' ', '_').replace("'", "")
            relationship = conn.get('relationship_type', 'related')
            
            lines.append(f"    {source} -->|{relationship}| {target}")
        
        lines.append("```")
        return "\n".join(lines)
    
    def format_facts_table(self, facts: List[Dict], category: str = None) -> str:
        """
        Format facts as markdown table.
        
        Args:
            facts: List of fact dictionaries
            category: Optional category filter
            
        Returns:
            Markdown table
        """
        if category:
            facts = [f for f in facts if f.get('category') == category]
        
        if not facts:
            return "_No facts in this category_\n"
        
        lines = [
            "| Fact | Confidence | Source |",
            "|------|------------|--------|"
        ]
        
        for fact in facts[:20]:  # Limit to 20 per category
            claim = fact.get('claim', 'Unknown')[:100]  # Truncate long claims
            confidence = fact.get('confidence', 0)
            source = fact.get('source_url', 'N/A')
            source_display = source.split('/')[2] if '/' in source else source  # Show domain
            
            lines.append(f"| {claim} | {confidence:.0%} | {source_display} |")
        
        return "\n".join(lines) + "\n"
    
    def format_risks_section(self, risks: List[Dict]) -> str:
        """
        Format risks by severity.
        
        Args:
            risks: List of risk dictionaries
            
        Returns:
            Formatted markdown section
        """
        if not risks:
            return "_No significant risks identified_\n"
        
        # Group by severity
        high = [r for r in risks if r.get('severity') == 'high']
        medium = [r for r in risks if r.get('severity') == 'medium']
        low = [r for r in risks if r.get('severity') == 'low']
        
        sections = []
        
        if high:
            sections.append("### 🔴 High Severity\n")
            for risk in high:
                sections.append(f"- **[{risk.get('category', 'unknown').upper()}]** {risk.get('description', 'Unknown risk')}")
                sections.append(f"  - Confidence: {risk.get('confidence', 0):.0%}\n")
        
        if medium:
            sections.append("### 🟡 Medium Severity\n")
            for risk in medium:
                sections.append(f"- **[{risk.get('category', 'unknown').upper()}]** {risk.get('description', 'Unknown risk')}")
                sections.append(f"  - Confidence: {risk.get('confidence', 0):.0%}\n")
        
        if low:
            sections.append("### 🟢 Low Severity\n")
            for risk in low:
                sections.append(f"- **[{risk.get('category', 'unknown').upper()}]** {risk.get('description', 'Unknown risk')}\n")
        
        return "\n".join(sections)
    
    def _clean_markdown_blocks(self, content: str) -> str:
        """
        Remove markdown code block wrappers from content.
        
        Args:
            content: Raw content that may be wrapped in ```markdown...```
            
        Returns:
            Cleaned content
        """
        import re
        
        # Pattern: ```markdown\n...\n```  or  ```\n...\n```
        pattern = r'^```(?:markdown)?\s*\n(.*?)\n```\s*$'
        match = re.search(pattern, content.strip(), re.DOTALL)
        
        if match:
            logger.debug("Stripped markdown code blocks from report content")
            return match.group(1)
        
        return content
    
    def save_report(
        self,
        state: ResearchState,
        filename: str = None
    ) -> Path:
        """
        Save research report to file.
        
        Args:
            state: Final research state
            filename: Optional filename (default: entity_name_timestamp.md)
            
        Returns:
            Path to saved report
        """
        if filename is None:
            entity_clean = state['entity'].replace(' ', '_').lower()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{entity_clean}_{timestamp}.md"
        
        filepath = self.output_dir / filename
        
        # Use final report from state if available, otherwise generate
        if state.get('final_report'):
            report_content = state['final_report']
        else:
            report_content = self.generate_report_content(state)
        
        # Clean markdown code blocks if present (model sometimes wraps response)
        report_content = self._clean_markdown_blocks(report_content)
        
        # Add metadata header
        header = f"""---
entity: {state['entity']}
generated: {datetime.now().isoformat()}
total_facts: {len(state['facts_discovered'])}
total_sources: {len(set(state['sources']))}
confidence: {state['overall_confidence']:.2f}
---

"""
        
        full_content = header + report_content
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        logger.info(f"Report saved to: {filepath}")
        return filepath
    
    def generate_report_content(self, state: ResearchState) -> str:
        """
        Generate report content from state (fallback if model didn't generate).
        
        Args:
            state: Research state
            
        Returns:
            Markdown report content
        """
        sections = []
        
        sections.append(f"# Research Report: {state['entity']}\n")
        
        sections.append("## Executive Summary\n")
        sections.append(f"Investigation completed with {state['iteration_count']} research iterations.\n")
        sections.append(f"**Total Facts Discovered**: {len(state['facts_discovered'])}\n")
        sections.append(f"**Connections Identified**: {len(state['connections'])}\n")
        sections.append(f"**Risk Flags**: {len(state['risks_identified'])}\n")
        sections.append(f"**Overall Confidence**: {state['overall_confidence']:.0%}\n\n")
        
        sections.append("## Key Facts\n")
        categories = set(f.get('category', 'other') for f in state['facts_discovered'])
        for category in categories:
            sections.append(f"### {category.title()}\n")
            sections.append(self.format_facts_table(state['facts_discovered'], category))
            sections.append("\n")
        
        sections.append("## Network & Connections\n")
        if state['connections']:
            sections.append(self.generate_connection_diagram(state['connections']))
            sections.append("\n")
        else:
            sections.append("_No significant connections identified_\n\n")
        
        sections.append("## Risk Assessment\n")
        sections.append(self.format_risks_section(state['risks_identified']))
        sections.append("\n")
        
        sections.append("## Research Methodology\n")
        sections.append(f"- **Queries Executed**: {len(state['queries_executed'])}\n")
        sections.append(f"- **Sources Consulted**: {len(set(state['sources']))}\n")
        sections.append(f"- **Research Depth**: {state['iteration_count']} iterations\n\n")
        
        sections.append("## Sources\n")
        unique_sources = list(set(state['sources']))[:30]  # Limit to 30
        for i, source in enumerate(unique_sources, 1):
            sections.append(f"{i}. {source}\n")
        
        return "".join(sections)


if __name__ == "__main__":
    # Test report generation
    from src.agent.state import create_initial_state
    test_state = create_initial_state("Test Entity")
    test_state['facts_discovered'] = [
        {'category': 'biographical', 'claim': 'Test fact', 'confidence': 0.8, 'source_url': 'https://example.com'}
    ]
    
    generator = ReportGenerator()
    print(generator.generate_report_content(test_state))