"""Unit tests for Issue #166 MDEPINT buckets and year-end MINTDATE overlay."""
from __future__ import annotations

import unittest

from qla_core.cso_mortality_crosswalk import ISWL_MPLAN_ALLOWLIST
from qla_core.mdepint_buckets import (
    mdepint_for_mplan,
    overlay_year_end_mintdate,
    prior_anniversary_yyyymmdd,
)
from qla_core.quikuint_loader import DEFAULT_RATE_450_PLANS


class TestMdepintIssue166(unittest.TestCase):
    def test_allowlist_unchanged(self):
        self.assertEqual(len(ISWL_MPLAN_ALLOWLIST), 8)
        self.assertNotIn("1668SP", ISWL_MPLAN_ALLOWLIST)

    def test_buckets(self):
        self.assertEqual(mdepint_for_mplan("1659C2"), "4.50")
        self.assertEqual(mdepint_for_mplan("1668SP"), "4.50")
        self.assertTrue("1668SP" in DEFAULT_RATE_450_PLANS)
        self.assertEqual(mdepint_for_mplan("1SALOL"), "2.00")
        self.assertEqual(mdepint_for_mplan("1SALML"), "2.00")
        self.assertEqual(mdepint_for_mplan("1960OL"), "3.50")
        self.assertEqual(mdepint_for_mplan("221END"), "3.50")
        self.assertIsNone(mdepint_for_mplan(""))
        self.assertIsNone(mdepint_for_mplan("9ADB10"))
        self.assertIsNone(mdepint_for_mplan("A96DAR"))

    def test_prior_anniversary(self):
        self.assertEqual(prior_anniversary_yyyymmdd("19840904", "20260831"), "20250904")
        self.assertEqual(prior_anniversary_yyyymmdd("19701201", "20260831"), "20251201")
        self.assertEqual(prior_anniversary_yyyymmdd("19610801", "20260831"), "20260801")
        self.assertEqual(prior_anniversary_yyyymmdd("19840904", "20260904"), "20260904")

    def test_overlay(self):
        self.assertEqual(
            overlay_year_end_mintdate("20251231", "1875.38", "19840904", "20260831"),
            "20250904",
        )
        self.assertEqual(
            overlay_year_end_mintdate("20251231", "0.00", "19840904", "20260831"),
            "",
        )
        self.assertEqual(
            overlay_year_end_mintdate("20260719", "100.00", "19840904", "20260831"),
            "",
        )


if __name__ == "__main__":
    unittest.main()
