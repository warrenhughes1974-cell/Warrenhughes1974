"""
QuikTvs L17 RV annual page expansion — durable rate emit path.

LifePRO PDAGE stores L17 RV as paged VALUE1..VALUE10 grids (DURATION page N =>
annual Dur((N-1)*10+1)..Dur(N*10)). Miss-fill previously emitted only VALUE1 per
page, producing sparse wrong QuikTvs. This module expands the full annual grid
with Issue #106 RV identity (LifePRO Dur N -> QL Dur N / TV N; Dur 0 stays empty).

Source selection: prefer active valuation PDAGE; when it has zero L17 RV rows,
use the newest dated PDAGE under QLA_Migration/Source that contains L17 RV
(audited fallback — never docs/Valuation load packages).
"""
from __future__ import annotations

import glob
import os
from typing import Any, Iterator

from qla_core import rate_dbf_schema as S
from qla_core import rate_factor_loader as L
from qla_core.dated_extract_merge import filename_extract_date

L17_COVERAGE_ID = "L17"
L17_RV_TYPE = "RV"
L17_PARENT_PLAN = "1L17SP"
L17_CHILD_PLANS = ("10L171", "10L172", "117JPO", "17MJPO")
L17_FAMILY_PLANS = frozenset({L17_PARENT_PLAN, *L17_CHILD_PLANS})

# Proof anchor for completeness gate (LifePRO F/00 band 1 standard UW S -> QL SM).
ANCHOR_AGE = "0"
ANCHOR_SEX = "F"
ANCHOR_BAND = "1"
ANCHOR_UWCLS = "S"
ANCHOR_PAGE1_VALUES = ("56.0937600", "57.8084100", "59.6381800")
ANCHOR_PAGE2_VALUE1 = "78.2870900"

# Cache L17 RV row counts per PDAGE path (discover scans many files).
_L17_RV_COUNT_CACHE: dict[str, int] = {}


def _norm_pdage_row(raw: dict) -> dict:
    return {(k or "").strip(): (v or "").strip() for k, v in raw.items()}


def _row_value(row: dict, index: int) -> str:
    key = f"VALUE{index}"
    val = row.get(key, "")
    if val:
        return val
    return row.get(f"{key}_FLOAT", "")


def count_l17_rv_rows(pdage_path: str) -> int:
    if not pdage_path or not os.path.isfile(pdage_path):
        return 0
    norm = os.path.normpath(pdage_path)
    cached = _L17_RV_COUNT_CACHE.get(norm)
    if cached is not None:
        return cached
    count = 0
    import csv

    with open(norm, encoding="utf-8-sig", errors="replace", newline="") as f:
        for raw in csv.DictReader(f):
            row = _norm_pdage_row(raw)
            if row.get("COVERAGE_ID") == L17_COVERAGE_ID and row.get("TYPE_CODE") == L17_RV_TYPE:
                count += 1
    _L17_RV_COUNT_CACHE[norm] = count
    return count


def discover_pdage_candidates(repo_root: str) -> list[tuple[str, str, int]]:
    """Return (YYYYMMDD, path, l17_rv_row_count) for PDAGE extracts under Source."""
    base = os.path.join(repo_root, "QLA_Migration", "Source")
    seen: set[str] = set()
    out: list[tuple[str, str, int]] = []
    patterns = [
        os.path.join(base, "PDAGE_AgeDuration_Rates_Extract_*.csv"),
        os.path.join(base, "**", "PDAGE_AgeDuration_Rates_Extract_*.csv"),
    ]
    for pattern in patterns:
        for path in glob.glob(pattern, recursive=True):
            path = os.path.normpath(path)
            if not os.path.isfile(path) or path in seen:
                continue
            seen.add(path)
            dt_s = filename_extract_date(path) or "00000000"
            out.append((dt_s, path, count_l17_rv_rows(path)))
    out.sort(key=lambda x: (x[0], x[1]))
    return out


def resolve_l17_rv_pdage_source(
    repo_root: str,
    active_pdage_path: str | None,
) -> tuple[str | None, dict[str, Any]]:
    """Prefer active PDAGE; fallback to newest dated file with L17 RV rows."""
    active = (active_pdage_path or "").strip()
    active_count = count_l17_rv_rows(active) if active else 0
    active_date = filename_extract_date(active) if active else None

    if active_count > 0:
        return active, {
            "mode": "active_pdage",
            "path": active,
            "extract_date": active_date,
            "l17_rv_rows": active_count,
            "fallback": False,
        }

    candidates = [(dt, path, n) for dt, path, n in discover_pdage_candidates(repo_root) if n > 0]
    if not candidates:
        return None, {
            "mode": "missing",
            "active_path": active,
            "active_extract_date": active_date,
            "active_l17_rv_rows": active_count,
            "fallback": False,
            "error": "no PDAGE extract with L17 RV rows",
        }

    dt, path, row_count = max(candidates, key=lambda x: (x[0], x[2]))
    return path, {
        "mode": "fallback_pdage",
        "path": path,
        "extract_date": dt,
        "l17_rv_rows": row_count,
        "fallback": True,
        "active_path": active,
        "active_extract_date": active_date,
        "active_l17_rv_rows": active_count,
        "warning": (
            f"active PDAGE {active_date or 'unknown'} has no L17 RV rows; "
            f"using fallback PDAGE {dt} ({row_count} L17 RV page rows)"
        ),
    }


