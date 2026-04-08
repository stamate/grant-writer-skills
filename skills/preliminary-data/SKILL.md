---
name: preliminary-data
description: Assess and organize the PI's existing preliminary data, figures, and pilot results to support proposal objectives.
---


# Preliminary Data Assessment

You are helping the PI organize and present their existing preliminary data to strengthen the grant proposal. Preliminary data demonstrates feasibility and the PI's capability to execute the proposed work.

## Arguments

- `--proposal-dir <path>`: Proposal directory (required)
- `--data-dir <path>`: Directory with PI's existing figures/data (optional)

Parse from the user's message.

## Procedure

### 0. Locate Plugin Root

```bash
```

### 1. Collect Information from PI

**Human checkpoint**: Ask the PI what preliminary data exists. Specifically ask about:

- **Published results**: Papers with data relevant to the proposed objectives
- **Unpublished results**: Pilot experiments, preliminary analyses
- **Figures**: Charts, graphs, images that can be included in the proposal
- **Datasets**: Existing datasets that will be reused or extended
- **Prototypes or tools**: Software, instruments, or methods already developed

### 2. Review Figures

If the PI provides figures (via `--data-dir` or by indicating file paths):

1. Read each figure file to review it visually
2. Assess each figure for:
   - **Clarity**: Is the figure readable and well-labeled?
   - **Relevance**: Does it directly support a specific objective?
   - **Quality**: Is it publication-quality for inclusion in the proposal?
3. Copy suitable figures to `sections/figures/`:
   ```bash
   cp <data_dir>/<figure_file> <proposal_dir>/sections/figures/
   ```

### 3. Evaluate Coverage

For each research objective (from `sections/objectives.md`), assess:

- Does preliminary data exist that supports this objective?
- How strong is the evidence? (Published > unpublished pilot > conceptual)
- Are there gaps where no preliminary data exists?

Create a coverage matrix:

| Objective | Preliminary Data | Strength | Gap |
|-----------|-----------------|----------|-----|
| Obj 1     | Fig 1, Paper X  | Strong   | —   |
| Obj 2     | Pilot data Y    | Moderate | Need validation dataset |
| Obj 3     | None            | Weak     | Critical gap — address in methodology |

### 4. Draft Preliminary Data Narrative

Write `sections/preliminary_data.md` that:

- Presents each piece of evidence linked to the objective it supports
- References figures using Markdown: `![Description](figures/filename.png)`
- Frames gaps honestly — explain how the proposed work will fill them
- Highlights the PI's unique position to execute this research

### 5. Report Gaps

If significant gaps exist (objectives with no supporting data), flag them:
- Suggest what the PI could generate before submission (if time permits)
- Recommend how the methodology section should address the gap (e.g., risk mitigation, pilot study as first work package)

## Notes

- Preliminary data is critical for credibility, especially for UEFISCDI where reviewers weight it heavily.
- For ERC proposals, preliminary data demonstrates the PI's track record and vision — it should tell a story of progression.
- If no figures are provided, the skill still produces a narrative from the PI's description of their existing work.
