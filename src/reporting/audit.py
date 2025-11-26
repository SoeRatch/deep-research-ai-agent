"""
Audit trail logger for agent decisions and actions.

Tracks every step for debugging and transparency.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class AuditLogger:
    """Logs agent decisions and actions for auditability."""
    
    def __init__(self, output_dir: Path = Path("reports")):
        """
        Initialize audit logger.
        
        Args:
            output_dir: Directory to save audit logs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_audit_trail(
        self,
        audit_trail: List[Dict[str, Any]],
        entity: str,
        filename: str = None
    ) -> Path:
        """
        Save audit trail to JSON file.
        
        Args:
            audit_trail: List of audit entries from state
            entity: Entity name
            filename: Optional filename
            
        Returns:
            Path to saved audit file
        """
        if filename is None:
            entity_clean = entity.replace(' ', '_').lower()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{entity_clean}_audit_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        audit_data = {
            'entity': entity,
            'timestamp': datetime.now().isoformat(),
            'total_steps': len(audit_trail),
            'trail': audit_trail
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(audit_data, f, indent=2)
        
        logger.info(f"Audit trail saved to: {filepath}")
        return filepath
    
    def generate_audit_summary(self, audit_trail: List[Dict]) -> str:
        """
        Generate human-readable audit summary.
        
        Args:
            audit_trail: List of audit entries
            
        Returns:
            Markdown formatted summary
        """
        lines = ["# Audit Trail Summary\n"]
        
        # Group by node
        by_node = {}
        for entry in audit_trail:
            node = entry.get('node', 'unknown')
            if node not in by_node:
                by_node[node] = []
            by_node[node].append(entry)
        
        for node, entries in by_node.items():
            lines.append(f"## {node.title()} ({len(entries)} calls)\n")
            
            for i, entry in enumerate(entries, 1):
                iteration = entry.get('iteration', 0)
                data = entry.get('data', {})
                
                lines.append(f"### Call {i} (Iteration {iteration})\n")
                
                # Format key data points
                for key, value in data.items():
                    if isinstance(value, list):
                        lines.append(f"- **{key}**: {len(value)} items\n")
                    elif isinstance(value, dict):
                        lines.append(f"- **{key}**: {json.dumps(value)[:100]}...\n")
                    else:
                        lines.append(f"- **{key}**: {value}\n")
                
                lines.append("\n")
        
        return "".join(lines)
    
    def save_audit_summary(
        self,
        audit_trail: List[Dict],
        entity: str
    ) -> Path:
        """
        Save human-readable audit summary.
        
        Args:
            audit_trail: Audit entries
            entity: Entity name
            
        Returns:
            Path to saved summary
        """
        entity_clean = entity.replace(' ', '_').lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{entity_clean}_audit_summary_{timestamp}.md"
        
        filepath = self.output_dir / filename
        
        summary = self.generate_audit_summary(audit_trail)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info(f"Audit summary saved to: {filepath}")
        return filepath
