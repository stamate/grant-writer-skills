---
name: aims
description: Iteratively generate and refine research objectives or specific aims with scoring, Codex review, and human approval.
---


# Aims / Objectives Refinement

You are generating and iteratively refining the core research objectives (or specific aims) for a grant proposal. This is the intellectual heart of the proposal — objectives must be ambitious yet feasible, clearly articulated, and aligned with the agency's review criteria.

## Arguments

- `--proposal-dir <path>`: Proposal directory (required)
- `--max-rounds <N>`: Max refinement rounds (default: 5)
- `--codex-rounds <N>`: Max Codex review rounds during aims (default: 2)

Parse from the user's message.

## Procedure

### 0. Locate Plugin Root

```bash
if [ -f "tools/verify_setup.py" ]; then GRANTWRITER_ROOT="$(pwd)"
else GRANTWRITER_ROOT=$(find ".claude/plugins" "$HOME/.claude/plugins" -maxdepth 8 -name "verify_setup.py" -path "*grant-writer*" 2>/dev/null | head -1 | xargs dirname | xargs dirname); fi
export GRANTWRITER_ROOT; if [ -z "$GRANTWRITER_ROOT" ]; then echo "ERROR: Could not find grant-writer-skills plugin root."; fi; echo "Plugin root: $GRANTWRITER_ROOT"
```

### 1. Load Context

Read the following inputs from the proposal directory:
- `foa_requirements.json` — funding opportunity requirements and review criteria
- `landscape/competitive_brief.md` — what competitors are doing, gaps, opportunities
- `landscape/literature.md` — if available from a prior literature phase
- `config.yaml` — agency, mechanism, scoring thresholds

Load agency review criteria:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/agency_requirements.py" review-criteria <agency> <mechanism>
```

### 2. Generate Initial Objectives

Draft 3-5 research objectives based on:
- The research question and PI's expertise
- FOA requirements and scope
- Competitive landscape gaps (what differentiates this proposal)
- Preliminary data (if available)

For each objective, include:
- Clear statement of the aim
- Rationale (why this objective matters)
- Approach (how it will be achieved)
- Expected outcome and deliverable
- Success criteria (measurable)

### 3. Score Against Agency Criteria

Evaluate the objectives against the agency's review criteria:

**For EU agencies** (Horizon Europe, ERC, MSCA):
- **Excellence**: Scientific quality, novelty, ambition, methodology soundness
- **Impact**: Expected outcomes, dissemination, exploitation potential
- **Implementation**: Feasibility, work plan realism, resource allocation

**For Romanian agencies** (UEFISCDI):
- **Scientific quality**: Novelty, contribution to the field
- **Methodology**: Appropriateness, rigor
- **Feasibility**: Timeline, resources, PI capability
- **Expected impact**: Publications, training, societal impact

Score each criterion on a 1-5 scale. Identify the weakest criterion.

### 4. Iterative Refinement Loop

For each round (up to `--max-rounds`):

1. **Identify weakness**: Which criterion scored lowest? Why?
2. **Targeted revision**: Revise objectives to strengthen the weakest dimension without degrading others
3. **Re-score**: Re-evaluate all criteria after revision
4. **Optional Codex review** (up to `--codex-rounds` times): If Codex is available, invoke:
   ```
   /codex:grant-review sections/objectives.md --agency <agency>
   ```
   Incorporate Codex feedback into the next revision.
5. **Human checkpoint**: Present the current objectives to the PI with scores per criterion. Ask:
   - Are the objectives aligned with your research vision?
   - Are there objectives missing or ones that should be removed?
   - Is the scope realistic for the proposed timeline and budget?
6. If PI approves, **exit loop**. If PI requests changes, incorporate and continue.

### 5. Save Output

Save the refined objectives to `sections/objectives.md`.

Also update state with the number of rounds used:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase aims --status complete
```

## EU-Specific Notes

- **Horizon Europe**: Objectives map to **Work Packages**. Each objective should correspond to a WP with clear tasks, deliverables, and milestones. Structure the objectives document to make this mapping explicit.
- **ERC**: Objectives are the **scientific aims of the PI's research program**. They should reflect the PI's personal intellectual vision and long-term research trajectory, not a consortium's shared goals.
- **MSCA**: Objectives should emphasize the **training and career development** dimension alongside scientific goals. Two-way knowledge transfer between host and researcher.

## Notes

- If the refinement loop stalls (max rounds reached, PI still not satisfied), save the current progress to `sections/objectives.md` and allow the PI to edit the file manually. The pipeline can resume after manual edits.
- Objectives are the foundation for all subsequent writing — the proposal, risk analysis, budget, and work plan all reference them.
