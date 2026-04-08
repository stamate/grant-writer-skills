---
name: fact-check
description: Multi-pass hallucination and factual accuracy checker — verifies citations, factual claims against real-world sources, claim-source alignment, and cross-model verification.
---


# Proposal Fact Check

You are a rigorous fact-checker verifying the factual accuracy of a grant proposal before it goes to peer review. Your job is to catch fabricated references, false factual claims, misattributed citations, hallucinated entities, and internal contradictions — any of which could be career-ending if submitted.

## Arguments

- `--proposal-dir <path>`: Proposal directory (required)
- `--no-codex`: Skip Codex cross-model verification even if available
- `--no-scientific-skills`: Skip enhanced database/web verification even if available

Parse from the user's message.

## Procedure

### 1. Load Proposal

Read the assembled proposal at `<proposal_dir>/final/proposal.md`. Also read:
- `<proposal_dir>/sections/bibliography.md` — the reference list
- `<proposal_dir>/config.yaml` — for agency and companion settings
- `<proposal_dir>/budget/budget.md` — for budget cross-checks
- `<proposal_dir>/sections/` — individual section files

### 2. Extract All Verifiable Claims

Before running any verification passes, scan the entire proposal and extract every factual claim into a structured list. A "verifiable claim" is any statement that asserts something about the real world that could be true or false.

**Categories of claims to extract:**

| Category | Examples | How to verify |
|----------|---------|---------------|
| **Citations** | "[1] Smith et al. (2024). Neural approaches..." | S2, CrossRef, DOI |
| **Named entities** | "Company X has developed...", "Professor Y at University Z" | WebSearch |
| **Statistics** | "The market is worth EUR 3B", "affects 500M people" | WebSearch, /database-lookup |
| **Performance claims** | "Current methods achieve 85% accuracy", "outperforms by 20%" | /paper-lookup, WebSearch |
| **State-of-the-art claims** | "No existing approach combines X with Y" | /paper-lookup, /research-lookup |
| **Historical claims** | "Since the discovery of X in 2015..." | WebSearch |
| **Competitor claims** | "The EU-funded project Z demonstrated..." | /grant-writer-grants (OpenAIRE), WebSearch |
| **Regulatory claims** | "EU regulation 2024/XXX requires..." | WebSearch |
| **Epidemiological/market data** | "Diabetes affects 10% of Europeans" | /database-lookup (WHO, Eurostat) |

Output a structured list:
```json
[
  {"id": 1, "text": "The global AI drug discovery market is projected to reach EUR 4B by 2028", "category": "statistics", "section": "excellence", "citation": null},
  {"id": 2, "text": "Smith et al. demonstrated 95% accuracy on PDBbind [3]", "category": "performance_claim", "section": "state_of_the_art", "citation": "[3]"},
  {"id": 3, "text": "No existing approach combines equivariant GNNs with multi-task learning for NTDs", "category": "state_of_the_art", "section": "innovation", "citation": null},
  ...
]
```

### 3. Pass 1: Citation Verification

For EVERY reference in the bibliography, verify it is a real publication.

#### a. Extract all references

Parse `bibliography.md` to extract each citation entry. For each, extract: title, authors, year, venue, and DOI (if present).

#### b. Verify via academic databases

For each reference, attempt to find it:

**If `/paper-lookup` is available** (claude-scientific-skills installed):
```
/paper-lookup "<paper title> <first author> <year>"
```
This searches 10 databases (PubMed, arXiv, bioRxiv, OpenAlex, Crossref, S2, CORE, Unpaywall).

**If `/paper-lookup` is not available**, use WebSearch:
```
WebSearch: "<paper title>" "<first author>" site:scholar.google.com OR site:semanticscholar.org OR site:pubmed.ncbi.nlm.nih.gov
```

#### c. Verify DOIs

For any reference with a DOI, verify it resolves:
```bash
curl -sI "https://doi.org/<DOI>" 2>&1 | head -5
```
A redirect (301/302) to the publisher means the DOI is valid. A 404 means it's fabricated.

#### d. Classify each reference

