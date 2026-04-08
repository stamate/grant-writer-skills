"""Validate proposal structure against agency requirements.

Checks word counts, required sections, bibliography, figure references,
and budget caps against the agency JSON specification.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# ── Import agency loader from sibling module ────────────────────────────────
# agency_requirements.py is built by Task 4 (parallel) — import defensively.

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from agency_requirements import load_agency
except ImportError:
    # Fallback: load agency.json directly from templates
    def load_agency(agency_key: str) -> dict:
        """Fallback loader when agency_requirements.py is not yet available."""
        templates_dir = Path(__file__).resolve().parent.parent / "templates" / "agencies"
        # Try exact match first, then prefix match
        candidates = [
            templates_dir / agency_key / "agency.json",
        ]
        # Also try agency dirs that start with the key
        if templates_dir.exists():
            for d in sorted(templates_dir.iterdir()):
                if d.is_dir() and d.name.startswith(agency_key):
                    candidates.append(d / "agency.json")

        for path in candidates:
            if path.exists():
                with open(path) as f:
                    return json.load(f)

        raise FileNotFoundError(
            f"No agency.json found for key '{agency_key}' in {templates_dir}"
        )


# ── Word counting ───────────────────────────────────────────────────────────


def count_words_md(text: str) -> int:
    """Count words in Markdown text, excluding syntax.

    Strips HTML comments, image refs, link syntax (keeps text), header markers,
    emphasis, table pipes, and horizontal rules before counting.
    """
    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    # Remove image references
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # Remove link syntax but keep text
    text = re.sub(r'\[([^\]]+)\]\(.*?\)', r'\1', text)
    # Remove header markers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove emphasis markers
    text = re.sub(r'[*_]{1,3}', '', text)
    # Remove table pipes
    text = re.sub(r'\|', ' ', text)
    # Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    return len(text.split())


# ── Individual checks ───────────────────────────────────────────────────────


def check_word_counts(
    proposal_dir: str,
    agency_data: dict,
) -> List[Dict[str, Any]]:
    """Check word counts per section against agency limits.

    Parameters
    ----------
    proposal_dir : str
        Path to the proposal directory (contains sections/*.md).
    agency_data : dict
        Loaded agency.json data.

    Returns
    -------
    list[dict]
        Per-section results with status pass/warning/fail.
    """
    sections_dir = Path(proposal_dir) / "sections"
    results: List[Dict[str, Any]] = []
    sections = agency_data.get("sections", [])

    for sec in sections:
        name = sec["name"]
        limit = sec.get("words")
        if limit is None:
            continue  # No word limit for this section

        # Look for matching .md file
        md_path = sections_dir / f"{name}.md"
        if not md_path.exists():
            results.append({
                "section": name,
                "words": 0,
                "limit": limit,
                "status": "fail",
                "message": f"Section file missing: {name}.md",
            })
            continue

        text = md_path.read_text(encoding="utf-8")
        words = count_words_md(text)

        if words > limit:
            pct_over = ((words - limit) / limit) * 100
            status = "fail" if pct_over > 10 else "warning"
            message = f"{words} words exceeds {limit} limit by {pct_over:.0f}%"
        elif words < limit * 0.5:
            status = "warning"
            message = f"Only {words}/{limit} words ({words/limit*100:.0f}%) \u2014 section may be underdeveloped"
        else:
            status = "pass"
            message = f"{words}/{limit} words"

        results.append({
            "section": name,
            "words": words,
            "limit": limit,
            "status": status,
            "message": message,
        })

    return results


def check_required_sections(
    proposal_dir: str,
    agency_data: dict,
) -> List[Dict[str, Any]]:
    """Verify all required sections from agency.json exist as .md files.

    Parameters
    ----------
    proposal_dir : str
        Path to the proposal directory.
    agency_data : dict
        Loaded agency.json data.

    Returns
    -------
    list[dict]
        Per-section existence check results.
    """
    sections_dir = Path(proposal_dir) / "sections"
    results: List[Dict[str, Any]] = []
    sections = agency_data.get("sections", [])

    for sec in sections:
        name = sec["name"]
        required = sec.get("required", False)
        md_path = sections_dir / f"{name}.md"

        if md_path.exists():
            results.append({
                "section": name,
                "required": required,
                "status": "pass",
                "message": f"Found {name}.md",
            })
        elif required:
            results.append({
                "section": name,
                "required": required,
                "status": "fail",
                "message": f"Required section missing: {name}.md",
            })
        else:
            results.append({
                "section": name,
                "required": required,
                "status": "warning",
                "message": f"Optional section missing: {name}.md",
            })

    return results


def check_bibliography(proposal_dir: str) -> Dict[str, Any]:
    """Verify that all citation references in sections have bibliography entries.

    Supports both numbered [N] and (Author, Year) citation styles.

    Parameters
    ----------
    proposal_dir : str
        Path to the proposal directory.

    Returns
    -------
    dict
        Citation check results including unresolved references.
    """
    sections_dir = Path(proposal_dir) / "sections"
    bib_path = sections_dir / "bibliography.md"

    # Collect all citations from section files
    citations_numbered: set = set()
    citations_author_year: set = set()

    if not sections_dir.exists():
        return {
            "total_citations": 0,
            "unresolved": [],
            "status": "warning",
            "message": "No sections directory found",
        }

    for md_file in sorted(sections_dir.glob("*.md")):
        if md_file.name == "bibliography.md":
            continue
        text = md_file.read_text(encoding="utf-8")

        # Numbered citations: [1], [2], [12]
        for m in re.finditer(r'\[(\d+)\]', text):
            citations_numbered.add(int(m.group(1)))

        # Author-year: (Author, Year) or (Author et al., Year)
        for m in re.finditer(r'\(([A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s*\d{4})\)', text):
            citations_author_year.add(m.group(1).strip())

    total = len(citations_numbered) + len(citations_author_year)

    if not bib_path.exists():
        if total > 0:
            return {
                "total_citations": total,
                "unresolved": list(citations_numbered) + list(citations_author_year),
                "status": "fail",
                "message": f"bibliography.md missing but {total} citations found in sections",
            }
        return {
            "total_citations": 0,
            "unresolved": [],
            "status": "pass",
            "message": "No citations and no bibliography (OK for sections without references)",
        }

    bib_text = bib_path.read_text(encoding="utf-8")

    # Check numbered citations
    unresolved_numbered = []
    for num in sorted(citations_numbered):
        # Look for [N] at start of a line or after whitespace in bibliography
        pattern = rf'\[{num}\]'
        if not re.search(pattern, bib_text):
            unresolved_numbered.append(num)

    # Check author-year citations
    unresolved_author = []
    for cite in sorted(citations_author_year):
        # Check if author name appears in bibliography
        author = cite.split(",")[0].strip()
        if author not in bib_text:
            unresolved_author.append(cite)

    unresolved: list = unresolved_numbered + unresolved_author

    if unresolved:
        status = "warning" if len(unresolved) <= 3 else "fail"
        message = f"{len(unresolved)} unresolved citation(s) out of {total}"
    else:
        status = "pass"
        message = f"All {total} citations resolved"

    return {
        "total_citations": total,
        "unresolved": unresolved,
        "status": status,
        "message": message,
    }


def check_figures(proposal_dir: str) -> List[Dict[str, Any]]:
    """Verify that all figure references in sections point to existing files.

    Looks for ![...](figures/...) references in section .md files.

    Parameters
    ----------
    proposal_dir : str
        Path to the proposal directory.

    Returns
    -------
    list[dict]
        Per-reference results with existence status.
    """
    sections_dir = Path(proposal_dir) / "sections"
    results: List[Dict[str, Any]] = []

    if not sections_dir.exists():
        return results

    for md_file in sorted(sections_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")

        for m in re.finditer(r'!\[([^\]]*)\]\((figures/[^)]+)\)', text):
            alt_text = m.group(1)
            fig_path_str = m.group(2)
            fig_path = sections_dir / fig_path_str
            exists = fig_path.exists()

            results.append({
                "reference": f"![{alt_text}]({fig_path_str})",
                "file": str(fig_path),
                "source": md_file.name,
                "exists": exists,
                "status": "pass" if exists else "fail",
            })

    return results


def check_budget(
    proposal_dir: str,
    agency_data: dict,
) -> Dict[str, Any]:
    """Check budget total against agency caps.

    Simple parsing of a Markdown table looking for a 'Total' row.

    Parameters
    ----------
    proposal_dir : str
        Path to the proposal directory.
    agency_data : dict
        Loaded agency.json data.

    Returns
    -------
    dict
        Budget check result.
    """
    budget_path = Path(proposal_dir) / "budget.md"
    if not budget_path.exists():
        # Also check sections/budget_justification.md
        budget_path = Path(proposal_dir) / "sections" / "budget_justification.md"
        if not budget_path.exists():
            return {
                "status": "warning",
                "message": "No budget.md or budget_justification.md found",
                "total_found": None,
                "caps": {},
            }

    text = budget_path.read_text(encoding="utf-8")

    # Find total in Markdown table: look for row containing "Total" or "TOTAL"
    total_found = None
    for line in text.splitlines():
        if re.search(r'\btotal\b', line, re.IGNORECASE) and '|' in line:
            # Extract numbers from the line
            numbers = re.findall(r'[\d,]+\.?\d*', line.replace(',', ''))
            if numbers:
                try:
                    total_found = float(numbers[-1])  # Take last number (usually the total)
                except ValueError:
                    pass

    # Extract caps from agency data
    budget_info = agency_data.get("budget", {})
    caps = {}
    for key, val in budget_info.items():
        if key.startswith("max_") and val is not None:
            caps[key] = val

    if total_found is None:
        return {
            "status": "warning",
            "message": "Could not parse budget total from table",
            "total_found": None,
            "caps": caps,
        }

    # Check against caps
    violations = []
    for cap_name, cap_val in caps.items():
        if isinstance(cap_val, (int, float)) and total_found > cap_val:
            violations.append(f"Budget {total_found:,.0f} exceeds {cap_name}={cap_val:,.0f}")

    if violations:
        status = "fail"
        message = "; ".join(violations)
    else:
        status = "pass"
        message = f"Budget total {total_found:,.0f} within caps"

    return {
        "status": status,
        "message": message,
        "total_found": total_found,
        "caps": caps,
    }


# ── Run all checks ─────────────────────────────────────────────────────────


def run_all_checks(
    proposal_dir: str,
    agency_key: str,
) -> Dict[str, Any]:
    """Run all compliance checks and return a structured report.

    Parameters
    ----------
    proposal_dir : str
        Path to the proposal directory.
    agency_key : str
        Agency identifier (e.g. 'horizon_ria', 'erc', 'uefiscdi_pce').

    Returns
    -------
    dict
        Full compliance report with per-check results and overall status.
    """
    agency_data = load_agency(agency_key)

    word_counts = check_word_counts(proposal_dir, agency_data)
    required = check_required_sections(proposal_dir, agency_data)
    bib = check_bibliography(proposal_dir)
    figures = check_figures(proposal_dir)
    budget = check_budget(proposal_dir, agency_data)

    # Determine severity levels
    checks = {
        "word_counts": {
            "severity": "critical",
            "results": word_counts,
        },
        "required_sections": {
            "severity": "critical",
            "results": required,
        },
        "bibliography": {
            "severity": "warning",
            "results": bib,
        },
        "figures": {
            "severity": "warning",
            "results": figures,
        },
        "budget": {
            "severity": "critical",
            "results": budget,
        },
    }

    # Overall pass/fail
    has_fail = False
    has_warning = False

    for check_name, check in checks.items():
        res = check["results"]
        if isinstance(res, list):
            for item in res:
                st = item.get("status", "pass")
                if st == "fail":
                    has_fail = True
                elif st == "warning":
                    has_warning = True
        elif isinstance(res, dict):
            st = res.get("status", "pass")
            if st == "fail":
                has_fail = True
            elif st == "warning":
                has_warning = True

    if has_fail:
        overall = "FAIL"
    elif has_warning:
        overall = "WARNING"
    else:
        overall = "PASS"

    return {
        "agency": agency_key,
        "agency_name": agency_data.get("name", agency_key),
        "proposal_dir": str(proposal_dir),
        "overall": overall,
        "checks": checks,
    }


# ── CLI ─────────────────────────────────────────────────────────────────────


def _format_report(report: dict) -> str:
    """Render a compliance report as human-readable text."""
    lines = [
        f"Compliance Report: {report['agency_name']}",
        f"Proposal: {report['proposal_dir']}",
        f"Overall: {report['overall']}",
        "=" * 60,
    ]

    for check_name, check in report["checks"].items():
        severity = check["severity"]
        results = check["results"]
        lines.append(f"\n--- {check_name.upper()} (severity: {severity}) ---")

        if isinstance(results, list):
            for item in results:
                status = item.get("status", "?")
                marker = {"pass": "+", "warning": "~", "fail": "!!"}.get(status, "?")
                msg = item.get("message", "")
                section = item.get("section", item.get("reference", ""))
                lines.append(f"  [{marker}] {section}: {msg}")
        elif isinstance(results, dict):
            status = results.get("status", "?")
            marker = {"pass": "+", "warning": "~", "fail": "!!"}.get(status, "?")
            msg = results.get("message", "")
            lines.append(f"  [{marker}] {msg}")

    return "\n".join(lines)


def _detect_agency(proposal_dir: str) -> Optional[str]:
    """Auto-detect agency key from proposal config.yaml or state.json.

    Tries ``{agency}_{mechanism}`` first (e.g. ``uefiscdi_pce``), then
    just ``{agency}`` (e.g. ``erc`` when template dir is ``erc/`` not
    ``erc_starting/``).  Validates that ``load_agency`` can resolve the
    key before returning it.
    """
    pdir = Path(proposal_dir)
    agency = ""
    mechanism = ""

    # Try config.yaml first, then state.json
    for filename in ("config.yaml", "state.json"):
        fpath = pdir / filename
        if not fpath.exists():
            continue
        try:
            if filename.endswith(".yaml"):
                import yaml
                data = yaml.safe_load(fpath.read_text()) or {}
            else:
                data = json.loads(fpath.read_text())
            agency = data.get("agency", "")
            mechanism = data.get("mechanism", "")
            if agency:
                break
        except Exception:
            continue

    if not agency:
        return None

    # Try compound key first, then bare agency name
    for candidate in [f"{agency}_{mechanism}", agency] if mechanism else [agency]:
        try:
            load_agency(candidate)
            return candidate
        except FileNotFoundError:
            continue

    return None


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Compliance checker for grant proposals.",
    )
    sub = parser.add_subparsers(dest="command")

    # check (full)
    sp_check = sub.add_parser("check", help="Run all compliance checks")
    sp_check.add_argument("proposal_dir", help="Path to proposal directory")
    sp_check.add_argument(
        "--agency",
        default=None,
        help="Agency key (e.g. horizon_ria, erc, uefiscdi_pce). Auto-detected from proposal config if omitted.",
    )
    sp_check.add_argument("--json", action="store_true", dest="json_output", help="Output JSON instead of text")

    # word-counts
    sp_wc = sub.add_parser("word-counts", help="Check word counts per section")
    sp_wc.add_argument("proposal_dir", help="Path to proposal directory")
    sp_wc.add_argument("--agency", default=None, help="Agency key (auto-detected if omitted)")

    # budget-check
    sp_budget = sub.add_parser("budget-check", help="Validate budget against caps")
    sp_budget.add_argument("proposal_dir", help="Path to proposal directory")
    sp_budget.add_argument("--agency", default=None, help="Agency key (auto-detected if omitted)")

    args = parser.parse_args(argv)

    # Auto-detect agency from proposal config.yaml or state.json if not provided
    if hasattr(args, "agency") and args.agency is None and hasattr(args, "proposal_dir"):
        agency_key = _detect_agency(args.proposal_dir)
        if agency_key is None:
            print("Error: Cannot detect agency. Provide --agency or ensure proposal has config.yaml/state.json.", file=sys.stderr)
            sys.exit(1)
        args.agency = agency_key

    if args.command == "check":
        report = run_all_checks(args.proposal_dir, args.agency)
        if args.json_output:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(_format_report(report))

    elif args.command == "word-counts":
        agency_data = load_agency(args.agency)
        results = check_word_counts(args.proposal_dir, agency_data)
        print(json.dumps(results, indent=2, ensure_ascii=False))

    elif args.command == "budget-check":
        agency_data = load_agency(args.agency)
        result = check_budget(args.proposal_dir, agency_data)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
