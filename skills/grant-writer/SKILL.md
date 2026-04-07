---
name: grant-writer
description: Orchestrate the full grant proposal pipeline from FOA analysis through writing, budgeting, compliance, review, and revision.
---


# Grant Writer — Full Proposal Pipeline

You are an autonomous grant writing agent that orchestrates the complete grant proposal lifecycle — from funding opportunity analysis through competitive positioning, iterative section writing, budget preparation, compliance checking, and multi-model peer review. This skill coordinates all sub-skills through a phased pipeline with human checkpoints.

## Arguments

- `--foa <path>`: Path to FOA/RFP document (PDF, HTML, or URL)
- `--agency <name>`: Agency key (horizon, erc, msca, uefiscdi, pnrr)
- `--mechanism <name>`: Mechanism type (ria, ia, starting, consolidator, advanced, postdoc, doctoral, pce, te, pd)
- `--config <path>`: Path to config YAML (default: `templates/grant_config.yaml`)
- `--proposal-dir <path>`: Resume from existing proposal directory
- `--lang <en|ro>`: Language for Romanian templates (default: en)
- `--skip-review`: Skip review phase
- `--reviews <path>`: Path to previous evaluation summary report PDF (triggers resubmission phase)
- `--use-codex`: Force enable Codex integration (even if auto-detection fails)
- `--no-codex`: Force disable Codex integration (even if Codex is installed)
- `--no-scientific-skills`: Disable claude-scientific-skills integration (even if installed)

Parse from the user's message. If neither `--agency` nor `--foa` is provided, ask the user which agency and mechanism they are targeting.

## Pipeline Overview

```
 0.   Setup              →  environment, companions, agency config
 1.   FOA Analysis       →  parse funding opportunity, extract requirements
 1.5  Competitive        →  funded grants DB + literature + market analysis
      Landscape
 2.   Aims Generation    →  specific aims / objectives with iterative refinement loop
 3.   Literature         →  systematic search, gap identification, citations
 4.   Preliminary Data   →  assess PI's existing evidence
 5.   Proposal Writing   →  project summary first, then agency-specific sections
 5.5  Risk & Feasibility →  What-If-Oracle scenarios + risk matrix
 6.   Budget             →  person-months, equipment, travel, subcontracts
 7.   Supporting Docs    →  CVs, facilities, DMP, ethics, consortium agreement
 8.   Compliance         →  word counts, required sections, structure validation
 8.5  Assembly           →  compile all sections into final/proposal.md
 9.   Review             →  Claude review + Codex panel (agency-calibrated)
 9.5  Resubmission       →  parse previous reviews, plan revisions (if applicable)
10.   Revision           →  address weaknesses, re-assemble, re-review
```

## Procedure

### Phase 0: Setup

0. **Locate plugin root** (required before any tool invocations):
   ```bash
   if [ -f "tools/verify_setup.py" ]; then
       GRANTWRITER_ROOT="$(pwd)"
   else
       GRANTWRITER_ROOT=$(find ".claude/plugins" "$HOME/.claude/plugins" -maxdepth 8 -name "verify_setup.py" -path "*grant-writer*" 2>/dev/null | head -1 | xargs dirname | xargs dirname)
   fi
   export GRANTWRITER_ROOT; if [ -z "$GRANTWRITER_ROOT" ]; then echo "ERROR: Could not find grant-writer-skills plugin root."; fi; echo "Grant Writer root: $GRANTWRITER_ROOT"
   ```
   **All subsequent `tools/` references must use `"$GRANTWRITER_ROOT/tools/"`** instead of bare `tools/`. Similarly, `templates/` becomes `"$GRANTWRITER_ROOT/templates/"`.

1. **Verify environment**:
   ```bash
   uv run python3 "$GRANTWRITER_ROOT/tools/verify_setup.py"
   ```
   If this fails (missing dependencies, wrong Python version), **stop and guide the user** through fixing the issues.

2. **Load configuration**:
   ```bash
   uv run python3 "$GRANTWRITER_ROOT/tools/config.py" --config <config_path>
   ```
   If `--config` was not provided, use `"$GRANTWRITER_ROOT/templates/grant_config.yaml"`.

3. **Initialize proposal directory** (skip if `--proposal-dir` provided):
   ```bash
   uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" init --agency <agency> --mechanism <mechanism> --config <config_path>
   ```
   This creates the proposal directory structure with `state.json` and `config.yaml`.

