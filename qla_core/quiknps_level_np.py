"""
QuikNps level net-premium flatten — durable rate emit path.

For CEN/ISWL mean-reserve families, LifePRO PDAGE NP schedules climb by duration.
QLAdmin adds the stored net premium between the terminal cash values, so every
year must carry the issue-year rate (LifePRO DURATION=1), not the climbed rate
at the start of each later 10-year page.

Warren 2026-09-22: later CNTL pages use the same duration-1 rate as CNTL 00.
A page leveled to its own NP0 (1659CR year 36 = 640) makes the policy-display
cash value jump from about 7,240 to about 11,390 and back.

Source field: PDAGE / Rate_Table VALUE.
Source duration: DURATION=1 -> ql_duration 0 -> CNTL 00 column NP0.
"""
from __future__ import annotations

from typing import Any

from qla_core import rate_dbf_schema as S

# CEN/ISWL families with duration-varying PDAGE NP that must emit level NP1..NP9.
QUIKNPS_LEVEL_NP_MPLANS = frozenset({
    "1658C1", "1658CS", "1659C2", "1659CR", "1659CS", "1659SR",
    "1668SP", "1669SR", "1679CS",
})

SOURCE_DURATION_ISSUE_YEAR = 1
NP0_QL_COL = 0
ISSUE_YEAR_CNTL = "00"
NP_LEVEL_COLS = tuple(range(S.N_DURATION_COLS))


def is_quiknps_level_np_plan(plan: str) -> bool:
    return str(plan or "").strip() in QUIKNPS_LEVEL_NP_MPLANS


def _cell_tuple(template: tuple, level_value: float, raw_value: str) -> tuple:
    """Preserve grid cell metadata while replacing the numeric payload."""
    if len(template) >= 6:
        return (level_value, raw_value, template[2], template[3], template[4], template[5])
    if len(template) >= 4:
        return (level_value, raw_value, template[2], template[3])
    return (level_value, raw_value, template[2])


def _identity(key: tuple) -> tuple:
    """Plan/age/sex/class/band/generation, without the 10-year CNTL page."""
    return (key[0], key[1], key[3], key[4], key[5], key[6], key[7], key[8])


def _is_issue_year_page(cntl) -> bool:
    text = str(cntl).strip()
    if text.isdigit():
        return int(text) == 0
    return text == ISSUE_YEAR_CNTL


def apply_quiknps_level_np_grid(
    quiknps_grid: dict[tuple, dict[int, tuple]] | None,
) -> dict[str, Any]:
    """Level every duration on allowlisted CEN/ISWL plans to the issue-year NP.

    Operates on the in-memory QuikNps grid before ``grid_to_factor_rows``.
    The issue-year cell is CNTL 00 column NP0 (LifePRO DURATION=1). That value
    is written onto NP0..NP9 of every CNTL page for the same age, sex, class,
    band, and generation. Traditional plans are untouched.

    Returns stats plus ``blockers`` when a key has no issue-year cell.
    """
    grid = quiknps_grid or {}
    stats: dict[str, Any] = {
        "plans": sorted(QUIKNPS_LEVEL_NP_MPLANS),
        "source_field": "VALUE1",
        "source_duration": SOURCE_DURATION_ISSUE_YEAR,
        "ql_col": NP0_QL_COL,
        "level_source": "issue_year_np0",
        "rows_examined": 0,
        "rows_flattened": 0,
        "cells_set": 0,
        "rows_already_level": 0,
        "blockers": [],
        "audit_samples": [],
    }

    issue_year: dict[tuple, tuple] = {}
    for key, cells in grid.items():
        plan = key[0]
        if not is_quiknps_level_np_plan(plan) or not _is_issue_year_page(key[2]):
            continue
        cell = cells.get(NP0_QL_COL)
        if cell is not None:
            issue_year[_identity(key)] = cell

    for key, cells in grid.items():
        plan, _age, cntl = key[0], key[1], key[2]
        if not is_quiknps_level_np_plan(plan):
            continue

        stats["rows_examined"] += 1
        np0_cell = issue_year.get(_identity(key))
        if np0_cell is None:
            stats["blockers"].append({
                "id": "QUIKNPS_LEVEL_NP_MISSING_ISSUE_YEAR",
                "severity": "BLOCKER",
                "table": "QuikNps",
                "detail": (
                    f"PLAN {plan} key={key}: missing source DURATION="
                    f"{SOURCE_DURATION_ISSUE_YEAR} (CNTL 00 NP0) — cannot level the page"
                ),
                "plan": plan,
                "key": key,
            })
            continue

        level_value, raw_value = np0_cell[0], np0_cell[1]
        changed = False
        for col in NP_LEVEL_COLS:
            prior = cells.get(col)
            if prior is None or round(prior[0], 8) != round(level_value, 8) or prior[1] != raw_value:
                cells[col] = _cell_tuple(np0_cell if prior is None else prior, level_value, raw_value)
                stats["cells_set"] += 1
                changed = True

        if changed:
            stats["rows_flattened"] += 1
            if len(stats["audit_samples"]) < 12:
                stats["audit_samples"].append({
                    "plan": plan,
                    "age": key[1],
                    "cntl": cntl,
                    "gender": key[3],
                    "uwclass": key[4],
                    "band": key[5],
                    "level_np": level_value,
                    "raw_value": raw_value,
                    "source_duration": SOURCE_DURATION_ISSUE_YEAR,
                })
        else:
            stats["rows_already_level"] += 1

    return stats
