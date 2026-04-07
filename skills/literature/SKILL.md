---
name: literature
description: Systematic literature search and citation gathering for grant proposal context, gap identification, and bibliography.
---


# Literature Review

You are conducting a systematic literature search for a grant proposal — gathering references, identifying the gap the proposal fills, and building a formatted bibliography.

## Arguments

- `--proposal-dir <path>`: Proposal directory (required)
- `--max-rounds <N>`: Search rounds (default: 3)
- `--min-citations <N>`: Minimum references to gather (default: 30)
- `--no-scientific-skills`: Skip enhanced search even if plugin is available

Parse from the user's message.

## Procedure

### 0. Locate Plugin Root

```bash
if [ -f "tools/verify_setup.py" ]; then GRANTWRITER_ROOT="$(pwd)"
else GRANTWRITER_ROOT=$(find ".claude/plugins" "$HOME/.claude/plugins" -maxdepth 8 -name "verify_setup.py" -path "*grant-writer*" 2>/dev/null | head -1 | xargs dirname | xargs dirname); fi
export GRANTWRITER_ROOT; if [ -z "$GRANTWRITER_ROOT" ]; then echo "ERROR: Could not find grant-writer-skills plugin root."; fi; echo "Plugin root: $GRANTWRITER_ROOT"
```

### 1. Load Context

Read from the proposal directory:
- `config.yaml` — agency, citation style preference
- `sections/objectives.md` — research objectives (drives search queries)
- `foa_requirements.json` — scope and keywords
- `landscape/competitive_brief.md` — known competing work

Load citation style from agency template:
```bash
uv run python3 "$GRANTWRITER_ROOT/tools/agency_requirements.py" info <agency> <mechanism>
```

The `citation_style` field determines formatting: `"numbered"` produces `[1]`, `[2]` style; `"author_year"` produces `(Smith et al., 2024)` style.

### 2. Search Semantic Scholar

For each search round (up to `--max-rounds`), query S2 with progressively refined terms:

**Round 1**: Broad topic keywords from the research objectives
**Round 2**: Specific methodology and technique terms
**Round 3**: Key authors and seminal works in the field

```bash
uv run python3 "$GRANTWRITER_ROOT/tools/search.py" "<query>" --limit 15 --json
```

If S2 returns no results or is unavailable, use WebSearch to search `scholar.google.com` and `arxiv.org`.

### 3. Enhanced Search (Optional — claude-scientific-skills)

**Skip if** `--no-scientific-skills` is set or plugin not available.

Check plugin availability:
```bash
find "$HOME/.claude/plugins" ".claude/plugins" -maxdepth 5 \
  -name "plugin.json" -exec grep -l '"claude-scientific"' {} \; 2>/dev/null | head -1
```
If not found, skip silently.

When available, run in parallel:
- `/research-lookup "<objectives keywords>"` — real-time preprint search
- `/paper-lookup "<specific methodology terms>"` — 10-database search
- `/database-lookup "<entity name>"` — for biology/chemistry/materials topics, query 78+ databases for mechanistic evidence

Merge results with S2 search, deduplicating by title similarity.

### 4. Categorize and Analyze

Organize references into categories:
- **Background / foundational work**: Seminal papers establishing the field
- **State of the art**: Recent advances directly relevant to the proposal
- **Methodology**: Papers describing techniques the proposal will use or extend
- **Competing approaches**: Alternative solutions to the same problem
- **PI's own work**: The PI's relevant publications (from landscape/prior_support.md)

Identify the **gap** in the literature that the proposal fills. This gap statement becomes a key argument in the proposal narrative.

### 5. Build Literature Review Document

Write `landscape/literature.md` with:
- Categorized references with brief annotation (1-2 sentences per paper)
- Gap analysis narrative (what is missing, what the proposal contributes)
- Connection to each research objective

### 6. Build Bibliography

Write `sections/bibliography.md` with all references formatted according to the agency's citation style:

**Numbered style** (`citation_style: "numbered"`):
```
[1] Author A, Author B. Title of paper. *Journal Name*, vol(issue):pages, Year. DOI: ...
[2] ...
```

**Author-year style** (`citation_style: "author_year"`):
```
Author A, Author B (Year). Title of paper. *Journal Name*, vol(issue):pages. DOI: ...
```

Ensure every reference cited in proposal sections has a matching entry in the bibliography.

## Notes

- Target at least `--min-citations` references, but prioritize quality over quantity.
- Include recent references (last 3-5 years) to show awareness of current developments.
- Include the PI's own publications where relevant — reviewers check for this.
- For EU proposals, include references to relevant EU policy documents or framework programme objectives if appropriate.
