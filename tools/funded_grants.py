"""Query public funding databases for competitive intelligence on funded grants.

Backend: OpenAIRE API (api.openaire.eu) — free, no API key required.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

import backoff
import requests


# ── OpenAIRE API ────────────────────────────────────────────────────────────

OPENAIRE_BASE = "https://api.openaire.eu/search/projects"

# Map user-friendly agency names to OpenAIRE funder codes / funding streams
AGENCY_MAP = {
    "horizon": {"funder": "EC", "fundingStream": "H2020"},
    "erc": {"funder": "EC", "fundingStream": "FP7,H2020"},
    "msca": {"funder": "EC", "fundingStream": "H2020"},
    "ec": {"funder": "EC"},
}


class OpenAIREError(Exception):
    """Raised on non-recoverable OpenAIRE API errors."""


def _is_retryable(exc: Exception) -> bool:
    """Return True for HTTP errors worth retrying (429, 5xx)."""
    if isinstance(exc, requests.exceptions.HTTPError):
        code = exc.response.status_code if exc.response is not None else 0
        return code == 429 or code >= 500
    return isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.Timeout))


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.RequestException,),
    max_tries=4,
    giveup=lambda e: not _is_retryable(e),
    jitter=backoff.full_jitter,
)
def _openaire_request(params: dict) -> dict:
    """Make a single request to the OpenAIRE search API and return parsed JSON."""
    params["format"] = "json"
    resp = requests.get(OPENAIRE_BASE, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _unwrap(value):
    """Unwrap OpenAIRE's {"$": actual_value} wrapper pattern."""
    if isinstance(value, dict):
        if "$" in value:
            return value["$"]
        if "#text" in value:
            return value["#text"]
    return value


def _parse_openaire_projects(data: dict) -> List[Dict[str, Any]]:
    """Extract structured project records from the OpenAIRE JSON response."""
    projects: List[Dict[str, Any]] = []

    # Navigate the nested response structure
    response = data.get("response", {})
    results = response.get("results", {})

    # results can be None when no hits
    if not results:
        return projects

    result_list = results.get("result", [])
    if not isinstance(result_list, list):
        result_list = [result_list]

    for item in result_list:
        metadata = item.get("metadata", {}).get("oaf:entity", {}).get("oaf:project", {})
        if not metadata:
            continue

        # Code / title
        code = str(_unwrap(metadata.get("code", "")))
        title = str(_unwrap(metadata.get("title", "")))

        # Dates
        start_date = str(_unwrap(metadata.get("startdate", "")))
        end_date = str(_unwrap(metadata.get("enddate", "")))

        # Funding
        fundingtree = metadata.get("fundingtree", {})
        programme = ""
        if isinstance(fundingtree, dict):
            funder = fundingtree.get("funder", {})
            programme = str(_unwrap(funder.get("shortname", "")))
        elif isinstance(fundingtree, list) and fundingtree:
            funder = fundingtree[0].get("funder", {})
            programme = str(_unwrap(funder.get("shortname", "")))

        # Budget
        total_cost = _unwrap(metadata.get("totalcost", ""))
        funded_amount = _unwrap(metadata.get("fundedamount", ""))

        # Relations — try to find coordinator / PI
        rels = metadata.get("rels", {})
        coordinator = ""
        institution = ""
        if rels:
            rel_list = rels.get("rel", [])
            if not isinstance(rel_list, list):
                rel_list = [rel_list]
            for rel in rel_list:
                rel_to = rel.get("to", {})
                rel_class = str(_unwrap(rel.get("class", "")))
                if rel_class in ("isCoordinatedBy", "hasParticipant") and not coordinator:
                    coordinator = str(_unwrap(rel_to.get("legalname", "")))
                    institution = coordinator

        # Abstract
        abstract = str(_unwrap(metadata.get("summary", "")))

        project_record = {
            "title": title,
            "project_id": code,
            "coordinator": coordinator,
            "institution": institution,
            "funded_amount": funded_amount,
            "total_cost": total_cost,
            "start_date": start_date,
            "end_date": end_date,
            "programme": programme,
            "abstract": str(abstract)[:500] if abstract else "",
        }
        projects.append(project_record)

    return projects


# ── Public API ──────────────────────────────────────────────────────────────


