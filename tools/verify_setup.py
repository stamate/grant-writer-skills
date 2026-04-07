"""Verify all prerequisites for Grant Writer Skills.

Run after cloning to ensure the environment is ready:
    python tools/verify_setup.py
"""

from __future__ import annotations

import importlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
CHECK = f"{GREEN}\u2713{RESET}"
CROSS = f"{RED}\u2717{RESET}"
WARN = f"{YELLOW}!{RESET}"


# pip name -> import name (only for packages where they differ)
IMPORT_MAP = {
    "PyMuPDF": "fitz",
    "pyyaml": "yaml",
    "pymupdf4llm": "pymupdf4llm",
    "Pillow": "PIL",
}


def parse_requirements() -> list[tuple[str, str]]:
    """Read requirements.txt and return (pip_name, import_name) pairs."""
    req_file = Path(__file__).resolve().parent.parent / "requirements.txt"
    packages = []
    if not req_file.exists():
        print(f"  {WARN} requirements.txt not found, skipping package check")
        return packages
    for line in req_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # strip version specifiers: requests>=2.31 -> requests
        name = re.split(r"[><=!~\[]", line)[0].strip()
        imp = IMPORT_MAP.get(name, name)
        packages.append((name, imp))
    return packages


def check_python() -> bool:
    v = sys.version_info
    ok = v >= (3, 11)
    status = CHECK if ok else CROSS
    print(f"  {status} Python {v.major}.{v.minor}.{v.micro}", end="")
    if not ok:
        print(f"  (requires 3.11+)", end="")
    print()
    return ok


def check_package(name: str, import_name: str | None = None) -> bool:
    mod = import_name or name
    try:
        m = importlib.import_module(mod)
        ver = getattr(m, "__version__", "ok")
        print(f"  {CHECK} {name} {ver}")
        return True
    except ImportError:
        print(f"  {CROSS} {name}  (pip install {name})")
        return False


def check_claude_code() -> bool:
    claude = shutil.which("claude")
    if claude:
        print(f"  {CHECK} Claude Code CLI ({claude})")
        return True
    else:
        print(f"  {CROSS} Claude Code CLI not found  (https://claude.ai/claude-code)")
        return False


def check_codex() -> bool:
    """Check if Codex CLI and Claude plugin are installed (optional enhancement)."""
    codex = shutil.which("codex")
    if not codex:
        print(f"  {WARN} Codex CLI not found — standard pipeline only (optional)")
        print(f"      Install: npm install -g @openai/codex")
        return False
    # CLI found — check if the Claude Code plugin is also installed
    plugin_found = False
    for root in [Path.home() / ".claude" / "plugins", Path(".claude") / "plugins"]:
        if not root.exists():
            continue
        try:
            result = subprocess.run(
                ["find", str(root), "-maxdepth", "5", "-name", "plugin.json"],
                capture_output=True, text=True, timeout=10,
            )
            for path in result.stdout.strip().splitlines():
                try:
                    content = Path(path).read_text()
                    if "codex" in content.lower():
                        plugin_found = True
                        break
                except Exception:
                    pass
            if plugin_found:
                break
        except Exception:
            pass
    if plugin_found:
        print(f"  {CHECK} Codex CLI ({codex}) + plugin — enhanced reviews available")
        return True
    else:
        print(f"  {WARN} Codex CLI found ({codex}) but codex-plugin-cc not installed")
        print(f"      Run: claude install gh:stamate/codex-plugin-cc")
        return False


def check_scientific_skills() -> bool:
    """Check if claude-scientific-skills plugin is installed (optional enhancement)."""
    plugin_found = False
    for root in [Path.home() / ".claude" / "plugins", Path(".claude") / "plugins"]:
        if not root.exists():
            continue
        try:
            result = subprocess.run(
                ["find", str(root), "-maxdepth", "8", "-name", "plugin.json"],
                capture_output=True, text=True, timeout=10,
            )
            for path in result.stdout.strip().splitlines():
                try:
                    content = Path(path).read_text()
                    if "claude-scientific" in content.lower():
                        plugin_found = True
                        break
                except Exception:
                    pass
            if plugin_found:
                break
        except Exception:
            pass
    if plugin_found:
        print(f"  {CHECK} claude-scientific-skills plugin — enhanced literature, writing, and review available")
        return True
    else:
        print(f"  {WARN} claude-scientific-skills not found — standard pipeline only (optional)")
        print(f"      Install: claude install gh:stamate/claude-scientific-skills")
        return False


def check_s2_api() -> bool:
    """Check Semantic Scholar API availability."""
    has_key = bool(os.environ.get("S2_API_KEY"))
    if has_key:
        print(f"  {CHECK} S2_API_KEY is set")
    else:
        print(f"  {WARN} S2_API_KEY not set — citation search will fall back to WebSearch")
        print(f"      Get a free key at https://www.semanticscholar.org/product/api#api-key")
    return has_key


def main():
    print()
    print("Grant Writer Skills — Environment Check")
    print("=" * 42)

    errors = 0
    warnings = 0

    # Python version
    print("\n[Python]")
    if not check_python():
        errors += 1

    # Core packages — read from requirements.txt
    print("\n[Python Packages]")
    packages = parse_requirements()
    for name, imp in packages:
        if not check_package(name, imp):
            errors += 1

    # Literature search
    print("\n[Literature Search]")
    if not check_s2_api():
        warnings += 1

    # Claude Code
    print("\n[Claude Code]")
    if not check_claude_code():
        errors += 1

    # Codex (optional enhancement)
    print("\n[Codex Integration (optional)]")
    if not check_codex():
        warnings += 1

    # Scientific skills (optional enhancement)
    print("\n[Scientific Skills (optional)]")
    if not check_scientific_skills():
        warnings += 1

    # Summary
    print("\n" + "=" * 42)
    if errors == 0 and warnings == 0:
        print(f"{CHECK} All checks passed. Ready to go!")
    elif errors == 0:
        print(f"{WARN} {warnings} warning(s) — functional but some features limited.")
    else:
        print(f"{CROSS} {errors} error(s) found. Fix them before running.")
    print()

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
