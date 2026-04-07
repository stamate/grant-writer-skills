"""Load and query agency requirement manifests from templates/agencies/.

Each agency directory contains an ``agency.json`` manifest describing the
funding agency, required proposal sections, budget rules, formatting
constraints, and review criteria.

Usage as a library::

    from tools.agency_requirements import list_agencies, load_agency, find_agency

Usage from the command line::

    python -m tools.agency_requirements list
    python -m tools.agency_requirements info horizon_ria
    python -m tools.agency_requirements sections uefiscdi_pce
    python -m tools.agency_requirements budget erc
    python -m tools.agency_requirements review-criteria pnrr
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "agencies"


# ── Core loaders ────────────────────────────────────────────────────────────


def list_agencies() -> List[Dict[str, Any]]:
    """Return a summary list of every agency manifest found in *TEMPLATES_DIR*.

    Each entry is a dict with keys: ``key``, ``agency``, ``mechanism``,
    ``name``, and ``region``.
    """
    results: List[Dict[str, Any]] = []
    if not TEMPLATES_DIR.is_dir():
        return results
    for entry in sorted(TEMPLATES_DIR.iterdir()):
        manifest = entry / "agency.json"
        if entry.is_dir() and manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            results.append({
                "key": entry.name,
                "agency": data.get("agency"),
                "mechanism": data.get("mechanism"),
                "name": data.get("name"),
                "region": data.get("region"),
            })
    return results


def load_agency(agency_key: str) -> Dict[str, Any]:
    """Load a full agency manifest by directory name.

    If *agency_key* is not a direct directory match, falls back to scanning
    every manifest for a matching ``agency`` field.

    Raises ``FileNotFoundError`` if no match is found.
    """
    # Direct lookup by directory name
    direct = TEMPLATES_DIR / agency_key / "agency.json"
    if direct.exists():
        return json.loads(direct.read_text(encoding="utf-8"))

    # Fallback: scan all manifests for a matching agency field
    for entry in sorted(TEMPLATES_DIR.iterdir()):
        manifest = entry / "agency.json"
        if entry.is_dir() and manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            if data.get("agency") == agency_key:
                return data

    raise FileNotFoundError(f"No agency manifest found for key '{agency_key}'")


def find_agency(agency: str, mechanism: Optional[str] = None) -> Dict[str, Any]:
    """Find a manifest by *agency* and optional *mechanism*.

    Search order:
    1. ``{agency}_{mechanism}`` as directory name
    2. ``{agency}`` as directory name
    3. ``{mechanism}`` as directory name
    4. Full scan matching agency + mechanism fields

    Raises ``FileNotFoundError`` if no match is found.
    """
    candidates: List[str] = []
    if mechanism:
        candidates.append(f"{agency}_{mechanism}".lower().replace(" ", "_"))
    candidates.append(agency.lower())
    if mechanism:
        candidates.append(mechanism.lower().replace(" ", "_"))

    # Try direct directory matches first
    for candidate in candidates:
        manifest = TEMPLATES_DIR / candidate / "agency.json"
        if manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            # If mechanism was specified, verify it matches (case-insensitive)
            if mechanism:
                m = data.get("mechanism", "")
                if m.lower() == mechanism.lower():
                    return data
            else:
                return data

    # Try again without mechanism check for direct hits
    for candidate in candidates:
        manifest = TEMPLATES_DIR / candidate / "agency.json"
        if manifest.exists():
            return json.loads(manifest.read_text(encoding="utf-8"))

    # Full scan
    for entry in sorted(TEMPLATES_DIR.iterdir()):
        manifest = entry / "agency.json"
        if entry.is_dir() and manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            if data.get("agency", "").lower() == agency.lower():
                if mechanism is None:
                    return data
                if data.get("mechanism", "").lower() == mechanism.lower():
                    return data

    raise FileNotFoundError(
        f"No agency manifest found for agency='{agency}'"
        + (f", mechanism='{mechanism}'" if mechanism else "")
    )


# ── Convenience accessors ──────────────────────────────────────────────────


def get_sections(agency_key: str) -> List[Dict[str, Any]]:
    """Return the ``sections`` list from the manifest for *agency_key*."""
    return load_agency(agency_key).get("sections", [])


def get_budget_rules(agency_key: str) -> Dict[str, Any]:
    """Return the ``budget`` dict from the manifest for *agency_key*."""
    return load_agency(agency_key).get("budget", {})


def get_review_criteria(agency_key: str) -> List[str]:
    """Return the ``review_criteria`` list from the manifest for *agency_key*."""
    return load_agency(agency_key).get("review_criteria", [])


def get_section_templates(agency_key: str) -> Dict[str, str]:
    """Load all ``.md`` files from the agency directory as section templates.

    Returns a dict mapping filename (without extension) to file contents.
    """
    agency_dir = TEMPLATES_DIR / agency_key
    if not agency_dir.is_dir():
        # Fallback: scan for matching agency field
        for entry in sorted(TEMPLATES_DIR.iterdir()):
            manifest = entry / "agency.json"
            if entry.is_dir() and manifest.exists():
                data = json.loads(manifest.read_text(encoding="utf-8"))
                if data.get("agency") == agency_key:
                    agency_dir = entry
                    break
        else:
            return {}

    templates: Dict[str, str] = {}
    for md_file in sorted(agency_dir.glob("*.md")):
        templates[md_file.stem] = md_file.read_text(encoding="utf-8")
    return templates


# ── CLI ─────────────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Query agency requirement manifests",
    )
    sub = parser.add_subparsers(dest="command")

    # list
    sub.add_parser("list", help="List all available agency manifests")

    # info
    p_info = sub.add_parser("info", help="Show full manifest for an agency")
    p_info.add_argument("agency", help="Agency key or name")
    p_info.add_argument("mechanism", nargs="?", default=None, help="Mechanism (optional)")

    # sections
    p_sec = sub.add_parser("sections", help="Show required sections")
    p_sec.add_argument("agency", help="Agency key or name")
    p_sec.add_argument("mechanism", nargs="?", default=None, help="Mechanism (optional)")

    # budget
    p_bud = sub.add_parser("budget", help="Show budget rules")
    p_bud.add_argument("agency", help="Agency key or name")
    p_bud.add_argument("mechanism", nargs="?", default=None, help="Mechanism (optional)")

    # review-criteria
    p_rev = sub.add_parser("review-criteria", help="Show review criteria")
    p_rev.add_argument("agency", help="Agency key or name")
    p_rev.add_argument("mechanism", nargs="?", default=None, help="Mechanism (optional)")

    return parser


def _resolve(agency: str, mechanism: Optional[str] = None) -> Dict[str, Any]:
    """Try to resolve an agency manifest by key or agency+mechanism."""
    try:
        return find_agency(agency, mechanism)
    except FileNotFoundError:
        return load_agency(agency)


def main(argv: Optional[List[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "list":
        agencies = list_agencies()
        if not agencies:
            print("No agency manifests found.")
            return
        fmt = "{:<20s} {:<10s} {:<30s} {:<40s} {:<10s}"
        print(fmt.format("KEY", "AGENCY", "MECHANISM", "NAME", "REGION"))
        print("-" * 112)
        for a in agencies:
            print(fmt.format(
                a["key"],
                a.get("agency", ""),
                a.get("mechanism", ""),
                a.get("name", ""),
                a.get("region", ""),
            ))
        return

    # All other commands need an agency
    data = _resolve(args.agency, getattr(args, "mechanism", None))

    if args.command == "info":
        print(json.dumps(data, indent=2, ensure_ascii=False))

    elif args.command == "sections":
        sections = data.get("sections", [])
        fmt = "{:<25s} {:>8s}  {:<10s}"
        print(fmt.format("SECTION", "WORDS", "REQUIRED"))
        print("-" * 46)
        for s in sections:
            words = str(s.get("words")) if s.get("words") is not None else "—"
            req = "yes" if s.get("required") else "no"
            print(fmt.format(s["name"], words, req))

    elif args.command == "budget":
        budget = data.get("budget", {})
        print(json.dumps(budget, indent=2, ensure_ascii=False))

    elif args.command == "review-criteria":
        criteria = data.get("review_criteria", [])
        weights = data.get("review_weights", {})
        for c in criteria:
            w = weights.get(c)
            if w is not None:
                print(f"  - {c} ({w}%)")
            else:
                print(f"  - {c}")


if __name__ == "__main__":
    main()
