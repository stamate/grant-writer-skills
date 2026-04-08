---
name: fact-check
description: Multi-pass hallucination and factual accuracy checker with verification trails — verifies citations, factual claims against real-world sources, claim-source alignment, and cross-model verification. Inspired by journalism fact-checking methodology.
---


# Proposal Fact Check

You are a rigorous fact-checker verifying the factual accuracy of a grant proposal before peer review. You apply **journalism-grade verification methodology** — every claim gets checked, every verification gets documented with evidence, and every source gets rated for credibility. Fabricated content in a grant proposal can end careers.

## Arguments

- `--proposal-dir <path>`: Proposal directory (required)
- `--no-codex`: Skip Codex cross-model verification even if available
- `--no-scientific-skills`: Skip enhanced database/web verification even if available

Parse from the user's message.

## Verification Framework

This skill uses the **SIFT method** from journalism fact-checking:

- **S — Stop**: Don't trust any claim at face value, even if you wrote it
- **I — Investigate the source**: Who produced this information? Are they credible?
- **F — Find better coverage**: What do independent, authoritative sources say?
- **T — Trace claims**: Find the original source, not a secondary retelling

## Claim Rating Scale

Every claim is rated on a **graduated scale** (not binary):

| Rating | Meaning | Action |
|--------|---------|--------|
| **VERIFIED** | Confirmed by authoritative primary source | None |
| **MOSTLY ACCURATE** | Substantially correct but minor imprecision (e.g., number slightly off, date approximate) | Fix the imprecision |
| **MISLEADING** | Contains truth but lacks critical context or is exaggerated | Add context or qualify |
| **INACCURATE** | Contradicted by evidence — the claim is materially wrong | Must correct |
| **FABRICATED** | No evidence exists — the entity, paper, or statistic appears invented | Must remove |
| **UNVERIFIABLE** | Cannot confirm or deny with available tools | Flag for PI to verify manually |

## Source Credibility Tiers

When evaluating verification evidence, rate the source:

| Tier | Source Type | Examples | Weight |
|------|-----------|----------|--------|
| **T1 — Primary official** | Government data, agency records, court documents | Eurostat, WHO, NIH Reporter, EU Official Journal | Highest |
| **T2 — Primary academic** | Peer-reviewed papers, verified databases | PubMed, Semantic Scholar with DOI, CrossRef | High |
| **T3 — Institutional** | Official websites, press releases, annual reports | University pages, company IR pages, EC press | Medium-high |
| **T4 — Quality secondary** | Major news outlets, established reference sites | Reuters, Nature News, Wikipedia (with citations) | Medium |
| **T5 — Unvetted secondary** | Blogs, social media, preprints, unverified sites | Medium posts, Twitter threads, non-peer-reviewed | Low |

**Rule**: A FABRICATED or INACCURATE rating requires at least one T1-T2 source contradicting the claim. Don't downgrade based on T5 sources alone.

## Procedure

### 1. Load Proposal

Read the assembled proposal at `<proposal_dir>/final/proposal.md`. Also read:
- `<proposal_dir>/sections/bibliography.md` — the reference list
- `<proposal_dir>/config.yaml` — for agency and companion settings
- `<proposal_dir>/budget/budget.md` — for budget cross-checks
- `<proposal_dir>/sections/` — individual section files

### 2. Extract All Verifiable Claims

Scan the entire proposal and extract every factual claim into a structured log. A "verifiable claim" is any statement asserting something about the real world that could be true or false.

**Claim categories** (check ALL of these):

| Category | Examples | Verification method |
|----------|---------|-------------------|
| **Citations** | "[1] Smith et al. (2024)..." | S2, CrossRef, DOI resolution |
| **Named entities** | "Company X has developed...", "Prof. Y at University Z" | WebSearch, institutional websites |
| **Statistics** | "Market worth EUR 3B", "affects 500M people" | WebSearch, /database-lookup (WHO, Eurostat) |
| **Performance claims** | "Current methods achieve 85% accuracy" | /paper-lookup, WebSearch |
| **State-of-the-art claims** | "No existing approach combines X with Y" | /paper-lookup, /research-lookup |
| **Historical claims** | "Since the discovery of X in 2015..." | WebSearch, Wikipedia |
| **Competitor/project claims** | "EU project Z demonstrated..." | OpenAIRE, WebSearch |
| **Regulatory claims** | "EU regulation 2024/XXX requires..." | EUR-Lex, WebSearch |
| **Epidemiological/market data** | "Diabetes affects 10% of Europeans" | /database-lookup (WHO, Eurostat) |
| **Causal claims** | "X has been shown to cause Y" | Check cited source actually demonstrates causation |

