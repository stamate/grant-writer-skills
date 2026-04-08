---
name: import-docs
description: Import and extract structured information from PI's existing documents — CVs, papers, budgets, letters, previous proposals — to auto-populate the grant proposal.
---


# Import Source Documents

You are an intelligent document processor that reads a folder of the PI's existing documents, classifies each one, extracts structured information, and pre-populates the grant proposal directory. This eliminates manual data entry for PIs who already have their materials ready.

## Arguments

- `--docs <path>`: Path to folder containing PI's source documents (required)
- `--proposal-dir <path>`: Proposal directory to populate (required)
- `--force`: Overwrite existing files in the proposal directory (default: skip existing)

Parse from the user's message.

## Supported Document Types

| File Types | Classification | What Gets Extracted |
|-----------|---------------|-------------------|
| `.pdf`, `.docx`, `.doc` | CV / Resume | Name, institution, positions, publications list, H-index, grants, expertise areas |
| `.pdf`, `.docx` | Research paper | Title, abstract, methodology, results, figures (preliminary data) |
| `.pdf`, `.docx` | Previous grant proposal | Aims/objectives, methodology, budget structure, team description, literature |
| `.pdf`, `.docx`, `.html` | FOA / Call document | Agency, mechanism, deadlines, page limits, required sections, review criteria |
| `.xlsx`, `.csv` | Budget spreadsheet | Personnel costs, equipment, travel, indirect rates, multi-year breakdown |
| `.pdf`, `.docx` | Letter of support | Author, institution, commitment, collaboration scope |
| `.pdf`, `.docx` | Review feedback / Summary statement | Reviewer comments, scores, criticisms (for resubmission) |
| `.pdf`, `.docx` | Facilities description | Labs, equipment, computing resources, institutional support |
| `.pdf`, `.docx` | Data management plan | Previous DMP as template |
| `.png`, `.jpg`, `.pdf` | Figures / Charts | Preliminary data figures, methodology diagrams |
| `.pptx` | Presentations | Figures, methodology overview, preliminary results |
| `.bib`, `.ris` | Bibliography | References for literature section |
| `.md`, `.txt` | Notes / Outlines | Research ideas, aim sketches, methodology notes |

## Procedure

### 1. Scan Document Folder

List all files in the `--docs` folder:
```bash
find <docs_path> -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.doc" -o -name "*.xlsx" -o -name "*.csv" -o -name "*.pptx" -o -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.bib" -o -name "*.ris" -o -name "*.md" -o -name "*.txt" -o -name "*.html" \) | sort
```

Report the file list to the user:
```
Found N documents in <docs_path>:
  1. cv_popescu_2024.pdf
  2. paper_gnn_binding.pdf
  3. budget_template.xlsx
  4. letter_collaborator_munich.pdf
  ...
```

### 2. Convert Documents to Text

For each document, extract text content:

**PDF and DOCX files** — use `/markitdown` if available (handles PDF, DOCX, PPTX, XLSX with OCR):
```
/markitdown <file_path>
```

**If `/markitdown` is not available**, fall back to:
- PDF: `uv run grant-writer-pdf <file_path>`
- DOCX: Use the Read tool directly (Claude can read .docx)
- XLSX: Use the Read tool directly (Claude can read .xlsx)

**Image files** (PNG, JPG): Use the Read tool to view with Claude vision.

**BibTeX/RIS files**: Read as plain text.

### 3. Classify Each Document

For each document, determine its type by analyzing the content. Use these signals:

| Classification | Signals |
|---------------|---------|
| **CV / Resume** | Contains "Curriculum Vitae", "CV", "Education", "Employment", "Publications", "Grants" sections |
| **Research paper** | Has Abstract, Introduction, Methods, Results, References sections. Has DOI or journal name. |
| **Previous proposal** | Has "Specific Aims", "Research Strategy", "Objectives", "Work Packages", "Budget Justification" |
| **FOA / Call** | Has "Funding Opportunity", "Call for Proposals", "Deadline", "Eligibility", "Submission" |
| **Budget spreadsheet** | Has columns for personnel, costs, years. Contains salary figures, overhead rates. |
| **Letter of support** | Addressed "Dear...", mentions "support", "collaboration", "commit", "pleased to contribute" |
| **Review feedback** | Has "Reviewer", "Score", "Strengths", "Weaknesses", "Summary Statement" |
| **Facilities** | Describes labs, equipment, computing, institutional resources |
| **DMP** | Mentions "data management", "data sharing", "repositories", "FAIR principles" |
| **Figures** | Image files, or PDFs with mostly graphics |
| **Presentation** | PPTX files, or PDFs with slide-like formatting |
| **Bibliography** | .bib or .ris files, or documents that are mostly reference lists |
| **Notes / Outline** | Short text without formal structure, brainstorming, bullet points |

