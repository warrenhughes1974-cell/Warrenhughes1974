"""Unit tests for Issue #172 shared UW-class key replication (Option K)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from qla_core.issue172_shared_uw_keys import (
    Issue172ConflictError,
    apply_shared_uw_key_replication,
    apply_to_rates_directory,
    feature_enabled,
    load_manifest,
)


def _factor(plan, age, cntl, gender, uw, cv0="1.00", **extra):
    row = {
        "PLAN": plan,
        "AGE": age,
        "CNTL": cntl,
        "CV0": cv0,
        "CV1": "2.00",
        "GENDER": gender,
        "UWCLASS": uw,
        "BAND": "00",
        "ISSCNTRY": "0000",
        "ISSUEST": "00",
        "EFFDATE": "19000101",
    }
    row.update(extra)
    return row


def _key(plan, gender, uw, mort="A1"):
    return {
        "PLAN": plan,
        "GENDER": gender,
        "UWCLASS": uw,
        "BAND": "00",
        "ISSCNTRY": "0000",
        "ISSUEST": "00",
        "EFFDATE": "19000101",
        "MORT": mort,
        "ETIMORT": "C1",
        "NFOINT": "A",
        "INTMETHCV": "0",
    }


def _mini_manifest(path: Path) -> Path:
    path.write_text(
        "plan,family,auth_uw,target_uw_list,proof,factor_tables,key_tables,notes\n"
        "1659C2,CV,ST,PR,B,QuikCvs,QuikPlCv,primary\n"
        "1L14SC,L14_RESERVE,NT,PQ|PR|ST,A,"
        "QuikTvs|QuikNps|QuikCvs|QuikNff,"
        "QuikPlTv|QuikPlCv|QuikPlDb|QuikPlDv,absorb\n",
        encoding="utf-8",
    )
    return path


class TestIssue172SharedUwKeys(unittest.TestCase):
    def test_feature_flag_default_on(self):
        self.assertTrue(feature_enabled({}))
        self.assertTrue(feature_enabled({"QLA_ISSUE172_SHARED_UW_KEYS": "1"}))
        self.assertFalse(feature_enabled({"QLA_ISSUE172_SHARED_UW_KEYS": "0"}))
        self.assertFalse(feature_enabled({"QLA_ISSUE172_SHARED_UW_KEYS": "off"}))

    def test_feature_off_no_rows_changed(self):
        factors = {
            "QuikCvs": [_factor("1659C2", "00", "00", "F", "ST")],
        }
        keys = {"QuikPlCv": [_key("1659C2", "F", "ST")]}
        before_f = [dict(r) for r in factors["QuikCvs"]]
        before_k = [dict(r) for r in keys["QuikPlCv"]]
        with tempfile.TemporaryDirectory() as td:
            man = _mini_manifest(Path(td) / "m.csv")
            summary = apply_shared_uw_key_replication(
                factors, keys, manifest_path=man, env={"QLA_ISSUE172_SHARED_UW_KEYS": "0"},
            )
        self.assertTrue(summary["skipped"])
        self.assertEqual(factors["QuikCvs"], before_f)
        self.assertEqual(keys["QuikPlCv"], before_k)

    def test_1659c2_st_to_pr_no_nt_pq(self):
        factors = {
            "QuikCvs": [
                _factor("1659C2", "00", "00", "F", "ST"),
                _factor("1659C2", "00", "00", "M", "ST"),
                _factor("1658C1", "00", "00", "F", "PR", cv0="9.99"),
                _factor("1658C1", "00", "00", "F", "ST", cv0="8.88"),
            ],
        }
        keys = {
            "QuikPlCv": [
                _key("1659C2", "F", "ST"),
                _key("1659C2", "M", "ST"),
                _key("1658C1", "F", "PR"),
                _key("1658C1", "F", "ST"),
            ],
        }
        with tempfile.TemporaryDirectory() as td:
            man = _mini_manifest(Path(td) / "m.csv")
            # Manifest includes L14 tables we do not populate — plan-absent skip.
            for t in ("QuikTvs", "QuikNps", "QuikNff"):
                factors.setdefault(t, [])
            for t in ("QuikPlTv", "QuikPlDb", "QuikPlDv"):
                keys.setdefault(t, [])
            summary = apply_shared_uw_key_replication(factors, keys, manifest_path=man)

        cvs = [r for r in factors["QuikCvs"] if r["PLAN"] == "1659C2"]
        classes = sorted({r["UWCLASS"] for r in cvs})
        self.assertEqual(classes, ["PR", "ST"])
        self.assertEqual(summary["inserted"], 4)  # 2 factor + 2 key
        # Category C control untouched and still distinct
        c1 = [r for r in factors["QuikCvs"] if r["PLAN"] == "1658C1"]
        self.assertEqual(len(c1), 2)
        self.assertNotEqual(c1[0]["CV0"], c1[1]["CV0"])

    def test_idempotent_rerun(self):
        factors = {"QuikCvs": [_factor("1659C2", "00", "00", "F", "ST")]}
        keys = {"QuikPlCv": [_key("1659C2", "F", "ST")]}
        with tempfile.TemporaryDirectory() as td:
            man = Path(td) / "m.csv"
            man.write_text(
                "plan,family,auth_uw,target_uw_list,proof,factor_tables,key_tables,notes\n"
                "1659C2,CV,ST,PR,B,QuikCvs,QuikPlCv,primary\n",
                encoding="utf-8",
            )
            s1 = apply_shared_uw_key_replication(factors, keys, manifest_path=man)
            n1 = len(factors["QuikCvs"])
            s2 = apply_shared_uw_key_replication(factors, keys, manifest_path=man)
        self.assertEqual(s1["inserted"], 2)
        self.assertEqual(s2["inserted"], 0)
        self.assertGreater(s2["identical_noop"], 0)
        self.assertEqual(len(factors["QuikCvs"]), n1)

    def test_conflict_fail_closed(self):
        factors = {
            "QuikCvs": [
                _factor("1659C2", "00", "00", "F", "ST", cv0="1.00"),
                _factor("1659C2", "00", "00", "F", "PR", cv0="9.99"),
            ],
        }
        keys = {"QuikPlCv": [_key("1659C2", "F", "ST")]}
        with tempfile.TemporaryDirectory() as td:
            man = Path(td) / "m.csv"
            man.write_text(
                "plan,family,auth_uw,target_uw_list,proof,factor_tables,key_tables,notes\n"
                "1659C2,CV,ST,PR,B,QuikCvs,QuikPlCv,primary\n",
                encoding="utf-8",
            )
            with self.assertRaises(Issue172ConflictError):
                apply_shared_uw_key_replication(factors, keys, manifest_path=man)

    def test_l14_table_scope_and_unrelated_untouched(self):
        factors = {
            "QuikCvs": [_factor("1L14SC", "45", "00", "F", "NT", cv0="5.00")],
            "QuikTvs": [
                {
                    "PLAN": "1L14SC", "AGE": "45", "CNTL": "00", "TV0": "6.00",
                    "GENDER": "F", "UWCLASS": "NT", "BAND": "00",
                    "ISSCNTRY": "0000", "ISSUEST": "00", "EFFDATE": "19000101",
                }
            ],
            "QuikNps": [
                {
                    "PLAN": "1L14SC", "AGE": "45", "CNTL": "00", "NP0": "7.00",
                    "GENDER": "F", "UWCLASS": "NT", "BAND": "00",
                    "ISSCNTRY": "0000", "ISSUEST": "00", "EFFDATE": "19000101",
                }
            ],
            "QuikNff": [
                {
                    "PLAN": "1L14SC", "AGE": "45", "CNTL": "00", "NFF0": "8.00",
                    "GENDER": "F", "UWCLASS": "NT", "BAND": "00",
                    "ISSCNTRY": "0000", "ISSUEST": "00", "EFFDATE": "19000101",
                }
            ],
            "QuikGps": [
                {
                    "PLAN": "1L14SC", "AGE": "45", "CNTL": "00", "GP0": "21.12",
                    "GENDER": "F", "UWCLASS": "NT", "BAND": "00",
                    "ISSCNTRY": "0000", "ISSUEST": "00", "EFFDATE": "19000101",
                }
            ],
        }
        keys = {
            "QuikPlCv": [_key("1L14SC", "F", "NT")],
            "QuikPlTv": [_key("1L14SC", "F", "NT")],
            "QuikPlDb": [_key("1L14SC", "F", "NT")],
            "QuikPlDv": [_key("1L14SC", "F", "NT")],
            "QuikPlGp": [_key("1L14SC", "F", "NT")],
        }
        gps_before = [dict(r) for r in factors["QuikGps"]]
        gp_key_before = [dict(r) for r in keys["QuikPlGp"]]
        with tempfile.TemporaryDirectory() as td:
            man = Path(td) / "m.csv"
            man.write_text(
                "plan,family,auth_uw,target_uw_list,proof,factor_tables,key_tables,notes\n"
                "1L14SC,L14_RESERVE,NT,PQ|PR|ST,A,"
                "QuikTvs|QuikNps|QuikCvs|QuikNff,"
                "QuikPlTv|QuikPlCv|QuikPlDb|QuikPlDv,absorb\n",
                encoding="utf-8",
            )
            apply_shared_uw_key_replication(factors, keys, manifest_path=man)

        for table in ("QuikCvs", "QuikTvs", "QuikNps", "QuikNff"):
            classes = sorted({r["UWCLASS"] for r in factors[table]})
            self.assertEqual(classes, ["NT", "PQ", "PR", "ST"], table)
        for table in ("QuikPlCv", "QuikPlTv", "QuikPlDb", "QuikPlDv"):
            classes = sorted({r["UWCLASS"] for r in keys[table]})
            self.assertEqual(classes, ["NT", "PQ", "PR", "ST"], table)
        # Premium / unrelated not in manifest → unchanged
        self.assertEqual(factors["QuikGps"], gps_before)
        self.assertEqual(keys["QuikPlGp"], gp_key_before)

    def test_repo_manifest_only_approved_scopes(self):
        root = Path(__file__).resolve().parents[2]
        man = root / "Issue_Log_Items" / "Issue_172" / "business_inputs" / (
            "issue172_shared_uw_keys_manifest.csv"
        )
        entries = load_manifest(man)
        self.assertEqual(len(entries), 2)
        plans = {e["plan"] for e in entries}
        self.assertEqual(plans, {"1659C2", "1L14SC"})
        primary = next(e for e in entries if e["plan"] == "1659C2")
        self.assertEqual(primary["auth_uw"], "ST")
        self.assertEqual(primary["targets"], ["PR"])
        self.assertEqual(primary["factor_tables"], ["QuikCvs"])
        self.assertEqual(primary["key_tables"], ["QuikPlCv"])
        self.assertNotIn("NT", primary["targets"])
        self.assertNotIn("PQ", primary["targets"])
        l14 = next(e for e in entries if e["plan"] == "1L14SC")
        self.assertEqual(l14["auth_uw"], "NT")
        self.assertEqual(l14["targets"], ["PQ", "PR", "ST"])
        self.assertNotIn("1L05", str(l14))
        self.assertIn("not L05", l14["notes"])

    def test_apply_to_rates_directory_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            rates = Path(td) / "rates"
            rates.mkdir()
            man = Path(td) / "m.csv"
            man.write_text(
                "plan,family,auth_uw,target_uw_list,proof,factor_tables,key_tables,notes\n"
                "1659C2,CV,ST,PR,B,QuikCvs,QuikPlCv,primary\n",
                encoding="utf-8",
            )
            # Write minimal CSVs
            (rates / "QuikCvs.csv").write_text(
                "PLAN,AGE,CNTL,CV0,GENDER,UWCLASS,BAND,ISSCNTRY,ISSUEST,EFFDATE\n"
                "1659C2,00,00,1.00,F,ST,00,0000,00,19000101\n",
                encoding="utf-8",
            )
            (rates / "QuikPlCv.csv").write_text(
                "PLAN,GENDER,UWCLASS,BAND,ISSCNTRY,ISSUEST,EFFDATE,MORT\n"
                "1659C2,F,ST,00,0000,00,19000101,A1\n",
                encoding="utf-8",
            )
            summary = apply_to_rates_directory(
                rates, repo_root=Path(td), manifest_path=man,
            )
            self.assertEqual(summary["inserted"], 2)
            cvs = (rates / "QuikCvs.csv").read_text(encoding="utf-8")
            self.assertIn(",PR,", cvs)
            self.assertIn(",ST,", cvs)


if __name__ == "__main__":
    unittest.main()