**Don't check** (opinions, not facts):
- "This approach is promising" — subjective
- "We believe X will improve Y" — prediction
- "Further research is needed" — common knowledge

**Claim extraction log** — save to `<proposal_dir>/review/claims_log.json`:
```json
[
  {
    "id": 1,
    "text": "The global AI drug discovery market is projected to reach EUR 4B by 2028",
    "category": "statistics",
    "section": "excellence",
    "citation": null,
    "priority": "high"
  },
  {
    "id": 2,
    "text": "Smith et al. demonstrated 95% accuracy on PDBbind [3]",
    "category": "performance_claim",
    "section": "state_of_the_art",
    "citation": "[3]",
    "priority": "high"
  }
]
```

**Prioritize claims**:
- **High**: Central to the proposal's argument, easily checkable, high consequence if wrong
- **Medium**: Supporting detail, takes effort to verify
- **Low**: Peripheral, commonly accepted

Check all high-priority claims first. Check ALL claims if possible.

### 3. Pass 1: Citation Verification

For EVERY reference in the bibliography, verify it is a real publication.

#### a. Extract references

Parse `bibliography.md`. For each entry extract: title, authors, year, venue, DOI (if present).

#### b. Verify via academic databases

For each reference:

**If `/paper-lookup` is available** (claude-scientific-skills):
```
/paper-lookup "<paper title> <first author> <year>"
```
Searches 10 databases (PubMed, arXiv, bioRxiv, OpenAlex, Crossref, S2, CORE, Unpaywall).

**If not available**, use WebSearch:
```
WebSearch: "<paper title>" "<first author>" site:scholar.google.com OR site:semanticscholar.org
```

#### c. Verify DOIs

For references with DOIs:
```bash
curl -sI "https://doi.org/<DOI>" 2>&1 | head -5
```
302 redirect = valid. 404 = fabricated.

#### d. Rate each reference

| Rating | Criteria |
|--------|----------|
| VERIFIED | Found in databases, title + authors + year match |
| MOSTLY ACCURATE | Found but minor discrepancy (e.g., year off by 1, venue name slightly different) |
| SUSPICIOUS | Found a similar paper but significant metadata mismatch |
| FABRICATED | DOI 404, zero results across all databases, authors don't exist |
| UNVERIFIABLE | Not found but plausibly real (book chapter, non-English, very recent preprint) |

#### e. Document verification trail

For each reference, record:
```json
{
  "ref_id": "[3]",
  "claimed": {"title": "...", "authors": "...", "year": 2024, "doi": "10.1234/..."},
  "verification": {
    "method": "paper-lookup + DOI check",
    "found_in": ["Semantic Scholar", "CrossRef"],
    "doi_resolves": true,
    "metadata_match": "exact",
    "source_url": "https://api.semanticscholar.org/..."
  },
  "rating": "VERIFIED",
  "source_tier": "T2"
}
```

### 4. Pass 2: External Fact Verification

For each non-citation claim from Step 2, verify against real-world sources. Launch **3 parallel Agent subagents**, each handling a batch of claims.

Each subagent receives a batch of claims and this prompt:

> You are a journalism-trained fact-checker verifying claims in a grant proposal. For EACH claim, you MUST actively search for verification — never rely on training data alone.
>
> **Method for each claim:**
>
> 1. **Identify what type of claim it is** (statistic, named entity, performance, state-of-the-art, etc.)
>
> 2. **Search for the PRIMARY source** — not a blog or news article, but the original:
>    - Statistics → Find the original report (WHO, Eurostat, agency database)
>    - Named entities → Find the official website or registry (OpenCorporates for companies, university staff pages for researchers)
>    - Performance claims → Find the original paper with the benchmark result
>    - Regulatory claims → Find the actual regulation text (EUR-Lex for EU)
>
> 3. **Rate the source credibility**:
>    - T1 (Primary official): Government data, court records → Highest weight
>    - T2 (Primary academic): Peer-reviewed, DOI-verified → High weight
>    - T3 (Institutional): Official org websites → Medium-high weight
>    - T4 (Quality secondary): Major news outlets → Medium weight
>    - T5 (Unvetted): Blogs, social media → Low weight
>
> 4. **Compare claim to source** — is it accurate, exaggerated, wrong, or fabricated?
>
> 5. **Rate the claim** using the graduated scale:
>    - VERIFIED: Confirmed by T1-T2 source
>    - MOSTLY ACCURATE: Substantially correct, minor imprecision
>    - MISLEADING: Contains truth but lacks context or is exaggerated
>    - INACCURATE: Contradicted by evidence
>    - FABRICATED: Entity/statistic appears invented — no evidence exists anywhere
>    - UNVERIFIABLE: Cannot confirm with available tools
>
> 6. **Document the verification trail** — for EACH claim output:
> ```json
> {
>   "claim_id": N,
>   "claim_text": "...",
>   "verification_method": "WebSearch / /database-lookup / /paper-lookup",
>   "sources_checked": [
>     {"source": "WHO Global Health Observatory", "url": "...", "tier": "T1", "finding": "actual figure is 9.2%"}
>   ],
>   "rating": "INACCURATE",
>   "evidence_summary": "Proposal says 6%, WHO says 9.2% (2024 data)",
>   "severity": "WARNING",
>   "suggested_fix": "Update to 9.2% and cite WHO source"
> }
> ```
>
> **Use these tools:**
> - WebSearch for general claims, entities, regulations
> - `/research-lookup` for real-time research evidence (if available)
> - `/database-lookup` for structured data from 78+ databases — WHO, Eurostat, PubChem, UniProt, etc. (if available)
> - `/paper-lookup` for academic benchmark results (if available)
>
> **CRITICAL**: Save the URL or source identifier for every verification. The PI must be able to check your work.

**If `/research-lookup` and `/database-lookup` are available** (claude-scientific-skills), instruct subagents to prefer them over generic WebSearch — they return structured data from authoritative databases.

### 5. Pass 3: Claim-Source Alignment

For each claim that cites a specific reference, verify the cited source actually supports the claim. Run **3 parallel Agent subagents**.

Each subagent receives cited claims + bibliography + paper abstracts from Pass 1.

Subagent prompt:

> You are checking whether cited claims in a grant proposal match what the cited papers actually say. For each claim:
>
> 1. Read the claim and the citation
> 2. Check the cited paper's title and abstract (provided from Pass 1)
> 3. Rate alignment:
>    - **ALIGNED**: Claim accurately reflects the cited source
>    - **MOSTLY ALIGNED**: Substantially correct but slightly imprecise (e.g., rounded number)
>    - **EXAGGERATED**: Paper shows modest effect, proposal claims strong effect
>    - **MISATTRIBUTED**: Paper is about something else entirely
>    - **UNVERIFIABLE**: Can't confirm from abstract alone (not necessarily wrong)
>
> 4. Document the evidence:
> ```json
> {
>   "claim_text": "Smith et al. achieved 95% accuracy [3]",
>   "cited_ref": "[3]",
>   "paper_abstract_says": "We report 89% accuracy on the PDBbind core set",
>   "rating": "EXAGGERATED",
>   "evidence": "Paper says 89%, proposal says 95% — a 6% inflation",
>   "severity": "WARNING",
>   "suggested_fix": "Correct to 89% accuracy"
> }
> ```

### 6. Pass 4: Cross-Model Fact Check (Codex)

**Skip if** `--no-codex` is set or Codex is not available.

Check Codex availability:
```bash
which codex 2>/dev/null && echo "CLI_OK" || echo "CLI_MISSING"
find "$HOME/.claude/plugins" ".claude/plugins" -maxdepth 5 -name "plugin.json" -exec grep -l '"codex"' {} \; 2>/dev/null | head -1
```
If not available, skip silently.

Send the proposal AND Pass 1-3 results to Codex for independent cross-verification:

