"""Focused unit tests for Issue 139 mixed ISWL/UNKNOWN fee suppression."""

from __future__ import annotations

import os
import tempfile
import unittest

import pandas as pd

from qla_core.modal_premium_factors import (
    issue139_fee_class,
    issue139_suppresses_mplan,
    policy_fees_suppressed,
    suppress_policy_fees,
)


class TestIssue139Classification(unittest.TestCase):
    def test_iswl_allowlist(self):
        self.assertEqual(issue139_fee_class("1658CS"), "ISWL")
        self.assertTrue(issue139_suppresses_mplan("1658CS"))

    def test_non_iswl(self):
        self.assertEqual(issue139_fee_class("17085M"), "NON_ISWL")
        self.assertFalse(issue139_suppresses_mplan("17085M"))

    def test_blank_is_unknown(self):
        self.assertEqual(issue139_fee_class(""), "UNKNOWN")
        self.assertEqual(issue139_fee_class(None), "UNKNOWN")
        self.assertTrue(issue139_suppresses_mplan(""))

    def test_flag_default_on(self):
        old = os.environ.pop("QLA_SUPPRESS_POLICY_FEES", None)
        try:
            self.assertTrue(policy_fees_suppressed())
            os.environ["QLA_SUPPRESS_POLICY_FEES"] = "0"
            self.assertFalse(policy_fees_suppressed())
            os.environ["QLA_SUPPRESS_POLICY_FEES"] = "1"
            self.assertTrue(policy_fees_suppressed())
        finally:
            if old is None:
                os.environ.pop("QLA_SUPPRESS_POLICY_FEES", None)
            else:
                os.environ["QLA_SUPPRESS_POLICY_FEES"] = old