def annual_duration_from_page(page_duration: int, value_index: int) -> int:
    """Page DURATION=N, VALUEk => annual Dur ((N-1)*10 + k)."""
    page = int(page_duration)
    vi = int(value_index)
    if page < 1 or vi < 1 or vi > S.N_DURATION_COLS:
        raise ValueError(f"invalid page/value index: page={page} value_index={vi}")
    return (page - 1) * S.N_DURATION_COLS + vi


def _anchor_rows_by_page(pdage_path: str) -> dict[int, dict]:
    import csv

    pages: dict[int, dict] = {}
    with open(pdage_path, encoding="utf-8-sig", errors="replace", newline="") as f:
        for raw in csv.DictReader(f):
            row = _norm_pdage_row(raw)
            if row.get("COVERAGE_ID") != L17_COVERAGE_ID or row.get("TYPE_CODE") != L17_RV_TYPE:
                continue
            if (
                row.get("AGE") == ANCHOR_AGE
                and row.get("SEX") == ANCHOR_SEX
                and row.get("BAND") == ANCHOR_BAND
                and row.get("UWCLS") == ANCHOR_UWCLS
            ):
                try:
                    page = int(row.get("DURATION", ""))
                except ValueError:
                    continue
                pages[page] = row
    return pages


def validate_l17_rv_source_complete(pdage_path: str) -> list[dict[str, Any]]:
    """Fail-closed completeness gate for L17 RV PDAGE expansion."""
    blockers: list[dict[str, Any]] = []
    if not pdage_path or not os.path.isfile(pdage_path):
        blockers.append({
            "id": "L17_RV_PDAGE_MISSING",
            "severity": "BLOCKER",
            "table": "QuikTvs",
            "detail": "L17 RV PDAGE source path missing",
        })
        return blockers

    if count_l17_rv_rows(pdage_path) == 0:
        blockers.append({
            "id": "L17_RV_PDAGE_EMPTY",
            "severity": "BLOCKER",
            "table": "QuikTvs",
            "detail": f"L17 RV PDAGE source has zero RV rows: {pdage_path}",
        })
        return blockers

    pages = _anchor_rows_by_page(pdage_path)
    page1 = pages.get(1)
    if page1 is None:
        blockers.append({
            "id": "L17_RV_INCOMPLETE_SOURCE",
            "severity": "BLOCKER",
            "table": "QuikTvs",
            "detail": (
                f"L17 RV anchor page 1 missing for {ANCHOR_SEX}/{ANCHOR_AGE} "
                f"BAND={ANCHOR_BAND} UWCLS={ANCHOR_UWCLS}"
            ),
        })
        return blockers

    for idx in range(1, S.N_DURATION_COLS + 1):
        val = _row_value(page1, idx)
        if not val or val in (".", "-", "-."):
            blockers.append({
                "id": "L17_RV_INCOMPLETE_SOURCE",
                "severity": "BLOCKER",
                "table": "QuikTvs",
                "detail": f"L17 RV anchor page 1 VALUE{idx} blank on {pdage_path}",
            })
            return blockers

    page2 = pages.get(2)
    if page2 is None or not _row_value(page2, 1):
        blockers.append({
            "id": "L17_RV_INCOMPLETE_SOURCE",
            "severity": "BLOCKER",
            "table": "QuikTvs",
            "detail": "L17 RV anchor page 2 VALUE1 missing",
        })
    return blockers