- **VERIFIED**: Found in databases, metadata matches (title, authors, year)
- **UNVERIFIED**: Not found but plausibly real (preprint, very recent, non-English venue, book chapter)
- **SUSPICIOUS**: Found but metadata doesn't match (wrong year, wrong authors, wrong venue)
- **FABRICATED**: DOI returns 404, title returns zero results across all databases, authors don't exist

**Any FABRICATED reference is a CRITICAL issue.**

### 4. Pass 2: External Fact Verification

This is the most important pass. For each non-citation claim extracted in Step 2, verify it against real-world sources. Run **3 parallel Agent subagents**, each handling a batch of claims.

Each subagent receives a batch of claims and this prompt:

> You are verifying factual claims from a grant proposal against real-world evidence. For EACH claim, you MUST search for verification — do not rely on your training data alone, as it may be outdated or wrong.
>
> For each claim, follow this procedure:
>
> **Statistics and numbers** (market sizes, prevalence rates, population figures):
> - Use WebSearch to find the actual number from a credible source (WHO, Eurostat, Statista, official reports)
> - Compare the proposal's number to the verified number
> - Flag if: number is fabricated (no source exists), significantly wrong (>20% off), outdated (>3 years old), or from an unreliable source
>
> **Named entities** (companies, people, institutions, projects):
> - Use WebSearch to verify the entity exists
> - Verify the specific claim about them (e.g., "Company X developed Y" — did they?)
> - Flag if: entity doesn't exist, claim about them is false, entity is mischaracterized
>
> **Performance/accuracy claims** ("achieves 85% accuracy", "outperforms baseline by 20%"):
> - If cited: check in Pass 3 (claim-source alignment)
> - If uncited: Use WebSearch or /paper-lookup to find the actual benchmark results
> - Flag if: number is fabricated, significantly different from published results, or benchmark is misidentified
>
> **State-of-the-art claims** ("no existing approach", "first to combine", "novel"):
> - Use WebSearch and /paper-lookup to search for prior work that contradicts the claim
> - Search specifically for: "<approach X> <approach Y>" to find if anyone has combined them
> - Flag if: prior work exists that the proposal claims doesn't exist
>
> **Competitor/project claims** ("EU project Z demonstrated..."):
> - Use WebSearch or `uv run grant-writer-grants search "<project name>"` to verify
> - Flag if: project doesn't exist, or claim about it is wrong
>
> **Regulatory claims** ("EU regulation requires..."):
> - Use WebSearch to verify the regulation exists and says what the proposal claims
> - Flag if: regulation doesn't exist, is misquoted, or is repealed
>
> **Epidemiological/demographic data** ("affects N people", "N% of population"):
> - Use WebSearch to find the actual figure from WHO, Eurostat, CDC, or peer-reviewed sources
> - Flag if: number is significantly wrong or fabricated
>
> For EACH claim, output:
> ```json
> {
>   "claim_id": N,
>   "claim_text": "...",
>   "verdict": "VERIFIED | UNVERIFIABLE | INACCURATE | FABRICATED",
>   "evidence": "What you found (source URL or database result)",
>   "issue": "What's wrong (if any)",
>   "severity": "CRITICAL | WARNING | INFO",
>   "suggested_fix": "How to correct it"
> }
> ```

**If `/research-lookup` and `/database-lookup` are available** (claude-scientific-skills), also instruct subagents to use them:
- `/research-lookup "<claim topic>"` — for real-time web evidence with citations
- `/database-lookup "<entity or statistic>"` — for structured data from 78 databases (WHO, Eurostat, PubChem, UniProt, etc.)

These provide much more reliable verification than WebSearch alone.

### 5. Pass 3: Claim-Source Alignment

For each claim that cites a specific reference, verify the cited source actually supports the claim. Run **3 parallel Agent subagents**, each covering a portion of the proposal sections.

Each subagent receives:
- A set of cited claims (from Step 2, filtered to those with citations)
- The bibliography
- Available paper abstracts/titles (from Pass 1 verification results)

Each subagent's prompt:

> You are verifying claim-source alignment in a grant proposal. For each statement that cites a reference (e.g., "X has been shown to improve Y [3]"), check:
>
> 1. Does the cited paper's title/abstract actually relate to the claim?
> 2. Is the claim a fair representation of the cited work, or is it exaggerated?
> 3. Are specific numbers or statistics attributed to a source actually from that source?
>
> Classify each:
> - **ALIGNED**: Claim accurately reflects the cited source
> - **EXAGGERATED**: Paper shows modest effect, proposal claims strong effect
> - **MISATTRIBUTED**: Claim says paper shows X, but paper is about something else
> - **UNVERIFIABLE**: Can't confirm from abstract alone (not necessarily wrong)
>
> For each issue, provide: claim text, citation, why it's problematic, suggested fix.

### 6. Pass 4: Cross-Model Fact Check (Codex)

**Skip if** `--no-codex` is set or Codex is not available.

Check Codex availability:
```bash
which codex 2>/dev/null && echo "CLI_OK" || echo "CLI_MISSING"
find "$HOME/.claude/plugins" ".claude/plugins" -maxdepth 5 -name "plugin.json" -exec grep -l '"codex"' {} \; 2>/dev/null | head -1
```
If not available, skip this pass silently.

When available, send the full proposal AND the results from Passes 1-3 to Codex for independent cross-verification:

```
/codex:rescue --fresh --wait "You are an independent fact-checker for a grant proposal. A first-pass fact check has already been done by Claude — your job is to catch anything it missed. You are a DIFFERENT AI model so you may have different knowledge.

PREVIOUS FACT-CHECK RESULTS (from Claude):
<include summary of Pass 1-3 findings>

YOUR TASK — verify these findings AND search for NEW issues Claude missed:

1. VERIFY CLAUDE'S FINDINGS: For each issue Claude flagged, do you agree? Are there false positives?
2. NEW FABRICATIONS: Read the full proposal and flag any factual claims that seem wrong based on your knowledge
3. HALLUCINATED ENTITIES: Companies, people, projects, organizations mentioned that you cannot verify
4. WRONG NUMBERS: Statistics, market sizes, prevalence rates that seem off
5. FALSE STATE-OF-THE-ART: Claims that 'no one has done X' when in fact it has been done
6. TEMPORAL ERRORS: References to future events as past, or outdated information presented as current
7. GEOGRAPHIC ERRORS: Wrong country for an institution, wrong agency for a program

For EACH issue:
- Location (section + quote)
- Category
- Severity (CRITICAL / WARNING / INFO)
- What's wrong + evidence
- Whether this confirms or contradicts Claude's finding (if applicable)

Proposal text: <include full final/proposal.md>"
```

### 7. Pass 5: Internal Consistency Check

Without external tools, perform a final consistency sweep:

1. **Budget vs Approach**: Count personnel described in the methodology. Compare to budget line items. Flag if approach describes N people but budget funds M.
2. **Timeline vs Scope**: Estimate if the described work is achievable within the stated duration and with the stated team size.
3. **Objectives vs Methodology**: Verify each stated objective has corresponding tasks, deliverables, and milestones.
4. **Figure references**: Every `![...]()` points to a file discussed in the text.
5. **Acronym consistency**: First use defines the acronym, subsequent uses are consistent.
6. **Number consistency**: If "5 work packages" appears in the summary, count exactly 5 in the implementation section.
7. **Cross-section consistency**: Claims in the abstract match what's in the detailed sections (amounts, timelines, team size).

### 8. Generate Fact Check Report

Compile ALL findings from all 5 passes into `<proposal_dir>/review/fact_check.md`:

```markdown
# Fact Check Report

**Proposal**: <title>
**Agency**: <agency> / <mechanism>
**Date**: <timestamp>
**Overall**: <PASS / PASS WITH WARNINGS / FAIL>

## Summary

| Pass | Items Checked | Issues Found |
|------|--------------|--------------|
| 1. Citation verification | N references | N fabricated, N suspicious |
| 2. External fact verification | N claims | N fabricated, N inaccurate |
| 3. Claim-source alignment | N cited claims | N misattributed, N exaggerated |
| 4. Cross-model verification (Codex) | N claims | N new issues, N confirmed |
| 5. Internal consistency | N checks | N contradictions |

## Critical Issues (must fix before submission)

### [FABRICATED REFERENCE] Reference [3] does not exist
- **Citation**: Smith et al. (2024). "Neural approaches to..."
- **Verification**: DOI 10.1234/fake returns 404. Zero results in Semantic Scholar, PubMed, Google Scholar.
- **Fix**: Remove this reference or replace with a verified publication.

### [FABRICATED STATISTIC] Market size claim is false
- **Claim**: "The global AI drug discovery market is projected to reach EUR 10B by 2025" (Section: Excellence)
- **Verification**: WebSearch finds the actual figure is EUR 3.2B by 2028 (source: Grand View Research 2024)
- **Fix**: Replace with verified figure and cite the source.

### [HALLUCINATED ENTITY] Company does not exist
- **Claim**: "BioTech Solutions Ltd. has demonstrated..." (Section: State of the Art)
- **Verification**: WebSearch finds no company by this name in the biotech space.
- **Fix**: Remove or replace with a real company and verified claim.

### [FALSE STATE-OF-THE-ART] Prior work exists
- **Claim**: "No existing approach combines equivariant GNNs with multi-task learning" (Section: Innovation)
- **Verification**: Found: Zhang et al. (2024) "Multi-task Equivariant GNNs for Drug Discovery" in NeurIPS 2024.
- **Fix**: Acknowledge prior work and differentiate your approach.

## Warnings (should fix)

### [EXAGGERATED CLAIM] Performance overstated
- **Claim**: "achieves 95% accuracy on PDBbind [7]" (Section: Methodology)
- **Source [7]**: Paper reports 89% accuracy on the core set, not 95%.
- **Fix**: Correct the number to 89% or specify which subset/metric.

### [OUTDATED STATISTIC] Number is from old source
- **Claim**: "Diabetes affects 6% of the European population" (Section: Impact)
- **Verification**: Current WHO data (2024) shows 9.2% prevalence in the EU.
- **Fix**: Update to current figure and cite WHO source.

### [INTERNAL CONTRADICTION] Budget-approach mismatch
- **Issue**: Approach describes 3 PhD students working on WP2-WP4, but budget lists 2 postdocs and 0 PhD students.
- **Fix**: Align budget personnel with described research activities.

## Cross-Model Analysis (Claude vs Codex)

| Finding | Claude | Codex | Confidence |
|---------|--------|-------|------------|
| Reference [3] fabricated | Flagged | Confirmed | HIGH |
| Market size wrong | Flagged | Confirmed | HIGH |
| Company X doesn't exist | Not flagged | Flagged | MEDIUM |
| Timeline unrealistic | Flagged (warning) | Not flagged | LOW |

**Cross-model agreements** (both flagged): These are the most reliable findings.
**Single-model findings**: Investigate manually — one model may have better/worse knowledge.

## Informational

### [VAGUE] Section 2.1 lacks specifics
- **Text**: "We will use state-of-the-art machine learning methods"
- **Suggestion**: Name the specific methods and cite foundational papers.
```

### 9. Gate Decision

- **CRITICAL issues exist** → **BLOCK** the review phase. The proposal cannot be reviewed with fabricated content. Report issues to the PI and require fixes.
- **Only warnings** → Proceed to review but prominently flag all warnings. The PI should fix them but they aren't submission-blocking.
- **Clean** → Proceed to review.

**Human checkpoint**: Present the fact check report. For each critical issue:
- Show the claim, the evidence it's wrong, and the suggested fix
- Ask PI to confirm: fix it, override with justification, or investigate further

### 10. Update State

```bash
uv run grant-writer-state update <proposal_dir> --phase fact_check --status <complete|failed>
```

If failed (critical issues), the orchestrator returns to the relevant phase (proposal writing or literature) to fix issues, then re-assembles and re-checks.
