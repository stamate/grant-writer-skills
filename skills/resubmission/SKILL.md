---
name: resubmission
description: Parse previous evaluation report, extract criticisms as structured items, and generate a point-by-point response plan for grant resubmission.
---


# Resubmission Handler

You are preparing a grant resubmission by parsing the previous evaluation report, extracting each criticism, and generating a structured response plan.

## Arguments

- `--proposal-dir <path>`: Proposal directory (required)
- `--reviews <path>`: Path to previous evaluation summary report / reviewer feedback (PDF)

Parse from the user's message.

## Procedure

### 0. Locate Plugin Root

```bash
```

### 1. Extract Reviewer Comments

Extract text from the evaluation report PDF:

```bash
uv run grant-writer-pdf <reviews_path>
```

Read the extracted text carefully. Identify each individual criticism, comment, and suggestion from the reviewers.

### 2. Parse Criticisms

Structure each criticism as an item with:
- **Reviewer**: Which reviewer or panel member (Reviewer 1, Reviewer 2, Panel, etc.)
- **Category**: Scientific quality, methodology, feasibility, impact, budget, writing quality, other
- **Severity**: Critical (must address), Major (should address), Minor (nice to address)
- **Quote**: The exact text or close paraphrase of the criticism
- **Section affected**: Which proposal section needs revision

Save the parsed criticisms to `<proposal_dir>/resubmission/previous_reviews.md` as a structured Markdown document with a table or list of all items, grouped by severity.

### 3. Map Criticisms to Sections

For each criticism, identify the specific section(s) in the proposal that need modification:
- Map to files in `sections/` (e.g., `sections/excellence.md`, `sections/methodology.md`)
- Note if a criticism requires adding new content vs revising existing content
- Flag criticisms that affect multiple sections

### 4. Generate Response Plan

For each criticism, draft a response that includes:
- **Acknowledgment**: Restate the reviewer's concern
- **Action taken**: Specific changes made or planned
- **Location**: Where in the revised proposal the change appears

#### Agency-specific response format

**For Horizon Europe resubmission**: Structure the response per ESR (Evaluation Summary Report) format. Group responses by evaluation criterion (Excellence, Impact, Implementation). For each criterion, list reviewer comments and responses sequentially.

**For UEFISCDI resubmission**: Structure the response per agency resubmission requirements. Present as a point-by-point table: reviewer comment, response, section modified.

**For ERC resubmission**: Address the panel's key concerns first, then individual reviewer comments. Focus on demonstrating how the research plan has been strengthened.

Save the response plan to `<proposal_dir>/resubmission/response.md`.

### 5. Prioritize Revisions

**Human checkpoint**: Present the PI with:
1. Summary of all criticisms by severity (N critical, N major, N minor)
2. Proposed response plan with specific actions
3. Estimated effort for each revision (word count changes, new content needed)
4. Recommended priority order for addressing criticisms

Ask the PI to:
- Confirm which criticisms to address (all critical and major by default)
- Provide additional context for responses where needed
- Approve the response strategy before revision begins

### 6. Update State

```bash
uv run grant-writer-state update <proposal_dir> --phase resubmission --status complete
```

Report:
- Number of criticisms extracted (N critical, N major, N minor)
- Sections requiring revision
- Response plan ready at `resubmission/response.md`
- Next step: run `/grant-writer:revision` to apply the changes