def iter_l17_rv_expanded_transforms(
    pdage_path: str,
    plan: str,
    config: L.LoaderConfig,
    *,
    source_label: str = "L17_RV_PDAGE_EXPANDED",
) -> Iterator[dict[str, Any]]:
    """Yield IN_SCOPE QuikTvs cells from expanded L17 RV PDAGE pages."""
    import csv

    lineno = 1
    with open(pdage_path, encoding="utf-8-sig", errors="replace", newline="") as f:
        for raw in csv.DictReader(f):
            lineno += 1
            row = _norm_pdage_row(raw)
            if row.get("COVERAGE_ID") != L17_COVERAGE_ID or row.get("TYPE_CODE") != L17_RV_TYPE:
                continue

            age = row.get("AGE", "")
            sex = row.get("SEX", "")
            band = row.get("BAND", "")
            uw = row.get("UWCLS", "")
            try:
                page_dur = int(row.get("DURATION", ""))
            except ValueError:
                continue

            gender = S.map_sex(sex)
            uwclass = S.map_uwclass(uw)
            band2 = S.map_band(band)
            if gender is None or uwclass is None or band2 is None:
                continue

            original_age = age
            emitted_age_int = age.zfill(2) if age.isdigit() else age
            age_capped = False
            if age.isdigit() and int(age) > S.MAX_AGE:
                emitted_age_int = str(S.MAX_AGE).zfill(2)
                age_capped = True
            age2 = emitted_age_int

            for vi in range(1, S.N_DURATION_COLS + 1):
                raw_val = _row_value(row, vi)
                if not raw_val or raw_val in (".", "-", "-."):
                    continue
                value = L._to_float(raw_val)
                if value is None:
                    continue
                try:
                    ql_dur = S.rv_source_duration_to_ql(annual_duration_from_page(page_dur, vi))
                except ValueError:
                    continue
                if ql_dur < 1:
                    continue
                cntl, col = S.duration_to_cntl_col(ql_dur)
                yield {
                    "status": "IN_SCOPE",
                    "coverage_id": L17_COVERAGE_ID,
                    "type_code": L17_RV_TYPE,
                    "table": "QuikTvs",
                    "plan": plan,
                    "age": age2,
                    "cntl": cntl,
                    "col": col,
                    "gender": gender,
                    "uwclass": uwclass,
                    "band": band2,
                    "source_band_raw": band,
                    "isscntry": config.isscntry,
                    "issuest": config.issuest,
                    "effdate": config.effdate,
                    "source_duration": str(annual_duration_from_page(page_dur, vi)),
                    "ql_duration": ql_dur,
                    "value": value,
                    "raw_value": raw_val,
                    "lineno": lineno,
                    "original_age": original_age,
                    "age_capped": age_capped,
                    "source": source_label,
                    "segment_resolution": "L17_RV_PAGE_EXPAND",
                    "pdage_page": page_dur,
                    "pdage_value_index": vi,
                }


def _clone_cell_meta(template: tuple, value: float, raw_value: str) -> tuple:
    if len(template) >= 6:
        return (value, raw_value, template[2], template[3], template[4], template[5])
    if len(template) >= 4:
        return (value, raw_value, template[2], template[3])
    return (value, raw_value, template[2])


def apply_l17_rv_quiktvs_grid(
    quiktvs_grid: dict[tuple, dict[int, tuple]] | None,
    repo_root: str,
    active_pdage_path: str | None,
    config: L.LoaderConfig,
) -> dict[str, Any]:
    """
    Replace L17-family QuikTvs grid cells with expanded annual L17 RV PDAGE data.

    Parent plan 1L17SP receives the expanded grid; child plans fingerprint the same
    keys (existing non-CV inheritance contract).
    """
    import collections

    grid = quiktvs_grid if quiktvs_grid is not None else {}
    stats: dict[str, Any] = {
        "plans": sorted(L17_FAMILY_PLANS),
        "parent_plan": L17_PARENT_PLAN,
        "child_plans": list(L17_CHILD_PLANS),
        "cells_removed": 0,
        "cells_injected": 0,
        "keys_removed": 0,
        "keys_injected_parent": 0,
        "keys_injected_children": 0,
        "blockers": [],
        "provenance": {},
        "applied": False,
    }

    source_path, provenance = resolve_l17_rv_pdage_source(repo_root, active_pdage_path)
    stats["provenance"] = provenance

    blockers = validate_l17_rv_source_complete(source_path or "")
    if blockers:
        stats["blockers"] = blockers
        return stats

    parent_cells: dict[tuple, dict[int, tuple]] = collections.defaultdict(dict)
    for t in iter_l17_rv_expanded_transforms(source_path, L17_PARENT_PLAN, config):
        key = (
            t["plan"], t["age"], t["cntl"], t["gender"], t["uwclass"],
            t["band"], t["isscntry"], t["issuest"], t["effdate"],
        )
        col = t["col"]
        parent_cells[key][col] = (
            t["value"], t["raw_value"], t["lineno"], t.get("age_capped", False), 0,
            S.band_collapse_priority(t.get("source_band_raw", "")),
        )

    if not parent_cells:
        stats["blockers"].append({
            "id": "L17_RV_EXPAND_EMPTY",
            "severity": "BLOCKER",
            "table": "QuikTvs",
            "detail": "L17 RV PDAGE expansion produced zero QuikTvs cells",
        })
        return stats

    remove_keys = [k for k in grid if k[0] in L17_FAMILY_PLANS]
    for key in remove_keys:
        stats["cells_removed"] += len(grid.pop(key, {}))
        stats["keys_removed"] += 1

    for key, cells in parent_cells.items():
        grid[key] = dict(cells)
        stats["keys_injected_parent"] += 1
        stats["cells_injected"] += len(cells)

    for child in L17_CHILD_PLANS:
        for key, cells in parent_cells.items():
            child_key = (child,) + key[1:]
            grid[child_key] = {
                col: _clone_cell_meta(meta, meta[0], meta[1])
                for col, meta in cells.items()
            }
            stats["keys_injected_children"] += 1
            stats["cells_injected"] += len(cells)

    stats["applied"] = True
    return stats
