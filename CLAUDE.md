# Grant Writer Skills for Claude Code

This project provides a complete grant proposal writing pipeline as Claude Code skills. It targets EU (Horizon Europe, ERC, MSCA) and Romanian (UEFISCDI, PNRR) funding agencies. Markdown throughout — no LaTeX needed. Final Word/PDF conversion via `/docx` or `/pdf` skills at submission time.

## Skills

| Command | Description |
|---------|-------------|
| `/grant-writer` | Full pipeline: FOA analysis -> landscape -> aims -> writing -> review |
| `/grant-writer:foa-analysis` | Parse funding opportunity announcements |
| `/grant-writer:landscape` | Competitive intelligence from funding databases |
| `/grant-writer:aims` | Iterative objectives/aims refinement |
| `/grant-writer:literature` | Systematic literature search for grant context |
| `/grant-writer:preliminary-data` | Assess PI's existing evidence |
| `/grant-writer:proposal` | Write agency-specific proposal sections |
| `/grant-writer:risk-analysis` | Structured risk assessment with scenario analysis |
| `/grant-writer:budget` | Budget preparation (person-months or monthly salary) |
| `/grant-writer:supporting-docs` | CVs, facilities, DMP, ethics, letters |
| `/grant-writer:compliance` | Validate structure, word counts, required sections |
| `/grant-writer:review` | Claude + optional Codex panel review |
| `/grant-writer:codex-review` | Standalone Codex grant review |
| `/grant-writer:resubmission` | Parse previous reviews, plan revisions |
| `/grant-writer:revision` | Address feedback, revise, re-review |

## Project Layout

- `skills/` — Skill directories, each containing a `SKILL.md` (Agent Skills standard)
- `tools/` — Python utilities (agency requirements, budget calculator, compliance, state, config, PDF reader)
- `templates/` — Agency templates (`agencies/`), default config (`grant_config.yaml`), review few-shot examples
- `examples/` — Example proposal directories

## Tool Usage

When running from a cloned repo, tools are invoked via `uv run python3 tools/<module>.py`. When installed as a plugin, skills discover the plugin root first and use absolute paths (`"$GRANTWRITER_ROOT/tools/<module>.py"`). See any skill's "Locate Plugin Root" step for the discovery pattern.

Tool reference (from project root):

```bash
uv run python3 tools/verify_setup.py                                        # Verify all prerequisites
uv run python3 tools/agency_requirements.py list                             # List all agencies
uv run python3 tools/agency_requirements.py info horizon ria                 # Show agency requirements
uv run python3 tools/agency_requirements.py sections erc starting            # Show section limits
uv run python3 tools/agency_requirements.py budget horizon ria               # Show budget rules
uv run python3 tools/agency_requirements.py review-criteria uefiscdi pce     # Show scoring
uv run python3 tools/funded_grants.py search "query" --agency horizon --limit 20  # Search funded grants
uv run python3 tools/funded_grants.py pi-grants "Name" --agency horizon      # PI's previous grants
uv run python3 tools/compliance_checker.py check <proposal_dir>              # Full compliance check
uv run python3 tools/compliance_checker.py word-counts <proposal_dir>        # Word counts per section
uv run python3 tools/compliance_checker.py budget-check <proposal_dir>       # Budget validation
uv run python3 tools/budget_calculator.py calculate <budget_input.yaml>      # Calculate budget
uv run python3 tools/budget_calculator.py format <input.yaml> --style horizon_wp  # Format for Horizon
uv run python3 tools/state_manager.py init --agency horizon --mechanism ria  # Init proposal state
uv run python3 tools/state_manager.py status <proposal_dir>                  # Check proposal state
uv run python3 tools/state_manager.py update <dir> --phase aims --status complete  # Update phase
uv run python3 tools/config.py --config <path>                               # Load/display config
uv run python3 tools/pdf_reader.py <file.pdf>                                # Extract PDF text
```

## Environment

- **Python**: 3.11+
- **No LaTeX needed** — Markdown output throughout
- **Optional**: `S2_API_KEY` env var for Semantic Scholar API (higher rate limits during literature search)

## Supported Agencies

| Template | Agency | Mechanism | Region | Budget Model |
|----------|--------|-----------|--------|-------------|
| `horizon_ria` | Horizon Europe | RIA (Research & Innovation Action) | EU | person-months |
| `horizon_ia` | Horizon Europe | IA (Innovation Action) | EU | person-months |
| `erc` | ERC | Starting / Consolidator / Advanced | EU | person-months |
| `msca_postdoc` | MSCA | Postdoctoral Fellowships | EU | person-months |
| `msca_doctoral` | MSCA | Doctoral Networks | EU | person-months |
| `uefiscdi_pce` | UEFISCDI | PCE (Exploratory Research) | Romania | monthly salary |
| `uefiscdi_te` | UEFISCDI | TE (Young Research Teams) | Romania | monthly salary |
| `uefiscdi_pd` | UEFISCDI | PD (Postdoctoral Research) | Romania | monthly salary |
| `pnrr` | PNRR | Component 9 (R&D Support) | Romania | monthly salary |

## Scientific Skills Integration (Optional)

When the **claude-scientific-skills** plugin is installed alongside grant-writer-skills, the pipeline gains:

- **Multi-Database Literature**: `/research-lookup` (Perplexity-powered), `/paper-lookup` (10 databases), `/database-lookup` (78+ databases) during landscape and literature phases
- **Enhanced Writing**: `/scientific-writing` (IMRAD prose, two-stage process) + `/citation-management` (DOI verification via CrossRef) during proposal writing
- **Publication Figures**: `/scientific-schematics` (methodology flowcharts, Gantt charts, work package diagrams) during proposal writing
- **Risk Analysis**: `/what-if-oracle` (Deep Oracle mode scenario analysis) during risk assessment
- **Evidence Assessment**: `/scientific-critical-thinking` (GRADE framework, bias detection) during review

All features are **optional**. Control via config:

```yaml
scientific_skills:
  enabled: auto               # auto | true | false
  enhanced_literature: true
  enhanced_writing: true
  enhanced_figures: true
  enhanced_review: true
```

## Codex Integration (Optional)

When the **codex-plugin-cc** plugin is installed alongside grant-writer-skills, the pipeline gains:

- **Agency-Calibrated Panel Review**: 3 independent reviewer personas (Scientific Reviewer, Program Officer, Feasibility Assessor) + synthesis via `/codex:grant-review --panel --agency <agency>`
- **Aims Review**: Adversarial Codex critique of objectives during aims refinement
- **Stuck Section Rescue**: Codex provides fresh perspective when writing stalls

All Codex features are **optional** — the pipeline works identically without it. Control via config:

```yaml
codex:
  enabled: auto           # auto | true | false
  panel_review: true
  aims_review: true
  rescue_on_stuck: true
  agency: auto            # auto | horizon | erc | msca | uefiscdi | pnrr
```