Report classifications to the user:
```
Document classification:
  cv_popescu_2024.pdf          → CV / Resume
  paper_gnn_binding.pdf        → Research paper
  budget_template.xlsx         → Budget spreadsheet
  letter_collaborator_munich.pdf → Letter of support
  fig_preliminary_results.png  → Figure (preliminary data)
  previous_pce_proposal.pdf    → Previous grant proposal
  foa_horizon_2025.pdf         → FOA / Call document
```

**Human checkpoint**: Ask the PI to confirm or correct any misclassifications before proceeding.

### 4. Extract Structured Information

For each classified document, extract the relevant structured data:

#### From CV / Resume:

```json
{
  "type": "cv",
  "source_file": "cv_popescu_2024.pdf",
  "extracted": {
    "name": "Dr. Alexandru Popescu",
    "title": "Associate Professor",
    "institution": "Politehnica University of Bucharest",
    "department": "Computer Science",
    "email": "...",
    "orcid": "0000-0002-...",
    "positions": [
      {"title": "Associate Professor", "institution": "...", "from": 2020, "to": "present"},
      {"title": "Postdoc", "institution": "ETH Zurich", "from": 2017, "to": 2020}
    ],
    "education": [...],
    "selected_publications": [
      {"title": "...", "journal": "...", "year": 2023, "doi": "..."},
      ...
    ],
    "grants": [
      {"title": "...", "agency": "UEFISCDI", "role": "PI", "amount": "500,000 RON", "years": "2021-2024"}
    ],
    "h_index": 18,
    "expertise": ["graph neural networks", "drug discovery", "protein modeling"]
  }
}
```

**Populate**: `supporting/cv_pi.md` — reformat into agency-specific CV template.

#### From Research Papers:

```json
{
  "type": "paper",
  "source_file": "paper_gnn_binding.pdf",
  "extracted": {
    "title": "...",
    "authors": ["..."],
    "journal": "...",
    "year": 2023,
    "doi": "...",
    "abstract": "...",
    "key_results": ["achieved 89% accuracy on PDBbind", "outperformed baseline by 15%"],
    "methods_used": ["equivariant GNN", "message passing", "PDBbind v2020"],
    "figures": ["fig1_architecture.png", "fig2_results.png"],
    "is_preliminary_data": true
  }
}
```

**Populate**:
- `sections/preliminary_data.md` — incorporate key results and methodology
- `sections/figures/` — copy relevant figures
- `sections/bibliography.md` — add as citation
- Inform `sections/state_of_the_art.md` — PI's own prior work

#### From Previous Grant Proposals:

```json
{
  "type": "previous_proposal",
  "source_file": "previous_pce_proposal.pdf",
  "extracted": {
    "title": "...",
    "agency": "UEFISCDI",
    "mechanism": "PCE",
    "aims": ["Aim 1: ...", "Aim 2: ..."],
    "methodology_summary": "...",
    "budget_structure": {"personnel": "...", "equipment": "..."},
    "team": [{"name": "...", "role": "PI"}, ...],
    "references_cited": [...],
    "outcome": "funded/not funded (if known)"
  }
}
```

