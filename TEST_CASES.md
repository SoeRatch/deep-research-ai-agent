# Test Cases - Real Public Figures

This file defines the evaluation set using **real public figures** with verifiable online information. The agent can actually discover these facts through web searches, allowing genuine performance measurement.

## Purpose

Test the Deep Research AI Agent's ability to:
- Find basic biographical facts (Level 1)
- Discover hidden connections and non-obvious relationships (Level 2)
- Build knowledge through consecutive searches
- Investigate second-order entities (family members, business connections)

---

## Test Personas

### 1. Sam Altman
**Profile:** CEO of OpenAI, former Y Combinator president

**Level 1 Facts** (Direct searches, 2-3 iterations):
- Y Combinator president 2014-2019
- Loopt founder, sold to Green Dot Corporation 2012
- CEO of OpenAI since 2019

**Level 2 Facts** (Requires consecutive searches, 4-5 iterations):
- Invested in Helion Energy (nuclear fusion company)
- Brother Jack Altman is CEO of Lattice (HR software)
- Early investor in Reddit and Airbnb
- Property ownership in San Francisco
- Briefly fired from OpenAI board in November 2023

**Why this tests consecutive search:**
- Basic bio is easy to find
- Investment portfolio requires digging into financial disclosures
- Family connections (Jack Altman) need second-order investigation
- OpenAI board controversy requires temporal search of recent news

---

### 2. Sheryl Sandberg
**Profile:** Former Meta COO, author of Lean In

**Level 1 Facts** (Direct searches):
- Meta COO 2008-2022
- Google Vice President of Sales and Operations 2001-2008
- Chief of Staff for Treasury Secretary Lawrence Summers

**Level 2 Facts** (Consecutive searches required):
- Husband Dave Goldberg (SurveyMonkey CEO) died suddenly in 2015
- Board member of Walt Disney Company
- Connection to SurveyMonkey through late husband
- Criticized for Facebook's role in 2016 election
- Founded Lean In Foundation nonprofit

**Why this tests consecutive search:**
- Career history is straightforward
- Personal tragedy (Dave Goldberg) connects to SurveyMonkey
- Board memberships scattered across sources
- Controversy requires searching beyond official bio

---

### 3. Marc Andreessen
**Profile:** Co-founder of Andreessen Horowitz, Netscape creator

**Level 1 Facts** (Direct searches):
- Co-founded Andreessen Horowitz venture capital firm 2009
- Created Mosaic web browser 1993
- Netscape co-founder 1994

**Level 2 Facts** (Consecutive searches required):
- Board member of Meta/Facebook since 2008
- Early Bitcoin and cryptocurrency advocate
- Invested in Coinbase, Ripple (crypto companies)
- Wife Laura Arrillaga-Andreessen is Stanford philanthropist
- Controversial tweets on various political topics

**Why this tests consecutive search:**
- Tech history is well-documented
- Crypto investments require financial source searches
- Family connection (wife) needs second-order investigation
- Board positions scattered across corporate filings
- Social media controversies need timeline searching

---

## Evaluation Metrics

### Discovery Rate Targets
- **Overall:** ≥70% of all facts
- **Level 1:** ≥80% (easier facts)
- **Level 2:** ≥60% (hidden connections)

### What Success Looks Like
1. Agent finds most basic biographical facts
2. Agent discovers family/business connections through second-order investigation
3. Agent identifies investments and board positions via financial sources
4. Agent uncovers controversies through news archive searches
5. Consecutive searches build on previous findings

---

## Usage

### Run Test
```bash
# Test on Sam Altman
./demo.sh "Sam Altman"

# Test on Sheryl Sandberg
./demo.sh "Sheryl Sandberg"

# Test on Marc Andreessen
./demo.sh "Marc Andreessen"
```

### Evaluate Results
```bash
python evaluate_results.py "Sam Altman" test_results/sam_altman/*_state_*.json
```

### Expected Behavior
- Initial queries: "Sam Altman CEO OpenAI biography"
- Refined queries: "Sam Altman investments Helion Energy"
- Second-order: "Jack Altman Lattice CEO" (brother investigation)
- Temporal: "Sam Altman OpenAI fired November 2023"

---

## Why Real People?

**Assignment Requirement:**
> "have a name with deeply hidden facts about the person that one can find with so many searches"

Using real public figures ensures:
- ✅ Facts are actually discoverable via web searches
- ✅ Agent performance is genuinely measurable
- ✅ Validation against real online sources
- ✅ Demonstrates real-world capability

**Note:** All information is publicly available. This evaluation is for legitimate technical assessment purposes.

---

## Machine-Readable Format

The expected facts are stored in **`evaluation_data.json`** for automated evaluation.

```json
{
  "personas": {
    "Sam Altman": {
      "level_1_facts": [...],
      "level_2_facts": [...]
    }
  }
}
```

The evaluation script (`evaluate_results.py`) reads from this file automatically.