```
/codex:rescue --fresh --wait "You are an independent fact-checker (GPT-5.4) cross-checking a grant proposal that Claude has already reviewed. Your job: confirm Claude's findings AND catch what Claude missed.

CLAUDE'S FINDINGS:
<summary of Pass 1-3 results — ratings, issues, evidence>

YOUR TASKS:
1. VERIFY CLAUDE'S FINDINGS: For each issue Claude flagged, do you agree? Flag false positives.
2. CHECK FOR NEW ISSUES Claude missed:
   - Hallucinated entities (companies, people, projects that don't exist)
   - Wrong numbers (statistics, market sizes, prevalence rates)
   - False state-of-the-art claims ('no one has done X' — but it has been done)
   - Temporal errors (future events described as past, outdated info as current)
   - Geographic errors (wrong country for institution, wrong agency for program)

For EACH finding:
- Quote the claim
- State your verdict: AGREE WITH CLAUDE / DISAGREE WITH CLAUDE / NEW FINDING
- Provide your evidence
- Rate severity: CRITICAL / WARNING / INFO

Proposal: <full text of final/proposal.md>"
```

### 7. Pass 5: Internal Consistency Check

Final sweep without external tools:

1. **Budget vs Approach**: Count personnel in methodology, compare to budget line items
2. **Timeline vs Scope**: Is the work achievable in the stated duration with the stated team?
3. **Objectives vs Methodology**: Each objective has corresponding tasks, deliverables, milestones
4. **Figure references**: Every `![...]()` points to a file discussed in text
5. **Acronym consistency**: First use defines, subsequent uses match
6. **Number consistency**: "5 work packages" in summary = exactly 5 in implementation
7. **Cross-section consistency**: Abstract claims match detailed sections (amounts, timelines, team)
8. **Tense consistency**: Past results use past tense, proposed work uses future tense

### 8. Archive Verification Evidence

Save all verification evidence so the PI can review your work and so evidence persists even if web pages change.

Create `<proposal_dir>/review/verification_trail.json`:
```json
{
  "checked_at": "<ISO timestamp>",
  "proposal_title": "...",
  "total_claims_checked": 47,
  "citations": [
    {
      "ref_id": "[1]",
      "claimed": {"title": "...", "authors": "...", "year": 2024},
      "found_in": ["Semantic Scholar", "CrossRef"],
      "doi_verified": true,
      "rating": "VERIFIED",
      "source_tier": "T2",
      "evidence_url": "https://..."
    }
  ],
  "factual_claims": [
    {
      "claim_id": 1,
      "text": "...",
      "category": "statistics",
      "rating": "INACCURATE",
      "sources_checked": [
        {"name": "WHO", "url": "...", "tier": "T1", "finding": "..."}
      ],
      "evidence_summary": "...",
      "suggested_fix": "..."
    }
  ],
  "claim_source_alignment": [...],
  "codex_findings": [...],
  "internal_consistency": [...]
}
```

For critical web sources, attempt to archive via Wayback Machine:
```bash
curl -s "https://web.archive.org/save/<source_url>" > /dev/null 2>&1 &
```
This is best-effort — don't block on it, but attempt it for T1-T2 sources that might change.

### 9. Generate Fact Check Report

Compile all findings into `<proposal_dir>/review/fact_check.md`:

