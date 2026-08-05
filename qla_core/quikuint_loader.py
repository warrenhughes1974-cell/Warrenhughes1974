"""
ISWL QUIKUINT loader — PDINT/PDINTTBL declared interest → QuikUint plan-level rows.

Hierarchy: PCOVRSGT → PSEGT(A1) → PDINT(CENII, TYPE=A1) → PDINTTBL → QuikUint.

Emit mode union_merge: collect unique START_DATE tiers from DINT_RULE 0 and 3;
tie-break at duplicate START_DATE prefers DINT_RULE=3.

Issue #95: additive current-tier buckets (SPWL/1668SP, SAL01, residual 3.50%)
without expanding shared ISWL_MPLAN_ALLOWLIST.
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

# Eric-approved named buckets (Issue #95). Shared ISWL allowlist stays separate.
DEFAULT_RATE_450_PLANS = frozenset(
    {
        "1668SP",
        "1669SR",
        "1658C1",
        "1658CS",
        "1659C2",
        "1659CR",
        "1659CS",
        "1659SR",
        "1679CS",
    }
)
DEFAULT_RATE_200_PLANS = frozenset({"1SALOL", "1SALML"})
DEFAULT_QUIKPLAN_CSV = "QLA_Migration/Output/quikplan.csv"


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


def _resolve_pdinttbl_path(repo_root: str, cfg: dict) -> str:
    """Prefer PDINTTBL for QLA_VALUATION_DATE over a stale hardcoded config path."""
    vd = "".join(c for c in os.environ.get("QLA_VALUATION_DATE", "") if c.isdigit())[:8]
    if len(vd) == 8:
        name = f"PDINTTBL_DeclaredInterestRates_Extract_{vd}.csv"
        for rel in (
            f"QLA_Migration/Source/{name}",
            f"QLA_Migration/Source/LifePRO_Extracts_{vd}/{name}",
        ):
            path = _resolve_path(repo_root, rel)
            if path and os.path.isfile(path):
                return path
    configured = _resolve_path(repo_root, cfg.get("pdinttbl_extract", ""))
    if configured and os.path.isfile(configured):
        return configured
    return configured or ""


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


def load_pdinttbl_current_tier(
    pdinttbl_path: str,
    *,
    ident: str,
    type_code: str | None = None,
) -> InterestTier | None:
    """
    Select the current PDINTTBL tier for an IDENT: max START_DATE,
    then higher DINT_RULE on ties. Optional TYPE_CODE filter.
    """
    tiers: list[InterestTier] = []
    with open(pdinttbl_path, encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            r = _norm_row(raw)
            if not r.get("IDENT") or r["IDENT"] in ("-----", ""):
                continue
            if r["IDENT"] != ident:
                continue
            if type_code is not None and r.get("TYPE_CODE", "") != type_code:
                continue
            start = r.get("START_DATE", "").strip()
            if not start or len(start) != 8:
                continue
            tiers.append(
                InterestTier(
                    start_date=start,
                    end_date=r.get("END_DATE", "").strip(),
                    declared_rate=_format_rate(r.get("DECLARED_RATE", "")),
                    dint_rule=r.get("DINT_RULE", "").strip(),
                    ident=ident,
                    type_code=r.get("TYPE_CODE", "").strip(),
                )
            )
    if not tiers:
        return None
    return max(tiers, key=lambda t: (t.start_date, t.dint_rule))


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


def issue95_config(cfg: dict) -> dict:
    return cfg.get("issue95_quikuint", {})


def iswl_uint_mplan_allowlist(cfg: dict) -> frozenset[str]:
    phase = iswl_phase5_config(cfg)
    allow = phase.get("mplan_allowlist")
    if allow:
        return frozenset(str(p).strip() for p in allow if str(p).strip())
    return ISWL_MPLAN_ALLOWLIST


def _plan_set(cfg_block: dict, key: str, default: frozenset[str]) -> frozenset[str]:
    raw = cfg_block.get(key)
    if not raw:
        return default
    return frozenset(str(p).strip() for p in raw if str(p).strip())


def load_quikplan_plans(quikplan_path: str) -> frozenset[str]:
    plans: set[str] = set()
    with open(quikplan_path, encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            r = _norm_row(raw)
            plan = r.get("PLAN", "")
            if plan:
                plans.add(plan)
    return frozenset(plans)


def residual_mplans_amem_safe(
    all_plans: frozenset[str] | set[str],
    *,
    rate_450: frozenset[str],
    rate_200: frozenset[str],
    exclude_prefixes: tuple[str, ...] = ("9", "A"),
) -> frozenset[str]:
    """A-MEM-SAFE residual: quikplan minus named 4.50/2.00 buckets, excluding 9*/A*."""
    out: set[str] = set()
    for plan in all_plans:
        if plan in rate_450 or plan in rate_200:
            continue
        if any(plan.startswith(pref) for pref in exclude_prefixes):
            continue
        out.add(plan)
    return frozenset(out)


def _assert_unique_keys(rows: list[dict]) -> None:
    seen: set[tuple[str, str]] = set()
    for r in rows:
        key = (r["MPLAN"], r["MEFFDATE"])
        if key in seen:
            raise ValueError(f"Duplicate QuikUint key MPLAN={key[0]} MEFFDATE={key[1]}")
        seen.add(key)


def _current_tier_rows_for_mplans(
    pdinttbl_path: str,
    *,
    mplans: frozenset[str] | set[str],
    ident: str,
    type_code: str | None,
    status: Counter,
    status_prefix: str,
) -> list[dict]:
    if not mplans:
        return []
    tier = load_pdinttbl_current_tier(pdinttbl_path, ident=ident, type_code=type_code)
    if tier is None:
        status[f"BLOCKER_NO_CURRENT_TIER_{status_prefix}"] += 1
        return []
    rows = build_quikuint_rows(mplans, [tier])
    status[f"ROWS_{status_prefix}"] += len(rows)
    status[f"MPLANS_{status_prefix}"] += len(mplans)
    return rows


def _load_cenii_iswl_rows(
    repo_root: str,
    cfg: dict,
    pdinttbl_path: str,
    status: Counter,
) -> list[dict]:
    """Preserve Issue #32 CENII union_merge historical schedule for 8 ISWL MPLANs."""
    phase = iswl_phase5_config(cfg)
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
    else:
        merged = union_merge_tiers(raw_tiers, tiebreak_rule=tiebreak)
        status["UNION_MERGE"] += len(merged)
        if emit_mode != "union_merge":
            status["EMIT_MODE_NON_UNION"] += 1

    rows = build_quikuint_rows(mplans, merged)
    status["ROWS_CENII_ISWL"] += len(rows)
    status["MPLANS_CENII_ISWL"] += len(mplans)
    return rows


