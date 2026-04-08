#!/usr/bin/env bash
set -euo pipefail

# Grant Writer Skills — Install
# Usage: curl -fsSL https://raw.githubusercontent.com/stamate/grant-writer-skills/main/scripts/install.sh | bash

REPO="https://github.com/stamate/grant-writer-skills.git"

echo "=== Grant Writer Skills — Install ==="
echo ""

# 1. Check prerequisites
for cmd in uv claude; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: $cmd not found. Please install it first."
        exit 1
    fi
done

# 2. Create .venv and install Python package + all dependencies
echo "[1/4] Creating .venv and installing Python tools..."
uv venv --quiet 2>/dev/null || true
uv pip install "git+${REPO}" --quiet
echo "  .venv created with: requests, backoff, pymupdf4llm, pyyaml, rich"
echo "  CLI tools: grant-writer-verify, grant-writer-state, grant-writer-config, ..."
echo "  OK"

# 3. Add and update marketplaces (update ensures latest version is cached)
echo "[2/4] Adding marketplaces..."
claude plugin marketplace add stamate/grant-writer-skills 2>/dev/null || true
claude plugin marketplace add stamate/codex-plugin-cc 2>/dev/null || true
claude plugin marketplace add K-Dense-AI/claude-scientific-skills 2>/dev/null || true
claude plugin marketplace add K-Dense-AI/claude-scientific-writer 2>/dev/null || true
claude plugin marketplace add anthropics/claude-plugins-official 2>/dev/null || true
claude plugin marketplace update grant-writer-skills 2>/dev/null || true
claude plugin marketplace update stm-codex 2>/dev/null || true
claude plugin marketplace update claude-scientific-skills 2>/dev/null || true
claude plugin marketplace update claude-scientific-writer 2>/dev/null || true
claude plugin marketplace update claude-plugins-official 2>/dev/null || true
echo "  OK"

# 4. Install plugins at project scope
echo "[3/4] Installing plugins..."
# Core: grant writer pipeline
claude plugin install grant-writer@grant-writer-skills --scope project 2>/dev/null || true
# Codex: multi-persona grant review with agency calibration
claude plugin install codex@stm-codex --scope project 2>/dev/null || true
# Scientific skills: 134 research skills (literature, databases, visualization, critical thinking)
claude plugin install scientific-skills@claude-scientific-skills --scope project 2>/dev/null || true
# Scientific writer: enhanced writing, image generation, schematics, Paper2Web
claude plugin install claude-scientific-writer@claude-scientific-writer --scope project 2>/dev/null || true
# Superpowers: brainstorming, planning, structured workflows
claude plugin install superpowers@claude-plugins-official --scope project 2>/dev/null || true
echo "  OK"

# 5. Create CLAUDE.md if it doesn't exist
echo "[4/4] Creating CLAUDE.md..."
if [ ! -f CLAUDE.md ]; then
    cat > CLAUDE.md << 'CLAUDEMD'
# Grant Writer Skills

## Environment

This project uses `uv` with a `.venv` directory. **ALWAYS** prefix `grant-writer-*` commands with `uv run`:

```bash
uv run grant-writer-verify
uv run grant-writer-config --config templates/grant_config.yaml
uv run grant-writer-state init --agency horizon --mechanism ria
uv run grant-writer-state status <proposal_dir>
uv run grant-writer-agency list
uv run grant-writer-grants search "query" --agency horizon --limit 10
uv run grant-writer-budget calculate <budget_input.yaml>
uv run grant-writer-compliance check <proposal_dir>
uv run grant-writer-pdf <file.pdf>
```

**Never** run `grant-writer-*` commands without `uv run` — they are installed in `.venv/bin/` and won't be found otherwise.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/stamate/grant-writer-skills/main/scripts/install.sh | bash
```

## Run

```bash
claude '/grant-writer --agency horizon --mechanism ria'
```
CLAUDEMD
    echo "  Created CLAUDE.md"
else
    echo "  CLAUDE.md already exists, skipping"
fi
echo "  OK"

echo ""
echo "=== Done ==="
echo ""
echo "  Verify: uv run grant-writer-verify"
echo "  Run:    claude '/grant-writer --agency horizon --mechanism ria'"
