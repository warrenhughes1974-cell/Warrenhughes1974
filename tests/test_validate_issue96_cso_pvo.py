"""Focused tests for Issue #96 L17 annual-grid validator helpers."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "Issue_Log_Items" / "Issue_96" / "validate_issue96_cso_pvo.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_issue96_cso_pvo", VALIDATOR_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


V = _load_validator()


def _row(plan: str, age: str, cntl: str, gender: str, uw: str, tvs: dict[str, str]) -> dict:
    base = {
        "PLAN": plan,
        "AGE": age,
        "CNTL": cntl,
        "GENDER": gender,
        "UWCLASS": uw,
        "BAND": "01",
    }
    for i in range(10):
        base[f"TV{i}"] = tvs.get(f"TV{i}", "")
    return base


def test_tv0_equivalence_allows_non_sp_child_zero():
    assert V._tv0_values_equivalent("", ".00", child_is_sp=False)
    assert V._tv0_values_equivalent("", "0.00", child_is_sp=False)
    assert not V._tv0_values_equivalent("", ".00", child_is_sp=True)
    assert V._tv0_values_equivalent("", "", child_is_sp=True)


def test_compare_child_fingerprint_sp_exact_tv0():
    parent = {
        ("00", "00", "F", "SM", "01"): {0: "", 1: "56.09", 2: "57.81"},
    }
    child_ok = {
        ("00", "00", "F", "SM", "01"): {0: "", 1: "56.09", 2: "57.81"},
    }
    child_bad = {
        ("00", "00", "F", "SM", "01"): {0: ".00", 1: "56.09", 2: "57.81"},
    }
    assert V.compare_l17_child_fingerprint(
        parent, child_ok, child_plan="10L171", sp_plans={"10L171", "1L17SP"}
    ) == []
    fails = V.compare_l17_child_fingerprint(
        parent, child_bad, child_plan="10L171", sp_plans={"10L171", "1L17SP"}
    )
    assert any("TV0 mismatch" in f for f in fails)


def test_compare_child_fingerprint_non_sp_tv0_formatting():
    parent = {
        ("00", "00", "F", "SM", "01"): {0: "", 1: "56.09", 2: "57.81"},
    }
    child = {
        ("00", "00", "F", "SM", "01"): {0: ".00", 1: "56.09", 2: "57.81"},
    }
    assert V.compare_l17_child_fingerprint(
        parent, child, child_plan="117JPO", sp_plans={"1L17SP", "10L171", "10L172"}
    ) == []


def test_compare_child_fingerprint_detects_rate_mismatch():
    parent = {("00", "00", "F", "SM", "01"): {1: "56.09"}}
    child = {("00", "00", "F", "SM", "01"): {1: "56.10"}}
    fails = V.compare_l17_child_fingerprint(
        parent, child, child_plan="117JPO", sp_plans=set()
    )
    assert any("Dur1 mismatch" in f for f in fails)


def test_validate_l17_annual_shape_rejects_sparse_grid():
    rows = [_row("1L17SP", "00", "00", "F", "SM", {"TV1": "1.00"})]
    fails, _ = V.validate_l17_annual_shape(rows, {"1L17SP": 38}, sp_plans=set())
    assert any("sparse" in f.lower() for f in fails)


def test_validate_l17_annual_shape_accepts_matching_family():
    anchor_tvs = {
        "TV1": "56.09",
        "TV2": "57.81",
        "TV3": "59.64",
        "TV9": "72.90",
    }
    cntl01 = {"TV0": "75.53", "TV1": "78.29"}
    cntl10 = {"TV0": "1000.00"}
    rows = []
    for plan in V.L17_PLANS:
        rows.append(_row(plan, "00", "00", "F", "SM", anchor_tvs))
        rows.append(_row(plan, "00", "01", "F", "SM", cntl01))
        rows.append(_row(plan, "00", "10", "F", "SM", cntl10))
        for c in range(2, 10):
            rows.append(_row(plan, "00", f"{c:02d}", "F", "SM", {"TV1": "1.00"}))
    counts = {p: 11 for p in V.L17_PLANS}
    fails, _ = V.validate_l17_annual_shape(
        rows,
        counts,
        sp_plans={"1L17SP", "10L171", "10L172"},
    )
    assert any("sparse" in f.lower() for f in fails)

    parent_fp = V.l17_annual_fingerprint(rows, "1L17SP")
    child_fp = V.l17_annual_fingerprint(rows, "117JPO")
    child_fp[("00", "00", "F", "SM", "01")][0] = ".00"
    assert V.compare_l17_child_fingerprint(
        parent_fp,
        child_fp,
        child_plan="117JPO",
        sp_plans={"1L17SP", "10L171", "10L172"},
    ) == []


def test_integration_real_output_when_present():
    out = ROOT / "QLA_Migration" / "Output" / "rates" / "QuikTvs.csv"
    if not out.is_file():
        return
    rows = V._load(out)
    counts = __import__("collections").Counter((r.get("PLAN") or "").strip() for r in rows)
    if counts.get("1L17SP", 0) <= V.L17_SPARSE_MAX:
        return
    fails, _ = V.validate_l17_annual_shape(rows, counts)
    assert fails == [], fails
