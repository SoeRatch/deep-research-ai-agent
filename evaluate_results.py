#!/usr/bin/env python3
"""
Evaluation script for test persona results.

Usage:
    python evaluate_results.py <persona_name> <state_file>

Example:
    python evaluate_results.py "Elena Vasquez" test_results/elena_vasquez/elena_vasquez_state_*.json
"""

import sys
import json
import glob
from pathlib import Path
from typing import Dict, List, Any

# Path to evaluation data file
EVALUATION_FILE = Path(__file__).parent / "evaluation_data.json"


def load_evaluation_data() -> Dict[str, Any]:
    """Load evaluation data from JSON file (single source of truth)."""
    if not EVALUATION_FILE.exists():
        print(f"❌ Evaluation data file not found: {EVALUATION_FILE}")
        print("Please ensure evaluation_data.json exists in the project root.")
        sys.exit(1)
    
    with open(EVALUATION_FILE, 'r') as f:
        data = json.load(f)
    
    # Convert to normalized format for backward compatibility
    evaluation_data = {}
    for persona_name, persona_info in data['personas'].items():
        normalized_name = persona_name.lower()
        evaluation_data[normalized_name] = {
            'level_1': persona_info['level_1_facts'],
            'level_2': persona_info['level_2_facts']
        }
    
    return evaluation_data, data.get('evaluation_criteria', {})


# Load evaluation data at module level
EVALUATION_DATA, CRITERIA = load_evaluation_data()



def load_state(file_pattern: str) -> Dict[str, Any]:
    """Load state snapshot from JSON file."""
    files = glob.glob(file_pattern)
    if not files:
        print(f"❌ No state file found matching: {file_pattern}")
        sys.exit(1)
    
    # Use most recent file
    state_file = sorted(files)[-1]
    print(f"📂 Loading state from: {state_file}\n")
    
    with open(state_file, 'r') as f:
        return json.load(f)


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    return text.lower().strip()


def check_fact_discovered(expected: str, facts: List[Dict]) -> bool:
    """Check if expected fact was discovered."""
    expected_keywords = set(normalize_text(expected).split())
    
    for fact in facts:
        fact_text = normalize_text(fact.get('claim', ''))
        fact_keywords = set(fact_text.split())
        
        # Check if most keywords match
        overlap = len(expected_keywords & fact_keywords)
        if overlap >= len(expected_keywords) * 0.5:  # 50% overlap
            return True
    
    return False


