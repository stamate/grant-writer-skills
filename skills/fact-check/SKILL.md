---
name: fact-check
description: Multi-pass hallucination and factual accuracy checker — verifies citations, claim-source alignment, and cross-model fact checking before review.
---


# Proposal Fact Check

You are a rigorous fact-checker verifying the factual accuracy of a grant proposal before it goes to peer review. Your job is to catch fabricated references, misattributed claims, unsupported superlatives, internal contradictions, and inflated statistics — any of which could be career-ending if submitted.

## Arguments

- `--proposal-dir <path>`: Proposal directory (required)
- `--no-codex`: Skip Codex cross-model verification even if available

Parse from the user's message.

## Procedure

### 1. Load Proposal

Read the assembled proposal at `<proposal_dir>/final/proposal.md`. Also read:
- `<proposal_dir>/sections/bibliography.md` — the reference list
- `<proposal_dir>/config.yaml` — for agency and companion settings
- `<proposal_dir>/budget/budget.md` — if it exists, for budget cross-checks
- `<proposal_dir>/sections/` — individual section files for detailed checking

### 2. Pass 1: Citation Verification

For EVERY reference in the bibliography, verify it is a real publication.

#### a. Extract all references

Parse `bibliography.md` to extract each citation entry. For each, extract: title, authors, year, venue, and DOI (if present).

#### b. Verify via Semantic Scholar

For each reference, search S2 to confirm the paper exists:
```bash
uv run grant-writer-grants search "<paper title>" --agency horizon --limit 3
```

If the tool doesn't find a match (grant search is for funded projects, not papers), use the Semantic Scholar API directly via WebSearch or the `/paper-lookup` skill if available:
```
/paper-lookup "<paper title> <first author> <year>"
```

#### c. Verify DOIs

For any reference with a DOI, verify it resolves:
```bash
curl -sI "https://doi.org/<DOI>" | head -5
```
A 302 redirect to the publisher means the DOI is valid. A 404 means it's fabricated.

#### d. Flag issues

For each reference, classify as:
- **VERIFIED**: Found in S2/CrossRef, metadata matches
- **UNVERIFIED**: Not found but could be legitimate (preprint, very recent, non-English venue)
- **SUSPICIOUS**: Metadata doesn't match (wrong year, wrong authors, wrong venue)
- **FABRICATED**: DOI doesn't resolve, paper not found anywhere, title returns zero results

**Any FABRICATED reference is a CRITICAL issue** — it must be removed or replaced before submission.

### 3. Pass 2: Claim-Source Alignment

For each major factual claim in the proposal that cites a reference, verify the cited source actually supports the claim. Run **3 parallel Agent subagents**, each covering a portion of the proposal sections.

Each subagent receives:
- A set of sections from the proposal
- The bibliography
- Available paper abstracts (from Pass 1 verification)

Each subagent's prompt:

> You are verifying claim-source alignment in a grant proposal. For each statement that cites a reference (e.g., "X has been shown to improve Y [3]"), check:
>
> 1. Does the cited paper's title/abstract actually relate to the claim?
> 2. Is the claim a fair representation of the cited work, or is it exaggerated?
> 3. Are specific numbers or statistics attributed to a source actually from that source?
>
> Flag these categories:
> - **MISATTRIBUTED**: Claim says paper shows X, but paper is about something else entirely
> - **EXAGGERATED**: Paper shows modest effect, proposal claims strong effect
> - **UNSUPPORTED**: Claim has no citation and is not common knowledge
> - **CORRECT**: Claim accurately reflects the cited source
>
> For each flagged issue, provide: the claim text, the citation, why it's problematic, and a suggested fix.

Collect results from all 3 subagents.

### 4. Pass 3: Cross-Model Fact Check (Codex)

**Skip if** `--no-codex` is set or Codex is not available.

Check Codex availability:
```bash
which codex 2>/dev/null && echo "CLI_OK" || echo "CLI_MISSING"
find "$HOME/.claude/plugins" ".claude/plugins" -maxdepth 5 -name "plugin.json" -exec grep -l '"codex"' {} \; 2>/dev/null | head -1
```
If not available, skip this pass silently.

When available, send the proposal to Codex for independent verification:

```
/codex:rescue --fresh --wait "You are a fact-checker for a grant proposal. Read the proposal below and flag ALL of the following issues. Be thorough — false claims in a grant can end careers.

FLAG THESE:
1. UNSUPPORTED SUPERLATIVES: 'first ever', 'unprecedented', 'no prior work', 'unique' — unless backed by evidence
2. INTERNAL CONTRADICTIONS: Budget says X postdocs but approach describes work for Y; timeline says 3 years but milestones span 4
3. INFLATED STATISTICS: Numbers that seem fabricated or unreasonably precise ('improves accuracy by 47.3%' without a source)
4. IMPOSSIBLE TIMELINES: Promising too much in too little time
5. VAGUE HANDWAVING: Sections that sound authoritative but say nothing concrete
6. STATE-OF-THE-ART CLAIMS: 'Current methods cannot...' or 'No existing approach...' — verify these are actually true
7. CIRCULAR CITATIONS: Citing the PI's own unpublished work as evidence without marking it as preliminary data

For EACH issue found, provide:
- Location (section and approximate text)
- Category (from list above)
- Severity (CRITICAL / WARNING / INFO)
- What's wrong
- Suggested fix

Proposal text: <read final/proposal.md and include full text>"
```

### 5. Pass 4: Internal Consistency Check

Without any external tools, perform a final consistency sweep across the full proposal:

1. **Budget vs Approach**: Count personnel mentioned in the approach section. Compare to personnel in `budget/budget.md`. Flag mismatches.
2. **Timeline vs Scope**: Check if the work described is achievable within the stated duration.
3. **Objectives vs Results**: Verify each stated objective has a corresponding methodology section and expected deliverable.
4. **Figure references**: Every `![...]()` reference points to a figure that's discussed in the text.
5. **Acronym consistency**: First use defines the acronym, subsequent uses are consistent.
6. **Number consistency**: If "5 work packages" is mentioned in the summary, verify there are exactly 5 in the implementation section.

### 6. Generate Fact Check Report

Compile all findings into `<proposal_dir>/review/fact_check.md`:

```markdown
# Fact Check Report

**Proposal**: <title>
**Agency**: <agency> / <mechanism>
**Date**: <timestamp>
**Overall**: <PASS / PASS WITH WARNINGS / FAIL>

## Summary

- Citations checked: N
- Verified: N | Unverified: N | Suspicious: N | Fabricated: N
- Claim-source issues: N
- Cross-model issues: N (or "Codex not available")
- Internal consistency issues: N

## Critical Issues (must fix before submission)

### [FABRICATED] Reference [3] does not exist
- **Citation**: Smith et al. (2024). "Neural approaches to..."
- **Evidence**: DOI 10.1234/fake returns 404. No results in Semantic Scholar.
- **Fix**: Remove this reference or replace with a verified publication.

### [MISATTRIBUTED] Claim on page 2 cites wrong source
- **Claim**: "Deep learning has achieved 95% accuracy on this task [7]"
- **Source [7]**: Paper is about natural language processing, not this task
- **Fix**: Find the correct source or rephrase the claim.

## Warnings (should fix)

### [UNSUPPORTED] Superlative on page 1
- **Text**: "This is the first approach to combine X with Y"
- **Issue**: No evidence provided. Similar approaches exist (see: <references>)
- **Fix**: Qualify as "one of the first" or "among the few" and cite related work.

### [INTERNAL] Budget-approach mismatch
- **Issue**: Approach describes 3 PhD students but budget lists 2 postdocs
- **Fix**: Align budget personnel with described research activities.

## Informational

### [VAGUE] Section 2.1 lacks specifics
- **Text**: "We will use state-of-the-art machine learning methods"
- **Suggestion**: Name the specific methods (e.g., "transformer-based architectures following [ref]")
```

### 7. Gate Decision

- If **any CRITICAL issues** exist: **BLOCK** the review phase. Report issues to the PI and require fixes before proceeding.
- If only **warnings**: Proceed to review but flag them prominently.
- If **clean**: Proceed to review.

**Human checkpoint**: Present the fact check report to the PI. For each critical issue, confirm whether to fix it or override (with justification).

### 8. Update State

```bash
uv run grant-writer-state update <proposal_dir> --phase fact_check --status <complete|failed>
```

If failed (critical issues), the orchestrator should return to the relevant phase (proposal writing or literature) to fix the issues before re-assembling and re-checking.
