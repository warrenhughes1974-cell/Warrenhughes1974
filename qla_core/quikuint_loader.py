"""
ISWL QUIKUINT loader — PDINT/PDINTTBL declared interest → QuikUint plan-level rows.

Hierarchy: PCOVRSGT → PSEGT(A1) → PDINT(CENII, TYPE=A1) → PDINTTBL → QuikUint.

Emit mode union_merge: collect unique START_DATE tiers from DINT_RULE 0 and 3;
tie-break at duplicate START_DATE prefers DINT_RULE=3.
"""
from __future__ import annotations

import csv
import os
from collections import Counter
from dataclasses import dataclass

from qla_core.cso_mortality_crosswalk import ISWL_MPLAN_ALLOWLIST

DEFAULT_IDENT = "CENII"
DEFAULT_TYPE_CODE = "A1"
DEFAULT_DINT_RULES = ("0", "3")
TIE_BREAK_RULE = "3"
CURRENT_TIER_START = "20020101"
CURRENT_TIER_RATE = "4.50000"
RATE_DECIMALS = 4


@dataclass(frozen=True)
class InterestTier:
    start_date: str
    end_date: str
    declared_rate: str
    dint_rule: str
    ident: str
    type_code: str


def _norm_row(d: dict) -> dict[str, str]:
    return {k.strip(): (v or "").strip() for k, v in d.items()}


def _resolve_path(repo_root: str, rel_or_abs: str) -> str:
    if not rel_or_abs:
        return ""
    return rel_or_abs if os.path.isabs(rel_or_abs) else os.path.join(repo_root, rel_or_abs)


def _format_rate(value: str) -> str:
    s = (value or "").strip()
    if not s:
        return ""
    try:
        return f"{float(s):.{RATE_DECIMALS}f}"
    except ValueError:
        return s


def load_pdinttbl_tiers(
    pdinttbl_path: str,
    *,
    ident: str = DEFAULT_IDENT,
    type_code: str = DEFAULT_TYPE_CODE,
    dint_rules: tuple[str, ...] = DEFAULT_DINT_RULES,
) -> list[InterestTier]:
    """Load PDINTTBL schedule rows for CENII/A1 and selected DINT_RULE values."""
    tiers: list[InterestTier] = []
    with open(pdinttbl_path, encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            r = _norm_row(raw)
            if not r.get("IDENT") or r["IDENT"] in ("-----", ""):
                continue
            if r["IDENT"] != ident or r["TYPE_CODE"] != type_code:
                continue
            rule = r["DINT_RULE"].strip()
            if rule not in dint_rules:
                continue
            start = r["START_DATE"].strip()
            if not start or len(start) != 8:
                continue
            tiers.append(
                InterestTier(
                    start_date=start,
                    end_date=r.get("END_DATE", "").strip(),
                    declared_rate=_format_rate(r.get("DECLARED_RATE", "")),
                    dint_rule=rule,
                    ident=ident,
                    type_code=type_code,
                )
            )
    return tiers


def union_merge_tiers(
    tiers: list[InterestTier],
    *,
    tiebreak_rule: str = TIE_BREAK_RULE,
) -> list[InterestTier]:
    """
    Merge tiers from multiple DINT_RULE headers by unique START_DATE.
    On duplicate START_DATE, prefer tiebreak_rule (default DINT_RULE=3).
    """
    by_start: dict[str, InterestTier] = {}
    for tier in sorted(tiers, key=lambda t: (t.start_date, t.dint_rule)):
        existing = by_start.get(tier.start_date)
        if existing is None or tier.dint_rule == tiebreak_rule:
            by_start[tier.start_date] = tier
    return [by_start[k] for k in sorted(by_start.keys())]


def fallback_current_tier(
    *,
    ident: str = DEFAULT_IDENT,
    type_code: str = DEFAULT_TYPE_CODE,
) -> list[InterestTier]:
    """Single current-tier row when historical PDINTTBL tiers are unavailable."""
    return [
        InterestTier(
            start_date=CURRENT_TIER_START,
            end_date="20991231",
            declared_rate=CURRENT_TIER_RATE,
            dint_rule=TIE_BREAK_RULE,
            ident=ident,
            type_code=type_code,
        )
    ]


def tier_to_quikuint_row(mplan: str, tier: InterestTier) -> dict:
    rate = tier.declared_rate
    return {
        "MPLAN": mplan,
        "MEFFDATE": tier.start_date,
        "MGTDRATE": rate,
        "MCURRATE": rate,
    }


def build_quikuint_rows(
    mplans: frozenset[str] | set[str],
    merged_tiers: list[InterestTier],
) -> list[dict]:
    rows: list[dict] = []
    for mplan in sorted(mplans):
        for tier in merged_tiers:
            rows.append(tier_to_quikuint_row(mplan, tier))
    return rows


def iswl_phase5_config(cfg: dict) -> dict:
    return cfg.get("iswl_phase5", {})


def iswl_uint_mplan_allowlist(cfg: dict) -> frozenset[str]:
    phase = iswl_phase5_config(cfg)
    allow = phase.get("mplan_allowlist")
    if allow:
        return frozenset(str(p).strip() for p in allow if str(p).strip())
    return ISWL_MPLAN_ALLOWLIST


def load_quikuint_from_config(repo_root: str, cfg: dict) -> tuple[list[dict], Counter]:
    """
    Load and emit QuikUint rows for ISWL MPLANs.
    Returns (rows, status_counter).
    """
    phase = iswl_phase5_config(cfg)
    if not phase.get("quikuint_enabled", False):
        return [], Counter()

    status: Counter = Counter()
    pdinttbl_path = _resolve_path(repo_root, cfg.get("pdinttbl_extract", ""))
    if not pdinttbl_path or not os.path.isfile(pdinttbl_path):
        status["BLOCKER_NO_PDINTTBL"] += 1
        return [], status

    ident = phase.get("pdint_ident", DEFAULT_IDENT)
    type_code = phase.get("type_code", DEFAULT_TYPE_CODE)
    rules = tuple(str(r) for r in phase.get("dint_rules", DEFAULT_DINT_RULES))
    tiebreak = str(phase.get("dint_rule_tiebreak", TIE_BREAK_RULE))
    emit_mode = phase.get("emit_mode", "union_merge")
    mplans = iswl_uint_mplan_allowlist(cfg)

    raw_tiers = load_pdinttbl_tiers(
        pdinttbl_path, ident=ident, type_code=type_code, dint_rules=rules,
    )
    if not raw_tiers:
        status["FALLBACK_CURRENT_TIER"] += 1
        merged = fallback_current_tier(ident=ident, type_code=type_code)
    elif emit_mode == "union_merge":
        merged = union_merge_tiers(raw_tiers, tiebreak_rule=tiebreak)
        status["UNION_MERGE"] += len(merged)
    else:
        merged = union_merge_tiers(raw_tiers, tiebreak_rule=tiebreak)
        status["UNION_MERGE"] += len(merged)

    rows = build_quikuint_rows(mplans, merged)
    status["ROWS_EMITTED"] += len(rows)
    status["MPLANS"] += len(mplans)
    return rows, status


def expected_union_schedule() -> dict[str, str]:
    """Authoritative CENII/A1 union-merge rates for validation."""
    return {
        "19800101": "11.0000",
        "19890101": "9.0000",
        "19990101": "5.0000",
        "20020101": "4.5000",
    }