def evaluate_persona(persona_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate results for a persona."""
    persona_key = normalize_text(persona_name)
    
    if persona_key not in EVALUATION_DATA:
        print(f"⚠️  No evaluation data for '{persona_name}'")
        print(f"Available personas: {', '.join(EVALUATION_DATA.keys())}")
        return {}
    
    expected = EVALUATION_DATA[persona_key]
    facts = state.get('data', {}).get('facts_discovered', [])
    
    # Check Level 1 facts
    level_1_found = 0
    level_1_total = len(expected['level_1'])
    for fact in expected['level_1']:
        if check_fact_discovered(fact, facts):
            level_1_found += 1
            print(f"✅ Level 1: {fact}")
        else:
            print(f"❌ Level 1: {fact}")
    
    # Check Level 2 facts
    level_2_found = 0
    level_2_total = len(expected['level_2'])
    for fact in expected['level_2']:
        if check_fact_discovered(fact, facts):
            level_2_found += 1
            print(f"✅ Level 2: {fact}")
        else:
            print(f"❌ Level 2: {fact}")
    
    # Calculate metrics
    total_expected = level_1_total + level_2_total
    total_found = level_1_found + level_2_found
    
    discovery_rate = total_found / total_expected if total_expected > 0 else 0
    level_1_rate = level_1_found / level_1_total if level_1_total > 0 else 0
    level_2_rate = level_2_found / level_2_total if level_2_total > 0 else 0
    
    return {
        'total_expected': total_expected,
        'total_found': total_found,
        'discovery_rate': discovery_rate,
        'level_1_rate': level_1_rate,
        'level_2_rate': level_2_rate,
        'level_1_found': level_1_found,
        'level_1_total': level_1_total,
        'level_2_found': level_2_found,
        'level_2_total': level_2_total,
    }


def print_summary(persona_name: str, state: Dict[str, Any], metrics: Dict[str, Any]):
    """Print evaluation summary."""
    print("\n" + "="*60)
    print(f"EVALUATION SUMMARY: {persona_name}")
    print("="*60)
    
    # Discovery rates
    print(f"\n📊 Discovery Rates:")
    print(f"  Overall:  {metrics['discovery_rate']:.0%} ({metrics['total_found']}/{metrics['total_expected']})")
    print(f"  Level 1:  {metrics['level_1_rate']:.0%} ({metrics['level_1_found']}/{metrics['level_1_total']})")
    print(f"  Level 2:  {metrics['level_2_rate']:.0%} ({metrics['level_2_found']}/{metrics['level_2_total']})")
    
    # Agent stats
    metadata = state.get('metadata', {})
    counts = state.get('counts', {})
    
    print(f"\n🔍 Agent Performance:")
    print(f"  Iterations:        {metadata.get('iteration_count', 'N/A')}/{metadata.get('research_depth', 'N/A')}")
    print(f"  Total facts:       {counts.get('total_facts', 0)}")
    print(f"  Connections:       {counts.get('total_connections', 0)}")
    print(f"  Risks identified:  {counts.get('total_risks', 0)}")
    print(f"  Overall confidence: {metadata.get('overall_confidence', 0):.0%}")
    print(f"  Queries executed:  {counts.get('total_queries', 0)}")
    
    # Search efficiency
    entities = state.get('entities', {})
    print(f"\n🕸️  Second-Order Investigation:")
    print(f"  Entities discovered:    {counts.get('entities_discovered', 0)}")
    print(f"  Entities investigated:  {counts.get('entities_investigated', 0)}")
    
    # Assessment
    print(f"\n✅ Assessment:")
    
    if metrics['discovery_rate'] >= 0.7:
        print("  🌟 EXCELLENT - Exceeded 70% discovery target")
    elif metrics['discovery_rate'] >= 0.5:
        print("  ✅ GOOD - Met minimum 50% threshold")
    else:
        print("  ⚠️  NEEDS IMPROVEMENT - Below 50% threshold")
    
    if metrics['level_1_rate'] >= 0.8:
        print("  🌟 EXCELLENT - Level 1 discovery ≥80%")
    elif metrics['level_1_rate'] >= 0.6:
        print("  ✅ GOOD - Level 1 discovery ≥60%")
    else:
        print("  ⚠️  NEEDS IMPROVEMENT - Level 1 discovery <60%")
    
    if metrics['level_2_rate'] >= 0.6:
        print("  🌟 EXCELLENT - Level 2 discovery ≥60%")
    elif metrics['level_2_rate'] >= 0.4:
        print("  ✅ GOOD - Level 2 discovery ≥40%")
    else:
        print("  ⚠️  NEEDS IMPROVEMENT - Level 2 discovery <40%")
    
    print("\n" + "="*60 + "\n")


def main():
    if len(sys.argv) < 3:
        print("Usage: python evaluate_results.py <persona_name> <state_file>")
        print("\nExamples:")
        print('  python evaluate_results.py "Sam Altman" test_results/sam_altman/*_state_*.json')
        print('  python evaluate_results.py "Sheryl Sandberg" test_results/sheryl_sandberg/*_state_*.json')
        print('  python evaluate_results.py "Marc Andreessen" test_results/marc_andreessen/*_state_*.json')
        sys.exit(1)
    
    persona_name = sys.argv[1]
    state_pattern = sys.argv[2]
    
    print(f"🎯 Evaluating: {persona_name}")
    print("-" * 60)
    
    # Load state
    state = load_state(state_pattern)
    
    # Evaluate
    print(f"\n📋 Checking discovered facts:\n")
    metrics = evaluate_persona(persona_name, state)
    
    if metrics:
        # Print summary
        print_summary(persona_name, state, metrics)


if __name__ == "__main__":
    main()
