---
name: revision
description: Address review weaknesses by revising affected sections, re-running compliance, re-assembling the proposal, and re-reviewing — up to max revision cycles.
---


# Proposal Revision

You are revising a grant proposal to address weaknesses identified during review. This is an iterative process: revise sections, re-check compliance, re-assemble, and re-review until the proposal meets the quality threshold or max cycles are reached.

## Arguments

- `--proposal-dir <path>`: Proposal directory (required)
- `--max-cycles <N>`: Maximum revision cycles (default: 2)

Parse from the user's message.

## Procedure

### 0. Locate Plugin Root

```bash
if [ -f "tools/verify_setup.py" ]; then GRANTWRITER_ROOT="$(pwd)"
else GRANTWRITER_ROOT=$(find ".claude/plugins" "$HOME/.claude/plugins" -maxdepth 8 -name "verify_setup.py" -path "*grant-writer*" 2>/dev/null | head -1 | xargs dirname | xargs dirname); fi
export GRANTWRITER_ROOT; if [ -z "$GRANTWRITER_ROOT" ]; then echo "ERROR: Could not find grant-writer-skills plugin root."; fi; echo "Plugin root: $GRANTWRITER_ROOT"
```

### 1. Load Review Findings

Read the review files that drive revision:
- `<proposal_dir>/review/claude_review.json` — Claude's agency-calibrated review
- `<proposal_dir>/review/codex_review.md` — Codex panel review (if exists)
- `<proposal_dir>/review/merged_review.json` — Merged review with priority actions (if exists)
- `<proposal_dir>/review/evidence_assessment.md` — GRADE evidence assessment (if exists)
- `<proposal_dir>/resubmission/response.md` — Resubmission response plan (if exists)

If a merged review exists, use its `priority_actions` list. Otherwise, extract actionable weaknesses from the Claude review.

### 2. Extract Actionable Weaknesses

For each weakness or priority action:
- Identify the affected section file(s) in `sections/`
- Classify the required change: content addition, content revision, restructuring, shortening
- Note the specific improvement needed (from reviewer suggestions)

Sort by impact: address critical weaknesses first, then major, then minor.

### 3. Revision Loop (up to max-cycles)

For each cycle:

#### 3a. Revise Affected Sections

For each actionable weakness, revise the corresponding section file in `sections/`:
- Inject the reviewer feedback as context when revising
- Preserve the overall structure and word limits
- Make targeted changes — do not rewrite sections that received positive reviews
- If the resubmission response plan exists, follow its prescribed actions

#### 3b. Re-run Compliance

```bash
python3 "$GRANTWRITER_ROOT/tools/compliance_checker.py" check <proposal_dir>
```

If critical violations emerge from the revision (e.g., word count exceeded after adding content), fix them before proceeding.

#### 3c. Re-assemble Proposal

Re-assemble `final/proposal.md` from the revised sections:
1. Read section order from `agency.json`
2. Concatenate sections with proper Markdown headers
3. Prepend project summary
4. Insert figures with Markdown references
5. Append bibliography
6. Validate total word count

```bash
python3 "$GRANTWRITER_ROOT/tools/agency_requirements.py" sections <agency> <mechanism>
```

Save the re-assembled proposal to `<proposal_dir>/final/proposal.md`.

#### 3d. Re-review

Run the Claude review on the revised proposal to check for improvement:

Score the revised proposal using the same agency-specific criteria as the original review (see `/grant-writer:review` for the rubric). Compare scores against the previous cycle.

Save the updated review to `<proposal_dir>/review/claude_review.json` (overwriting the previous review).

#### 3e. Human Checkpoint

**Human checkpoint**: Present the PI with:
1. Changes made in this revision cycle (which sections, what changed)
2. Updated scores compared to previous cycle
3. Remaining weaknesses (if any)
4. Recommendation: accept revision / continue to next cycle / stop

If the PI accepts or max cycles are reached, exit the loop. Otherwise, continue to the next cycle.

### 4. Read Score Threshold

```bash
python3 -c "
import yaml
try:
    cfg = yaml.safe_load(open('<proposal_dir>/config.yaml'))
    threshold = cfg.get('review', {}).get('score_threshold', 3)
    print(f'threshold={threshold}')
except: print('threshold=3')
" 2>/dev/null
```

If the revised proposal scores above the threshold on all criteria, recommend finalizing. If still below threshold after max cycles, warn the PI about remaining weaknesses.

### 5. Update State

```bash
python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase revision --status complete
```

Report:
- Number of revision cycles completed
- Score improvement (before vs after, per criterion)
- Sections revised
- Final recommendation (ready for submission / needs further work)
- Path to revised `final/proposal.md`
