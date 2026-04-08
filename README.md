<div align="center">

  <p>
    <img src="https://img.shields.io/badge/Claude_Code-Skills-blueviolet?style=flat-square" alt="Claude Code"/>
    <img src="https://img.shields.io/badge/Funding-EU%20|%20Romania-blue?style=flat-square" alt="Funding"/>
    <img src="https://img.shields.io/badge/Output-Markdown-green?style=flat-square" alt="Markdown"/>
    <img src="https://img.shields.io/badge/Python-3.11+-orange?style=flat-square" alt="Python"/>
    <img src="https://img.shields.io/badge/Skills-17-red?style=flat-square" alt="17 Skills"/>
  </p>

</div>

> Write competitive grant proposals with AI assistance. Full pipeline from FOA analysis to peer review with journalism-grade fact checking. Targets EU (Horizon Europe, ERC, MSCA) and Romanian (UEFISCDI, PNRR) funding agencies.

## Quick Navigation

| Section | What it helps with |
|---|---|
| [Why This Project](#why-this-project) | Understand the motivation and design philosophy |
| [Supported Agencies](#supported-agencies) | See which funding programs are covered |
| [Quick Start](#quick-start) | Install and run your first pipeline |
| [Getting Started](#getting-started) | Realistic first-use examples after installation |
| [Pipeline Overview](#pipeline-overview) | See the end-to-end flow from FOA to reviewed proposal |
| [Skills Reference](#skills-reference) | Browse all 17 skills and what they do |
| [Configuration](#configuration) | Tune aims rounds, literature depth, and review cycles |
| [Companion Plugins](#companion-plugins) | Enhanced reviews (Codex) and research tools (scientific skills) |

## Why This Project

Grant writing is one of the most time-consuming activities in academic research. A typical Horizon Europe RIA proposal takes 3-6 months of work across multiple researchers, with success rates around 15%.

This project takes a different approach:

> **Claude Code orchestrates the full proposal lifecycle.** From parsing funding announcements, through competitive landscape analysis, iterative aims refinement, agency-specific section writing, budget preparation, compliance checking, fact verification, and multi-model peer review. The PI remains in the loop at every decision point.

| Aspect | Manual Grant Writing | Grant Writer Skills |
|--------|---------------------|---------------------|
| Document import | Manually re-enter CV, budget, references | Auto-extract from existing PDFs, DOCX, XLSX |
| FOA analysis | Read 50+ page PDF, extract requirements manually | Automated extraction with structured output |
| Competitive landscape | Ad hoc Google searches | Systematic funded grants database queries (OpenAIRE) |
| Literature review | Weeks of manual searching | Multi-database parallel search (S2 + 78 databases) |
| Section writing | Blank page, agency guidelines open in another tab | Agency-aware templates with word limit tracking |
| Budget | Spreadsheet with manual calculations | Automated person-months / monthly salary calculation |
| Compliance | Manual checklist before submission | Automated word counts, section validation, citation checks |
| Fact checking | Trust what you wrote | 5-pass verification with journalism-grade evidence trails |
| Peer review | Ask colleagues (if available) | Claude 3-persona panel + optional Codex panel (6 reviewers total) |
| Revision | Start over with reviewer comments | Structured point-by-point revision with re-review |

## Supported Agencies

### EU Agencies

| Agency | Mechanism | Template | Budget Model |
|--------|-----------|----------|-------------|
| Horizon Europe | RIA (Research & Innovation Action) | `horizon_ria/` | person-months (EUR) |
| Horizon Europe | IA (Innovation Action) | `horizon_ia/` | person-months (EUR) |
| ERC | Starting / Consolidator / Advanced | `erc/` | person-months (EUR) |
| MSCA | Postdoctoral Fellowships | `msca_postdoc/` | person-months (EUR) |
| MSCA | Doctoral Networks | `msca_doctoral/` | person-months (EUR) |

### Romanian Agencies

| Agency | Mechanism | Template | Budget Model |
|--------|-----------|----------|-------------|
| UEFISCDI | PCE (Exploratory Research) | `uefiscdi_pce/` | monthly salary (RON) |
| UEFISCDI | TE (Young Research Teams) | `uefiscdi_te/` | monthly salary (RON) |
| UEFISCDI | PD (Postdoctoral Research) | `uefiscdi_pd/` | monthly salary (RON) |
| PNRR | Component 9 (R&D Support) | `pnrr/` | monthly salary (RON) |

## Quick Start

### Prerequisites

- [Claude Code](https://claude.ai/claude-code) CLI
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Python 3.11+

No LaTeX needed. All output is Markdown. Convert to Word/PDF at submission time via `/docx` or `/pdf` skills.

### Install

**One command** (recommended):
```bash
curl -fsSL https://raw.githubusercontent.com/stamate/grant-writer-skills/main/scripts/install.sh | bash
```

This installs:
- `.venv` with all Python dependencies
- **grant-writer-skills** — the core pipeline (this plugin)
- **codex-plugin-cc** — multi-persona grant review with 14 agency calibrations
- **claude-scientific-skills** — 134 research skills (literature, databases, visualization)
- **claude-hud** — status line display

All plugins installed at project scope. A `CLAUDE.md` is created with usage instructions.

**Minimal** (plugin only, add companions manually):
```bash
claude plugin marketplace add stamate/grant-writer-skills
claude plugin install grant-writer@grant-writer-skills
```

### Verify

```bash
uv run grant-writer-verify
```

Checks Python, packages, Claude Code CLI, and optional companions (Codex, scientific skills).

## Getting Started

After installation, describe your task in natural language. Below are realistic starting points.

### 1. Full Pipeline with Existing Documents (Fastest Start)

If you already have your CV, papers, budget spreadsheet, and the FOA document:

```
/grant-writer --foa call_document.pdf --agency horizon --mechanism ria --docs ~/my-grant-materials/
```

The system will:
1. Auto-import your documents (CV → biosketch, papers → preliminary data, budget → input)
2. Parse the FOA and extract requirements
3. Query OpenAIRE for competing funded projects
4. Generate and iteratively refine objectives with your approval
5. Write each section with imported context, respecting agency word limits
6. Prepare budget from your spreadsheet data
7. Run compliance checks + 5-pass fact verification
8. Run dual multi-perspective peer review (Claude + Codex panels)
9. Present scores, weaknesses, and a revision plan

### 2. Full Pipeline from Scratch

```
/grant-writer --foa call_document.pdf --agency uefiscdi --mechanism pce --lang en
```

Same pipeline, but the system asks for information at each human checkpoint instead of importing documents.

### 3. Just Refine Your Aims

```
/grant-writer:aims --proposal-dir ./my_proposal --max-rounds 3
```

Iteratively generates, scores, and refines objectives against agency criteria. Optional Codex adversarial feedback.

### 4. Review an Existing Proposal

```
/grant-writer:review --proposal-dir ./my_proposal
```

Runs dual multi-perspective panel:
- **Claude panel**: 3 parallel personas (Scientific Reviewer, Program Officer, Feasibility Assessor) with confidence-weighted synthesis
- **Codex panel** (if installed): 3 additional personas via GPT-5.4 + Panel Chair synthesis
- Cross-panel agreements are the highest-confidence findings

### 5. Fact-Check Before Submission

```
/grant-writer:fact-check --proposal-dir ./my_proposal
```

5-pass verification:
1. **Citations**: Every reference checked against S2/CrossRef/DOI
2. **External facts**: Statistics, companies, claims verified via web + 78 databases
3. **Claim-source alignment**: Cited claims match what papers actually say
4. **Cross-model check**: Codex independently flags what Claude missed
5. **Internal consistency**: Budget vs approach, timeline vs scope, number consistency

Produces a journalism-grade fact-check report with evidence trails, source credibility tiers, and graduated ratings.

### 6. Competitive Landscape Search

```
/grant-writer:landscape --agency horizon --query "spatial transcriptomics" --pi-name "Maria Popescu"
```

Queries OpenAIRE for funded projects, checks PI's own grants for overlap, produces competitive brief.

### 7. Import Documents Only

```
/grant-writer:import-docs --docs ~/my-materials/ --proposal-dir ./my_proposal
```

Scans your folder, classifies each document (CV, paper, budget, letter, FOA...), extracts structured data, and pre-populates proposal sections. Reports what was imported and what still needs manual input.

### 8. Prepare a Resubmission

```
/grant-writer:resubmission --proposal-dir ./my_proposal --reviews evaluation_summary.pdf
```

Parses previous reviewer feedback, generates point-by-point response plan.

## Pipeline Overview

```
/grant-writer --foa call.pdf --agency horizon --mechanism ria --docs ~/materials/
```

One command triggers the full lifecycle:

```
 0.   Setup           →  environment, companions, agency config
 0.5  Import Docs     →  auto-extract from PI's CVs, papers, budgets, letters
 1.   FOA Analysis    →  parse funding opportunity, extract requirements
 1.5  Landscape       →  funded grants DB + literature + market analysis
 2.   Aims            →  specific objectives with iterative refinement
 3.   Literature      →  systematic search, gap identification, citations
 4.   Preliminary     →  assess PI's existing evidence
      Data
 5.   Proposal        →  project summary first, then agency-specific sections
      Writing
 5.5  Risk &          →  What-If-Oracle scenarios + risk matrix
      Feasibility
 6.   Budget          →  person-months (EU) or monthly salary (Romania)
 7.   Supporting      →  CVs, facilities, DMP, ethics, letters
      Docs
 8.   Compliance      →  word counts, required sections, structure validation
 8.5  Assembly        →  compile all sections into final/proposal.md
 8.7  Fact Check      →  5-pass verification with journalism-grade evidence trails
 9.   Review          →  Claude 3-persona panel + optional Codex panel
10.   Revision        →  address weaknesses, re-assemble, re-review
```

**Human checkpoints** at phases 0.5, 1, 2, 4, 5, 6, 7, 8.7, and 9 ensure PI control over every major decision.

## Skills Reference

17 skills covering the complete grant proposal lifecycle.

### Pipeline Orchestration

| Skill | Description |
|-------|-------------|
| `/grant-writer` | Full pipeline orchestrator. Supports `--foa`, `--agency`, `--mechanism`, `--docs`, `--lang`, `--skip-review`, `--use-codex`, `--no-codex`, `--no-scientific-skills`. |

### Document Import & Analysis

| Skill | Description |
|-------|-------------|
| `/grant-writer:import-docs` | Auto-extract from PI's existing documents (PDF, DOCX, XLSX, PPTX, images, BibTeX). Classifies each, extracts structured data, pre-populates proposal. |
| `/grant-writer:foa-analysis` | Parse funding opportunity announcements (PDF, HTML, URL). Extract eligibility, word limits, sections, deadlines. |
| `/grant-writer:landscape` | Competitive intelligence from OpenAIRE (EU) and UEFISCDI. Funded grants, overlap analysis, prior support, differentiation. |

### Research & Writing

| Skill | Description |
|-------|-------------|
| `/grant-writer:aims` | Iterative objectives refinement with agency-criteria scoring. Optional Codex adversarial review. |
| `/grant-writer:literature` | Systematic multi-database literature search. Gap identification and formatted citations. |
| `/grant-writer:preliminary-data` | Assess PI's existing evidence. Review figures with vision. Link evidence to objectives. |
| `/grant-writer:proposal` | Write agency-specific proposal sections with word limit tracking. Project summary first. |
| `/grant-writer:risk-analysis` | Structured risk assessment (5 categories) with mitigation strategies. Uses What-If-Oracle. |
| `/grant-writer:budget` | Budget preparation: person-months (EU) or monthly salary (Romania). Multi-year projection. |
| `/grant-writer:supporting-docs` | Generate CVs, facilities, DMP, ethics self-assessment, consortium agreements, letters of support. |

### Quality Assurance & Review

| Skill | Description |
|-------|-------------|
| `/grant-writer:compliance` | Validate structure, word counts, bibliography, budget caps, figure references. Blocks assembly on critical violations. |
| `/grant-writer:fact-check` | 5-pass hallucination checker with journalism-grade evidence trails, graduated ratings (Verified → Fabricated), source credibility tiers (T1-T5), and cross-model verification. |
| `/grant-writer:review` | Claude 3-persona panel (Scientific Reviewer, Program Officer, Feasibility Assessor) + optional Codex 3-persona panel. Cross-panel analysis identifies highest-confidence findings. |
| `/grant-writer:codex-review` | Standalone Codex grant review with agency calibration (requires codex-plugin-cc). |
| `/grant-writer:resubmission` | Parse previous evaluation summary reports. Generate point-by-point response plan. |
| `/grant-writer:revision` | Address review feedback, revise affected sections, re-check compliance, re-fact-check, re-review. |

## Python Tools

All tools are installed as CLI entry points. Use `uv run` to invoke them.

| Command | Purpose |
|---------|---------|
| `uv run grant-writer-verify` | Validate all prerequisites (Python, packages, Claude CLI, Codex, scientific skills) |
| `uv run grant-writer-agency` | Load agency rules from `agency.json` manifests. List agencies, sections, budget rules, review criteria |
| `uv run grant-writer-grants` | Query funded grants databases (OpenAIRE for EU). Search by topic, PI, agency |
| `uv run grant-writer-compliance` | Validate proposal: word counts, required sections, citations, budget caps, figures |
| `uv run grant-writer-budget` | Budget calculation: person-months (EU) or monthly salary (Romania). Multi-year, multi-currency |
| `uv run grant-writer-state` | Proposal state persistence. Track phases, section progress, resume interrupted pipelines |
| `uv run grant-writer-config` | Load and display YAML configuration with CLI overrides |
| `uv run grant-writer-pdf` | PDF text extraction for FOAs and evaluation reports |

## Project Structure

```
grant-writer-skills/
├── skills/                      # 17 skills (Agent Skills standard)
│   ├── grant-writer/SKILL.md      # Orchestrator
│   ├── import-docs/SKILL.md       # Document import
│   ├── foa-analysis/SKILL.md      # FOA parser
│   ├── landscape/SKILL.md         # Competitive intelligence
│   ├── aims/SKILL.md              # Objectives refinement
│   ├── literature/SKILL.md        # Literature search
│   ├── preliminary-data/SKILL.md  # Evidence assessment
│   ├── proposal/SKILL.md          # Section writing
│   ├── risk-analysis/SKILL.md     # Risk assessment
│   ├── budget/SKILL.md            # Budget preparation
│   ├── supporting-docs/SKILL.md   # Supporting documents
│   ├── compliance/SKILL.md        # Compliance validation
│   ├── fact-check/SKILL.md        # Fact verification
│   ├── review/SKILL.md            # Multi-persona review
│   ├── codex-review/SKILL.md      # Standalone Codex review
│   ├── resubmission/SKILL.md      # Resubmission handler
│   └── revision/SKILL.md          # Revision loop
├── tools/                       # Python CLI tools (uv run grant-writer-*)
│   ├── agency_requirements.py     # grant-writer-agency
│   ├── funded_grants.py           # grant-writer-grants
│   ├── compliance_checker.py      # grant-writer-compliance
│   ├── budget_calculator.py       # grant-writer-budget
│   ├── state_manager.py           # grant-writer-state
│   ├── config.py                  # grant-writer-config
│   ├── verify_setup.py            # grant-writer-verify
│   └── pdf_reader.py              # grant-writer-pdf
├── templates/
│   ├── agencies/                  # 9 agency templates
│   │   ├── horizon_ria/           #   Horizon Europe RIA
│   │   ├── horizon_ia/            #   Horizon Europe IA
│   │   ├── erc/                   #   European Research Council
│   │   ├── msca_postdoc/          #   MSCA Postdoctoral
│   │   ├── msca_doctoral/         #   MSCA Doctoral Networks
│   │   ├── uefiscdi_pce/          #   UEFISCDI Exploratory
│   │   ├── uefiscdi_te/           #   UEFISCDI Young Teams
│   │   ├── uefiscdi_pd/           #   UEFISCDI Postdoctoral
│   │   └── pnrr/                  #   Romania PNRR
│   └── grant_config.yaml          # Default configuration
├── examples/                    # Example proposal directories
├── scripts/
│   └── install.sh               # One-command install (curl | bash)
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

## Configuration

Edit `templates/grant_config.yaml` or pass overrides at runtime:

```yaml
agency: horizon
mechanism: ria
language: en                 # en | ro (Romanian templates only)

proposal:
  title: ""
  pi_name: ""
  institution: ""
  acronym: ""                # EU proposals need a project acronym

aims:
  max_refinement_rounds: 5
  score_threshold: 4         # Out of 5 (EU scale)
  codex_review_rounds: 2

literature:
  max_search_rounds: 3
  min_citations: 30

writing:
  reflection_rounds: 3

budget:
  indirect_rate: 0.25        # 25% flat rate for Horizon Europe
  currency: EUR              # EUR for EU, RON for Romania

review:
  revision_cycles: 2
  score_threshold: 3         # Out of 5 (EU: threshold for funding)

scientific_skills:
  enabled: auto              # auto | true | false
codex:
  enabled: auto              # auto | true | false
```

Override specific values without editing the file:
```bash
uv run grant-writer-config --config templates/grant_config.yaml --set agency=uefiscdi mechanism=pce budget.currency=RON
```

## Companion Plugins

The install script sets up all companions automatically. They're optional — the pipeline works without them.

### Codex (codex-plugin-cc)

Adds a **second AI model** (GPT-5.4) for independent review. When installed:
- **Agency-calibrated panel review**: 3 personas (Scientific Reviewer, Program Officer, Feasibility Assessor) + Panel Chair synthesis. 14 agency calibrations including MSCA, UEFISCDI, PNRR.
- **Adversarial aims review**: Independent critique during objectives refinement
- **Cross-model fact checking**: Codex flags claims Claude missed (different model = different knowledge)
- **Rescue**: Fresh perspective when section writing stalls

```bash
# Manual install (install.sh does this automatically)
claude plugin marketplace add stamate/codex-plugin-cc
claude plugin install codex@stm-codex
npm install -g @openai/codex && codex login
```

### Scientific Skills (claude-scientific-skills)

Adds **134 specialized research skills**. When installed:
- **78+ scientific databases** (UniProt, STRING, PubChem, WHO, Eurostat, etc.) during landscape and fact checking
- **10 academic databases** (PubMed, arXiv, bioRxiv, OpenAlex, etc.) for literature
- **IMRAD prose structure** and **DOI verification** during writing
- **Methodology flowcharts**, **Gantt charts**, and **work package diagrams**
- **What-If-Oracle** scenario analysis during risk assessment
- **GRADE evidence assessment** during review

```bash
# Manual install (install.sh does this automatically)
claude plugin marketplace add K-Dense-AI/claude-scientific-skills
claude plugin install scientific-skills@claude-scientific-skills
```

## Output Format

All proposal output is **Markdown** (`.md` files). This is intentional:
- Both Claude and Codex read Markdown natively — no conversion needed for review
- Easy to version control with git (diff-friendly)
- Human-readable and editable at every stage
- PI can open and edit any section in any text editor

At submission time, convert to the required format:
```bash
# Word document (for most EU/Romanian submission portals)
claude "/docx final/proposal.md"

# PDF
claude "/pdf final/proposal.md"
```

## Romanian Templates

All Romanian agency templates (UEFISCDI PCE/TE/PD, PNRR) support bilingual output:

```bash
# English (default)
/grant-writer --agency uefiscdi --mechanism pce

# Romanian headers + English scientific content
/grant-writer --agency uefiscdi --mechanism pce --lang ro
```

With `--lang ro`: section headers use Romanian names (e.g., "Rezumatul proiectului"), boilerplate in Romanian, scientific content in English for international review panels.

## License

MIT — see [LICENSE](LICENSE).