def search_openaire(
    query: str,
    funder: str = "EC",
    years: Optional[tuple] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Search OpenAIRE for funded projects.

    Parameters
    ----------
    query : str
        Free-text keyword search.
    funder : str
        Funder code (default "EC" for European Commission).
    years : tuple[int, int] | None
        Optional (start_year, end_year) range filter.
    limit : int
        Max results to return (default 20).

    Returns
    -------
    list[dict]
        Parsed project records.
    """
    params: Dict[str, Any] = {
        "keywords": query,
        "funder": funder,
        "size": min(limit, 100),
    }

    if years:
        params["startYear"] = years[0]
        params["endYear"] = years[1]

    try:
        data = _openaire_request(params)
        return _parse_openaire_projects(data)
    except requests.exceptions.RequestException as exc:
        print(f"WARNING: OpenAIRE request failed: {exc}", file=sys.stderr)
        return []


def search_uefiscdi(query: str, limit: int = 10) -> None:
    """Search UEFISCDI for Romanian grants.

    Returns None — UEFISCDI has no public API.
    The skill layer should fall back to WebSearch.
    """
    print(
        "UEFISCDI has no public API \u2014 use WebSearch fallback at skill level.",
        file=sys.stderr,
    )
    return None


def search_pi_grants(
    pi_name: str,
    agency: str = "horizon",
) -> List[Dict[str, Any]]:
    """Search for a specific PI's funded grants via OpenAIRE.

    Parameters
    ----------
    pi_name : str
        Full name of the principal investigator.
    agency : str
        Agency key (horizon, erc, msca, ec).

    Returns
    -------
    list[dict]
        Matching project records.
    """
    mapping = AGENCY_MAP.get(agency.lower(), {"funder": "EC"})
    funder = mapping.get("funder", "EC")
    return search_openaire(pi_name, funder=funder, limit=20)


def format_results(projects: List[Dict[str, Any]]) -> str:
    """Render project records as human-readable text.

    Parameters
    ----------
    projects : list[dict]
        Records from search_openaire / search_pi_grants.

    Returns
    -------
    str
        Formatted multi-line summary.
    """
    if not projects:
        return "No projects found."

    lines: list[str] = []
    for i, p in enumerate(projects, 1):
        lines.append(f"{'=' * 60}")
        lines.append(f"[{i}] {p.get('title', 'Untitled')}")
        if p.get("project_id"):
            lines.append(f"    Project ID : {p['project_id']}")
        if p.get("coordinator"):
            lines.append(f"    Coordinator: {p['coordinator']}")
        if p.get("institution") and p["institution"] != p.get("coordinator"):
            lines.append(f"    Institution: {p['institution']}")
        if p.get("funded_amount"):
            lines.append(f"    Funded     : {p['funded_amount']} EUR")
        if p.get("total_cost"):
            lines.append(f"    Total cost : {p['total_cost']} EUR")
        dates = []
        if p.get("start_date"):
            dates.append(p["start_date"])
        if p.get("end_date"):
            dates.append(p["end_date"])
        if dates:
            lines.append(f"    Dates      : {' \u2013 '.join(dates)}")
        if p.get("programme"):
            lines.append(f"    Programme  : {p['programme']}")
        if p.get("abstract"):
            lines.append(f"    Abstract   : {p['abstract'][:200]}...")
        lines.append("")

    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────────────────────────


def _parse_years(years_str: str) -> tuple:
    """Parse 'START-END' into (int, int)."""
    parts = years_str.split("-")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"Years must be START-END, got: {years_str}")
    return (int(parts[0]), int(parts[1]))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Search public funding databases for funded grants.",
    )
    sub = parser.add_subparsers(dest="command")

    # search sub-command
    sp_search = sub.add_parser("search", help="Search for funded projects")
    sp_search.add_argument("query", help="Search keywords")
    sp_search.add_argument(
        "--agency",
        default="horizon",
        choices=["horizon", "erc", "msca", "ec", "uefiscdi"],
        help="Funding agency (default: horizon)",
    )
    sp_search.add_argument("--years", type=_parse_years, default=None, help="Year range START-END")
    sp_search.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")
    sp_search.add_argument("--text", action="store_true", help="Output formatted text instead of JSON")

    # pi-grants sub-command
    sp_pi = sub.add_parser("pi-grants", help="Search grants for a specific PI")
    sp_pi.add_argument("pi_name", help="PI full name")
    sp_pi.add_argument("--agency", default="horizon", help="Agency key (default: horizon)")
    sp_pi.add_argument("--text", action="store_true", help="Output formatted text instead of JSON")

    args = parser.parse_args(argv)

    if args.command == "search":
        # UEFISCDI has no API
        if args.agency == "uefiscdi":
            search_uefiscdi(args.query)
            return

        mapping = AGENCY_MAP.get(args.agency, {"funder": "EC"})
        funder = mapping.get("funder", "EC")
        projects = search_openaire(args.query, funder=funder, years=args.years, limit=args.limit)

        if args.text:
            print(format_results(projects))
        else:
            print(json.dumps(projects, indent=2, ensure_ascii=False))

    elif args.command == "pi-grants":
        projects = search_pi_grants(args.pi_name, agency=args.agency)
        if args.text:
            print(format_results(projects))
        else:
            print(json.dumps(projects, indent=2, ensure_ascii=False))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
