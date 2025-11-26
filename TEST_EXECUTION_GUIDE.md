# Test Execution Guide

Quick guide for running and evaluating the Deep Research AI Agent.

---

## Running Tests

### Basic Execution

```bash
python -m src.main --entity "Sam Altman" --depth 5 --output-dir test_results/sam_altman
```

### Test All Cases

```bash
# Test Case 1
python -m src.main --entity "Sam Altman" --depth 5 --output-dir test_results/sam_altman

# Test Case 2  
python -m src.main --entity "Sheryl Sandberg" --depth 5 --output-dir test_results/sheryl_sandberg

# Test Case 3
python -m src.main --entity "Marc Andreessen" --depth 5 --output-dir test_results/marc_andreessen
```

---

## Evaluating Results

After running a test case, evaluate discovery rate:

```bash
python evaluate_results.py "Sam Altman" test_results/sam_altman/*_state_*.json
```

**Output:**
- Discovery rate (% of expected facts found)
- Level 1 vs Level 2 performance
- Agent statistics (queries, iterations, confidence)

### Evaluate results of all test cases

```bash
# Test Case 1
python evaluate_results.py "Sam Altman" test_results/sam_altman/*_state_*.json

# Test Case 2
python evaluate_results.py "Sheryl Sandberg" test_results/sheryl_sandberg/*_state_*.json

# Test Case 3
python evaluate_results.py "Marc Andreessen" test_results/marc_andreessen/*_state_*.json
```

---

## Generated Files

Each test run creates:

| File | Description |
|------|-------------|
| `*_report_*.md` | Human-readable report |
| `*_audit_*.json` | Full execution log |
| `*_state_*.json` | Complete state snapshot |

---

## Troubleshooting

### No Results Found
```bash
# Verify Tavily API key
python -c "from src.config import load_config; load_config(validate=True)"
```

### Check Logs
```bash
tail -f research_agent.log
```

### Adjust Depth
```bash
# Increase iterations if not finding enough
python -m src.main --entity "Sam Altman" --depth 6
```

---

## Quick Reference

**Run test:**
```bash
python -m src.main --entity "Sam Altman" --depth 5 --output-dir test_results/sam_altman
```

**Evaluate:**
```bash
python evaluate_results.py "Sam Altman" test_results/sam_altman/*_state_*.json
```

**Check logs:**
```bash
tail -f research_agent.log
```

---

**See [`TEST_CASES.md`](TEST_CASES.md) for expected facts.**
