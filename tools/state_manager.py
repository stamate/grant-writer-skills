"""Grant proposal state management — phase tracking and session resume.

File-based JSON state for tracking proposal pipeline progress across
multiple Claude Code invocations.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


# ── Phase pipeline ──────────────────────────────────────────────────────────

PHASE_ORDER = [
    "setup",
    "foa_analysis",
    "landscape",
    "aims",
    "literature",
    "preliminary_data",
    "proposal_writing",
    "risk_analysis",
    "budget",
    "supporting_docs",
    "compliance",
    "assembly",
    "review",
    "revision",
]

# Subdirectories created inside every proposal
_SUBDIRS = [
    "landscape",
    "sections/figures",
    "budget",
    "supporting/letters",
    "review",
    "resubmission",
    "final",
]


# ── State creation ──────────────────────────────────────────────────────────


def create_state(agency: str, mechanism: str, language: str = "en") -> Dict[str, Any]:
    """Return a fresh proposal state dict with all phases pending."""
    now = datetime.now().isoformat()
    return {
        "agency": agency,
        "mechanism": mechanism,
        "language": language,
        "current_phase": "setup",
        "phases": {phase: {"status": "pending"} for phase in PHASE_ORDER},
        "config": {},
        "created_at": now,
        "updated_at": now,
    }


# ── Persistence ─────────────────────────────────────────────────────────────


def load_state(proposal_dir: str | Path) -> Dict[str, Any]:
    """Read state.json from *proposal_dir*."""
    state_path = Path(proposal_dir) / "state.json"
    with open(state_path) as f:
        return json.load(f)


def save_state(proposal_dir: str | Path, state: Dict[str, Any]) -> None:
    """Write *state* to state.json, updating the timestamp."""
    state["updated_at"] = datetime.now().isoformat()
    state_path = Path(proposal_dir) / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)


# ── Initialisation ──────────────────────────────────────────────────────────


def init_proposal(
    agency: str,
    mechanism: str,
    config_path: Optional[str] = None,
    language: str = "en",
) -> str:
    """Create a proposal directory with scaffolding and initial state.

    Returns the proposal directory path as a string.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dirname = f"{agency}_{mechanism}_{timestamp}"
    proposal_dir = Path("proposals") / dirname
    proposal_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    for sub in _SUBDIRS:
        (proposal_dir / sub).mkdir(parents=True, exist_ok=True)

    # Write initial state
    state = create_state(agency, mechanism, language)
    save_state(proposal_dir, state)

    # Write config — merge user config (if provided) with defaults
    default_cfg_path = Path(__file__).resolve().parent.parent / "templates" / "grant_config.yaml"
    cfg_data: dict = {}
    if default_cfg_path.exists():
        cfg_data = yaml.safe_load(default_cfg_path.read_text()) or {}
    if config_path:
        src = Path(config_path)
        if src.exists():
            user_cfg = yaml.safe_load(src.read_text()) or {}
            cfg_data.update(user_cfg)
    # Always set agency/mechanism/language from the init arguments
    cfg_data["agency"] = agency
    cfg_data["mechanism"] = mechanism
    cfg_data["language"] = language
    (proposal_dir / "config.yaml").write_text(
        yaml.dump(cfg_data, default_flow_style=False, sort_keys=False)
    )

    print(str(proposal_dir))
    return str(proposal_dir)


# ── Phase updates ───────────────────────────────────────────────────────────


def update_phase(
    proposal_dir: str | Path, phase: str, status: str, **extra: Any
) -> Dict[str, Any]:
    """Update a phase's status and manage current_phase advancement.

    *status* should be one of: ``pending``, ``in_progress``, ``complete``.
    Extra keyword arguments are merged into the phase dict (e.g.
    ``sections_done=["abstract", "aims"]``, ``rounds=3``, ``citations=35``).
    """
    state = load_state(proposal_dir)

    if phase not in state["phases"]:
        raise ValueError(f"Unknown phase: {phase}")

    state["phases"][phase]["status"] = status
    state["phases"][phase].update(extra)

    if status == "in_progress":
        state["current_phase"] = phase
    elif status == "complete":
        # Advance current_phase to the next pending phase
        state["current_phase"] = _next_pending(state)

    save_state(proposal_dir, state)
    return state


