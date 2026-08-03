"""Unit tests for QLAdmin payee MSEQ align (Issue #135 join rule)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from qla_core.claims_payee_mseq_align import (  # noqa: E402
    ClaimsPayeeMseqAlignError,
    align_clmp_mseq_to_claim_header,
    validate_payee_mseq_join,
)


def _clms(rows):
    return pd.DataFrame(rows)


def _clmp(rows):
    return pd.DataFrame(rows)


class TestClaimsPayeeMseqAlign(unittest.TestCase):
    def test_payees_1_n_become_header_0(self):
        clms = _clms(
            [
                {"MPOLICY": "9011156655C", "MPHASE": "1", "MSEQ": "0"},
            ]
        )
        clmp = _clmp(
            [
                {"MPOLICY": "9011156655C", "MPHASE": "1", "MSEQ": "1", "MAMOUNT": "1"},
                {"MPOLICY": "9011156655C", "MPHASE": "1", "MSEQ": "2", "MAMOUNT": "2"},
                {"MPOLICY": "9011156655C", "MPHASE": "1", "MSEQ": "3", "MAMOUNT": "3"},
                {"MPOLICY": "9011156655C", "MPHASE": "1", "MSEQ": "4", "MAMOUNT": "4"},
            ]
        )
        out, stats = align_clmp_mseq_to_claim_header(clms, clmp)
        self.assertEqual(stats["changed"], 4)
        self.assertEqual(sorted(set(out["MSEQ"].astype(str))), ["0"])
        self.assertEqual(list(out["MAMOUNT"]), ["1", "2", "3", "4"])
        gate = validate_payee_mseq_join(clms, out, require_golden=True)
        self.assertTrue(gate["ok"], gate)

    def test_idempotent_when_already_aligned(self):
        clms = _clms([{"MPOLICY": "A", "MPHASE": "1", "MSEQ": "0"}])
        clmp = _clmp(
            [
                {"MPOLICY": "A", "MPHASE": "1", "MSEQ": "0", "MAMOUNT": "10"},
                {"MPOLICY": "A", "MPHASE": "1", "MSEQ": "0", "MAMOUNT": "20"},
            ]
        )
        out1, s1 = align_clmp_mseq_to_claim_header(clms, clmp)
        out2, s2 = align_clmp_mseq_to_claim_header(clms, out1)
        self.assertEqual(s1["changed"], 0)
        self.assertEqual(s2["changed"], 0)
        self.assertTrue(out1.equals(out2))

    def test_missing_header_hard_fails(self):
        clms = _clms([{"MPOLICY": "A", "MPHASE": "1", "MSEQ": "0"}])
        clmp = _clmp([{"MPOLICY": "B", "MPHASE": "1", "MSEQ": "1", "MAMOUNT": "1"}])
        with self.assertRaises(ClaimsPayeeMseqAlignError):
            align_clmp_mseq_to_claim_header(clms, clmp)

    def test_multi_sequence_matching_payees_preserved(self):
        clms = _clms(
            [
                {"MPOLICY": "A", "MPHASE": "0", "MSEQ": "1"},
                {"MPOLICY": "A", "MPHASE": "0", "MSEQ": "2"},
            ]
        )
        clmp = _clmp(
            [
                {"MPOLICY": "A", "MPHASE": "0", "MSEQ": "1", "MAMOUNT": "10"},
                {"MPOLICY": "A", "MPHASE": "0", "MSEQ": "2", "MAMOUNT": "20"},
            ]
        )
        out, stats = align_clmp_mseq_to_claim_header(clms, clmp)
        self.assertEqual(stats["changed"], 0)
        self.assertEqual(list(out["MSEQ"]), ["1", "2"])

    def test_orphan_under_mixed_headers_joins_to_0(self):
        clms = _clms(
            [
                {"MPOLICY": "A", "MPHASE": "1", "MSEQ": "0"},
                {"MPOLICY": "A", "MPHASE": "1", "MSEQ": "2"},
            ]
        )
        clmp = _clmp([{"MPOLICY": "A", "MPHASE": "1", "MSEQ": "9", "MAMOUNT": "5"}])
        out, stats = align_clmp_mseq_to_claim_header(clms, clmp)
        self.assertEqual(stats["changed"], 1)
        self.assertEqual(out.iloc[0]["MSEQ"], "0")

    def test_orphan_without_resolvable_header_fails(self):
        clms = _clms(
            [
                {"MPOLICY": "A", "MPHASE": "0", "MSEQ": "1"},
                {"MPOLICY": "A", "MPHASE": "0", "MSEQ": "2"},
            ]
        )
        clmp = _clmp([{"MPOLICY": "A", "MPHASE": "0", "MSEQ": "9", "MAMOUNT": "5"}])
        with self.assertRaises(ClaimsPayeeMseqAlignError):
            align_clmp_mseq_to_claim_header(clms, clmp)


if __name__ == "__main__":
    unittest.main()
