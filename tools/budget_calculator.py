"""Budget arithmetic and formatting for EU and Romanian grant proposals.

Supports two models:
- Person-months (EU agencies: Horizon, ERC, MSCA)
- Monthly salary (Romanian agencies: UEFISCDI, PNRR)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# ── Person-months model (EU) ────────────────────────────────────────────────


def calculate_person_months(budget_input: dict) -> dict:
    """Calculate budget using the EU person-months model.

    Parameters
    ----------
    budget_input : dict
        Must contain 'model': 'person_months' plus personnel list and cost items.

    Returns
    -------
    dict
        Structured budget result with totals and breakdowns.
    """
    currency = budget_input.get("currency", "EUR")
    indirect_rate = budget_input.get("indirect_rate", 0.25)

    # Personnel
    personnel = budget_input.get("personnel", [])
    personnel_breakdown = []
    personnel_total = 0.0
    for person in personnel:
        cost = person["pm"] * person["unit_cost"]
        personnel_total += cost
        personnel_breakdown.append({
            "name": person["name"],
            "person_months": person["pm"],
            "unit_cost": person["unit_cost"],
            "total": cost,
        })

    # Other direct costs
    subcontracting = budget_input.get("subcontracting", 0)
    travel = budget_input.get("travel", 0)
    equipment = budget_input.get("equipment", 0)
    other_goods = budget_input.get("other_goods", 0)

    other_direct = travel + equipment + other_goods
    total_direct = personnel_total + subcontracting + other_direct

    # Indirect costs: 25% of (total_direct - subcontracting) per EU flat-rate
    indirect_base = total_direct - subcontracting
    indirect = indirect_rate * indirect_base

    total = total_direct + indirect

    return {
        "model": "person_months",
        "currency": currency,
        "personnel_total": personnel_total,
        "subcontracting": subcontracting,
        "other_direct": other_direct,
        "total_direct": total_direct,
        "indirect": round(indirect, 2),
        "indirect_rate": indirect_rate,
        "total": round(total, 2),
        "breakdown": {
            "personnel": personnel_breakdown,
            "travel": travel,
            "equipment": equipment,
            "other_goods": other_goods,
            "subcontracting": subcontracting,
        },
    }


# ── Monthly salary model (Romania) ─────────────────────────────────────────


def calculate_monthly_salary(budget_input: dict) -> dict:
    """Calculate budget using the Romanian monthly-salary model.

    Parameters
    ----------
    budget_input : dict
        Must contain 'model': 'monthly_salary' plus personnel and cost items.

    Returns
    -------
    dict
        Structured budget result with totals, per-year breakdown, and details.
    """
    currency = budget_input.get("currency", "RON")
    indirect_rate_cap = budget_input.get("indirect_rate_cap", 0.25)
    years = budget_input.get("years", 3)

    # Personnel
    personnel = budget_input.get("personnel", [])
    personnel_breakdown = []
    personnel_total = 0.0
    for person in personnel:
        monthly = person["monthly_salary"]
        effort = person.get("effort_pct", 100) / 100.0
        months = person.get("months", years * 12)
        cost = monthly * effort * months
        personnel_total += cost
        personnel_breakdown.append({
            "name": person["name"],
            "monthly_salary": monthly,
            "effort_pct": person.get("effort_pct", 100),
            "months": months,
            "total": cost,
        })

    # Other direct costs
    mobility = budget_input.get("mobility", 0)
    equipment = budget_input.get("equipment", 0)
    consumables = budget_input.get("consumables", 0)

    total_direct = personnel_total + mobility + equipment + consumables

    # Indirect: capped at indirect_rate_cap * total_direct
    indirect = indirect_rate_cap * total_direct

    total = total_direct + indirect

    # Per-year breakdown (simple equal distribution)
    per_year: List[Dict[str, Any]] = []
    for y in range(1, years + 1):
        year_share = {
            "year": y,
            "personnel": round(personnel_total / years, 2),
            "mobility": round(mobility / years, 2),
            "equipment": round(equipment / years, 2),
            "consumables": round(consumables / years, 2),
            "direct": round(total_direct / years, 2),
            "indirect": round(indirect / years, 2),
            "total": round(total / years, 2),
        }
        per_year.append(year_share)

    return {
        "model": "monthly_salary",
        "currency": currency,
        "personnel_total": personnel_total,
        "mobility": mobility,
        "equipment": equipment,
        "consumables": consumables,
        "total_direct": total_direct,
        "indirect": round(indirect, 2),
        "indirect_rate_cap": indirect_rate_cap,
        "total": round(total, 2),
        "per_year": per_year,
        "breakdown": {
            "personnel": personnel_breakdown,
            "mobility": mobility,
            "equipment": equipment,
            "consumables": consumables,
        },
    }


# ── Dispatcher ──────────────────────────────────────────────────────────────


def calculate(budget_input: dict) -> dict:
    """Dispatch to the correct budget model based on budget_input['model'].

    Parameters
    ----------
    budget_input : dict
        Must include 'model' key: 'person_months' or 'monthly_salary'.

    Returns
    -------
    dict
        Budget calculation result.

    Raises
    ------
    ValueError
        If model is unrecognised.
    """
    model = budget_input.get("model", "")
    if model == "person_months":
        return calculate_person_months(budget_input)
    elif model == "monthly_salary":
        return calculate_monthly_salary(budget_input)
    else:
        raise ValueError(f"Unknown budget model: {model!r}. Use 'person_months' or 'monthly_salary'.")


# ── YAML loader ─────────────────────────────────────────────────────────────


def load_budget_input(yaml_path: str) -> dict:
    """Load budget input from a YAML file.

    Parameters
    ----------
    yaml_path : str
        Path to YAML file with budget specification.

    Returns
    -------
    dict
        Parsed budget input.
    """
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Budget file not found: {yaml_path}")
    with open(path) as f:
        return yaml.safe_load(f)


# ── Markdown formatting ────────────────────────────────────────────────────


def format_markdown(result: dict, style: str = "default") -> str:
    """Render budget result as Markdown tables.

    Parameters
    ----------
    result : dict
        Output from calculate().
    style : str
        Formatting style: 'default', 'horizon_wp', or 'uefiscdi'.

    Returns
    -------
    str
        Markdown-formatted budget summary.
    """
    if style == "horizon_wp":
        return _format_horizon_wp(result)
    elif style == "uefiscdi":
        return _format_uefiscdi(result)
    else:
        return _format_default(result)


def _fmt(amount: float, currency: str = "") -> str:
    """Format a monetary amount with thousands separator."""
    prefix = f"{currency} " if currency else ""
    return f"{prefix}{amount:,.2f}"


def _format_default(result: dict) -> str:
    """Default summary table."""
    cur = result.get("currency", "")
    lines = [
        "## Budget Summary",
        "",
        "| Category | Amount |",
        "|----------|--------|",
    ]

    model = result.get("model", "")

    if model == "person_months":
        lines.append(f"| Personnel | {_fmt(result['personnel_total'], cur)} |")
        lines.append(f"| Subcontracting | {_fmt(result.get('subcontracting', 0), cur)} |")
        lines.append(f"| Other direct costs | {_fmt(result.get('other_direct', 0), cur)} |")
        lines.append(f"| **Total direct** | **{_fmt(result['total_direct'], cur)}** |")
        lines.append(f"| Indirect ({result.get('indirect_rate', 0.25)*100:.0f}%) | {_fmt(result['indirect'], cur)} |")
    elif model == "monthly_salary":
        lines.append(f"| Personnel | {_fmt(result['personnel_total'], cur)} |")
        lines.append(f"| Mobility | {_fmt(result.get('mobility', 0), cur)} |")
        lines.append(f"| Equipment | {_fmt(result.get('equipment', 0), cur)} |")
        lines.append(f"| Consumables | {_fmt(result.get('consumables', 0), cur)} |")
        lines.append(f"| **Total direct** | **{_fmt(result['total_direct'], cur)}** |")
        lines.append(f"| Indirect ({result.get('indirect_rate_cap', 0.25)*100:.0f}%) | {_fmt(result['indirect'], cur)} |")

    lines.append(f"| **TOTAL** | **{_fmt(result['total'], cur)}** |")

    # Personnel breakdown
    breakdown = result.get("breakdown", {})
    personnel = breakdown.get("personnel", [])
    if personnel:
        lines.append("")
        lines.append("### Personnel Breakdown")
        lines.append("")
        if model == "person_months":
            lines.append("| Role | Person-months | Unit cost | Total |")
            lines.append("|------|---------------|-----------|-------|")
            for p in personnel:
                lines.append(
                    f"| {p['name']} | {p['person_months']} | {_fmt(p['unit_cost'], cur)} | {_fmt(p['total'], cur)} |"
                )
        elif model == "monthly_salary":
            lines.append("| Role | Monthly salary | Effort % | Months | Total |")
            lines.append("|------|----------------|----------|--------|-------|")
            for p in personnel:
                lines.append(
                    f"| {p['name']} | {_fmt(p['monthly_salary'], cur)} | {p['effort_pct']}% | {p['months']} | {_fmt(p['total'], cur)} |"
                )

    return "\n".join(lines)


def _format_horizon_wp(result: dict) -> str:
    """Horizon-style per-work-package budget table (simplified)."""
    cur = result.get("currency", "")
    lines = [
        "## Horizon Europe Budget Table",
        "",
        "| Cost category | Amount |",
        "|---------------|--------|",
        f"| A. Personnel costs | {_fmt(result['personnel_total'], cur)} |",
        f"| B. Subcontracting | {_fmt(result.get('subcontracting', 0), cur)} |",
        f"| C. Purchase costs | {_fmt(result.get('other_direct', 0), cur)} |",
        f"| D. Other cost categories | {_fmt(0, cur)} |",
        f"| E. Indirect costs ({result.get('indirect_rate', 0.25)*100:.0f}%) | {_fmt(result['indirect'], cur)} |",
        f"| **Total** | **{_fmt(result['total'], cur)}** |",
    ]
    return "\n".join(lines)


def _format_uefiscdi(result: dict) -> str:
    """UEFISCDI-style per-year budget table."""
    cur = result.get("currency", "")
    per_year = result.get("per_year", [])

    lines = [
        "## UEFISCDI Budget Table (per year)",
        "",
    ]

    if per_year:
        headers = ["Category"] + [f"Year {y['year']}" for y in per_year] + ["Total"]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "|".join(["--------"] * len(headers)) + "|")

        cats = ["personnel", "mobility", "equipment", "consumables", "direct", "indirect", "total"]
        labels = ["Personnel", "Mobility", "Equipment", "Consumables", "Total direct", "Indirect", "**TOTAL**"]

        for cat, label in zip(cats, labels):
            row = [label]
            cat_total = 0.0
            for y in per_year:
                val = y.get(cat, 0)
                cat_total += val
                row.append(_fmt(val, cur))
            row.append(_fmt(cat_total, cur))
            lines.append("| " + " | ".join(row) + " |")
    else:
        lines.append("_No per-year breakdown available._")

    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Budget calculator for grant proposals.",
    )
    sub = parser.add_subparsers(dest="command")

    # calculate
    sp_calc = sub.add_parser("calculate", help="Calculate budget from YAML input")
    sp_calc.add_argument("budget_yaml", help="Path to budget YAML file")

    # format
    sp_fmt = sub.add_parser("format", help="Format budget as Markdown tables")
    sp_fmt.add_argument("budget_yaml", help="Path to budget YAML file")
    sp_fmt.add_argument(
        "--style",
        default="default",
        choices=["default", "horizon_wp", "uefiscdi"],
        help="Table style (default: default)",
    )
    sp_fmt.add_argument("--currency", default=None, help="Override currency")

    args = parser.parse_args(argv)

    if args.command == "calculate":
        budget_input = load_budget_input(args.budget_yaml)
        result = calculate(budget_input)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "format":
        budget_input = load_budget_input(args.budget_yaml)
        if args.currency:
            budget_input["currency"] = args.currency
        result = calculate(budget_input)
        print(format_markdown(result, style=args.style))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
