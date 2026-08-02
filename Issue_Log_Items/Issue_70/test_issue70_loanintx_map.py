"""Focused Issue #70 unit tests: LOAN_ADV_ARREARS → LOANINTX codebook + row emit."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from qla_core.quikplan_converter import (  # noqa: E402
    _normalize_quikplan_loanintx,
    _restore_authoritative_loanintx_from_source,
    convert_quikplan_row,
    map_loan_adv_arrears_to_loanintx,
)
from qla_core.quikplan_rate_variation_flags import (  # noqa: E402
    VARY_FIELD_NAMES,
    apply_default_only_pvo_clear,
)
from qla_core.schema_constants import QUIKPLAN_SCHEMA  # noqa: E402


class Issue70LoanintxMapTests(unittest.TestCase):
    def test_codebook(self):
        cases = [
            ("0", "A", "mapped_0"),
            ("N", "A", "mapped_n"),
            ("n", "A", "mapped_n"),
            ("1", "R", "mapped_1"),
            ("1.0", "R", "mapped_1"),
            ("", "A", "blank_default"),
            (None, "A", "blank_default"),
            ("X", "A", "unknown_default"),
            ("22", "A", "unknown_default"),
        ]
        for raw, expect, tag in cases:
            got, got_tag = map_loan_adv_arrears_to_loanintx(raw)
            self.assertEqual(got, expect, raw)
            self.assertEqual(got_tag, tag, raw)

    def test_normalize_preserves_r(self):
        df = pd.DataFrame({"LOANINTX": ["A", "R", "22", "", "a"]})
        out, fixed = _normalize_quikplan_loanintx(df)
        self.assertEqual(list(out["LOANINTX"]), ["A", "R", "A", "A", "A"])
        # invalid 22 and blank → A (2); lowercase a canonicalized, not counted as invalid
        self.assertEqual(fixed, 2)

    def test_convert_row_maps_arrears(self):
        source = pd.DataFrame(
            [
                {
                    "COVERAGE_ID": "SAL OL",
                    "LOAN_ADV_ARREARS": "1",
                    "POLICY_FORM_NUM": "",
                    "DESCRIPTION": "SAL",
                }
            ]
        )
        rules = pd.DataFrame(
            [
                {
                    "Source_Field": "COVERAGE_ID",
                    "Target_Field": "PLAN",
                    "Default_Value": "",
                    "Lookup_Table": "",
                    "Join_Key": "",
                    "Transformation_Note": "",
                },
                {
                    "Source_Field": "LOAN_ADV_ARREARS",
                    "Target_Field": "LOANINTX",
                    "Default_Value": "A",
                    "Lookup_Table": "",
                    "Join_Key": "",
                    "Transformation_Note": "SKIP_TRANSLATION",
                },
            ]
        )
        audits: list = []
        row = convert_quikplan_row(
            source.iloc[0],
            source,
            rules,
            QUIKPLAN_SCHEMA,
            lookups={},
            trans_map={"A": "22"},  # must not mistranslate when SKIP / post-map applies
            cw_map={"SAL OL": "1SALOL"},
            loanintx_audits=audits,
        )
        self.assertEqual(row["LOANINTX"], "R")
        self.assertEqual(audits, [])

    def test_blank_source_audited(self):
        source = pd.DataFrame(
            [{"COVERAGE_ID": "XYZ", "LOAN_ADV_ARREARS": "", "DESCRIPTION": "x"}]
        )
        rules = pd.DataFrame(
            [
                {
                    "Source_Field": "LOAN_ADV_ARREARS",
                    "Target_Field": "LOANINTX",
                    "Default_Value": "A",
                    "Lookup_Table": "",
                    "Join_Key": "",
                    "Transformation_Note": "SKIP_TRANSLATION",
                },
            ]
        )
        audits: list = []
        row = convert_quikplan_row(
            source.iloc[0],
            source,
            rules,
            QUIKPLAN_SCHEMA,
            lookups={},
            trans_map={},
            cw_map={},
            loanintx_audits=audits,
        )
        self.assertEqual(row["LOANINTX"], "A")
        self.assertEqual(len(audits), 1)
        self.assertEqual(audits[0]["AUDIT"], "blank_default")

    def test_authoritative_arrears_survives_later_normalization(self):
        plans = ["1SALOL", "1SALML", "1SALMI", "9SLADB"]
        source = pd.DataFrame(
            [{"COVERAGE_ID": plan, "LOAN_ADV_ARREARS": "1"} for plan in plans]
        )
        output = pd.DataFrame(
            [{"PLAN": plan, "LOANINTX": "A"} for plan in plans]
        )
        restored = _restore_authoritative_loanintx_from_source(output, source)
        self.assertEqual(list(restored["LOANINTX"]), ["R", "R", "R", "R"])

    def test_default_only_pvo_clear_preserves_rated_control(self):
        default_plans = ["121PUA", "170PUA", "165PUA", "185PUA", "1OLPUA", "1POPUA", "1970PA"]
        rows = [
            {
                "PLAN": plan,
                "PLANVALOPT": "Y",
                **{field: "Y" for field in VARY_FIELD_NAMES},
            }
            for plan in default_plans
        ]
        rows.append(
            {
                "PLAN": "1960OL",
                "PLANVALOPT": "Y",
                **{field: "Y" for field in VARY_FIELD_NAMES},
            }
        )
        cleared, _count = apply_default_only_pvo_clear(rows)
        by_plan = {row["PLAN"]: row for row in cleared}
        for plan in default_plans:
            self.assertEqual(by_plan[plan]["PLANVALOPT"], "N")
            self.assertTrue(all(by_plan[plan][field] == "N" for field in VARY_FIELD_NAMES))
        self.assertEqual(by_plan["1960OL"]["PLANVALOPT"], "Y")
        self.assertTrue(all(by_plan["1960OL"][field] == "Y" for field in VARY_FIELD_NAMES))


if __name__ == "__main__":
    unittest.main()
