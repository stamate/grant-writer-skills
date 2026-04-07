# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Grant Writer Skills — One-command setup. Run directly from GitHub:

  uv run https://raw.githubusercontent.com/stamate/grant-writer-skills/main/scripts/setup.py

Modes:
  (default)  Install plugins globally (--scope user)
  --project  Install plugins into current project (--scope project)
  --local    Clone repo here + install plugins at project scope + Python deps
  --check    Verify installation status
  --deps     Python dependencies only (requires local repo)

Plugin scopes (from `claude plugin install --scope`):
  user     ~/.claude/plugins/ — available in all projects (default)
  project  .claude/plugins/   — available only in this project
  local    .claude/plugins/   — available only on this machine for this project
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = "stamate/grant-writer-skills"
REPO_URL = f"https://github.com/{REPO}.git"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"
CHECK = f"{GREEN}\u2713{RESET}"
CROSS = f"{RED}\u2717{RESET}"
WARN = f"{YELLOW}!{RESET}"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300, **kwargs)


def run_live(cmd: list[str], **kwargs) -> int:
    return subprocess.call(cmd, timeout=300, **kwargs)


def step(msg: str) -> None:
    print(f"\n{BOLD}{msg}{RESET}")


def ok(msg: str) -> None:
    print(f"  {CHECK} {msg}")


def fail(msg: str) -> None:
    print(f"  {CROSS} {msg}")


def warn(msg: str) -> None:
    print(f"  {WARN} {msg}")


# ── Clone ──────────────────────────────────────────────────────────────────────


def clone_repo(target: Path) -> bool:
    step("Cloning grant-writer-skills")
    if (target / ".git").exists():
        ok(f"Already cloned at {target}")
        return True

    git = shutil.which("git")
    if not git:
        fail("git not found")
        return False

    result = run([git, "clone", REPO_URL, str(target)])
    if result.returncode == 0:
        ok(f"Cloned to {target}")
        return True

    fail(f"Clone failed: {result.stderr[:200]}")
    return False


# ── Python deps ────────────────────────────────────────────────────────────────


def install_python_deps(project_root: Path) -> bool:
    step("Python dependencies")
    req_file = project_root / "requirements.txt"

    if not req_file.exists():
        warn("requirements.txt not found — skipping Python deps")
        return False

    uv = shutil.which("uv")
    if uv:
        # Try with active venv first, then --system
        for extra in [[], ["--system"]]:
            result = run([uv, "pip", "install", *extra, "-r", str(req_file)])
            if result.returncode == 0:
                suffix = " (--system)" if extra else ""
                ok(f"Installed via uv{suffix}")
                return True

    pip = shutil.which("pip3") or shutil.which("pip")
    if pip:
        result = run([pip, "install", "-r", str(req_file)])
        if result.returncode == 0:
            ok("Installed via pip")
            return True
        warn(f"pip failed: {result.stderr[:200]}")
        return False

    fail("Neither uv nor pip found")
    return False


# ── Claude plugins ─────────────────────────────────────────────────────────────


def add_marketplace(repo: str, scope: str = "user") -> bool:
    """Register a GitHub repo as a Claude Code marketplace."""
    claude = shutil.which("claude")
    if not claude:
        return False
    result = run([claude, "plugin", "marketplace", "add", repo, "--scope", scope])
    return result.returncode == 0 or "already" in (result.stdout + result.stderr).lower()


def install_claude_plugin(marketplace: str, plugin: str, repo: str, scope: str = "user") -> bool:
    claude = shutil.which("claude")
    if not claude:
        fail(f"Claude Code CLI not found — cannot install {plugin}")
        return False

    # Step 1: Add the marketplace (repo) if not already registered
    add_marketplace(repo, scope)

    # Step 2: Install the plugin from that marketplace
    plugin_ref = f"{plugin}@{marketplace}"
    result = run([claude, "plugin", "install", plugin_ref, "--scope", scope])
    out = result.stdout + result.stderr
    if result.returncode == 0 or "already" in out.lower():
        ok(f"{plugin_ref} (scope: {scope})")
        return True

    fail(f"{plugin_ref} — {out.strip()[:200]}")
    return False


def install_all_plugins(scope: str = "user") -> bool:
    # (marketplace_name, plugin_name, github_repo)
    plugins = [
        ("grant-writer-skills", "grant-writer", "stamate/grant-writer-skills"),
        ("stamate-codex", "codex", "stamate/codex-plugin-cc"),
        ("claude-scientific-skills", "scientific-skills", "stamate/claude-scientific-skills"),
    ]
    step(f"Claude Code plugins ({len(plugins)}, scope: {scope})")
    all_ok = True
    for marketplace, plugin, repo in plugins:
        if not install_claude_plugin(marketplace, plugin, repo, scope):
            all_ok = False
    return all_ok


# ── Codex CLI ──────────────────────────────────────────────────────────────────


def install_codex_cli() -> bool:
    step("Codex CLI")
    if shutil.which("codex"):
        ok("Already installed")
        return True

    npm = shutil.which("npm")
    if not npm:
        warn("npm not found — install Node.js to get Codex CLI")
        return False

    result = run([npm, "install", "-g", "@openai/codex"])
    if result.returncode == 0:
        ok("Installed")
        warn("Run 'codex login' to authenticate")
        return True

    warn(f"npm install failed: {result.stderr[:200]}")
    return False


