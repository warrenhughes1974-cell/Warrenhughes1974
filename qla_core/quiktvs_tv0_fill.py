"""
QuikTvs TV0 blank fill — durable rate emit path.

For non-single-premium plans, blank TV0 cells are formatted as numeric zero
(`.00` via rate_dbf_schema.format_factor). True single-premium plans keep
blank TV0 unchanged (conservative detection from config + quikplan evidence).
"""
from __future__ import annotations

import csv
import os
from typing import Any

from qla_core import rate_dbf_schema as S
from qla_core.quikplan_converter import load_single_premium_plans

_DESC_KEY_HINTS = ("DESCR", "FRIEND", "NAME", "LONG")
_SP_DESC_MARKERS = ("SINGLE PREM", "SINGLE-PREM")


def _normalize_plan(value: Any) -> str:
    return str(value or "").strip()


def _tv0_is_blank(value: Any) -> bool:
    return _normalize_plan(value) == ""


def _payyrs_is_one(value: Any) -> bool:
    s = _normalize_plan(value)
    if not s:
        return False
    try:
        return int(float(s)) == 1
    except (ValueError, TypeError):
        return False


def _row_has_single_premium_description(row: dict) -> bool:
    for key, raw in row.items():
        ku = str(key or "").upper()
        if not any(hint in ku for hint in _DESC_KEY_HINTS):
            continue
        blob = str(raw or "").upper()
        if any(marker in blob for marker in _SP_DESC_MARKERS):
            return True
    return False


def default_quikplan_csv_path(repo_root: str) -> str:
    return os.path.normpath(
        os.path.join(repo_root, "QLA_Migration", "Output", "quikplan.csv")
    )


def resolve_quikplan_csv_path(repo_root: str, config: dict | None) -> str:
    """Prefer rate-loader config quikplan_csv when present."""
    cfg = config or {}
    rel = (
        (cfg.get("issue95_quikuint") or {}).get("quikplan_csv")
        or cfg.get("quikplan_csv")
    )
    if rel:
        path = rel if os.path.isabs(rel) else os.path.join(repo_root, rel)
        if os.path.isfile(path):
            return os.path.normpath(path)
    return default_quikplan_csv_path(repo_root)


def load_true_single_premium_plans(
    repo_root: str,
    quikplan_path: str | None = None,
    config: dict | None = None,
) -> set[str]:
    """Conservative single-premium plan set for QuikTvs TV0 blank preservation.

    Primary: QLA_Migration/Configs/single_premium_plans.csv (+ plan_classification).
    Extension: quikplan row with PAYYRS=1 AND description/friendly SINGLE PREM evidence.
    PAYYRS=1 alone is insufficient (avoids misclassifying ordinary/ISWL/SAL plans).
    """
    plans = set(load_single_premium_plans(repo_root))
    qp_path = quikplan_path or resolve_quikplan_csv_path(repo_root, config)
    if not os.path.isfile(qp_path):
        return plans
    try:
        with open(qp_path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                plan = _normalize_plan(row.get("PLAN"))
                if not plan or plan in plans:
                    continue
                if _payyrs_is_one(row.get("PAYYRS")) and _row_has_single_premium_description(row):
                    plans.add(plan)
    except OSError:
        pass
    return plans


def quiktvs_tv0_zero_text(source_decimals: int = 2) -> str:
    text, _, _ = S.format_factor(
        0.0,
        max_len=S.factor_field_len("QuikTvs"),
        source_decimals=source_decimals,
    )
    return text


def apply_quiktvs_tv0_blank_fill(
    factor_rows: dict[str, list[dict]],
    single_premium_plans: set[str],
    source_decimals: int = 2,
) -> dict[str, Any]:
    """Fill blank QuikTvs TV0 on non-SP rows; preserve nonblank and SP blanks."""
    rows = factor_rows.get("QuikTvs")
    if not rows:
        return {
            "filled": 0,
            "preserved_nonblank": 0,
            "preserved_sp_blank": 0,
            "sp_blank_plans": [],
        }

    zero_text = quiktvs_tv0_zero_text(source_decimals)
    stats: dict[str, Any] = {
        "filled": 0,
        "preserved_nonblank": 0,
        "preserved_sp_blank": 0,
        "sp_blank_plans": set(),
    }

    for row in rows:
        if not _tv0_is_blank(row.get("TV0")):
            stats["preserved_nonblank"] += 1
            continue
        plan = _normalize_plan(row.get("PLAN"))
        if plan in single_premium_plans:
            stats["preserved_sp_blank"] += 1
            stats["sp_blank_plans"].add(plan)
            continue
        row["TV0"] = zero_text
        stats["filled"] += 1

    stats["sp_blank_plans"] = sorted(stats["sp_blank_plans"])
    return stats
