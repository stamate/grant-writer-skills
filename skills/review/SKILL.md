---
name: review
description: Perform a structured review of the grant proposal — Claude agency-calibrated scoring, optional GRADE evidence assessment, and optional Codex panel review with merged findings.
---


# Proposal Review

You are an experienced grant reviewer performing a rigorous evaluation of a grant proposal against agency-specific review criteria. This is the primary quality gate before submission.

## Arguments

- `--proposal-dir <path>`: Proposal directory (required)
- `--no-codex`: Skip Codex panel review even if Codex is available
- `--no-scientific-skills`: Skip evidence assessment even if plugin is available

Parse from the user's message.

## Procedure

### 0. Locate Plugin Root

```bash
if [ -f "tools/verify_setup.py" ]; then GRANTWRITER_ROOT="$(pwd)"
else GRANTWRITER_ROOT=$(find ".claude/plugins" "$HOME/.claude/plugins" -maxdepth 8 -name "verify_setup.py" -path "*grant-writer*" 2>/dev/null | head -1 | xargs dirname | xargs dirname); fi
export GRANTWRITER_ROOT; if [ -z "$GRANTWRITER_ROOT" ]; then echo "ERROR: Could not find grant-writer-skills plugin root."; fi; echo "Plugin root: $GRANTWRITER_ROOT"
```

### 1. Load Review Context

Read the assembled proposal and agency review criteria:

```bash
uv run python3 "$GRANTWRITER_ROOT/tools/agency_requirements.py" review-criteria <agency> <mechanism>
```

Read the full proposal at `<proposal_dir>/final/proposal.md`. Also read `<proposal_dir>/config.yaml` for agency, mechanism, and companion settings.

### 2. Claude Review Against Agency Criteria

Adopt the following reviewer persona:

> You are a panel reviewer evaluating a grant proposal submitted to this agency. Apply the official scoring criteria rigorously. Be critical — if a section is weak or you are unsure of feasibility, score it accordingly.

Score using the **agency-specific rubric**:

#### EU — Horizon Europe / ERC / MSCA (scored 0-5 per criterion)

| Score | Meaning |
|-------|---------|
| 0 | Proposal fails to address the criterion or cannot be assessed |
| 1 | Poor — significant weaknesses |
| 2 | Fair — some strengths but important weaknesses |
| 3 | Good — well addressed with minor weaknesses |
| 4 | Very good — addressed very well with negligible shortcomings |
| 5 | Excellent — successfully addresses all aspects, any shortcomings are minor |

**Horizon Europe (RIA/IA)** criteria: Excellence (objectives, methodology, ambition), Impact (expected outcomes, dissemination, exploitation), Implementation (work plan, consortium, management).

**ERC** criteria: Groundbreaking nature, Methodology, PI track record.

**MSCA** criteria: Excellence (50%), Impact (30%), Implementation (20%).

#### Romania — UEFISCDI (scored 1-5 per criterion)

Criteria: Scientific quality, Methodology, Feasibility, PI capability, Expected impact.

#### Romania — PNRR (threshold-based)

Criteria: Relevance to PNRR objectives, Technical quality, Sustainability, Budget efficiency.

For each criterion, provide:
- Numeric score
- Key strengths supporting the score
- Key weaknesses reducing the score
- Specific suggestions for improvement

Also provide:
- Overall assessment (fund / fund with revisions / do not fund)
- Top 3 strengths across all criteria
- Top 3 weaknesses across all criteria
- Priority actions for improvement

Save the review to `<proposal_dir>/review/claude_review.json`.

### 3. Scientific Evidence Assessment (Optional Enhancement)

**Skip this step if** `--no-scientific-skills` is set.

Check if claude-scientific-skills is installed:
```bash
find "$HOME/.claude/plugins" ".claude/plugins" -maxdepth 5 -name "plugin.json" -exec grep -l '"claude-scientific"' {} \; 2>/dev/null | head -1
```
If no result, skip this step silently.

