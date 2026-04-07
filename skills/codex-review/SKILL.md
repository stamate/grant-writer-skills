---
name: codex-review
description: Standalone Codex agency-calibrated grant review with optional panel mode and supporting document analysis. Requires codex-plugin-cc to be installed.
---


# Codex Grant Review

You are a review coordinator that leverages the Codex plugin to produce an agency-calibrated review of a grant proposal, optionally using a 3-persona panel (Scientific Reviewer, Program Officer, Feasibility Assessor).

## Prerequisites

This skill requires the **codex-plugin-cc** Claude Code plugin. If Codex is not available, inform the user and suggest using `/grant-writer:review` instead.

## Arguments

- `--proposal <path>`: Path to proposal Markdown file (required)
- `--agency <name>`: Agency key for calibration (horizon, erc, msca, uefiscdi, pnrr)
- `--panel / --no-panel`: Enable/disable 3-persona panel (default: enabled)
- `--docs <path>`: Additional documents folder (e.g., `sections/`)

Parse from the user's message.

## Procedure

### 1. Check Codex Availability

Both the Codex CLI and the codex-plugin-cc Claude Code plugin must be installed and authenticated:

```bash
which codex 2>/dev/null && echo "CLI_OK" || echo "CLI_MISSING"
find "$HOME/.claude/plugins" ".claude/plugins" -maxdepth 5 -name "plugin.json" -exec grep -l '"codex"' {} \; 2>/dev/null | head -1
codex login status 2>/dev/null && echo "AUTH_OK" || echo "AUTH_MISSING"
```

If CLI is missing:
- Print: "Codex CLI not found. Install with: npm install -g @openai/codex"
- **Stop here.**

If CLI found but plugin missing:
- Print: "Codex CLI found but codex-plugin-cc not installed. Install with: claude install gh:stamate/codex-plugin-cc"
- **Stop here.**

If CLI + plugin found but not authenticated:
- Print: "Codex installed but not authenticated. Run: codex login"
- **Stop here.**

### 2. Read the Proposal

Read the proposal file at `<proposal_path>`. Confirm the proposal content is present and non-empty.

### 3. Run Codex Grant Review

Build the command based on arguments:

**With panel mode (default)**:
```
/codex:grant-review <proposal_path> --panel --agency <agency> --wait
```

**With panel mode and supporting docs**:
```
/codex:grant-review <proposal_path> --docs <docs_path> --panel --agency <agency> --wait
```

**Without panel mode** (`--no-panel`):
```
/codex:grant-review <proposal_path> --agency <agency> --wait
```

The Codex plugin returns agency-calibrated review output with:
- `recommendation`: fund / fund-with-revisions / do-not-fund
- `summary`, `strengths`, `weaknesses`
- Per-criterion scores calibrated to the specified agency
- In panel mode: individual reviewer assessments + synthesis with `consensus_points`, `disagreements`, `aggregated_scores`, `priority_actions`

### 4. Save Output

Save the Codex review output:

Determine the output directory from the proposal path (use the parent directory, or `review/` within the proposal directory if part of a larger proposal structure).

```bash
cat > <output_dir>/codex_review.md << 'MD_EOF'
<codex review output>
MD_EOF
```

### 5. Merge with Claude Review (if exists)

If a Claude review already exists at `<output_dir>/claude_review.json` (from a prior `/grant-writer:review` run), generate a merged summary.

Read the Claude review JSON and the Codex review output. Produce a merged review at `<output_dir>/merged_review.json` combining:
- Claude scores and assessment
- Codex scores and recommendation
- Consensus points (both agree)
- Disagreements (reviews diverge)
- Combined recommendation

### 6. Report Summary

Present:
- Codex recommendation and per-criterion scores
- Top 3 strengths
- Top 3 weaknesses
- Priority actions for improvement
- If merged: combined recommendation incorporating both reviews
- Path to saved review file(s)
