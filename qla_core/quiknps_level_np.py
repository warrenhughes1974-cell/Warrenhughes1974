"""
QuikNps level net-premium flatten — durable rate emit path.

For CEN/ISWL mean-reserve families, LifePRO PDAGE NP schedules climb by duration
(DURATION=2..9) but QLAdmin QuikNps must carry a level NP1..NP9 grid keyed to each
row's own issue-year rate (LifePRO DURATION=1 / QuikNps NP0 on that key/page).

Source field: PDAGE / Rate_Table VALUE (VALUE1 in PDAGE extract).
Source duration: DURATION=1 (issue-year) -> ql_duration 0 -> NP0 on each CNTL page.
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
NP_FLATTEN_COLS = tuple(range(1, S.N_DURATION_COLS))


def is_quiknps_level_np_plan(plan: str) -> bool:
    return str(plan or "").strip() in QUIKNPS_LEVEL_NP_MPLANS


def _cell_tuple(template: tuple, level_value: float, raw_value: str) -> tuple:
    """Preserve grid cell metadata while replacing the numeric payload."""
    if len(template) >= 6:
        return (level_value, raw_value, template[2], template[3], template[4], template[5])
    if len(template) >= 4:
        return (level_value, raw_value, template[2], template[3])
    return (level_value, raw_value, template[2])


def apply_quiknps_level_np_grid(
    quiknps_grid: dict[tuple, dict[int, tuple]] | None,
) -> dict[str, Any]:
    """Flatten NP1..NP9 to each row's own NP0 level for allowlisted CEN/ISWL plans.

    Operates on the in-memory QuikNps grid before ``grid_to_factor_rows``.
    Every affected key/page (all CNTL values): NP0 is preserved; cols 1..9 receive
    the same value/raw/lineage as that row's NP0. Traditional plans are untouched.

    Returns stats plus ``blockers`` (BLOCKER issue dicts) when a row's NP0 is absent.
    """
    grid = quiknps_grid or {}
    stats: dict[str, Any] = {
        "plans": sorted(QUIKNPS_LEVEL_NP_MPLANS),
        "source_field": "VALUE1",
        "source_duration": SOURCE_DURATION_ISSUE_YEAR,
        "ql_col": NP0_QL_COL,
        "level_source": "row_np0",
        "rows_examined": 0,
        "rows_flattened": 0,
        "cells_set": 0,
        "rows_already_level": 0,
        "blockers": [],
        "audit_samples": [],
    }

    for key, cells in grid.items():
        plan, _age, cntl = key[0], key[1], key[2]
        if not is_quiknps_level_np_plan(plan):
            continue

        stats["rows_examined"] += 1
        np0_cell = cells.get(NP0_QL_COL)
        if np0_cell is None:
            stats["blockers"].append({
                "id": "QUIKNPS_LEVEL_NP_MISSING_ISSUE_YEAR",
                "severity": "BLOCKER",
                "table": "QuikNps",
                "detail": (
                    f"PLAN {plan} key={key}: missing source DURATION="
                    f"{SOURCE_DURATION_ISSUE_YEAR} (NP0) — cannot level NP1..NP9"
                ),
                "plan": plan,
                "key": key,
            })
            continue

        level_value, raw_value = np0_cell[0], np0_cell[1]
        changed = False
        for col in NP_FLATTEN_COLS:
            prior = cells.get(col)
            if prior is None or round(prior[0], 8) != round(level_value, 8):
                cells[col] = _cell_tuple(np0_cell, level_value, raw_value)
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
