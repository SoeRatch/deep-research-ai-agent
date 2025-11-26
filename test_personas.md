# Test Personas & Evaluation Set

This document defines three test personas with documented hidden facts that serve as ground truth for evaluating the Deep Research AI Agent's capability to uncover non-obvious information through consecutive searches.

---

## Persona 1: Elena Vasquez - Tech Executive with Obscure Connections

### Public Profile
- **Name:** Elena Vasquez
- **Role:** Former CTO of MicroDyne Systems (2015-2019)
- **Current:** Independent AI consultant
- **LinkedIn:** Standard professional history
- **Known for:** Speaking at tech conferences, open-source contributions

### Hidden Facts (Evaluation Set)

#### Level 1: Moderately Hidden (2-3 searches)
1. **Early Career Controversy**
   - Left previous company (DataCore Inc.) abruptly in 2014
   - Settlement with non-disclosure agreement
   - **Source hints:** Industry forums, archived news
   - **Expected discovery:** Within 2-3 iterations

2. **Board Member of Obscure Nonprofit**
   - Serves on board of "Digital Ethics Alliance" (small organization)
   - Organization funded by controversial tech billionaire
   - **Source hints:** Nonprofit databases, obscure press releases
   - **Expected discovery:** Within 2-3 iterations

#### Level 2: Deeply Hidden (4-5 searches)
3. **Family Connection to Defense Contractor**
   - Brother-in-law is senior executive at Northrop subsidiary
   - Potential conflict with her AI ethics advocacy
   - **Source hints:** Cross-referencing family records, LinkedIn connections
   - **Expected discovery:** Requires second-order entity investigation

4. **Patent Dispute Settlement**
   - Settled patent dispute with former employer in 2016
   - Terms sealed, only court filing numbers publicly accessible
   - **Source hints:** PACER database mentions, legal blogs
   - **Expected discovery:** Advanced search depth

5. **Advisory Role to Controversial Startup**
   - Unpaid advisor to facial recognition startup (2018)
   - Startup later investigated for privacy violations
   - Never publicly disclosed this relationship
   - **Source hints:** Startup's early press releases (archived), investor communications
   - **Expected discovery:** Requires consecutive searches building on previous findings

### Risk Patterns to Detect
- **Inconsistency:** Public AI ethics stance vs. advisory role to surveillance tech
- **Non-disclosure:** Hidden connections to defense industry
- **Pattern:** Multiple NDAs and settlements suggest potential legal issues

### Expected Connections
- Elena Vasquez → MicroDyne Systems → Government contracts
- Elena Vasquez → Brother-in-law → Defense industry
- Elena Vasquez → Digital Ethics Alliance → Controversial funder

---

## Persona 2: Marcus Chen - Political Figure with Historical Incidents

### Public Profile
- **Name:** Marcus Chen
- **Role:** City Council Member, San Francisco (2018-Present)
- **Background:** Community organizer, small business owner
- **Public stance:** Affordable housing advocate, tech regulation supporter
- **Wikipedia:** Basic biographical info

### Hidden Facts (Evaluation Set)

#### Level 1: Moderately Hidden (2-3 searches)
1. **Failed Business Venture**
   - Owned restaurant that closed in 2015 with unpaid debts
   - Small claims court cases from vendors
   - **Source hints:** Local business records, court databases
   - **Expected discovery:** Within 2-3 iterations

2. **Campaign Finance Irregularity**
   - 2018 campaign received donation that was later returned
   - Donor had pending ethics violation
   - **Source hints:** Campaign finance databases, local news archives
   - **Expected discovery:** Within 2-3 iterations

#### Level 2: Deeply Hidden (4-5 searches)
3. **College Disciplinary Action**
   - Academic probation at UC Berkeley (1998)
   - Minor plagiarism incident, resolved internally
   - **Source hints:** Obscure student newspaper archives
   - **Expected discovery:** Requires specific temporal queries

4. **Real Estate Investment Conflict**
   - Wife owns property in district he regulates
   - Purchased before taking office but not disclosed
   - **Source hints:** Property records cross-referenced with spouse
   - **Expected discovery:** Requires second-order entity investigation (spouse)

5. **Association with Lobbying Firm**
   - Brother worked for tech lobbying firm while Chen voted on tech issues
   - Not illegal but potential appearance of conflict
   - **Source hints:** LinkedIn, lobbying disclosure databases
   - **Expected discovery:** Requires connecting family relationships to policy votes

### Risk Patterns to Detect
- **Financial irregularity:** Business debts, undisclosed property
- **Conflict of interest:** Family members in regulated industries
- **Inconsistency:** Affordable housing advocacy vs. property investment

### Expected Connections
- Marcus Chen → Wife → Real estate holdings → Zoning votes
- Marcus Chen → Brother → Tech lobbying firm → Tech regulation votes
- Marcus Chen → Campaign donors → Policy decisions

---

## Persona 3: Alexandra "Alex" Thornton - Entrepreneur with Complex Financial Ties

### Public Profile
- **Name:** Alexandra Thornton
- **Role:** CEO & Founder, GreenTech Innovations (2017-Present)
- **Background:** Serial entrepreneur, sustainability advocate
- **Funding:** $15M Series A (public knowledge)
- **Press:** Featured in Forbes, TechCrunch for clean energy work

### Hidden Facts (Evaluation Set)

