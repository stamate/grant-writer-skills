---
name: compliance
description: Validate proposal structure against agency requirements — word counts, required sections, bibliography, budget caps, and EU-specific checks.
---


# Compliance Validation

You are validating a grant proposal against agency-specific requirements before final assembly.

## Arguments

- `--proposal-dir <path>`: Proposal directory (required)

Parse from the user's message.

## Procedure

### 0. Locate Plugin Root

```bash
```

### 1. Load Agency Requirements

```bash
uv run grant-writer-agency sections <agency> <mechanism>
```

This returns the required sections, word limits, and formatting rules from `agency.json`.

### 2. Run Compliance Checker

```bash
uv run grant-writer-compliance check <proposal_dir>
```

The checker validates:
- **Word count per section**: Each `.md` file in `sections/` checked against limits from `agency.json`. Words are counted excluding Markdown syntax.
- **Required sections present**: All sections marked `required: true` in `agency.json` must exist.
- **Bibliography completeness**: Every in-text citation (`[N]` or `(Author, Year)`) has a matching entry in `sections/bibliography.md`.
- **Figure references valid**: Every `![...](<path>)` Markdown image reference points to an existing file in `sections/figures/`.
- **Budget within caps**: Total, per-year, and indirect rate checked against agency limits.
- **Personnel completeness**: All named team members have CVs in `supporting/`.
- **EU-specific checks** (Horizon Europe, ERC, MSCA only): Ethics self-assessment present, DMP present, gender dimension addressed in relevant sections.

### 3. Classify Violations

Parse the checker output and classify each issue:

**Critical violations** (block assembly):
- Missing required section
- Word count exceeded by more than 10%
- Missing bibliography for cited references
- Budget exceeds agency cap

**Warnings** (allow proceeding with caution):
- Word count within 5-10% of limit
- Missing optional sections
- Minor formatting inconsistencies
- Missing figures referenced in text

For each violation, provide a specific fix suggestion (e.g., "Section `excellence.md` is 2,347 words — limit is 2,000. Cut 347 words, focusing on the methodology sub-section which is the most verbose.").

### 4. Run Supplementary Checks

Check word counts in detail:
```bash
uv run grant-writer-compliance word-counts <proposal_dir>
```

Check budget specifically:
```bash
uv run grant-writer-compliance budget-check <proposal_dir>
```

### 5. Save Compliance Report

Save the full report to `<proposal_dir>/review/compliance_report.md` with:
- Summary: total checks run, passed, failed (critical), warnings
- Per-check detail: check name, status, actual vs expected, fix suggestion
- Word count table: section name, current count, limit, status
- Budget summary: total vs cap, indirect rate vs cap

### 6. Gate Decision

If **any critical violations** exist:
- Print all critical violations with fix suggestions
- Do NOT allow assembly to proceed
- State: "Critical compliance violations must be fixed before assembly. Fix the issues above and re-run `/grant-writer:compliance`."

If **only warnings** exist:
- Print warnings with suggestions
- State: "Compliance check passed with warnings. Assembly may proceed."

If **all checks pass**:
- State: "Compliance check passed. Ready for assembly."

### 7. Update State

```bash
uv run grant-writer-state update <proposal_dir> --phase compliance --status <complete|failed>
```

Report:
- Total checks: N passed, N warnings, N critical
- Critical violations (if any) with fix instructions
- Path to `review/compliance_report.md`
