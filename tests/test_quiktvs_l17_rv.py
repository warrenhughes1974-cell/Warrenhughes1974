"""Focused tests for L17 RV QuikTvs PDAGE page expansion and identity mapping."""
from __future__ import annotations

import csv
import os
import tempfile
import unittest
from pathlib import Path

from qla_core import rate_dbf_schema as S
from qla_core import rate_factor_loader as L
from qla_core import quiktvs_l17_rv as L17
from qla_core import quiktvs_tv0_fill as TV0

ROOT = Path(__file__).resolve().parents[1]
FALLBACK_PDAGE = (
    ROOT
    / "QLA_Migration"
    / "Source"
    / "LifePRO_Extracts_20260731"
    / "PDAGE_AgeDuration_Rates_Extract_20260731.csv"
)
ACTIVE_PDAGE = ROOT / "QLA_Migration" / "Source" / "PDAGE_AgeDuration_Rates_Extract_20260630.csv"

PDAGE_HEADER = [
    "COVERAGE_ID",
    "TYPE_CODE",
    "AGE",
    "SEX",
    "BAND",
    "UWCLS",
    "DURATION",
    "VALUE1",
    "VALUE2",
    "VALUE3",
    "VALUE4",
    "VALUE5",
    "VALUE6",
    "VALUE7",
    "VALUE8",
    "VALUE9",
    "VALUE10",
]

PAGE1_VALUES = [
    "56.0937600",
    "57.8084100",
    "59.6381800",
    "61.5734500",
    "63.6042100",
    "65.7496100",
    "68.0148400",
    "70.3979700",
    "72.9043400",
    "75.5322000",
]
PAGE2_VALUES = [
    "78.2870900",
    "81.1528600",
    "84.1200700",
    "87.1862200",
    "90.3487500",
    "93.6050400",
    "96.9668500",
    "100.4464000",
    "104.0494000",
    "107.7887000",
]