4. **Detect claude-scientific-skills** (optional enhancement):

   Check if the plugin is installed using plugin.json identity:
   ```bash
   find "$HOME/.claude/plugins" ".claude/plugins" -maxdepth 5 \
     -name "plugin.json" -exec grep -l '"claude-scientific"' {} \; 2>/dev/null | head -1
   ```

   Also read the `scientific_skills.enabled` value from the loaded config.

   Determine `SCIENTIFIC_SKILLS_ENABLED`:
   - If `--no-scientific-skills` is set: `SCIENTIFIC_SKILLS_ENABLED=false`
   - If `scientific_skills.enabled` is `"false"` in config: `SCIENTIFIC_SKILLS_ENABLED=false`
   - If `scientific_skills.enabled` is `"auto"`: `SCIENTIFIC_SKILLS_ENABLED=true` only if plugin found
   - If `scientific_skills.enabled` is `"true"`: `SCIENTIFIC_SKILLS_ENABLED=true` (warn if missing)

   Print result:
   - If enabled: "Scientific skills detected — enhanced literature, writing, and review enabled"
   - If not found: "claude-scientific-skills not found — using standard pipeline (install for 78+ database access, DOI verification, and IMRAD writing)"

5. **Detect Codex** (optional enhancement):

   Check using plugin.json identity:
   ```bash
   which codex 2>/dev/null && echo "CLI_OK" || echo "CLI_MISSING"
   find "$HOME/.claude/plugins" ".claude/plugins" -maxdepth 5 \
     -name "plugin.json" -exec grep -l '"codex-plugin-cc\|codex"' {} \; 2>/dev/null | head -1
   codex login status 2>/dev/null && echo "AUTH_OK" || echo "AUTH_MISSING"
   ```

   Determine `CODEX_ENABLED`:
   - If `--no-codex` is set: `CODEX_ENABLED=false` regardless of anything else
   - If `codex.enabled` is `"false"` in config: `CODEX_ENABLED=false`
   - If `--use-codex` is set: `CODEX_ENABLED=true` (warn if CLI/plugin missing)
   - If `codex.enabled` is `"auto"`: `CODEX_ENABLED=true` only if ALL of: CLI found, plugin found, auth OK
   - If `codex.enabled` is `"true"`: `CODEX_ENABLED=true` (warn if CLI/plugin missing)

   Print result:
   - If enabled: "Codex detected — agency-calibrated panel review enabled"
   - If disabled: "Codex not enabled — using Claude-only review pipeline"

### Phase 1: FOA Analysis

Invoke the FOA analysis skill:
```
/grant-writer:foa-analysis --foa <foa_path> --agency <agency> --output <proposal_dir>
```

This parses the funding opportunity and produces `foa_requirements.json`.

Update state:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase foa_analysis --status complete
```

### Phase 1.5: Competitive Landscape

Invoke the landscape skill. Forward `--no-scientific-skills` if disabled:
```
/grant-writer:landscape --agency <agency> --query "<research topic>" --pi-name "<PI name>" --proposal-dir <proposal_dir>
```
Add `--no-scientific-skills` if `SCIENTIFIC_SKILLS_ENABLED` is false.

Update state:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase landscape --status complete
```

### Phase 2: Aims / Objectives

Invoke the aims skill:
```
/grant-writer:aims --proposal-dir <proposal_dir> --max-rounds 5
```

This runs an iterative refinement loop with human checkpoints until the PI approves.

Update state:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase aims --status complete
```

### Phase 3: Literature Review

Invoke the literature skill. Forward `--no-scientific-skills` if disabled:
```
/grant-writer:literature --proposal-dir <proposal_dir>
```
Add `--no-scientific-skills` if `SCIENTIFIC_SKILLS_ENABLED` is false.

Update state:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase literature --status complete
```

### Phase 4: Preliminary Data

Invoke the preliminary data skill:
```
/grant-writer:preliminary-data --proposal-dir <proposal_dir>
```

Update state:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase preliminary_data --status complete
```

### Phase 5: Proposal Writing

Invoke the proposal writing skill. Forward `--no-scientific-skills` if disabled:
```
/grant-writer:proposal --proposal-dir <proposal_dir>
```
Add `--no-scientific-skills` if `SCIENTIFIC_SKILLS_ENABLED` is false.

Update state:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase proposal_writing --status complete
```

### Phase 5.5: Risk & Feasibility

Invoke the risk analysis skill:
```
/grant-writer:risk-analysis --proposal-dir <proposal_dir>
```

Update state:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase risk_analysis --status complete
```

### Phase 6: Budget

Invoke the budget skill:
```
/grant-writer:budget --proposal-dir <proposal_dir>
```

Update state:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase budget --status complete
```

### Phase 7: Supporting Documents

Invoke the supporting documents skill:
```
/grant-writer:supporting-docs --proposal-dir <proposal_dir>
```

Update state:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase supporting_docs --status complete
```

### Phase 8: Compliance Check

Invoke the compliance skill:
```
/grant-writer:compliance --proposal-dir <proposal_dir>
```

Read the compliance report. If **critical violations** exist (missing required section, word count exceeded by >10%), **do NOT proceed** to assembly. List violations and fix them first by re-invoking the relevant writing/budget/supporting-docs skill. Re-run compliance until all critical violations pass.

Non-critical **warnings** (word count close to limit, missing optional sections) may proceed.

Update state:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase compliance --status complete
```

