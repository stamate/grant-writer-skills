<div align="center">

  <p>
    <img src="https://img.shields.io/badge/Claude_Code-Skills-blueviolet?style=flat-square" alt="Claude Code"/>
    <img src="https://img.shields.io/badge/Funding-EU%20|%20Romania-blue?style=flat-square" alt="Funding"/>
    <img src="https://img.shields.io/badge/Output-Markdown-green?style=flat-square" alt="Markdown"/>
    <img src="https://img.shields.io/badge/Python-3.11+-orange?style=flat-square" alt="Python"/>
  </p>

</div>

> Write competitive grant proposals with AI assistance. Full pipeline from FOA analysis to peer review. Targets EU (Horizon Europe, ERC, MSCA) and Romanian (UEFISCDI, PNRR) funding agencies.

## Quick Navigation

| Section | What it helps with |
|---|---|
| [Why This Project](#why-this-project) | Understand the motivation and design philosophy. |
| [Supported Agencies](#supported-agencies) | See which funding programs are covered. |
| [Quick Start](#quick-start) | Install and run your first pipeline. |
| [Getting Started](#getting-started) | Realistic first-use examples after installation. |
| [Pipeline Overview](#pipeline-overview) | See the end-to-end flow from FOA to reviewed proposal. |
| [Skills Reference](#skills-reference) | Browse all available skills and what they do. |
| [Configuration](#configuration) | Tune aims rounds, literature depth, and review cycles. |

## Why This Project

Grant writing is one of the most time-consuming activities in academic research. A typical Horizon Europe RIA proposal takes 3-6 months of work across multiple researchers, with success rates around 15%.

This project takes a different approach:

> **Claude Code orchestrates the full proposal lifecycle.** From parsing funding announcements, through competitive landscape analysis, iterative aims refinement, agency-specific section writing, budget preparation, compliance checking, and multi-model peer review. The PI remains in the loop at every decision point.

| Aspect | Manual Grant Writing | Grant Writer Skills |
|--------|---------------------|---------------------|
| FOA analysis | Read 50+ page PDF, extract requirements manually | Automated extraction with structured output |
| Competitive landscape | Ad hoc Google searches | Systematic funded grants database queries (OpenAIRE) |
| Literature review | Weeks of manual searching | Multi-database parallel search (S2 + 78 databases) |
| Section writing | Blank page, agency guidelines open in another tab | Agency-aware templates with word limit tracking |
| Budget | Spreadsheet with manual calculations | Automated person-months / salary model calculation |
| Compliance | Manual checklist before submission | Automated word counts, section validation, citation checks |
| Peer review | Ask colleagues (if available) | Claude review + Codex agency-calibrated panel |
| Revision | Start over with reviewer comments | Structured point-by-point revision with re-review |

The result is a faster, more systematic process that catches compliance issues early and provides structured feedback before submission.

## Supported Agencies

| Agency | Mechanism | Region | Template Dir | Budget Model |
|--------|-----------|--------|-------------|-------------|
| Horizon Europe | RIA (Research & Innovation Action) | EU | `horizon_ria/` | person-months |
| Horizon Europe | IA (Innovation Action) | EU | `horizon_ia/` | person-months |
| ERC | Starting / Consolidator / Advanced | EU | `erc/` | person-months |
| MSCA | Postdoctoral Fellowships | EU | `msca_postdoc/` | person-months |
| MSCA | Doctoral Networks | EU | `msca_doctoral/` | person-months |
| UEFISCDI | PCE (Exploratory Research) | Romania | `uefiscdi_pce/` | monthly salary (RON) |
| UEFISCDI | TE (Young Research Teams) | Romania | `uefiscdi_te/` | monthly salary (RON) |
| UEFISCDI | PD (Postdoctoral Research) | Romania | `uefiscdi_pd/` | monthly salary (RON) |
| PNRR | Component 9 (R&D Support) | Romania | `pnrr/` | monthly salary (RON) |

## Quick Start

### Prerequisites

- [Claude Code](https://claude.ai/claude-code) CLI
- Python 3.11+

No LaTeX installation needed. All output is Markdown. Convert to Word/PDF at submission time via `/docx` or `/pdf` skills.

### Install

**Option A -- One command, global install** (recommended):
```bash
uv run https://raw.githubusercontent.com/stamate/grant-writer-skills/main/scripts/setup.py
```
Installs all 3 Claude Code plugins globally (grant-writer-skills + codex-plugin-cc + claude-scientific-skills). No clone needed. Available in all projects.

**Option B -- Project-scoped install**:
```bash
uv run https://raw.githubusercontent.com/stamate/grant-writer-skills/main/scripts/setup.py --project
```
Installs plugins into `.claude/plugins/` in the current directory only.

**Option C -- Clone + full local setup**:
```bash
uv run https://raw.githubusercontent.com/stamate/grant-writer-skills/main/scripts/setup.py --local
```
Clones repo + Python deps + project-scoped plugins. Everything contained in one directory.

**Option D -- Minimal**:
```bash
claude plugin marketplace add stamate/grant-writer-skills
claude plugin install grant-writer@grant-writer-skills
```

### Verify

```bash
uv run python3 tools/verify_setup.py
```

Checks Python version, required packages, Claude Code CLI, and optional companions (Codex, scientific skills) in one go.

## Getting Started

After installation, describe your task in natural language. Below are realistic starting points.

### 1. Run the Full Pipeline (Start Here)

**You say:**
> /grant-writer --foa call_document.pdf --agency horizon --mechanism ria

**What happens:**
- Claude extracts requirements from the funding opportunity PDF,
- queries OpenAIRE for competing funded projects,
- iteratively generates and refines objectives with your approval,
- searches literature across multiple databases,
- writes each proposal section respecting agency word limits,
- prepares budget (person-months model for EU),
- validates compliance against agency rules,
- assembles the full proposal and runs peer review,
- presents scores, strengths, weaknesses, and a revision plan.

### 2. Just Refine Your Aims

**You say:**
> /grant-writer:aims --proposal-dir ./my_proposal --max-rounds 3

**What happens:**
- Claude generates initial objectives from your research question and FOA requirements,
- scores them against agency criteria (excellence, impact, implementation),
- revises weak points iteratively,
- optionally gets Codex adversarial feedback,
- presents each round for your approval.

### 3. Review an Existing Proposal

**You say:**
> /grant-writer:review --proposal-dir ./my_proposal

**What happens:**
- Claude reviews `final/proposal.md` against agency-specific criteria,
- if Codex is available, runs a 3-persona panel review (Scientific Reviewer, Program Officer, Feasibility Assessor),
- if scientific skills are available, runs GRADE evidence assessment,
- merges all reviews with consensus, disagreements, and priority actions.

### 4. Competitive Landscape Search

**You say:**
> /grant-writer:landscape --agency horizon --query "spatial transcriptomics single cell" --pi-name "Maria Popescu"

**What happens:**
- Queries OpenAIRE for funded Horizon Europe projects matching your topic,
- looks up the PI's own funded grants for overlap analysis,
- if scientific skills are available, searches recent publications by funded PIs,
- produces a competitive brief with top competing projects, trends, gaps, and differentiation opportunities.

### 5. Prepare a Resubmission

**You say:**
> /grant-writer:resubmission --proposal-dir ./my_proposal --reviews evaluation_summary.pdf

**What happens:**
- Extracts reviewer comments from the evaluation summary report PDF,
- parses each criticism with severity, category, and affected section,
- generates a point-by-point response plan,
- you prioritize which criticisms to address, then run `/grant-writer:revision` to implement changes.

## Pipeline Overview

```
/grant-writer --foa call.pdf --agency horizon --mechanism ria
```

One command triggers the full lifecycle:

```
 0. Setup           -->  environment, companions, agency config
 1. FOA Analysis    -->  parse funding opportunity, extract requirements
 1.5 Landscape      -->  funded grants DB + literature + market analysis
 2. Aims            -->  specific objectives with iterative refinement
 3. Literature      -->  systematic search, gap identification, citations
 4. Preliminary     -->  assess PI's existing evidence
    Data
 5. Proposal        -->  project summary first, then agency-specific sections
    Writing
 5.5 Risk &         -->  What-If-Oracle scenarios + risk matrix
     Feasibility
 6. Budget          -->  person-months (EU) or monthly salary (Romania)
 7. Supporting      -->  CVs, facilities, DMP, ethics, letters
    Docs
 8. Compliance      -->  word counts, required sections, structure validation
 8.5 Assembly       -->  compile all sections into final/proposal.md
 9. Review          -->  Claude review + Codex panel (agency-calibrated)
10. Revision        -->  address weaknesses, re-assemble, re-review
```

Human checkpoints at phases 1, 2, 4, 5, 6, 7, and 9 ensure PI control over every major decision.

## Skills Reference

15 skills covering the complete grant proposal lifecycle.

### Pipeline Orchestration

| Type | Skill | Description |
|------|-------|-------------|
| Orchestrator | `/grant-writer` | Full pipeline: FOA analysis -> landscape -> aims -> writing -> review -> revision. Supports `--skip-review`, `--use-codex`, `--no-scientific-skills`. |

### Analysis & Planning

| Type | Skill | Description |
|------|-------|-------------|
| Skill | `/grant-writer:foa-analysis` | Parse funding opportunity announcements (PDF, HTML, URL). Extract eligibility, word limits, sections, deadlines. |
| Skill | `/grant-writer:landscape` | Competitive intelligence from OpenAIRE (EU) and UEFISCDI databases. Funded grants, overlap analysis, prior support. |
| Skill | `/grant-writer:aims` | Iterative objectives/aims refinement with agency-criteria scoring. Optional Codex adversarial review. |
| Skill | `/grant-writer:literature` | Systematic multi-database literature search. Gap identification and formatted citations. |
| Skill | `/grant-writer:preliminary-data` | Assess PI's existing evidence. Review figures with vision. Link evidence to objectives. |

### Writing & Budget

| Type | Skill | Description |
|------|-------|-------------|
| Skill | `/grant-writer:proposal` | Write agency-specific proposal sections with word limit tracking. Project summary first. |
| Skill | `/grant-writer:risk-analysis` | Structured risk assessment (5 categories) with mitigation strategies. Uses What-If-Oracle. |
| Skill | `/grant-writer:budget` | Budget preparation: person-months (EU) or monthly salary (Romania). Multi-year projection. |
| Skill | `/grant-writer:supporting-docs` | Generate CVs, facilities, DMP, ethics self-assessment, consortium agreements, letters of support. |

### Review & Compliance

| Type | Skill | Description |
|------|-------|-------------|
| Skill | `/grant-writer:compliance` | Validate structure, word counts, bibliography completeness, budget caps, figure references. |
| Skill | `/grant-writer:review` | Claude structured review + optional Codex agency-calibrated panel + optional GRADE evidence assessment. |
| Optional | `/grant-writer:codex-review` | Standalone Codex grant review with 3-persona panel (requires codex-plugin-cc). |
| Skill | `/grant-writer:resubmission` | Parse previous evaluation summary reports. Generate point-by-point response plan. |
| Skill | `/grant-writer:revision` | Address review feedback, revise affected sections, re-check compliance, re-review. |

## Python Tools

All tools are invoked via `uv run python3 tools/<module>.py` from the project root.

| Tool | Purpose |
|------|---------|
| `agency_requirements.py` | Load agency rules from `agency.json` manifests. List agencies, show sections, budget rules, review criteria. |
| `funded_grants.py` | Query public funding databases (OpenAIRE for EU, UEFISCDI for Romania). Search by topic, PI, agency. |
| `compliance_checker.py` | Validate proposal against agency requirements: word counts, sections, citations, budget caps, figures. |
| `budget_calculator.py` | Budget arithmetic for person-months (EU) and monthly salary (Romania) models. Multi-year, multi-currency. |
| `state_manager.py` | Grant proposal state persistence. Track phase completion, section progress, resume interrupted pipelines. |
| `config.py` | Load and merge YAML configuration with CLI overrides. |
| `verify_setup.py` | Validate all prerequisites (Python, packages, Claude CLI, optional Codex, scientific skills). |
| `pdf_reader.py` | PDF text extraction for FOAs and evaluation reports (pymupdf4llm > PyMuPDF > pypdf fallback). |

## Project Structure

```
grant-writer-skills/
├── .claude-plugin/
│   └── plugin.json            # Agent Skills plugin manifest
├── skills/                    # 15 skills (Agent Skills standard)
│   ├── grant-writer/SKILL.md    #   Main orchestrator
│   ├── foa-analysis/SKILL.md    #   FOA parser
│   ├── landscape/SKILL.md       #   Competitive intelligence
│   ├── aims/SKILL.md            #   Objectives refinement
│   ├── literature/SKILL.md      #   Literature search
│   ├── preliminary-data/SKILL.md #  Evidence assessment
│   ├── proposal/SKILL.md        #   Section writing
│   ├── risk-analysis/SKILL.md   #   Risk assessment
│   ├── budget/SKILL.md          #   Budget preparation
│   ├── supporting-docs/SKILL.md #   Supporting documents
│   ├── compliance/SKILL.md      #   Compliance validation
│   ├── review/SKILL.md          #   Combined review
│   ├── codex-review/SKILL.md    #   Standalone Codex review
│   ├── resubmission/SKILL.md    #   Resubmission handler
│   └── revision/SKILL.md        #   Revision loop
├── tools/                     # Python utilities (all via uv run python3)
│   ├── agency_requirements.py   #   Agency rules database
│   ├── funded_grants.py         #   Funded grants search
│   ├── compliance_checker.py    #   Proposal validation
│   ├── budget_calculator.py     #   Budget calculation
│   ├── state_manager.py         #   Proposal state
│   ├── config.py                #   Configuration
│   ├── verify_setup.py          #   Environment verification
│   └── pdf_reader.py            #   PDF text extraction
├── templates/
│   ├── agencies/                #   9 agency templates (agency.json + section templates)
│   │   ├── horizon_ria/
│   │   ├── horizon_ia/
│   │   ├── erc/
│   │   ├── msca_postdoc/
│   │   ├── msca_doctoral/
│   │   ├── uefiscdi_pce/
│   │   ├── uefiscdi_te/
│   │   ├── uefiscdi_pd/
│   │   └── pnrr/
│   ├── grant_config.yaml        #   Default configuration
│   └── review_fewshot/          #   Few-shot review examples
├── examples/                  # Example proposal directories
├── scripts/
│   └── setup.py               #   One-command install (uv run from URL)
├── CLAUDE.md                  # Claude Code project instructions
├── requirements.txt
└── pyproject.toml
```

## Configuration

Edit `templates/grant_config.yaml` or pass overrides at runtime:

```yaml
agency: horizon
mechanism: ria
language: en

proposal:
  title: ""
  pi_name: ""
  institution: ""
  acronym: ""              # EU proposals need a project acronym

aims:
  max_refinement_rounds: 5
  score_threshold: 4       # Out of 5 (EU scale)
  codex_review_rounds: 2

literature:
  max_search_rounds: 3
  min_citations: 30

writing:
  reflection_rounds: 3

budget:
  indirect_rate: 0.25      # 25% flat rate for Horizon Europe
  currency: EUR

review:
  revision_cycles: 2
  score_threshold: 3       # Out of 5 (EU: threshold for funding)

scientific_skills:
  enabled: auto
  enhanced_literature: true
  enhanced_writing: true
  enhanced_figures: true
  enhanced_review: true

codex:
  enabled: auto
  panel_review: true
  aims_review: true
  rescue_on_stuck: true
  agency: auto
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `S2_API_KEY` | No | Semantic Scholar API key for higher rate limits. Falls back to unauthenticated access or WebSearch. |

## Scientific Skills Integration

Install the [claude-scientific-skills](https://github.com/stamate/claude-scientific-skills) plugin for enhanced research capabilities:

```bash
claude plugin marketplace add stamate/claude-scientific-skills
claude plugin install scientific-skills@claude-scientific-skills
```

When scientific skills are available, the pipeline automatically:
- Uses **78+ scientific databases** (UniProt, STRING, PubChem, ChEMBL, Reactome, etc.) during landscape and literature phases
- Searches **10 academic databases** (PubMed, arXiv, bioRxiv, OpenAlex, etc.) for literature
- Applies **IMRAD prose structure** and **DOI verification** during proposal writing
- Generates **methodology flowcharts**, **Gantt charts**, and **work package diagrams** via `/scientific-schematics`
- Runs **What-If-Oracle** scenario analysis during risk assessment
- Runs **GRADE evidence assessment** and **bias detection** during review

Disable with `--no-scientific-skills` or in config:
```yaml
scientific_skills:
  enabled: false
```

## Codex Integration

Install the [codex-plugin-cc](https://github.com/stamate/codex-plugin-cc) plugin for enhanced reviews:

```bash
claude plugin marketplace add stamate/codex-plugin-cc
claude plugin install codex@stamate-codex
npm install -g @openai/codex
codex login
```

When Codex is available, the pipeline automatically:
- Runs **agency-calibrated panel review** with 3 personas (Scientific Reviewer, Program Officer, Feasibility Assessor) + synthesis
- Performs **adversarial aims review** during objectives refinement
- Provides **rescue delegation** when section writing stalls

Disable with `--no-codex` or in config:
```yaml
codex:
  enabled: false
```

## Output Format

All proposal output is **Markdown** (`.md` files). This is intentional:
- Both Claude and Codex read Markdown natively
- Easy to version control with git
- Human-readable at every stage

At submission time, convert to the required format:
```bash
# Word document (for most EU/Romanian portals)
claude "/docx final/proposal.md"

# PDF (for agencies that accept PDF uploads)
claude "/pdf final/proposal.md"
```

## Romanian Templates

All Romanian agency templates (UEFISCDI PCE/TE/PD, PNRR) support bilingual output:

```bash
# English (default)
claude "/grant-writer --foa call.pdf --agency uefiscdi --mechanism pce"

# Romanian section headers and boilerplate, English scientific content
claude "/grant-writer --foa call.pdf --agency uefiscdi --mechanism pce --lang ro"
```

With `--lang ro`:
- Section headers use Romanian names (e.g., "Rezumatul proiectului", "Starea actuala a cunoasterii")
- Boilerplate text (declarations, ethics statements) in Romanian
- Scientific content remains in English for international review panels

## License

See [LICENSE](LICENSE) for full terms.

## Acknowledgments

Built with [Claude Code](https://claude.ai/claude-code) CLI.
