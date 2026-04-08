"""Configuration loading and defaults for grant-writer-skills."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import yaml


# ── Data classes mirroring the grant proposal configuration ─────────────────


@dataclass
class AimsConfig:
    max_refinement_rounds: int = 5
    score_threshold: int = 4
    codex_review_rounds: int = 2


@dataclass
class LiteratureConfig:
    max_search_rounds: int = 3
    min_citations: int = 30


@dataclass
class WritingConfig:
    reflection_rounds: int = 3


@dataclass
class BudgetConfig:
    indirect_rate: float = 0.25
    currency: str = "EUR"


@dataclass
class ReviewConfig:
    revision_cycles: int = 2
    score_threshold: int = 3


@dataclass
class ScientificSkillsConfig:
    enabled: str = "auto"  # "auto" | "true" | "false"
    enhanced_literature: bool = True
    enhanced_writing: bool = True
    enhanced_figures: bool = True
    enhanced_review: bool = True

    def __post_init__(self):
        # Normalize enabled to string (YAML may parse true/false as bool)
        self.enabled = str(self.enabled).lower()


@dataclass
class CodexConfig:
    enabled: str = "auto"  # "auto" | "true" | "false"
    panel_review: bool = True
    aims_review: bool = True
    rescue_on_stuck: bool = True
    agency: str = "auto"  # "auto" | "horizon" | "erc" | "uefiscdi" | "pnrr"

    def __post_init__(self):
        # Normalize enabled to string (YAML may parse true/false as bool)
        self.enabled = str(self.enabled).lower()


@dataclass
class ProposalConfig:
    title: str = ""
    pi_name: str = ""
    institution: str = ""
    acronym: str = ""


@dataclass
class Config:
    """Top-level configuration for a grant proposal run."""

    # Funding agency and mechanism
    agency: str = "horizon"       # horizon | erc | msca | uefiscdi | pnrr
    mechanism: str = "ria"        # ria | ia | erc-stg | erc-cog | erc-adg | msca-pf | pn-iii
    language: str = "en"          # en | ro

    # Proposal metadata
    proposal: ProposalConfig = field(default_factory=ProposalConfig)

    # Specific aims / objectives
    aims: AimsConfig = field(default_factory=AimsConfig)

    # Literature search
    literature: LiteratureConfig = field(default_factory=LiteratureConfig)

    # Writing
    writing: WritingConfig = field(default_factory=WritingConfig)

    # Budget
    budget: BudgetConfig = field(default_factory=BudgetConfig)

    # Review
    review: ReviewConfig = field(default_factory=ReviewConfig)

    # Scientific skills integration (optional)
    scientific_skills: ScientificSkillsConfig = field(default_factory=ScientificSkillsConfig)

    # Codex integration (optional)
    codex: CodexConfig = field(default_factory=CodexConfig)


# ── Default config path ──────────────────────────────────────────────────────

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
DEFAULT_CONFIG_PATH = TEMPLATES_DIR / "grant_config.yaml"


# ── Loading / merging ────────────────────────────────────────────────────────


def _nested_dataclass_from_dict(cls, data: dict):
    """Recursively instantiate nested dataclasses from a dict."""
    if not isinstance(data, dict):
        return data
    field_types = {f.name: f.type for f in cls.__dataclass_fields__.values()}
    kwargs = {}
    for key, value in data.items():
        if key in field_types:
            ft = field_types[key]
            # Resolve string type annotations
            if isinstance(ft, str):
                ft = eval(ft)
            if isinstance(ft, type) and hasattr(ft, "__dataclass_fields__") and isinstance(value, dict):
                kwargs[key] = _nested_dataclass_from_dict(ft, value)
            else:
                kwargs[key] = value
    return cls(**kwargs)


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into *base* in place."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def load_config(path: Optional[str] = None, overrides: Optional[dict] = None) -> Config:
    """Load configuration from a YAML file and apply optional overrides.

    Parameters
    ----------
    path : str | None
        Path to YAML config file.  Falls back to templates/grant_config.yaml.
    overrides : dict | None
        Key-value pairs that override loaded values (flat or nested).
    """
    cfg_dict: dict = {}
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH

    if config_path.exists():
        with open(config_path) as f:
            cfg_dict = yaml.safe_load(f) or {}

    # Apply overrides
    if overrides:
        _deep_merge(cfg_dict, overrides)

    cfg = _nested_dataclass_from_dict(Config, cfg_dict)
    return cfg


def save_config(cfg: Config, path: str) -> None:
    """Persist a Config to YAML."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        yaml.dump(asdict(cfg), f, default_flow_style=False, sort_keys=False)


# ── CLI helper ───────────────────────────────────────────────────────────────


def parse_config_args(argv=None) -> Config:
    """Quick CLI wrapper for loading config with --config and --set overrides."""
    parser = argparse.ArgumentParser(description="Grant Writer config loader")
    parser.add_argument("--config", type=str, default=None, help="Path to YAML config")
    parser.add_argument(
        "--set",
        nargs="*",
        metavar="KEY=VALUE",
        default=[],
        help="Override config values (e.g. --set budget.currency=RON review.score_threshold=4)",
    )
    args = parser.parse_args(argv)

    overrides = {}
    for kv in args.set:
        key, _, val = kv.partition("=")
        # Try to parse as JSON for booleans / numbers
        try:
            val = json.loads(val)
        except (json.JSONDecodeError, TypeError):
            pass
        # Support dotted keys -> nested dict
        parts = key.split(".")
        d = overrides
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = val

    cfg = load_config(args.config, overrides)
    print(yaml.dump(asdict(cfg), default_flow_style=False, sort_keys=False))
    return cfg


if __name__ == "__main__":
    parse_config_args()
