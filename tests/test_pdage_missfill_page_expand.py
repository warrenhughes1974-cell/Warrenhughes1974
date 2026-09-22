"""PDAGE miss-fill stores ten policy years per page, not the page number."""
from __future__ import annotations

import unittest

from qla_core import pdage_missfill as PDM
from qla_core import rate_factor_loader as L


def _l05_page(page, values):
    row = {
        "COVERAGE_ID": "L05 10Y",
        "TYPE_CODE": "NP",
        "AGE": "28",
        "SEX": "F",
        "BAND": "1",
        "UWCLS": "S",
        "DURATION": str(page),
    }
    for i in range(1, 11):
        row[f"VALUE{i}"] = values[i - 1] if i <= len(values) else ""
    return row


class PageExpandTests(unittest.TestCase):
    def test_page_four_value_two_is_duration_32(self):
        rows = PDM._pdage_page_to_rate_table_rows(
            _l05_page(4, ["15.59", "15.59", "15.76"])
        )
        by_dur = {int(r[6]): r[7] for r in rows}
        self.assertEqual(by_dur[31], "15.59")
        self.assertEqual(by_dur[32], "15.59")
        self.assertEqual(by_dur[33], "15.76")

    def test_page_one_keeps_years_between_the_old_page_starts(self):
        rows = PDM._pdage_page_to_rate_table_rows(
            _l05_page(1, ["1.38", "1.44", "1.50", "1.57"])
        )
        by_dur = {int(r[6]): r[7] for r in rows}
        self.assertEqual(by_dur[1], "1.38")
        self.assertEqual(by_dur[2], "1.44")
        self.assertEqual(by_dur[3], "1.50")
        self.assertEqual(by_dur[4], "1.57")

    def test_zeros_are_omitted(self):
        rows = PDM._pdage_page_to_rate_table_rows(
            _l05_page(6, ["78.19", "0.00", ""])
        )
        self.assertEqual([int(r[6]) for r in rows], [51])

    def test_duration_32_lands_on_quiknps_cntl_03_np1(self):
        config = L.LoaderConfig()
        emitted = list(PDM._transform_rate_table_row(
            ["L05 10Y", "NP", "28", "F", "1", "S", "32", "15.59"],
            1,
            {"L05 10Y": "5L0510"},
            config,
            None,
            None,
        ))
        self.assertEqual(len(emitted), 1)
        cell = emitted[0]
        self.assertEqual(cell["status"], "IN_SCOPE")
        self.assertEqual(cell["plan"], "5L0510")
        self.assertEqual(cell["ql_duration"], 31)
        self.assertEqual(cell["cntl"], "03")
        self.assertEqual(cell["col"], 1)
        self.assertEqual(cell["uwclass"], "ST")


class ZeroTerminalClassTests(unittest.TestCase):
    def test_standard_class_gets_a_zero_terminal_row(self):
        factor_rows = {
            "QuikNps": [{
                "PLAN": "5L0510", "AGE": "28", "CNTL": "03",
                "NP0": "15.59", "NP1": "15.59",
                "GENDER": "F", "UWCLASS": "ST", "BAND": "00",
                "ISSCNTRY": "0000", "ISSUEST": "00", "EFFDATE": "19000101",
            }],
            "QuikTvs": [{
                "PLAN": "5L0510", "AGE": "28", "CNTL": "00",
                **{f"TV{i}": ".00" for i in range(10)},
                "GENDER": "F", "UWCLASS": "00", "BAND": "00",
                "ISSCNTRY": "0000", "ISSUEST": "00", "EFFDATE": "19000101",
            }],
        }
        key_rows = {"QuikPlTv": [{
            "PLAN": "5L0510", "GENDER": "F", "UWCLASS": "00", "BAND": "00",
            "ISSCNTRY": "0000", "ISSUEST": "00", "EFFDATE": "19000101",
            "MORT": "A1", "RSVINT": "C", "RSVMETH": "3",
        }]}
        stats = PDM.restore_zero_terminal_class_rows(factor_rows, key_rows)
        st = [
            r for r in factor_rows["QuikTvs"]
            if r["UWCLASS"] == "ST" and r["AGE"] == "28"
        ]
        self.assertEqual(len(st), 1)
        self.assertEqual(st[0]["TV0"], ".00")
        self.assertEqual(stats["classes_added"], 1)
        self.assertTrue(any(r["UWCLASS"] == "ST" for r in key_rows["QuikPlTv"]))

    def test_nonzero_terminal_grid_is_not_copied(self):
        factor_rows = {
            "QuikNps": [{
                "PLAN": "1L14SC", "AGE": "45", "CNTL": "00",
                "GENDER": "F", "UWCLASS": "PQ", "BAND": "00",
                "ISSCNTRY": "0000", "ISSUEST": "00", "EFFDATE": "19000101",
            }],
            "QuikTvs": [{
                "PLAN": "1L14SC", "AGE": "45", "CNTL": "00",
                "TV0": ".00", "TV1": "12.92",
                "GENDER": "F", "UWCLASS": "NT", "BAND": "00",
                "ISSCNTRY": "0000", "ISSUEST": "00", "EFFDATE": "19000101",
            }],
        }
        before = len(factor_rows["QuikTvs"])
        stats = PDM.restore_zero_terminal_class_rows(factor_rows, {"QuikPlTv": []})
        self.assertEqual(stats["rows_added"], 0)
        self.assertEqual(len(factor_rows["QuikTvs"]), before)

    def test_667_art_is_left_to_its_own_patch(self):
        factor_rows = {
            "QuikNps": [{
                "PLAN": "5667AT", "AGE": "35", "CNTL": "00",
                "GENDER": "M", "UWCLASS": "PR", "BAND": "00",
                "ISSCNTRY": "0000", "ISSUEST": "00", "EFFDATE": "19000101",
            }],
            "QuikTvs": [],
        }
        stats = PDM.restore_zero_terminal_class_rows(factor_rows, {"QuikPlTv": []})
        self.assertEqual(stats["rows_added"], 0)
        self.assertEqual(factor_rows["QuikTvs"], [])


if __name__ == "__main__":
    unittest.main()