def _next_pending(state: Dict[str, Any]) -> str:
    """Return the first phase whose status is not 'complete', or 'complete'."""
    for phase in PHASE_ORDER:
        if state["phases"][phase]["status"] != "complete":
            return phase
    return "complete"


# ── Resume / query helpers ──────────────────────────────────────────────────


def get_resume_phase(proposal_dir: str | Path) -> str:
    """Find the first non-complete phase.  Returns ``'complete'`` if all done."""
    state = load_state(proposal_dir)
    return _next_pending(state)


def get_sections_status(proposal_dir: str | Path) -> Dict[str, Dict[str, Any]]:
    """Scan ``sections/*.md`` and return ``{stem: {exists: True, words: N}}``."""
    sections_dir = Path(proposal_dir) / "sections"
    result: Dict[str, Dict[str, Any]] = {}
    if not sections_dir.is_dir():
        return result
    for md in sorted(sections_dir.glob("*.md")):
        text = md.read_text(errors="replace")
        word_count = len(text.split())
        result[md.stem] = {"exists": True, "words": word_count}
    return result


# ── Pretty printing ─────────────────────────────────────────────────────────


def print_status(proposal_dir: str | Path) -> None:
    """Print a human-readable status summary."""
    state = load_state(proposal_dir)

    print(f"Agency:    {state['agency']}")
    print(f"Mechanism: {state['mechanism']}")
    print(f"Language:  {state['language']}")
    print(f"Phase:     {state['current_phase']}")
    print()

    for phase in PHASE_ORDER:
        info = state["phases"][phase]
        status = info["status"]
        if status == "complete":
            icon = "✓"
        elif status == "in_progress":
            icon = "→"
        else:
            icon = " "
        extras = {k: v for k, v in info.items() if k != "status"}
        extra_str = f"  {extras}" if extras else ""
        print(f"  [{icon}] {phase}{extra_str}")

    # Section word counts
    sections = get_sections_status(proposal_dir)
    if sections:
        print()
        print("Sections:")
        for name, info in sections.items():
            print(f"  {name}: {info['words']} words")


# ── CLI ─────────────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Grant proposal state manager",
    )
    sub = parser.add_subparsers(dest="command")

    # init
    p_init = sub.add_parser("init", help="Initialise a new proposal directory")
    p_init.add_argument("--agency", required=True)
    p_init.add_argument("--mechanism", required=True)
    p_init.add_argument("--config", default=None, help="Path to config YAML")
    p_init.add_argument("--lang", default="en")

    # status
    p_status = sub.add_parser("status", help="Print proposal status")
    p_status.add_argument("proposal_dir")

    # update
    p_update = sub.add_parser("update", help="Update a phase status")
    p_update.add_argument("proposal_dir")
    p_update.add_argument("--phase", required=True)
    p_update.add_argument("--status", required=True)

    # resume
    p_resume = sub.add_parser("resume", help="Print the next phase to resume")
    p_resume.add_argument("proposal_dir")

    # sections
    p_sections = sub.add_parser("sections", help="Show section word counts")
    p_sections.add_argument("proposal_dir")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        init_proposal(args.agency, args.mechanism, args.config, args.lang)

    elif args.command == "status":
        print_status(args.proposal_dir)

    elif args.command == "update":
        update_phase(args.proposal_dir, args.phase, args.status)
        print_status(args.proposal_dir)

    elif args.command == "resume":
        print(get_resume_phase(args.proposal_dir))

    elif args.command == "sections":
        sections = get_sections_status(args.proposal_dir)
        if sections:
            for name, info in sections.items():
                print(f"{name}: {info['words']} words")
        else:
            print("No sections found.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
