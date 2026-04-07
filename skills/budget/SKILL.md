---
name: budget
description: Prepare agency-specific budget with person-months or monthly salary model, justification narrative, and per-year cost breakdown.
---


# Budget Preparation

You are preparing the budget for a grant proposal, using the agency-specific budget model (person-months for EU, monthly salary for Romania).

## Arguments

- `--proposal-dir <path>`: Proposal directory (required)

Parse from the user's message.

## Procedure

### 0. Locate Plugin Root

```bash
if [ -f "tools/verify_setup.py" ]; then GRANTWRITER_ROOT="$(pwd)"
else GRANTWRITER_ROOT=$(find ".claude/plugins" "$HOME/.claude/plugins" -maxdepth 8 -name "verify_setup.py" -path "*grant-writer*" 2>/dev/null | head -1 | xargs dirname | xargs dirname); fi
export GRANTWRITER_ROOT; if [ -z "$GRANTWRITER_ROOT" ]; then echo "ERROR: Could not find grant-writer-skills plugin root."; fi; echo "Plugin root: $GRANTWRITER_ROOT"
```

### 1. Load Budget Model

Read the agency configuration to determine the budget model:

```bash
python3 "$GRANTWRITER_ROOT/tools/agency_requirements.py" budget <agency> <mechanism>
```

Also read `<proposal_dir>/config.yaml` for budget overrides (indirect rate, currency).

Two budget models exist:
- **`person_months`** (Horizon Europe, ERC, MSCA): Personnel = person-months x unit cost. Indirect = 25% flat rate of eligible direct costs (excluding subcontracting). Per-work-package breakdown.
- **`monthly_salary`** (UEFISCDI, PNRR): Personnel = monthly salary x effort% x months. Indirect capped at 25% of direct costs (UEFISCDI). Per-year breakdown.

### 2. Collect PI Budget Inputs

**Human checkpoint**: Ask the PI for budget data. Ask different questions depending on the budget model.

**For EU (person-months model)**, ask:
1. How many person-months per work package per partner?
2. Unit cost per person-month (or use institutional rates)?
3. Equipment costs (itemize major equipment >EUR 15,000)?
4. Travel budget (conferences, project meetings, secondments)?
5. Subcontracting costs (what tasks, to whom)?
6. Other direct costs (consumables, open access, audit)?

**For Romania (monthly salary model)**, ask:
1. Team members with role, monthly salary, and effort percentage?
2. Duration in months?
3. Mobility/travel costs?
4. Equipment and consumables?
5. Any other direct costs (services, software licenses)?

Save the PI's raw inputs to `<proposal_dir>/budget/budget_input.yaml`.

### 3. Calculate Budget

Run the budget calculator with the PI's inputs:

```bash
python3 "$GRANTWRITER_ROOT/tools/budget_calculator.py" calculate <proposal_dir>/budget/budget_input.yaml
```

This produces:
- Per-year and total costs
- Direct vs indirect breakdown (using the agency-specific indirect model)
- Currency-appropriate formatting (EUR for EU, RON for Romania)
- Per-work-package breakdown (Horizon Europe) or per-year breakdown (UEFISCDI/PNRR)

### 4. Format Output

Generate the formatted budget tables:

```bash
python3 "$GRANTWRITER_ROOT/tools/budget_calculator.py" format <proposal_dir>/budget/budget_input.yaml --style <agency_style>
```

Where `<agency_style>` is `horizon_wp` for EU or `uefiscdi` for Romania.

Save formatted output to `<proposal_dir>/budget/budget.md`.

### 5. Write Budget Justification

Draft `<proposal_dir>/budget/justification.md` with a narrative explanation of each cost category:
- Why each team member's effort level is appropriate
- How equipment costs are essential to the project objectives
- Travel justification tied to dissemination and collaboration goals
- For EU: explain subcontracting needs and why the work cannot be done in-house
- For Romania: explain mobility costs and their link to project activities

Use formal grant-writing language. Every cost line must be tied to a specific project activity or objective.

### 6. Review Budget

**Human checkpoint**: Present the PI with:
- Total budget summary (direct + indirect)
- Per-year breakdown table
- Per-work-package breakdown (EU) or per-category breakdown (Romania)
- Justification narrative highlights
- Any budget cap warnings from agency.json

Ask the PI to confirm line items or request adjustments. If adjustments are needed, update `budget_input.yaml` and re-run the calculator.

### 7. Update State

```bash
python3 "$GRANTWRITER_ROOT/tools/state_manager.py" update <proposal_dir> --phase budget --status complete
```

Report:
- Budget model used (person-months / monthly salary)
- Total budget with currency
- Direct vs indirect split
- Number of cost categories
- Path to `budget/budget.md` and `budget/justification.md`
