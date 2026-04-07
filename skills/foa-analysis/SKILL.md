---
name: foa-analysis
description: Parse a funding opportunity announcement and extract structured requirements, eligibility criteria, and deadlines.
---


# FOA Analysis

You are parsing a funding opportunity announcement (FOA/RFP/call text) to extract structured requirements that guide the entire proposal.

## Arguments

- `--foa <path>`: Path to FOA document (PDF, HTML, or URL) (required)
- `--agency <name>`: Agency hint to aid parsing (horizon, erc, msca, uefiscdi, pnrr)
- `--output <path>`: Output directory for results (default: current proposal directory)

Parse from the user's message.

## Procedure

### 0. Locate Plugin Root

```bash
if [ -f "tools/verify_setup.py" ]; then GRANTWRITER_ROOT="$(pwd)"
else GRANTWRITER_ROOT=$(find ".claude/plugins" "$HOME/.claude/plugins" -maxdepth 8 -name "verify_setup.py" -path "*grant-writer*" 2>/dev/null | head -1 | xargs dirname | xargs dirname); fi
export GRANTWRITER_ROOT; if [ -z "$GRANTWRITER_ROOT" ]; then echo "ERROR: Could not find grant-writer-skills plugin root."; fi; echo "Plugin root: $GRANTWRITER_ROOT"
```

### 1. Extract FOA Text

If the FOA is a PDF:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/pdf_reader.py" <foa_path>
```

If the FOA is a URL, use the WebFetch tool to retrieve the page content.

If extraction fails (unreadable PDF, broken URL), ask the user to paste the key requirements as text.

### 2. Identify Requirements

Parse the FOA text and extract:

- **Eligibility criteria**: Who can apply (institution type, country restrictions, career stage, PI requirements)
- **Page or word limits**: Per section and total
- **Required sections**: Ordered list of mandatory proposal sections
- **Review criteria**: Scoring dimensions and weights (e.g., Excellence 50%, Impact 30%, Implementation 20% for Horizon Europe)
- **Deadlines**: Submission deadline, pre-registration deadline (if any)
- **Budget caps**: Maximum funding amount, duration, co-funding requirements
- **Special requirements**: Ethics requirements, open access policy, gender dimension (EU), data management plan, consortium size requirements

### 3. Match Against Agency Template

Load the known agency template for validation:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/agency_requirements.py" info <agency> <mechanism>
```

Compare extracted requirements against the template. Flag any discrepancies — the FOA may have call-specific additions or modifications to the standard template.

### 4. Output Structured Requirements

Save the extracted requirements as `foa_requirements.json` in the output directory:

```json
{
  "agency": "<agency>",
  "mechanism": "<mechanism>",
  "call_id": "<call identifier if found>",
  "deadline": "<submission deadline>",
  "eligibility": ["<criterion 1>", "<criterion 2>"],
  "sections": [
    {"name": "<section_name>", "words": <limit_or_null>, "required": true}
  ],
  "review_criteria": [
    {"name": "<criterion>", "weight": <percentage>}
  ],
  "budget": {
    "max_total": <amount_or_null>,
    "max_years": <N>,
    "currency": "<EUR|RON>"
  },
  "special_requirements": ["<requirement 1>", "<requirement 2>"],
  "notes": "<any call-specific deviations from standard template>"
}
```

### 5. Human Checkpoint

**Human checkpoint**: Present the extracted requirements to the PI for confirmation. Specifically ask:

1. Are the eligibility criteria correct? Is the PI eligible?
2. Are there any additional requirements not captured from the FOA?
3. Does the budget cap and duration match their expectations?
4. Are the deadlines correct?

Incorporate any corrections before proceeding.

## Notes

- For EU agencies, pay special attention to: ethics issues table, gender dimension requirements, open science / open access mandates, and consortium composition rules.
- For Romanian agencies (UEFISCDI), check for language requirements — some calls require the proposal in Romanian.
- If the FOA is in a language other than English, extract requirements and present them in English for processing, noting the original language.