class TestIssue139SuppressPolicyFees(unittest.TestCase):
    def _frames(self):
        ridr = pd.DataFrame(
            [
                # ISWL base — suppress
                {
                    "MPOLICY": "9010000001C",
                    "MPHASE": "1",
                    "MPLAN": "1658CS",
                    "MANNLFEE": "25.0000",
                    "MSEMIFEE": "13.0000",
                    "MQTRLFEE": "6.6250",
                    "MMTHDFEE": "2.2500",
                    "MMTHBFEE": "2.0833",
                },
                # Rider on ISWL policy — ignored for classification / fees
                {
                    "MPOLICY": "9010000001C",
                    "MPHASE": "2",
                    "MPLAN": "17085M",
                    "MANNLFEE": "",
                    "MSEMIFEE": "",
                    "MQTRLFEE": "",
                    "MMTHDFEE": "",
                    "MMTHBFEE": "",
                },
                # Non-ISWL base — passthrough
                {
                    "MPOLICY": "9010000002C",
                    "MPHASE": "1",
                    "MPLAN": "17085M",
                    "MANNLFEE": "10.4400",
                    "MSEMIFEE": "5.4288",
                    "MQTRLFEE": "2.7666",
                    "MMTHDFEE": "0.9396",
                    "MMTHBFEE": "0.8700",
                },
                # UNKNOWN base — suppress
                {
                    "MPOLICY": "9010000003C",
                    "MPHASE": "1",
                    "MPLAN": "",
                    "MANNLFEE": "12.0000",
                    "MSEMIFEE": "6.0000",
                    "MQTRLFEE": "3.0000",
                    "MMTHDFEE": "1.0000",
                    "MMTHBFEE": "1.0000",
                },
                # Non-ISWL base with ISWL rider — stays non-ISWL
                {
                    "MPOLICY": "9010000004C",
                    "MPHASE": "1",
                    "MPLAN": "1960PO",
                    "MANNLFEE": "10.0000",
                    "MSEMIFEE": "5.0000",
                    "MQTRLFEE": "2.5000",
                    "MMTHDFEE": "0.9000",
                    "MMTHBFEE": "0.8500",
                },
                {
                    "MPOLICY": "9010000004C",
                    "MPHASE": "2",
                    "MPLAN": "1658CS",
                    "MANNLFEE": "",
                    "MSEMIFEE": "",
                    "MQTRLFEE": "",
                    "MMTHDFEE": "",
                    "MMTHBFEE": "",
                },
            ]
        )
        mstr = pd.DataFrame(
            [
                {
                    "MPOLICY": "9010000001C",
                    "MMODE": "01",
                    "MBILLFRM": "2",
                    "MMODEPREM": "20.08",
                },
                {
                    "MPOLICY": "9010000002C",
                    "MMODE": "03",
                    "MBILLFRM": "1",
                    "MMODEPREM": "15.90",
                },
                {
                    "MPOLICY": "9010000003C",
                    "MMODE": "12",
                    "MBILLFRM": "1",
                    "MMODEPREM": "112.00",
                },
                {
                    "MPOLICY": "9010000004C",
                    "MMODE": "12",
                    "MBILLFRM": "1",
                    "MMODEPREM": "110.00",
                },
            ]
        )
        return ridr, mstr

    def test_mixed_suppression(self):
        ridr, mstr = self._frames()
        with tempfile.TemporaryDirectory() as td:
            audit = os.path.join(td, "policy_fee_suppression_audit.csv")
            out_r, out_m, stats = suppress_policy_fees(ridr, mstr, audit_path=audit)

            self.assertEqual(stats["iswl_policies"], 1)
            self.assertEqual(stats["non_iswl_policies"], 2)
            self.assertEqual(stats["unknown_policies"], 1)
            self.assertEqual(stats["unknown_mpolicies"], ["9010000003C"])
            self.assertEqual(stats["ridr_rows_zeroed"], 2)
            self.assertEqual(stats["iswl_rows_zeroed"], 1)
            self.assertEqual(stats["unknown_rows_zeroed"], 1)

            iswl = out_r[
                (out_r["MPOLICY"] == "9010000001C") & (out_r["MPHASE"] == "1")
            ].iloc[0]
            self.assertEqual(iswl["MANNLFEE"], "0.0000")
            self.assertEqual(iswl["MMTHBFEE"], "0.0000")

            non = out_r[
                (out_r["MPOLICY"] == "9010000002C") & (out_r["MPHASE"] == "1")
            ].iloc[0]
            self.assertEqual(non["MANNLFEE"], "10.4400")
            self.assertEqual(non["MQTRLFEE"], "2.7666")

            unk = out_r[
                (out_r["MPOLICY"] == "9010000003C") & (out_r["MPHASE"] == "1")
            ].iloc[0]
            self.assertEqual(unk["MANNLFEE"], "0.0000")

            # Non-ISWL with ISWL rider still passthrough
            non2 = out_r[
                (out_r["MPOLICY"] == "9010000004C") & (out_r["MPHASE"] == "1")
            ].iloc[0]
            self.assertEqual(non2["MANNLFEE"], "10.0000")

            # MMODEPREM: ISWL monthly bank draft 20.08 - 2.0833 = 18.00
            m1 = out_m[out_m["MPOLICY"] == "9010000001C"].iloc[0]
            self.assertEqual(m1["MMODEPREM"], "18.00")
            # Non-ISWL unchanged (no subtract)
            m2 = out_m[out_m["MPOLICY"] == "9010000002C"].iloc[0]
            self.assertEqual(m2["MMODEPREM"], "15.90")
            # UNKNOWN annual 112 - 12 = 100
            m3 = out_m[out_m["MPOLICY"] == "9010000003C"].iloc[0]
            self.assertEqual(m3["MMODEPREM"], "100.00")
            m4 = out_m[out_m["MPOLICY"] == "9010000004C"].iloc[0]
            self.assertEqual(m4["MMODEPREM"], "110.00")

            self.assertTrue(os.path.isfile(audit))
            unk_csv = os.path.join(td, "policy_fee_suppression_unknown.csv")
            self.assertTrue(os.path.isfile(unk_csv))
            unk_df = pd.read_csv(unk_csv, dtype=str)
            self.assertEqual(list(unk_df["MPOLICY"]), ["9010000003C"])


if __name__ == "__main__":
    unittest.main()
