"""Focused tests for durable QuikNps level NP1..NP9 flatten (CEN/ISWL families)."""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

from qla_core import rate_dbf_schema as S
from qla_core import rate_factor_loader as L
from qla_core.quiknps_level_np import (
    QUIKNPS_LEVEL_NP_MPLANS,
    apply_quiknps_level_np_grid,
    is_quiknps_level_np_plan,
)


def _nps_key(
    plan: str,
    age: str = "37",
    cntl: str = "00",
    gender: str = "M",
    uwclass: str = "PR",
    band: str = "00",
) -> tuple:
    return (plan, age, cntl, gender, uwclass, band, "0000", "00", "19000101")


def _cell(value: float, raw: str | None = None, lineno: int = 1) -> tuple:
    return (value, raw or str(value), lineno, False, 0, 99)


def _climbing_grid(plan: str, issue_year: float = 4.0, **key_kw) -> dict:
    key = _nps_key(plan, **key_kw)
    return {
        key: {
            0: _cell(issue_year, f"{issue_year:.7f}"),
            1: _cell(49.0, "49.0000000"),
            2: _cell(113.0, "113.0000000"),
            3: _cell(187.0, "187.0000000"),
            4: _cell(257.0, "257.0000000"),
            5: _cell(311.0, "311.0000000"),
            6: _cell(363.0, "363.0000000"),
            7: _cell(43.0, "43.0000000"),
            8: _cell(43.0, "43.0000000"),
            9: _cell(43.0, "43.0000000"),
        }
    }


def test_1658c1_m37_pr_cntl00_flattens_to_issue_year():
    grid = _climbing_grid("1658C1", issue_year=4.0, uwclass="PR")
    stats = apply_quiknps_level_np_grid(grid)
    cells = grid[_nps_key("1658C1", uwclass="PR")]
    assert cells[0][0] == 4.0
    for col in range(1, 10):
        assert cells[col][0] == 4.0
        assert cells[col][1] == "4.0000000"
    assert stats["rows_flattened"] == 1
    assert stats["cells_set"] == 9
    assert not stats["blockers"]


def test_sm_row_flattens():
    grid = _climbing_grid("1658C1", issue_year=4.0, uwclass="SM")
    apply_quiknps_level_np_grid(grid)
    cells = grid[_nps_key("1658C1", uwclass="SM")]
    assert all(cells[col][0] == 4.0 for col in range(10))


def test_all_affected_sibling_families():
    grid = {}
    for plan in sorted(QUIKNPS_LEVEL_NP_MPLANS):
        grid.update(_climbing_grid(plan, issue_year=4.0))
    stats = apply_quiknps_level_np_grid(grid)
    assert stats["rows_flattened"] == len(QUIKNPS_LEVEL_NP_MPLANS)
    for plan in QUIKNPS_LEVEL_NP_MPLANS:
        cells = grid[_nps_key(plan)]
        assert cells[0][0] == 4.0
        assert all(cells[col][0] == 4.0 for col in range(1, 10))


def test_traditional_plans_170858_1960ol_unchanged():
    grid = _climbing_grid("170858", issue_year=1.5)
    grid.update(_climbing_grid("1960OL", issue_year=2.25))
    before_170 = {col: grid[_nps_key("170858")][col][0] for col in range(10)}
    before_196 = {col: grid[_nps_key("1960OL")][col][0] for col in range(10)}
    stats = apply_quiknps_level_np_grid(grid)
    after_170 = {col: grid[_nps_key("170858")][col][0] for col in range(10)}
    after_196 = {col: grid[_nps_key("1960OL")][col][0] for col in range(10)}
    assert before_170 == after_170
    assert before_196 == after_196
    assert stats["rows_flattened"] == 0
    assert stats["rows_examined"] == 0


def test_missing_issue_year_emits_blocker_not_invented():
    key = _nps_key("1659C2")
    grid = {key: {1: _cell(49.0), 2: _cell(113.0)}}
    stats = apply_quiknps_level_np_grid(grid)
    assert len(stats["blockers"]) == 1
    assert stats["blockers"][0]["id"] == "QUIKNPS_LEVEL_NP_MISSING_ISSUE_YEAR"
    assert stats["blockers"][0]["severity"] == "BLOCKER"
    assert grid[key][1][0] == 49.0


def test_1658c1_cntl01_flattens_to_own_np0():
    """CNTL01 M/37 PR — NP0=49; climbing NP1..NP9 must level to 49."""
    key = _nps_key("1658C1", cntl="01", uwclass="PR")
    climbing = [49.0, 55.0, 61.0, 67.0, 73.0, 80.0, 86.0, 93.0, 100.0, 107.0]
    grid = {
        key: {
            col: _cell(climbing[col], f"{climbing[col]:.7f}")
            for col in range(10)
        }
    }
    stats = apply_quiknps_level_np_grid(grid)
    cells = grid[key]
    assert cells[0][0] == 49.0
    for col in range(1, 10):
        assert cells[col][0] == 49.0
        assert cells[col][1] == "49.0000000"
    assert stats["rows_flattened"] == 1
    assert stats["cells_set"] == 9
    assert stats["level_source"] == "row_np0"


