---
name: landscape
description: Map the competitive funding landscape with funded grants databases, literature analysis, and PI overlap assessment.
---


# Competitive Landscape

You are conducting competitive intelligence for a grant proposal — understanding who is funded, what approaches dominate, and how to differentiate.

## Arguments

- `--agency <name>`: Which funding database to query (horizon, erc, msca, uefiscdi, pnrr)
- `--query <text>`: Research topic keywords
- `--pi-name <name>`: PI's name for prior support / overlap lookup
- `--proposal-dir <path>`: Proposal directory (required)
- `--no-scientific-skills`: Skip enhanced search even if plugin is available

Parse from the user's message.

## Procedure

### 0. Locate Plugin Root

```bash
if [ -f "tools/verify_setup.py" ]; then GRANTWRITER_ROOT="$(pwd)"
else GRANTWRITER_ROOT=$(find ".claude/plugins" "$HOME/.claude/plugins" -maxdepth 8 -name "verify_setup.py" -path "*grant-writer*" 2>/dev/null | head -1 | xargs dirname | xargs dirname); fi
export GRANTWRITER_ROOT; if [ -z "$GRANTWRITER_ROOT" ]; then echo "ERROR: Could not find grant-writer-skills plugin root."; fi; echo "Plugin root: $GRANTWRITER_ROOT"
```

### 1. Query Funded Grants Databases

Search for funded projects in the relevant database:

**For EU agencies** (Horizon Europe, ERC, MSCA) — query OpenAIRE:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/funded_grants.py" search "<query>" --agency <agency> --years 2022-2026 --limit 20
```

**For Romanian agencies** (UEFISCDI, PNRR) — query UEFISCDI public results with WebSearch fallback:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/funded_grants.py" search "<query>" --agency uefiscdi --limit 10
```

Save raw results to `landscape/funded_grants.json`.

### 2. Query PI's Own Grants

Search for the PI's existing and previous grants:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/funded_grants.py" pi-grants "<pi_name>" --agency <agency>
```

### 3. Enhanced Search (Optional — claude-scientific-skills)

**Skip if** `--no-scientific-skills` is set or plugin not available.

Check plugin availability:
```bash
find "$HOME/.claude/plugins" ".claude/plugins" -maxdepth 5 \
  -name "plugin.json" -exec grep -l '"claude-scientific"' {} \; 2>/dev/null | head -1
```
If not found, skip this section silently.

When available, run enhanced searches in parallel:
- `/research-lookup "<query> funded grants recent results"` — for real-time preprints and publications by funded PIs
- `/paper-lookup "<query>"` — search 10 academic databases for published work in this area

For translational grants (industry partnerships, innovation actions), optionally invoke:
- `/market-research-reports` — for market context and commercialization landscape

### 4. Build Competitive Brief

Analyze all gathered data and write `landscape/competitive_brief.md` covering:

- **Top 10 competing projects**: PI name, title, funding amount, dates, institution, key approach
- **Funding trends**: What topics are being funded? Growing or declining interest?
- **Common approaches**: What methodologies dominate?
- **Gaps and opportunities**: What is NOT being funded? Where is the differentiation opportunity?
- **Reviewer implications**: What will reviewers expect based on the funded landscape?

### 5. Build Overlap Analysis

Write `landscape/overlap_analysis.md` with an explicit comparison of each of the PI's active grants against the proposed work:

- For each active grant: title, agency, dates, budget, scientific scope
- **Scientific overlap**: Do the research questions overlap? Are the datasets the same?
- **Budgetary overlap**: Is the same personnel or equipment funded by both?
- **Conclusion per grant**: "No overlap", "Complementary — distinct objectives", or "Potential overlap — requires clarification"

This document feeds directly into the supporting documents phase (overlap/current support statement).

### 6. Build Prior Support Summary

Write `landscape/prior_support.md` summarizing the PI's previous funded projects and their results:

- Grant title, agency, period, amount
- Key publications resulting from each grant
- Stated objectives vs. achieved outcomes
- How prior work connects to the current proposal

## Notes

- If the funded grants API is down (OpenAIRE timeout, UEFISCDI unavailable), log a warning and continue with literature-only competitive context. Do not block the pipeline.
- The overlap analysis is critical for EU proposals where reviewers check for double funding.
- Prior support demonstrates the PI's track record — a key evaluation criterion for most agencies.
