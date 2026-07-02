"""
ISWL QUIKISSC loader — Rate_Table TYPE_CODE=SL surrender schedule → QuikIssc rows.

Hierarchy: PCOVRSGT → PSEGT(SL) → OSLNS00XT/SLD000 → Rate_Table SL → QuikIssc.

Replicates hub segment 659 CEN II SL schedule to all 8 ISWL MPLANs (one row each).
"""
from __future__ import annotations

import csv
import os
from collections import Counter

from qla_core import rate_dbf_schema as S
from qla_core.cso_mortality_crosswalk import ISWL_MPLAN_ALLOWLIST

DEFAULT_HUB_COVERAGE = "659 CEN II"
DEFAULT_TYPE_CODE = "SL"
DEFAULT_SEX = "M"
DEFAULT_BAND = "1"
DEFAULT_UWCLASS = "S"
DEFAULT_AGE = "0"
SCHG_POPULATED = 14
SCHG_MAX = 20
RATE_DECIMALS = 4


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


def expected_hub_schg_schedule() -> dict[int, str]:
    """Authoritative 659 CEN II SL duration ladder (percent literals) for validation."""
    return {
        1: "100.0000",
        2: "100.0000",
        3: "70.0000",
        4: "60.0000",
        5: "50.0000",
        6: "40.0000",
        7: "30.0000",
        8: "20.0000",
        9: "15.0000",
        10: "10.0000",
        11: "8.0000",
        12: "6.0000",
        13: "4.0000",
        14: "2.0000",
    }


def load_rate_table_sl_schedule(
    rate_table_path: str,
    *,
    coverage_id: str = DEFAULT_HUB_COVERAGE,
    type_code: str = DEFAULT_TYPE_CODE,
    sex: str = DEFAULT_SEX,
    band: str = DEFAULT_BAND,
    uwclass: str = DEFAULT_UWCLASS,
    age: str = DEFAULT_AGE,
) -> dict[int, str]:
    """
    Load hub SL surrender schedule from Rate_Table extract.
    Returns duration (1-based) → formatted percent literal.
    """
    schedule: dict[int, str] = {}
    with open(rate_table_path, encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            r = _norm_row(raw)
            if r.get("COVERAGE_ID", "").strip() != coverage_id:
                continue
            if r.get("TYPE_CODE", "").strip() != type_code:
                continue
            if r.get("SEX", "").strip() != sex:
                continue
            if r.get("BAND", "").strip() != band:
                continue
            if r.get("UNDERWRITING_CLASS", "").strip() != uwclass:
                continue
            if r.get("AGE", "").strip() != age:
                continue
            dur_s = r.get("DURATION", "").strip()
            if not dur_s:
                continue
            try:
                dur = int(dur_s)
            except ValueError:
                continue
            schedule[dur] = _format_rate(r.get("VALUE", ""))
    return schedule


def _blank_schg_tail() -> dict[str, str]:
    return {f"SCHG{i:02d}": "" for i in range(SCHG_POPULATED + 1, SCHG_MAX + 1)}


def schedule_to_schg_fields(schedule: dict[int, str]) -> dict[str, str]:
    """Pivot duration-indexed schedule to SCHG01..SCHG14; SCHG15..20 blank."""
    out = _blank_schg_tail()
    for dur in range(1, SCHG_POPULATED + 1):
        out[f"SCHG{dur:02d}"] = schedule.get(dur, "")
    return out


def build_quikissc_row(
    plan: str,
    schedule: dict[int, str],
    *,
    isscntry: str = "0000",
    issuest: str = "00",
) -> dict:
    gender = S.map_sex(DEFAULT_SEX) or "M"
    uwclass = S.map_uwclass(DEFAULT_UWCLASS) or "SM"
    band = S.map_band(DEFAULT_BAND) or "01"
    row = {
        "PLAN": plan,
        "AGE": DEFAULT_AGE,
        "GENDER": gender,
        "UWCLASS": uwclass,
        "BAND": band,
        "ISSCNTRY": isscntry,
        "ISSUEST": issuest,
    }
    row.update(schedule_to_schg_fields(schedule))
    return row


def build_quikissc_rows(
    mplans: frozenset[str] | set[str],
    schedule: dict[int, str],
    *,
    isscntry: str = "0000",
    issuest: str = "00",
) -> list[dict]:
    return [
        build_quikissc_row(plan, schedule, isscntry=isscntry, issuest=issuest)
        for plan in sorted(mplans)
    ]


def iswl_phase6_config(cfg: dict) -> dict:
    return cfg.get("iswl_phase6", {})


def iswl_issc_mplan_allowlist(cfg: dict) -> frozenset[str]:
    phase = iswl_phase6_config(cfg)
    allow = phase.get("mplan_allowlist")
    if allow:
        return frozenset(str(p).strip() for p in allow if str(p).strip())
    return ISWL_MPLAN_ALLOWLIST


def load_quikissc_from_config(repo_root: str, cfg: dict) -> tuple[list[dict], Counter]:
    """
    Load and emit QuikIssc rows for ISWL MPLANs.
    Returns (rows, status_counter).
    """
    phase = iswl_phase6_config(cfg)
    if not phase.get("quikissc_enabled", False):
        return [], Counter()

    status: Counter = Counter()
    rate_path = _resolve_path(repo_root, cfg.get("source_rate_extract", ""))
    if not rate_path or not os.path.isfile(rate_path):
        status["BLOCKER_NO_RATE_TABLE"] += 1
        return [], status

    seg = cfg.get("segmentation_defaults", {})
    coverage_id = phase.get("rate_coverage_id", phase.get("hub_segment_id", DEFAULT_HUB_COVERAGE))
    type_code = phase.get("rate_type_code", DEFAULT_TYPE_CODE)
    isscntry = phase.get("iss_cntry_default", seg.get("isscntry", "0000"))
    issuest = phase.get("iss_state_default", seg.get("issuest", "00"))
    mplans = iswl_issc_mplan_allowlist(cfg)

    schedule = load_rate_table_sl_schedule(
        rate_path,
        coverage_id=coverage_id,
        type_code=type_code,
    )
    if len(schedule) < SCHG_POPULATED:
        status["BLOCKER_INCOMPLETE_SL"] += 1
        status["DURATIONS_FOUND"] += len(schedule)
        return [], status

    status["HUB_DURATIONS"] += len(schedule)
    rows = build_quikissc_rows(mplans, schedule, isscntry=isscntry, issuest=issuest)
    status["ROWS_EMITTED"] += len(rows)
    status["MPLANS"] += len(mplans)
    return rows, status