def test_1658c1_cntl02_and_later_pages_flatten_to_own_np0():
    """CNTL02+ pages level NP1..NP9 to that page's NP0, not CNTL00."""
    cntl02_np = [113.0, 121.0, 128.0, 136.0, 144.0, 152.0, 160.0, 168.0, 179.0, 179.0]
    key02 = _nps_key("1658C1", cntl="02", uwclass="PR")
    key09 = _nps_key("1658C1", cntl="09", uwclass="PR")
    grid = {
        key02: {col: _cell(cntl02_np[col], f"{cntl02_np[col]:.7f}") for col in range(10)},
        key09: {0: _cell(200.0, "200.0000000"), 1: _cell(210.0), 2: _cell(220.0)},
    }
    stats = apply_quiknps_level_np_grid(grid)
    assert grid[key02][0][0] == 113.0
    assert all(grid[key02][col][0] == 113.0 for col in range(1, 10))
    assert grid[key09][0][0] == 200.0
    assert grid[key09][1][0] == 200.0
    assert grid[key09][2][0] == 200.0
    assert stats["rows_flattened"] == 2
    assert stats["rows_examined"] == 2


def test_1658c1_all_cntl_pages_independent_level_source():
    """Each CNTL page uses its own NP0 — not cross-page CNTL00 value."""
    grid = {}
    cntl00 = [4.0] + [49.0 + i * 6 for i in range(9)]
    cntl01 = [49.0, 55.0, 61.0, 67.0, 73.0, 80.0, 86.0, 93.0, 100.0, 107.0]
    for cntl, values in (("00", cntl00), ("01", cntl01)):
        key = _nps_key("1658C1", cntl=cntl, uwclass="PR")
        grid[key] = {col: _cell(values[col], f"{values[col]:.7f}") for col in range(10)}
    stats = apply_quiknps_level_np_grid(grid)
    assert grid[_nps_key("1658C1", cntl="00")][0][0] == 4.0
    assert all(grid[_nps_key("1658C1", cntl="00")][col][0] == 4.0 for col in range(1, 10))
    assert grid[_nps_key("1658C1", cntl="01")][0][0] == 49.0
    assert all(grid[_nps_key("1658C1", cntl="01")][col][0] == 49.0 for col in range(1, 10))
    assert stats["rows_flattened"] == 2


def test_sibling_family_cntl01_flattens():
    key = _nps_key("1659CS", cntl="01")
    grid = {key: {0: _cell(7.5, "7.5000000"), 1: _cell(8.0), 2: _cell(9.0)}}
    apply_quiknps_level_np_grid(grid)
    assert grid[key][0][0] == 7.5
    assert grid[key][1][0] == 7.5
    assert grid[key][2][0] == 7.5


def test_non_allowlisted_cntl01_unchanged():
    key = ("170858", "37", "01", "M", "PR", "00", "0000", "00", "19000101")
    grid = {key: {0: _cell(99.0), 1: _cell(100.0)}}
    stats = apply_quiknps_level_np_grid(grid)
    assert stats["rows_examined"] == 0
    assert grid[key][1][0] == 100.0


def test_quiktvs_grid_untouched_by_nps_module():
    tvs_key = ("1658C1", "37", "00", "M", "PR", "00", "0000", "00", "19000101")
    tvs_grid = {
        tvs_key: {
            0: _cell(0.0, ""),
            1: _cell(1.23, "1.23"),
        }
    }
    before = dict(tvs_grid[tvs_key])
    apply_quiknps_level_np_grid({})
    assert tvs_grid[tvs_key] == before


def test_grid_to_factor_rows_preserves_np0_and_levels_np1_plus():
    grid = _climbing_grid("1658C1")
    apply_quiknps_level_np_grid(grid)
    config = L.LoaderConfig(source_decimals=2)
    rows, _ = L.grid_to_factor_rows("QuikNps", grid, config)
    assert len(rows) == 1
    row = rows[0]
    assert row["NP0"] == "4.00"
    for i in range(1, 10):
        assert row[f"NP{i}"] == "4.00"


def test_end_to_end_from_rate_table_source(tmp_path: Path):
    """658 CEN I NP M/37/P — DURATION=1 VALUE=4; DURATION=2 VALUE=49 (climbing)."""
    rate_csv = tmp_path / "rates.csv"
    with rate_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["COVERAGE_ID", "TYPE_CODE", "AGE", "SEX", "BAND", "UWCLASS", "DURATION", "VALUE"])
        w.writerow(["658 CEN I", "NP", "37", "M", "1", "P", "1", "4.0000000"])
        w.writerow(["658 CEN I", "NP", "37", "M", "1", "P", "2", "49.0000000"])
        w.writerow(["658 CEN I", "NP", "37", "M", "1", "P", "3", "113.0000000"])
        w.writerow(["170858", "NP", "37", "M", "1", "P", "1", "1.5000000"])
        w.writerow(["170858", "NP", "37", "M", "1", "P", "2", "2.5000000"])

    cov2plan = {"658 CEN I": "1658C1", "170858": "170858"}
    config = L.LoaderConfig()
    transformed = list(L.transform_source(str(rate_csv), cov2plan, config))
    in_scope = [t for t in transformed if t["status"] == "IN_SCOPE" and t["table"] == "QuikNps"]
    grids, collisions, _ = L.build_factor_grid(iter(in_scope), config)
    assert not collisions

    pre_170 = grids["QuikNps"][_nps_key("170858")][1][0]
    stats = apply_quiknps_level_np_grid(grids["QuikNps"])
    post_170 = grids["QuikNps"][_nps_key("170858")][1][0]
    assert post_170 == pre_170

    iswl_cells = grids["QuikNps"][_nps_key("1658C1")]
    assert iswl_cells[0][0] == 4.0
    assert all(iswl_cells[col][0] == 4.0 for col in range(1, 10))
    assert stats["rows_flattened"] == 1
    assert stats["source_duration"] == 1
    assert stats["source_field"] == "VALUE1"


def test_is_quiknps_level_np_plan_helper():
    assert is_quiknps_level_np_plan("1658C1")
    assert is_quiknps_level_np_plan("1668SP")
    assert not is_quiknps_level_np_plan("170858")
    assert not is_quiknps_level_np_plan("1960OL")