### Phase 8.5: Assembly

Assemble the final proposal document:

1. Read section order from `agency.json`:
   ```bash
   uv run python3 "$GRANTWRITER_ROOT/tools/agency_requirements.py" sections <agency> <mechanism>
   ```

2. Concatenate sections with proper Markdown headers (# for top-level, ## for sub-sections). Prepend project summary. Insert figures with proper Markdown references. Append bibliography.

3. Validate total word count:
   ```bash
   uv run python3 "$GRANTWRITER_ROOT/tools/compliance_checker.py" word-counts <proposal_dir>
   ```

4. Save assembled document to `final/proposal.md`.

Update state:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase assembly --status complete
```

### Phase 9: Review

**Skip if** `--skip-review` is set.

Invoke the review skill. Forward `--no-codex` and `--no-scientific-skills` flags as appropriate:
```
/grant-writer:review --proposal-dir <proposal_dir>
```
Add `--no-codex` if `CODEX_ENABLED` is false.
Add `--no-scientific-skills` if `SCIENTIFIC_SKILLS_ENABLED` is false.

Update state:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase review --status complete
```

### Phase 9.5: Resubmission Analysis

**Skip if** `--reviews` was not provided.

If the user provided previous reviewer feedback (evaluation summary report), invoke the resubmission skill:
```
/grant-writer:resubmission --proposal-dir <proposal_dir> --reviews <reviews_path>
```

This parses the previous review and generates a point-by-point response plan.

### Phase 10: Revision

Invoke the revision skill:
```
/grant-writer:revision --proposal-dir <proposal_dir> --max-cycles 2
```

This addresses review weaknesses, re-runs compliance, re-assembles, and re-reviews up to max cycles.

Update state:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase revision --status complete
```

## Resume Support

The pipeline supports resuming at any phase:
- Provide `--proposal-dir` to resume from an existing proposal
- Read `state.json` to find the first phase with `status != "complete"`
- Skip all complete phases, resume from the incomplete phase
- For partially-complete phases (e.g., `proposal_writing` with `sections_done: ["project_summary", "excellence"]`), resume writing from the next unfinished section

```bash
uv run python3 "$GRANTWRITER_ROOT/tools/state_manager.py" status <proposal_dir>
```

## Error Handling

- **FOA parsing fails** (unreadable PDF): Ask user to provide requirements manually via text input. Create `foa_requirements.json` from their description.
- **Funded grants API down** (OpenAIRE / UEFISCDI timeout): Skip landscape phase, warn user, continue with literature-only competitive context.
- **Aims loop stalls** (max rounds reached, PI not satisfied): Save progress to `sections/objectives.md`, allow manual editing, resume when ready.
- **Budget calculation error**: Present raw numbers from PI input, let PI verify and correct directly in `budget/budget_input.yaml`.
- **Codex review timeout**: Skip Codex review, Claude review is sufficient on its own. Log warning.
- **Compliance fails** (critical violations): List all violations, do NOT proceed to assembly/review until ALL critical violations are fixed. Non-critical warnings may proceed with a note.
- **Scientific-skills unavailable**: Skip enhanced features silently, use S2 + WebSearch for literature.

## Final Report

After all phases complete, print a summary:

```
═══════════════════════════════════════════════════════════
  Grant Writer Pipeline Complete
═══════════════════════════════════════════════════════════

  Agency:      <agency> (<mechanism>)
  Proposal:    <proposal_dir>/final/proposal.md
  Language:    <en|ro>

  Sections:
    project_summary.md   ✓  (<N> words / <limit>)
    excellence.md        ✓  (<N> words / <limit>)
    impact.md            ✓  (<N> words / <limit>)
    implementation.md    ✓  (<N> words / <limit>)

  Total Words:   <N> / <limit>
  Figures:       <N> in sections/figures/
  Citations:     <N> references in bibliography.md

  Budget:        <total> <currency> over <N> years
  Compliance:    ✓ All checks passed (or <N> warnings)

  Review:
    Claude Score:   <score>/5 — <recommendation>
    Codex Panel:    <score>/5 — <recommendation> (if available)
    Evidence:       <quality> (GRADE framework) (if scientific-skills)

  Revisions:     <N> cycle(s) (score: <initial> → <final>)

═══════════════════════════════════════════════════════════

  To convert for submission:
    Word:  /docx final/proposal.md
    PDF:   /pdf final/proposal.md
═══════════════════════════════════════════════════════════
```

## Notes

- The full pipeline is collaborative — expect multiple human checkpoints where the PI must review and approve.
- Token usage scales with the number of sections, revision cycles, and companion skill invocations.
- For a quick test, use `--skip-review` to skip the review and revision phases.
- Romanian templates support `--lang ro` for Romanian section headers with English scientific content.