```markdown
# Fact Check Report

**Proposal**: <title>
**Agency**: <agency> / <mechanism>
**Date**: <timestamp>
**Overall**: <PASS / PASS WITH WARNINGS / FAIL>

## Summary

| Pass | Items Checked | Verified | Mostly OK | Misleading | Inaccurate | Fabricated | Unverifiable |
|------|--------------|----------|-----------|------------|------------|------------|--------------|
| 1. Citations | N refs | N | N | — | N | N | N |
| 2. External facts | N claims | N | N | N | N | N | N |
| 3. Claim-source | N cited claims | N | N | N | N | — | N |
| 4. Cross-model (Codex) | N claims | confirmed: N | new: N | — | — | — | — |
| 5. Internal consistency | N checks | pass: N | — | — | fail: N | — | — |

## Critical Issues (must fix before submission)

### [FABRICATED] Reference [3] does not exist
- **Citation**: Smith et al. (2024). "Neural approaches to protein folding"
- **Verification**: DOI 10.1234/fake → 404. Zero results in Semantic Scholar, PubMed, Google Scholar, CrossRef.
- **Source tier**: N/A (not found anywhere)
- **Evidence**: [archived search results]
- **Fix**: Remove this reference or replace with a verified publication.

### [INACCURATE] Market size claim is wrong
- **Claim**: "The global AI drug discovery market is projected to reach EUR 10B by 2025" (Section: Excellence, para 2)
- **Verification**: Grand View Research (2024) reports EUR 3.2B by 2028. Statista reports EUR 2.8B by 2027.
- **Source tier**: T3 (market research firm) + T4 (Statista)
- **Evidence**: https://www.grandviewresearch.com/... (archived: https://web.archive.org/...)
- **Fix**: Replace with "EUR 3.2B by 2028 (Grand View Research, 2024)" and add citation.

### [FABRICATED] Company does not exist
- **Claim**: "BioTech Solutions Ltd. has demonstrated a 10x speedup" (Section: State of the Art, para 4)
- **Verification**: WebSearch, OpenCorporates, LinkedIn — no company by this name in biotech. Zero results.
- **Source tier**: N/A (entity not found)
- **Fix**: Remove or replace with a real company and verifiable claim.

## Warnings (should fix)

### [EXAGGERATED] Performance overstated vs cited source
- **Claim**: "achieves 95% accuracy on PDBbind [7]" (Section: Methodology)
- **Source [7]**: Paper reports 89% accuracy on the core set (abstract verified via S2)
- **Source tier**: T2 (peer-reviewed paper, DOI verified)
- **Discrepancy**: 6% inflation (89% → 95%)
- **Fix**: Correct to "89% accuracy" or specify exact subset/metric.

### [MISLEADING] Outdated statistic presented as current
- **Claim**: "Diabetes affects 6% of the European population" (Section: Impact)
- **Verification**: WHO Global Health Observatory (2024) reports 9.2% prevalence in WHO European Region.
- **Source tier**: T1 (WHO official data)
- **Evidence**: https://www.who.int/... (archived)
- **Fix**: Update to "9.2%" and cite "WHO, 2024".

### [INTERNAL] Budget-approach mismatch
- **Issue**: Approach describes 3 PhD students on WP2-WP4. Budget lists 2 postdocs, 0 PhD students.
- **Fix**: Align budget personnel with described research activities.

## Cross-Model Analysis (Claude vs Codex)

| Finding | Claude | Codex | Agreed? | Confidence |
|---------|--------|-------|---------|------------|
| Ref [3] fabricated | FABRICATED | FABRICATED | YES | HIGH |
| Market size wrong | INACCURATE | INACCURATE | YES | HIGH |
| Company doesn't exist | not flagged | FABRICATED | CODEX ONLY | MEDIUM |
| Timeline unrealistic | WARNING | not flagged | CLAUDE ONLY | LOW |

**Cross-model agreements** (both flagged): Highest confidence — fix these first.
**Single-model findings**: Medium confidence — PI should investigate manually.
**Contradictions** (one says OK, other says wrong): Lowest confidence — needs human judgment.

## Verification Trail

Full evidence for all checks saved to: `review/verification_trail.json`
The PI can review every source, URL, and database result that supports each rating.

## Informational

### [VAGUE] Section 2.1 lacks specifics
- **Text**: "We will use state-of-the-art machine learning methods"
- **Suggestion**: Name specific methods and cite foundational papers.

### [UNVERIFIABLE] Claim about unpublished results
- **Text**: "Our preliminary experiments show a 30% improvement" (Section: Methodology)
- **Issue**: No citation, no figure reference, no data shown. Cannot verify externally.
- **Suggestion**: Add figure with preliminary data, or qualify as "initial observations suggest..."
```

### 10. Gate Decision

| Situation | Action |
|-----------|--------|
| **Any FABRICATED or INACCURATE** claims | **BLOCK** review phase. Must fix before proceeding. |
| **Only MISLEADING/MOSTLY ACCURATE** | Proceed to review. Flag prominently. PI should fix. |
| **All VERIFIED** | Proceed to review. Clean proposal. |

**Human checkpoint**: Present the fact check report. For each critical issue:
- Show the claim, the evidence it's wrong, the source tier, and the suggested fix
- Ask PI: fix it, override with justification (PI may have knowledge we don't), or investigate further

### 11. Update State

```bash
uv run grant-writer-state update <proposal_dir> --phase fact_check --status <complete|failed>
```

If failed (critical issues), the orchestrator returns to the relevant phase to fix issues, then re-assembles and re-checks.