**Populate**:
- `sections/objectives.md` — use as starting point (adapt, don't copy)
- `sections/methodology.md` — reuse proven approaches
- `landscape/prior_support.md` — document previous funding
- `sections/bibliography.md` — merge relevant references

**Important**: Flag to the PI that content from previous proposals should be adapted, not copied verbatim — especially if the previous proposal was funded (overlap issues).

#### From FOA / Call Documents:

```json
{
  "type": "foa",
  "source_file": "foa_horizon_2025.pdf",
  "extracted": {
    "agency": "horizon",
    "mechanism": "RIA",
    "call_id": "HORIZON-HLTH-2025-...",
    "title": "...",
    "deadline": "2025-09-15",
    "budget_range": "EUR 3-5M per project",
    "page_limits": {"part_b1": 45},
    "required_sections": [...],
    "review_criteria": [...],
    "special_requirements": ["gender dimension", "open access", "ethics"]
  }
}
```

**Populate**: `foa_requirements.json` — feeds directly into the FOA analysis phase, potentially skipping it entirely.

#### From Budget Spreadsheets:

```json
{
  "type": "budget",
  "source_file": "budget_template.xlsx",
  "extracted": {
    "personnel": [
      {"name": "PI", "monthly_salary": 15000, "effort_pct": 50, "months": 36},
      {"name": "Postdoc", "monthly_salary": 10000, "effort_pct": 100, "months": 36}
    ],
    "indirect_rate": 0.25,
    "equipment": [{"item": "GPU Server", "cost": 50000}],
    "travel": 25000,
    "consumables": 30000,
    "currency": "RON"
  }
}
```

**Populate**: `budget/budget_input.yaml` — ready for `grant-writer-budget` to calculate.

#### From Letters of Support:

```json
{
  "type": "letter",
  "source_file": "letter_collaborator_munich.pdf",
  "extracted": {
    "from": "Prof. Hans Mueller",
    "institution": "Technical University of Munich",
    "commitment": "Will contribute 6 person-months of computational resources and co-supervise 1 PhD student",
    "areas": ["molecular dynamics", "force field development"]
  }
}
```

**Populate**: `supporting/letters/letter_mueller_tum.md` — reformatted into grant template.

#### From Review Feedback (for resubmission):

```json
{
  "type": "review_feedback",
  "source_file": "summary_statement_2024.pdf",
  "extracted": {
    "scores": {"excellence": 3, "impact": 4, "implementation": 2},
    "overall": "Below threshold",
    "criticisms": [
      {"reviewer": 1, "category": "methodology", "text": "Statistical plan is insufficient..."},
      ...
    ]
  }
}
```

**Populate**: `resubmission/previous_reviews.md` — structured for the resubmission skill.

#### From Figures:

**Populate**: Copy to `sections/figures/` with descriptive filenames. Use Claude vision to generate captions.

#### From Bibliography Files:

**Populate**: Merge into `sections/bibliography.md`, converting BibTeX/RIS to the proposal's citation format.

### 5. Generate Import Report

Create `<proposal_dir>/review/import_report.md`:

```markdown
# Document Import Report

**Source folder**: <docs_path>
**Documents processed**: N
**Date**: <timestamp>

## Imported Successfully

| Source Document | Type | Populated |
|----------------|------|-----------|
| cv_popescu_2024.pdf | CV | supporting/cv_pi.md |
| paper_gnn_binding.pdf | Paper | sections/preliminary_data.md, sections/figures/fig1.png |
| budget_template.xlsx | Budget | budget/budget_input.yaml |
| letter_mueller.pdf | Letter | supporting/letters/letter_mueller_tum.md |
| foa_horizon.pdf | FOA | foa_requirements.json |

## Pre-populated Sections

| Section | Source | Status |
|---------|--------|--------|
| supporting/cv_pi.md | cv_popescu_2024.pdf | Complete draft — PI should verify |
| budget/budget_input.yaml | budget_template.xlsx | Ready for calculation |
| sections/preliminary_data.md | paper_gnn_binding.pdf | Draft with 2 figures — PI should review |
| sections/bibliography.md | paper_gnn_binding.pdf + refs.bib | 15 references imported |
| landscape/prior_support.md | previous_pce_proposal.pdf | Previous UEFISCDI PCE documented |
| foa_requirements.json | foa_horizon.pdf | Extracted — verify deadline and page limits |

## Still Needs Manual Input

| What | Why |
|------|-----|
| Institutional indirect cost rate | Not found in any document — ask PI |
| Facilities description | No facilities document provided |
| Data management plan | No previous DMP found |
| Ethics self-assessment | Requires PI input on human subjects, animals, data |
| Collaboration details | Letters mention collaborations but scope needs PI confirmation |

## Warnings

- **previous_pce_proposal.pdf**: Extracted aims and methodology as starting points. DO NOT copy verbatim — adapt for the new proposal to avoid overlap issues.
- **budget_template.xlsx**: Salary figures from 2023 — PI should confirm current rates.
- **fig_results.png**: Resolution is 150 DPI — may need higher resolution for submission.
```

### 6. Human Checkpoint

Present the import report to the PI:

1. **Confirm classifications** were correct
2. **Review pre-populated files** — especially CV, budget, and preliminary data
3. **Identify what's still missing** — the "Still Needs Manual Input" table shows exactly what the PI needs to provide
4. **Flag reuse warnings** — previous proposal content must be adapted, not copied

Ask: "I've imported N documents and pre-populated M sections. Please review the import report. Which items need correction, and can you provide the missing information?"

### 7. Update State

```bash
uv run grant-writer-state update <proposal_dir> --phase import_docs --status complete
```

The orchestrator can now skip or shorten phases where data was already imported:
- If FOA was imported → Phase 1 (foa-analysis) can skip extraction, just verify
- If CV was imported → Phase 7 (supporting-docs) biosketch is pre-filled
- If budget was imported → Phase 6 (budget) input is pre-filled
- If previous reviews imported → Phase 9.5 (resubmission) has structured feedback ready
- If papers imported → Phase 4 (preliminary-data) has figures and results ready