# ── Verify ─────────────────────────────────────────────────────────────────────


def verify(project_root: Path | None) -> None:
    step("Verification")
    if project_root and (project_root / "tools" / "verify_setup.py").exists():
        run_live([sys.executable, str(project_root / "tools" / "verify_setup.py")])
    else:
        # Quick check without local repo
        for name, cmd in [
            ("Claude Code", ["claude", "--version"]),
            ("Codex CLI", ["codex", "--version"]),
        ]:
            if shutil.which(cmd[0]):
                ok(name)
            else:
                warn(f"{name} not found")


# ── Main ───────────────────────────────────────────────────────────────────────


def detect_project_root() -> Path | None:
    """Find project root if we're inside the repo."""
    here = Path.cwd()
    for p in [here, *here.parents]:
        if (p / "pyproject.toml").exists() and (p / "skills").exists():
            return p
    # Also check relative to this script (when run locally)
    script_parent = Path(__file__).resolve().parent.parent
    if (script_parent / "pyproject.toml").exists():
        return script_parent
    return None


def main():
    import argparse

    url = f"https://raw.githubusercontent.com/{REPO}/main/scripts/setup.py"
    parser = argparse.ArgumentParser(
        description="Grant Writer Skills — one-command setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Install plugins globally (available everywhere):
  uv run {url}

  # Install plugins into current project only:
  uv run {url} --project

  # Clone repo + project-scoped install + Python deps:
  uv run {url} --local

  # Just check what's installed:
  uv run {url} --check
""",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--local", action="store_true",
        help="Clone repo here + install plugins at project scope + Python deps",
    )
    mode.add_argument(
        "--project", action="store_true",
        help="Install plugins at project scope (.claude/plugins/ in cwd)",
    )
    mode.add_argument("--deps", action="store_true", help="Python deps only (needs local repo)")
    mode.add_argument("--check", action="store_true", help="Verify installation")
    args = parser.parse_args()

    print(f"\n{BOLD}=== Grant Writer Skills — Setup ==={RESET}")

    project_root = detect_project_root()

    if args.check:
        verify(project_root)
        return

    if args.deps:
        if not project_root:
            fail("Not inside the repo — use --local to clone first")
            sys.exit(1)
        install_python_deps(project_root)
        return

    # Determine scope
    if args.local or args.project:
        scope = "project"
    else:
        scope = "user"

    success = True

    if args.local:
        # Clone + project-scoped install
        target = Path.cwd() / "grant-writer-skills"
        if project_root:
            print(f"  Already in repo at {project_root}")
            target = project_root
        else:
            if not clone_repo(target):
                sys.exit(1)
        # cd into the clone so project-scoped plugins install into clone/.claude/plugins/
        os.chdir(target)
        install_python_deps(target)
        if not install_all_plugins(scope):
            success = False
        install_codex_cli()
        verify(target)
    else:
        # Plugin install (user or project scope)
        if not install_all_plugins(scope):
            success = False
        install_codex_cli()

        # Try to install Python deps from the plugin's requirements.txt
        step("Python dependencies")
        if project_root:
            install_python_deps(project_root)
        else:
            # Find requirements.txt in the installed plugin directory
            plugin_req = None
            for search_root in [Path.home() / ".claude" / "plugins", Path(".claude") / "plugins"]:
                if not search_root.exists():
                    continue
                try:
                    result = run(["find", str(search_root), "-maxdepth", "6",
                                  "-name", "requirements.txt", "-path", "*grant-writer*"])
                    if result.stdout.strip():
                        plugin_req = Path(result.stdout.strip().splitlines()[0])
                        break
                except Exception:
                    pass
            if plugin_req and plugin_req.exists():
                ok(f"Found {plugin_req}")
                uv = shutil.which("uv")
                if uv:
                    # Ensure a venv exists in the user's project directory
                    venv_path = Path.cwd() / ".venv"
                    if not venv_path.exists():
                        print(f"  Creating virtual environment at {venv_path}")
                        run([uv, "venv", str(venv_path)])
                    # Install into the project's venv
                    r = run([uv, "pip", "install", "-r", str(plugin_req)])
                    if r.returncode == 0:
                        ok("Installed into project .venv/")
                    else:
                        warn(f"Install failed. Run manually: uv pip install -r {plugin_req}")
                else:
                    warn("uv not found for dep install. Run: pip install -r " + str(plugin_req))
            else:
                warn("Could not find requirements.txt in plugin directory")
                print(f"      Run manually: pip install requests backoff pymupdf4llm pyyaml rich")

        verify(project_root)

    if success:
        print(f"\n{BOLD}=== Done ==={RESET}")
    else:
        print(f"\n{BOLD}=== Done (with errors) ==={RESET}")
    scope_note = "project (.claude/plugins/)" if scope == "project" else "global (~/.claude/plugins/)"
    print(f"  Scope: {scope_note}")
    if args.local or project_root:
        # After --local os.chdir, cwd IS the target — don't append again
        root = project_root or (target if args.local else Path.cwd() / "grant-writer-skills")
        print(f"\n  Quick start:")
        print(f"    cd {root}")
        print(f"    claude '/grant-writer --foa call.pdf --agency horizon --mechanism ria'")
    else:
        scope_label = "at project scope" if scope == "project" else "globally"
        print(f"\n  Plugins installed {scope_label}. To also clone the repo:")
        print(f"    uv run {url} --local")
    print()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