Check config (if available):
```bash
python3 -c "
import yaml
try:
    cfg = yaml.safe_load(open('<proposal_dir>/config.yaml'))
    enabled = str(cfg.get('scientific_skills', {}).get('enabled', 'auto')).lower()
    review = cfg.get('scientific_skills', {}).get('enhanced_review', True)
    print(f'enabled={enabled} enhanced_review={review}')
except: print('enabled=auto enhanced_review=True')
" 2>/dev/null
```
If `enabled` is `false` or `enhanced_review` is `false`, skip this step.

When enabled, invoke the GRADE evidence assessment:

```
/scientific-critical-thinking
```

Provide the proposal text and request evaluation of:
- **Methodology critique**: Is the research design appropriate? Are controls adequate?
- **Evidence quality**: Rate using GRADE framework (High / Moderate / Low / Very Low)
- **Logical rigor**: Check for unsupported causal claims, circular reasoning, overgeneralization
- **Bias assessment**: Selection, measurement, and analysis biases

Save to `<proposal_dir>/review/evidence_assessment.md`.

### 4. Codex Panel Review (Optional Enhancement)

**Skip this step if** `--no-codex` is set.

Check Codex availability (CLI + plugin + auth):
```bash
which codex 2>/dev/null && echo "CLI_OK" || echo "CLI_MISSING"
find "$HOME/.claude/plugins" ".claude/plugins" -maxdepth 5 -name "plugin.json" -exec grep -l '"codex"' {} \; 2>/dev/null | head -1
codex login status 2>/dev/null && echo "AUTH_OK" || echo "AUTH_MISSING"
```
All three must succeed. If any fails, skip this step silently.

Check config:
```bash
python3 -c "
import yaml
try:
    cfg = yaml.safe_load(open('<proposal_dir>/config.yaml'))
    enabled = str(cfg.get('codex', {}).get('enabled', 'auto')).lower()
    panel = cfg.get('codex', {}).get('panel_review', True)
    print(f'enabled={enabled} panel={panel}')
except: print('enabled=auto panel=true')
" 2>/dev/null
```
If `enabled` is `false`, skip this step.

Invoke the Codex grant review:

```
/codex:grant-review final/proposal.md --docs sections/ --panel --agency <agency> --wait
```

If `panel` is `false`, omit `--panel`:
```
/codex:grant-review final/proposal.md --docs sections/ --agency <agency> --wait
```

Save the Codex output to `<proposal_dir>/review/codex_review.md`.

### 5. Merge Reviews

If both Claude and Codex reviews exist, generate a merged review at `<proposal_dir>/review/merged_review.json`:

```json
{
  "claude_review": {
    "scores": {},
    "overall": "<fund / fund with revisions / do not fund>",
    "key_strengths": ["..."],
    "key_weaknesses": ["..."]
  },
  "codex_review": {
    "recommendation": "<accept/minor-revision/major-revision/reject>",
    "aggregated_scores": {},
    "key_strengths": ["..."],
    "key_weaknesses": ["..."]
  },
  "consensus": ["Points both reviews agree on..."],
  "disagreements": ["Points where reviews diverge..."],
  "combined_recommendation": "<overall assessment considering both reviews>",
  "priority_actions": ["Ranked list of revisions to make..."]
}
```

If only the Claude review exists, the merged review contains only the Claude section with its priority actions.

### 6. Present Results

**Human checkpoint**: Present the PI with a clear summary:

1. **Scores**: Table of criterion scores (Claude + Codex if available)
2. **Strengths**: Top 3-5 strengths across both reviews
3. **Weaknesses**: Top 3-5 weaknesses, ranked by severity
4. **Evidence quality**: GRADE assessment (if scientific-skills was used)
5. **Priority actions**: Ordered list of revisions that would most improve the score
6. **Recommendation**: Combined fund/revise/reject assessment

Ask the PI: "Would you like to proceed to revision to address the identified weaknesses?"

### 7. Update State

```bash
uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase review --status complete
```

Report:
- Claude review scores (per criterion)
- Codex review scores (if available)
- Combined recommendation
- Number of priority actions identified
- Paths to all review files
