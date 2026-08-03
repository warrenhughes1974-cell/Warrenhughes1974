"""Focused regression tests for the approved Issue A11 + A3 rules."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from qla_core.issue_a_plan_setup import apply_issue_a_plan_setup
from qla_core.quikplan_rate_variation_flags import (
    SegmentationStats,
    derive_plan_flags,
)
from qla_core.rate_pipeline import collapse_equal_uw_families


def _key(plan, uw):
    return (plan, "01", "00", "M", uw, "00", "0000", "00", "19000101")


def _cell(value):
    return {0: (value, value, 1)}


class IssueA11A3Tests(unittest.TestCase):
    def test_cv_and_tv_collapse_independently(self):
        grids = {
            "QuikCvs": {
                _key("P1", "NS"): _cell(1.0),
                _key("P1", "SM"): _cell(1.0),
            },
            "QuikTvs": {
                _key("P1", "NS"): _cell(2.0),
                _key("P1", "SM"): _cell(3.0),
            },
            "QuikGps": {
                _key("P1", "NS"): _cell(4.0),
                _key("P1", "SM"): _cell(4.0),
            },
        }
        collapse_equal_uw_families(grids)
        self.assertEqual({k[4] for k in grids["QuikCvs"]}, {"00"})
        self.assertEqual({k[4] for k in grids["QuikTvs"]}, {"NS", "SM"})
        self.assertEqual({k[4] for k in grids["QuikGps"]}, {"NS", "SM"})

    def test_default_only_stats_do_not_activate_variation(self):
        stats = SegmentationStats()
        stats.genders = {"0"}
        stats.uwclasses = {"00"}
        stats.bands = {"00"}
        stats.row_count = 1
        updates = derive_plan_flags({("P1", "GP"): stats})
        self.assertEqual(updates, {})

    def test_a11_sets_deficiency_and_par_when_no_dv_factors(self):
        with tempfile.TemporaryDirectory() as tmp:
            df = pd.DataFrame([{
                "PLAN": "P1", "DEFICIENCY": "Y", "PAR": "1",
                "PLANVALOPT": "N",
            }])
            out = apply_issue_a_plan_setup(df, repo_root=tmp, rates_dir=str(Path(tmp) / "rates"))
            self.assertEqual(out.at[0, "DEFICIENCY"], "N")
            self.assertEqual(out.at[0, "PAR"], "0")

    def test_a11_clears_blank_par_but_preserves_real_dv_factor_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            rates = Path(tmp) / "rates"
            rates.mkdir()
            with (rates / "QuikDvs.csv").open("w", newline="", encoding="utf-8") as fh:
                fh.write("PLAN,AGE,DV0,GENDER,UWCLASS,BAND\n")
                fh.write("261PUA,00,1.00,M,00,00\n")
            df = pd.DataFrame([
                {"PLAN": "NO_DV", "PAR": ""},
                {"PLAN": "REAL_DV", "PAR": "1"},
                {"PLAN": "261PUA", "PAR": "1"},
            ])
            out = apply_issue_a_plan_setup(df, repo_root=tmp, rates_dir=str(rates))
            self.assertEqual(out.loc[out["PLAN"] == "NO_DV", "PAR"].iloc[0], "0")
            self.assertEqual(out.loc[out["PLAN"] == "REAL_DV", "PAR"].iloc[0], "0")
            self.assertEqual(out.loc[out["PLAN"] == "261PUA", "PAR"].iloc[0], "1")

    def test_a3_clears_new_default_only_plan_codes(self):
        from qla_core.quikplan_rate_variation_flags import (
            VARY_FIELD_NAMES,
            apply_default_only_pvo_clear,
        )

        rows = [{
            "PLAN": plan,
            "PLANVALOPT": "Y",
            **{field: "Y" for field in VARY_FIELD_NAMES},
        } for plan in ("7647SP", "9L16PF")]
        out, _ = apply_default_only_pvo_clear(rows)
        for row in out:
            self.assertEqual(row["PLANVALOPT"], "N")
            self.assertTrue(all(row[field] == "N" for field in VARY_FIELD_NAMES))


if __name__ == "__main__":
    unittest.main()
