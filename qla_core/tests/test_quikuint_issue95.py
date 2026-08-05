"""Unit tests for Issue #95 QuikUint bucket helpers (no full rate pipeline)."""
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from qla_core import quikuint_loader as U
from qla_core.cso_mortality_crosswalk import ISWL_MPLAN_ALLOWLIST


class TestQuikUintIssue95(unittest.TestCase):
    def test_allowlist_unchanged(self):
        self.assertEqual(len(ISWL_MPLAN_ALLOWLIST), 8)
        self.assertNotIn("1668SP", ISWL_MPLAN_ALLOWLIST)

    def test_residual_amem_safe(self):
        plans = {
            "1659C2",
            "1668SP",
            "1SALOL",
            "1SALML",
            "1SALMI",
            "1L1095",
            "9ADB10",
            "A96DAR",
        }
        residual = U.residual_mplans_amem_safe(
            plans,
            rate_450=U.DEFAULT_RATE_450_PLANS,
            rate_200=U.DEFAULT_RATE_200_PLANS,
        )
        self.assertEqual(residual, frozenset({"1SALMI", "1L1095"}))

    def test_expected_union_schedule(self):
        self.assertEqual(
            U.expected_union_schedule(),
            {
                "19800101": "11.0000",
                "19890101": "9.0000",
                "19990101": "5.0000",
                "20020101": "4.5000",
            },
        )

    def test_current_tier_and_concat(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "PDINTTBL.csv"
            with src.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(
                    f,
                    fieldnames=[
                        "IDENT",
                        "TYPE_CODE",
                        "DINT_RULE",
                        "START_DATE",
                        "END_DATE",
                        "DECLARED_RATE",
                    ],
                )
                w.writeheader()
                # CENII history (subset)
                for start, rate, rule in (
                    ("19800101", "11.00000", "0"),
                    ("19890101", "9.00000", "0"),
                    ("19990101", "5.00000", "3"),
                    ("20020101", "4.50000", "3"),
                ):
                    w.writerow(
                        {
                            "IDENT": "CENII",
                            "TYPE_CODE": "A1",
                            "DINT_RULE": rule,
                            "START_DATE": start,
                            "END_DATE": "20991231",
                            "DECLARED_RATE": rate,
                        }
                    )
                w.writerow(
                    {
                        "IDENT": "SPWL",
                        "TYPE_CODE": "A1",
                        "DINT_RULE": "3",
                        "START_DATE": "19940101",
                        "END_DATE": "20991231",
                        "DECLARED_RATE": "4.50000",
                    }
                )
                w.writerow(
                    {
                        "IDENT": "SAL01",
                        "TYPE_CODE": "C1",
                        "DINT_RULE": "1",
                        "START_DATE": "19000101",
                        "END_DATE": "20991231",
                        "DECLARED_RATE": "2.00000",
                    }
                )
                w.writerow(
                    {
                        "IDENT": "L1001",
                        "TYPE_CODE": "C1",
                        "DINT_RULE": "1",
                        "START_DATE": "20060131",
                        "END_DATE": "20991231",
                        "DECLARED_RATE": "3.50000",
                    }
                )

            qp = root / "quikplan.csv"
            with qp.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["PLAN"])
                w.writeheader()
                for p in (
                    "1658C1",
                    "1658CS",
                    "1659C2",
                    "1659CR",
                    "1659CS",
                    "1659SR",
                    "1669SR",
                    "1679CS",
                    "1668SP",
                    "1SALOL",
                    "1SALML",
                    "1SALMI",
                    "9ADB10",
                    "A96DAR",
                ):
                    w.writerow({"PLAN": p})

            cfg = {
                "pdinttbl_extract": str(src),
                "iswl_phase5": {
                    "quikuint_enabled": True,
                    "pdint_ident": "CENII",
                    "type_code": "A1",
                    "dint_rules": ["0", "3"],
                    "emit_mode": "union_merge",
                    "dint_rule_tiebreak": "3",
                    "mplan_allowlist": [
                        "1658C1",
                        "1658CS",
                        "1659C2",
                        "1659CR",
                        "1659CS",
                        "1659SR",
                        "1669SR",
                        "1679CS",
                    ],
                },
                "issue95_quikuint": {
                    "enabled": True,
                    "quikplan_csv": str(qp),
                    "rate_450_plans": sorted(U.DEFAULT_RATE_450_PLANS),
                    "rate_200_plans": sorted(U.DEFAULT_RATE_200_PLANS),
                    "spwl_1668": {
                        "mplans": ["1668SP"],
                        "pdint_ident": "SPWL",
                        "type_code": "A1",
                    },
                    "sal01": {
                        "mplans": ["1SALOL", "1SALML"],
                        "pdint_ident": "SAL01",
                        "type_code": "C1",
                    },
                    "residual_350": {
                        "pdint_ident": "L1001",
                        "type_code": "C1",
                        "exclude_prefixes": ["9", "A"],
                    },
                },
            }
            rows, status = U.load_quikuint_from_config(str(root), cfg)
            self.assertEqual(status["ROWS_CENII_ISWL"], 32)
            self.assertEqual(status["ROWS_SPWL_1668"], 1)
            self.assertEqual(status["ROWS_SAL01"], 2)
            self.assertEqual(status["ROWS_RESIDUAL_350"], 1)  # 1SALMI only
            self.assertEqual(len(rows), 36)
            by = {}
            for r in rows:
                by.setdefault(r["MPLAN"], []).append(r)
            self.assertEqual(len(by["1659C2"]), 4)
            self.assertEqual(by["1668SP"][0]["MEFFDATE"], "19940101")
            self.assertEqual(by["1668SP"][0]["MCURRATE"], "4.5000")
            self.assertEqual(by["1SALOL"][0]["MCURRATE"], "2.0000")
            self.assertEqual(by["1SALMI"][0]["MCURRATE"], "3.5000")
            self.assertNotIn("9ADB10", by)
            self.assertNotIn("A96DAR", by)


if __name__ == "__main__":
    unittest.main()