def _write_pdage(path: Path, rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(PDAGE_HEADER)
        for row in rows:
            w.writerow(row)


def _minimal_complete_pdage(path: Path) -> None:
    _write_pdage(
        path,
        [
            ["L17", "RV", "0", "F", "1", "S", "1", *PAGE1_VALUES],
            ["L17", "RV", "0", "F", "1", "S", "2", *PAGE2_VALUES],
        ],
    )


def _grid_slice(grid: dict, plan: str, gender: str, age: str, uw: str) -> dict[int, str]:
    config = L.LoaderConfig(source_decimals=2)
    rows, _ = L.grid_to_factor_rows("QuikTvs", grid, config)
    out: dict[int, str] = {}
    for row in rows:
        if (
            row["PLAN"].strip() == plan
            and row["GENDER"].strip() == gender
            and row["AGE"].strip() == age
            and row["UWCLASS"].strip() == uw
        ):
            cntl = int(row["CNTL"])
            for i in range(S.N_DURATION_COLS):
                val = (row.get(f"TV{i}") or "").strip()
                if val:
                    out[cntl * 10 + i] = val
    return out


class TestL17RvPageExpansion(unittest.TestCase):
    def setUp(self):
        L17._L17_RV_COUNT_CACHE.clear()

    def test_annual_duration_from_page(self):
        self.assertEqual(L17.annual_duration_from_page(1, 1), 1)
        self.assertEqual(L17.annual_duration_from_page(1, 10), 10)
        self.assertEqual(L17.annual_duration_from_page(2, 1), 11)
        self.assertEqual(L17.annual_duration_from_page(3, 1), 21)

    def test_incomplete_source_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            incomplete = Path(td) / "pdage_incomplete.csv"
            _write_pdage(
                incomplete,
                [
                    ["L17", "RV", "0", "F", "1", "S", "1", "56.09", "", "", "", "", "", "", "", "", ""],
                ],
            )
            blockers = L17.validate_l17_rv_source_complete(str(incomplete))
            self.assertTrue(blockers)
            stats = L17.apply_l17_rv_quiktvs_grid({}, str(ROOT), str(incomplete), L.LoaderConfig())
            self.assertFalse(stats["applied"])
            self.assertTrue(stats["blockers"])

    def test_minimal_fixture_identity_tv1_not_tv0(self):
        with tempfile.TemporaryDirectory() as td:
            pdage = Path(td) / "pdage_min.csv"
            _minimal_complete_pdage(pdage)
            grid: dict = {}
            stats = L17.apply_l17_rv_quiktvs_grid(grid, str(ROOT), str(pdage), L.LoaderConfig())
            self.assertTrue(stats["applied"], stats.get("blockers"))

            vals = _grid_slice(grid, "1L17SP", "F", "00", "SM")
            self.assertNotIn(0, vals)
            self.assertAlmostEqual(float(vals[1]), 56.09, places=2)
            self.assertAlmostEqual(float(vals[2]), 57.81, places=2)
            self.assertAlmostEqual(float(vals[3]), 59.64, places=2)
            self.assertAlmostEqual(float(vals[11]), 78.29, places=2)

            factor_rows = {"QuikTvs": []}
            rows, _ = L.grid_to_factor_rows("QuikTvs", grid, L.LoaderConfig(source_decimals=2))
            factor_rows["QuikTvs"] = rows
            TV0.apply_quiktvs_tv0_blank_fill(
                factor_rows,
                {"1L17SP", "10L171", "10L172", "117JPO", "17MJPO"},
                source_decimals=2,
            )
            sp_row = next(
                r
                for r in factor_rows["QuikTvs"]
                if r["PLAN"] == "1L17SP"
                and r["GENDER"] == "F"
                and r["AGE"] == "00"
                and r["UWCLASS"] == "SM"
                and r["CNTL"] == "00"
            )
            self.assertIn(sp_row.get("TV0"), ("", ".00"))
            self.assertEqual(sp_row.get("TV1"), "56.09")

    def test_minimal_fixture_all_five_fingerprint_equal(self):
        with tempfile.TemporaryDirectory() as td:
            pdage = Path(td) / "pdage_min.csv"
            _minimal_complete_pdage(pdage)
            grid: dict = {}
            L17.apply_l17_rv_quiktvs_grid(grid, str(ROOT), str(pdage), L.LoaderConfig())

            def fp(plan: str) -> tuple:
                rows, _ = L.grid_to_factor_rows("QuikTvs", grid, L.LoaderConfig(source_decimals=2))
                sig = []
                for row in rows:
                    if row["PLAN"].strip() != plan:
                        continue
                    sig.append(tuple((row.get(f"TV{i}") or "").strip() for i in range(S.N_DURATION_COLS)))
                return tuple(sig)

            parent = fp("1L17SP")
            self.assertTrue(parent)
            for child in L17.L17_CHILD_PLANS:
                self.assertEqual(fp(child), parent)

    def test_controls_unchanged_with_minimal_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            pdage = Path(td) / "pdage_min.csv"
            _minimal_complete_pdage(pdage)
            config = L.LoaderConfig(source_decimals=2)
            grid: dict = {}
            control = ("170858", "17", "00", "M", "00", "01", "0000", "00", config.effdate)
            sal = ("1SALMI", "17", "00", "M", "00", "01", "0000", "00", config.effdate)
            grid[control] = {1: (0.0, "0", 1, False, 0, 99), 2: (8.76, "8.76", 1, False, 0, 99)}
            grid[sal] = {1: (438.0, "438.0", 1, False, 0, 99)}
            before = {control: dict(grid[control]), sal: dict(grid[sal])}
            L17.apply_l17_rv_quiktvs_grid(grid, str(ROOT), str(pdage), config)
            self.assertEqual(grid.get(control), before[control])
            self.assertEqual(grid.get(sal), before[sal])

    @unittest.skipUnless(ACTIVE_PDAGE.is_file() and FALLBACK_PDAGE.is_file(), "PDAGE fixtures missing")
    def test_resolve_fallback_when_active_lacks_l17(self):
        path, prov = L17.resolve_l17_rv_pdage_source(str(ROOT), str(ACTIVE_PDAGE))
        self.assertTrue(prov.get("fallback"))
        self.assertEqual(os.path.normpath(path), os.path.normpath(str(FALLBACK_PDAGE)))
        self.assertIn("20260731", os.path.basename(path))
        self.assertGreater(prov.get("l17_rv_rows", 0), 0)

    @unittest.skipUnless(FALLBACK_PDAGE.is_file(), "20260731 PDAGE fixture missing")
    def test_integration_real_pdage_anchor(self):
        grid: dict = {}
        stats = L17.apply_l17_rv_quiktvs_grid(grid, str(ROOT), str(ACTIVE_PDAGE), L.LoaderConfig())
        self.assertTrue(stats["applied"], stats.get("blockers"))
        vals = _grid_slice(grid, "1L17SP", "F", "00", "SM")
        self.assertAlmostEqual(float(vals[1]), 56.09, places=2)
        self.assertAlmostEqual(float(vals[11]), 78.29, places=2)


if __name__ == "__main__":
    unittest.main()