def _load_issue95_bucket_rows(
    repo_root: str,
    cfg: dict,
    pdinttbl_path: str,
    status: Counter,
) -> list[dict]:
    """
    Issue #95 additive buckets (A-HIST current-only):
      - 1668SP from SPWL current
      - 1SALOL / 1SALML from SAL01 current
      - A-MEM-SAFE residual from L1001 current
    """
    i95 = issue95_config(cfg)
    if not i95.get("enabled", False):
        return []

    rate_450 = _plan_set(i95, "rate_450_plans", DEFAULT_RATE_450_PLANS)
    rate_200 = _plan_set(i95, "rate_200_plans", DEFAULT_RATE_200_PLANS)
    rows: list[dict] = []

    spwl_cfg = i95.get("spwl_1668", {})
    spwl_plans = _plan_set(spwl_cfg, "mplans", frozenset({"1668SP"}))
    rows.extend(
        _current_tier_rows_for_mplans(
            pdinttbl_path,
            mplans=spwl_plans,
            ident=str(spwl_cfg.get("pdint_ident", "SPWL")),
            type_code=str(spwl_cfg.get("type_code", "A1")),
            status=status,
            status_prefix="SPWL_1668",
        )
    )

    sal_cfg = i95.get("sal01", {})
    sal_plans = _plan_set(sal_cfg, "mplans", DEFAULT_RATE_200_PLANS)
    rows.extend(
        _current_tier_rows_for_mplans(
            pdinttbl_path,
            mplans=sal_plans,
            ident=str(sal_cfg.get("pdint_ident", "SAL01")),
            type_code=str(sal_cfg.get("type_code", "C1")),
            status=status,
            status_prefix="SAL01",
        )
    )

    resid_cfg = i95.get("residual_350", {})
    quikplan_rel = i95.get("quikplan_csv", DEFAULT_QUIKPLAN_CSV)
    quikplan_path = _resolve_path(repo_root, quikplan_rel)
    if not quikplan_path or not os.path.isfile(quikplan_path):
        status["BLOCKER_NO_QUIKPLAN"] += 1
        return rows

    all_plans = load_quikplan_plans(quikplan_path)
    prefixes = tuple(
        str(p) for p in resid_cfg.get("exclude_prefixes", ["9", "A"]) if str(p)
    )
    residual = residual_mplans_amem_safe(
        all_plans,
        rate_450=rate_450,
        rate_200=rate_200,
        exclude_prefixes=prefixes or ("9", "A"),
    )
    status["MPLANS_EXCLUDED_RIDER_ANNUITY"] += sum(
        1
        for p in all_plans
        if p not in rate_450
        and p not in rate_200
        and any(p.startswith(pref) for pref in (prefixes or ("9", "A")))
    )
    rows.extend(
        _current_tier_rows_for_mplans(
            pdinttbl_path,
            mplans=residual,
            ident=str(resid_cfg.get("pdint_ident", "L1001")),
            type_code=str(resid_cfg.get("type_code", "C1")),
            status=status,
            status_prefix="RESIDUAL_350",
        )
    )
    return rows


def load_quikuint_from_config(repo_root: str, cfg: dict) -> tuple[list[dict], Counter]:
    """
    Load and emit QuikUint rows for ISWL CENII history plus optional Issue #95 buckets.
    Returns (rows, status_counter).
    """
    phase = iswl_phase5_config(cfg)
    if not phase.get("quikuint_enabled", False):
        return [], Counter()

    status: Counter = Counter()
    pdinttbl_path = _resolve_pdinttbl_path(repo_root, cfg)
    if not pdinttbl_path or not os.path.isfile(pdinttbl_path):
        status["BLOCKER_NO_PDINTTBL"] += 1
        return [], status

    rows = _load_cenii_iswl_rows(repo_root, cfg, pdinttbl_path, status)
    rows.extend(_load_issue95_bucket_rows(repo_root, cfg, pdinttbl_path, status))

    try:
        _assert_unique_keys(rows)
    except ValueError:
        status["BLOCKER_DUPLICATE_KEYS"] += 1
        raise

    status["ROWS_EMITTED"] += len(rows)
    status["MPLANS"] += len({r["MPLAN"] for r in rows})
    return rows, status


def expected_union_schedule() -> dict[str, str]:
    """Authoritative CENII/A1 union-merge rates for validation."""
    return {
        "19800101": "11.0000",
        "19890101": "9.0000",
        "19990101": "5.0000",
        "20020101": "4.5000",
    }