#### Level 1: Moderately Hidden (2-3 searches)
1. **Previous Startup Failure**
   - Founded "SolarWave" in 2013, shut down in 2015
   - Investors lost money, some complaints on social media
   - **Source hints:** Crunchbase history, investor forums
   - **Expected discovery:** Within 2-3 iterations

2. **Shell Company Ownership**
   - Owns "Thornton Holdings LLC" in Delaware
   - Used for personal investments, not disclosed
   - **Source hints:** Delaware corporate database
   - **Expected discovery:** Within 2-3 iterations

#### Level 2: Deeply Hidden (4-5 searches)
3. **Offshore Account Connection**
   - Name appears in Paradise Papers leak peripherally
   - Connected to financial advisor who managed offshore accounts
   - Not accused of wrongdoing but association exists
   - **Source hints:** Paradise Papers database, financial advisor connections
   - **Expected discovery:** Requires consecutive searches on connected entities

4. **Family Member's Criminal Record**
   - Father convicted of securities fraud (1995)
   - Different last name (mother's maiden name used by Alex)
   - **Source hints:** Court records, family tree databases
   - **Expected discovery:** Requires second-order investigation with name variations

5. **Competitor Acquisition Irregularity**
   - GreenTech acquired small competitor in 2019
   - Competitor's founder alleged IP theft before acquisition
   - Quietly settled, terms not disclosed
   - **Source hints:** Patent office disputes, archived startup blogs, legal filings
   - **Expected discovery:** Requires building context from previous findings

### Risk Patterns to Detect
- **Pattern of failure:** Multiple business closures with investor losses
- **Opacity:** Shell companies, offshore associations
- **Family history:** Potential learned behavior from father's fraud
- **Legal disputes:** Pattern of IP conflicts and settlements

### Expected Connections
- Alexandra Thornton → SolarWave → Angry investors
- Alexandra Thornton → Thornton Holdings LLC → Undisclosed investments
- Alexandra Thornton → Financial advisor → Paradise Papers
- Alexandra Thornton → Father (different surname) → Securities fraud conviction

---

## Evaluation Metrics

### Success Criteria for Agent Performance

#### Discovery Rate by Level
- **Level 1 Facts (6 total):** Agent should discover ≥80% (≥5 facts)
- **Level 2 Facts (9 total):** Agent should discover ≥60% (≥6 facts)
- **Overall:** ≥70% of all hidden facts discovered

#### Search Efficiency
- **Depth required:** Match expected iteration count (±1)
- **Query relevance:** Successive queries build on findings
- **No redundancy:** Minimal duplicate queries

#### Quality Metrics
1. **Accuracy:** Facts discovered must be verifiable
2. **Confidence Scoring:** Appropriate confidence levels (0.6-0.9 for hidden facts)
3. **Risk Identification:** Agent flags inconsistencies and patterns
4. **Connection Mapping:** Discovers at least 70% of expected connections

#### Second-Order Investigation
- Agent must identify and investigate at least 2 related entities per persona
- Examples: spouse, family members, business partners, advisors

---

## Testing Protocol

### For Each Persona:

1. **Run Agent:**
   ```bash
   python -m src.main --entity "[Persona Name]" --depth 5 --output-dir test_results
   ```

2. **Collect Outputs:**
   - Main report: `test_results/[persona]_report_*.md`
   - Audit trail: `test_results/[persona]_audit_*.json`
   - State snapshot: `test_results/[persona]_state_*.json`

3. **Evaluate:**
   - Compare discovered facts against evaluation set
   - Check discovery timing (iteration count)
   - Verify risk pattern detection
   - Validate connection mapping

4. **Score:**
   - Calculate discovery rate
   - Assess search efficiency
   - Document any missed facts and reasons

---

## Expected Agent Behavior

### Persona 1 (Elena Vasquez)
- **Initial queries:** "Elena Vasquez CTO MicroDyne", "Elena Vasquez controversy", "Elena Vasquez patents"
- **Refined queries:** "DataCore Inc settlement 2014", "Digital Ethics Alliance funding", "Elena Vasquez family"
- **Second-order:** Investigate brother-in-law, Digital Ethics Alliance funder

### Persona 2 (Marcus Chen)
- **Initial queries:** "Marcus Chen San Francisco council", "Marcus Chen business", "Marcus Chen campaign finance"
- **Refined queries:** "Marcus Chen restaurant lawsuit", "Marcus Chen wife property", "Marcus Chen family lobbying"
- **Second-order:** Investigate wife's property holdings, brother's employment

### Persona 3 (Alexandra Thornton)
- **Initial queries:** "Alexandra Thornton GreenTech", "Alexandra Thornton previous companies", "Alexandra Thornton investments"
- **Refined queries:** "SolarWave startup failure", "Thornton Holdings Delaware", "Alexandra Thornton Paradise Papers"
- **Second-order:** Investigate father with surname variations, financial advisor

---

## Notes for Demonstration

- These personas are **fictional** but based on realistic scenarios
- Hidden facts are designed to mirror real-world intelligence gathering challenges
- Some facts require **consecutive searches** (can't find in one search)
- Some facts require **second-order investigation** (investigating connected entities)
- The evaluation set tests all core capabilities:
  - Deep fact extraction
  - Risk pattern recognition
  - Connection mapping
  - Source validation
  - Dynamic query refinement

**Use these personas to demonstrate your agent's capability during Phase 2 live demo.**
