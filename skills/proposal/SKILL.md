---
name: proposal
description: Write agency-specific proposal sections with templates, citation management, figure generation, and human review per section.
---


# Proposal Section Writing

You are writing the core sections of a grant proposal according to agency-specific templates, word limits, and formatting requirements. Each section is written with full context from prior pipeline phases and reviewed by the PI before finalization.

## Arguments

- `--proposal-dir <path>`: Proposal directory (required)
- `--section <name>`: Write a specific section only (optional — writes all sections if omitted)
- `--no-scientific-skills`: Skip enhanced writing even if plugin is available

Parse from the user's message.

## Procedure

### 0. Locate Plugin Root

```bash
```

### 1. Load Context

Read from the proposal directory:
- `config.yaml` — agency, mechanism, language, proposal metadata (title, PI, acronym)
- `foa_requirements.json` — section requirements and word limits
- `sections/objectives.md` — research objectives
- `landscape/competitive_brief.md` — competitive positioning
- `landscape/literature.md` — literature context and gap analysis
- `sections/preliminary_data.md` — PI's evidence
- `sections/bibliography.md` — citation list

Load agency template and section order:
```bash
uv run grant-writer-agency sections <agency> <mechanism>
```

Read the citation style from `agency.json`:
- `"numbered"`: Use `[1]`, `[2]` inline citations
- `"author_year"`: Use `(Author et al., Year)` inline citations

### 2. Write Project Summary FIRST

The project summary (abstract) is always written first as a standalone document with its own word limits. It provides the framing for all subsequent sections.

Write `sections/project_summary.md`:
- Concise statement of the problem and its significance
- Proposed approach and objectives (high-level)
- Expected outcomes and impact
- Respect the word limit from `agency.json` (typically 250-500 words)

**Human checkpoint**: Present the project summary for PI review before continuing.

### 3. Write Remaining Sections

For each section in the agency's section order, load the corresponding template and write the content.

**Section order varies by agency:**

**Horizon Europe RIA**:
1. `project_summary.md` (written in step 2)
2. `excellence.md` — objectives, methodology, ambition, state of the art
3. `impact.md` — expected outcomes, dissemination, exploitation, communication
4. `implementation.md` — work plan, work packages, milestones, deliverables, consortium management, risk management

**UEFISCDI PCE**:
1. `project_summary.md` (written in step 2)
2. `state_of_the_art.md` — current knowledge, gaps, positioning
3. `objectives.md` — detailed research objectives (expanded from aims)
4. `methodology.md` — detailed research methodology per objective
5. `work_plan.md` — timeline, tasks, milestones, Gantt chart
6. `expected_results.md` — anticipated outcomes, publications, impact

**ERC Starting/Consolidator/Advanced**:
1. `project_summary.md` (written in step 2)
2. `extended_synopsis.md` — 5-page scientific proposal summary
3. `scientific_proposal.md` — 15-page detailed research plan
4. `curriculum_vitae.md` — PI's academic CV

For each section:

#### a. Load Template

Load the section template. Use the agency info to find templates:
```bash
uv run grant-writer-agency info <agency_dir>
```
The tool prints the agency's template directory path. Read the section template `.md` from that directory.

#### b. Write Content

Write the section content respecting:
- Word limit from `agency.json`
- Template structure and required sub-sections
- Citation style from `agency.json`
- Language setting (`--lang ro` for Romanian headers with English scientific content)

#### c. Reference Figures

Reference figures using Markdown syntax with captions:
```
![Description of the figure](figures/filename.png)
*Figure N: Caption text explaining the figure content.*
```

Ensure every referenced figure exists in `sections/figures/`.

#### d. Enhanced Writing (Optional — claude-scientific-skills)

**Skip if** `--no-scientific-skills` is set or plugin not available.

Check plugin availability:
```bash
find "$HOME/.claude/plugins" ".claude/plugins" -maxdepth 5 \
  -name "plugin.json" -exec grep -l '"claude-scientific"' {} \; 2>/dev/null | head -1
```
If not found, skip silently.

When available:
- `/scientific-writing` — apply IMRAD structure and academic prose quality (two-stage: outline then full paragraphs)
- `/citation-management` — verify DOIs and metadata accuracy via CrossRef
- `/scientific-schematics` — generate methodology flowcharts, Gantt charts, work package diagrams. Save generated figures to `sections/figures/`

#### e. Human Checkpoint

**Human checkpoint**: Present each major section to the PI for review. Ask:
- Does the content accurately reflect your research plan?
- Are there missing elements or incorrect claims?
- Is the emphasis correct (which aspects should be highlighted vs. minimized)?

Incorporate feedback before saving.

#### f. Save Section

Save to `sections/<section_name>.md`.

Update state with section completion:
```bash
uv run grant-writer-state update <proposal_dir> --phase proposal_writing --sections-done <section_name>
```

### 4. Verify Word Counts

After all sections are written, verify word counts:
```bash
uv run grant-writer-compliance word-counts <proposal_dir>
```

If any section exceeds its limit, revise to fit within the constraint. Prioritize cutting redundancy over removing content.

## Writing Guidelines

- Write in full paragraphs, never bullet-point lists (unless the template explicitly requires them).
- Use active voice and concrete language. Avoid hedging ("may", "might", "could possibly").
- Every claim should be supported by a citation or preliminary data reference.
- Connect each section back to the objectives — reviewers look for internal coherence.
- For EU proposals: explicitly address all evaluation criteria (Excellence, Impact, Implementation) even when writing specific sections.
- For Romanian proposals: emphasize international collaboration and ISI-indexed publication targets.

## Notes

- If `--section` is provided, write only that section (useful for revisions or manual re-runs).
- The project summary should be self-contained — a reviewer who reads only the abstract should understand the full proposal.
- Section templates provide structure guidance but should not be copied verbatim.
