#!/usr/bin/env python3
"""Issue #32 QuikLoan mapping validators (v1.2)."""

from __future__ import annotations

import argparse
import json
import os
import sys

import pandas as pd

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from qla_core.quikloan_converter import convert_quikloan_from_ploan, load_derivation_rules

TRACE_POLICY = "9010331768"
EXPECTED = {
    "MLOANPRIN": "3707.11",
    "MLOANBAL": "3707.11",
    "MLOANINT": "5.00",
    "MLOANINTX": "A",
    "MLOANIDT": "20250725",
    "MLOANDATE": "20250725",
    "MLOANACCR": "0.00",
    "MLOANBILL": "0.00",
}


def _default_paths() -> dict[str, str]:
    root = _REPO_ROOT
    ploan = os.environ.get("QLA_PLOAN_PATH", "").strip()
    if not ploan or not os.path.isfile(ploan):
        for name in (
            "PLOAN_LoanInformation_Extract_20260530.csv",
            "PLOAN.csv",
        ):
            p = os.path.join(root, "QLA_Migration", "Source", name)
            if os.path.isfile(p):
                ploan = p
                break
    return {
        "ploan": ploan,
        "crosswalk": os.path.join(root, "QLA_Migration", "Mapping", "Master_Crosswalk.csv"),
        "quikplan": os.path.join(root, "QLA_Migration", "Output", "quikplan.csv"),
        "quikmstr": os.path.join(root, "QLA_Migration", "Output", "quikmstr.csv"),
        "emit_csv": os.path.join(root, "plan_analysis", "phase_l1_quikloan", "quikloan_emit_candidates.csv"),
    }


def run_validation(*, write_json: str | None = None) -> dict:
    paths = _default_paths()
    rules = load_derivation_rules()
    qp = paths["quikplan"] if os.path.isfile(paths["quikplan"]) else None
    qm = paths["quikmstr"] if os.path.isfile(paths["quikmstr"]) else None

    passed_df, trace_df, exceptions_df, stats = convert_quikloan_from_ploan(
        paths["ploan"],
        rules=rules,
        crosswalk_path=paths["crosswalk"],
        quikplan_path=qp,
        quikmstr_path=qm,
    )

    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str = ""):
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    trace_row = trace_df[trace_df["SOURCE_POLICY"].astype(str).str.strip() == TRACE_POLICY]
    if len(trace_row):
        row = trace_row.iloc[0]
        for field, exp in EXPECTED.items():
            got = str(row.get(field, "")).strip()
            add(f"trace_{TRACE_POLICY}_{field}", got == exp, f"expected={exp} got={got}")
    else:
        add(f"trace_{TRACE_POLICY}_found", False, "policy not in trace")

    add("emit_row_count", 380 <= len(passed_df) <= 390, f"rows={len(passed_df)}")
    add("no_duplicate_mpolicy", passed_df["MPOLICY"].duplicated().sum() == 0, "")
    add("mloanaccr_all_zero", (passed_df["MLOANACCR"].astype(str).str.strip() == "0.00").all(), "")
    add("mloanbill_all_zero", (passed_df["MLOANBILL"].astype(str).str.strip() == "0.00").all(), "")
    rates = set(passed_df["MLOANINT"].astype(str).str.strip().unique())
    add("mloanint_rates", rates <= {"5.00", "7.40"}, f"rates={sorted(rates)}")
    intx = set(passed_df["MLOANINTX"].astype(str).str.strip().unique()) - {""}
    add("mloanintx_ar", intx <= {"A", "R"}, f"values={sorted(intx)}")
    add("mloandate_populated", passed_df["MLOANDATE"].astype(str).str.strip().ne("").all(), "")
    add("mloanidt_populated", passed_df["MLOANIDT"].astype(str).str.strip().ne("").all(), "")
    add("zero_balance_excluded", stats.get("zero_balance_held", 0) >= 500, f"held={stats.get('zero_balance_held')}")

    failed = [c for c in checks if c["status"] == "FAIL"]
    result = {
        "issue": "32",
        "version": "v1.2",
        "emit_passed": len(passed_df),
        "emit_exceptions": len(exceptions_df),
        "stats": {k: v for k, v in stats.items() if k != "quikmstr_orphan_df" and k != "report_paths"},
        "checks": checks,
        "overall": "PASS" if not failed else "FAIL",
        "failed_count": len(failed),
    }
    if write_json:
        os.makedirs(os.path.dirname(write_json) or ".", exist_ok=True)
        with open(write_json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #32 QuikLoan validators")
    parser.add_argument("--json", default="", help="Write JSON results path")
    args = parser.parse_args()
    out_path = args.json or os.path.join(
        _REPO_ROOT, "Issue_Log_Items", "Issue_32", "Issue_32_Validation_Evidence.json"
    )
    result = run_validation(write_json=out_path)
    print(json.dumps(result, indent=2))
    for c in result["checks"]:
        if c["status"] == "FAIL":
            print(f"FAIL: {c['check']} — {c.get('detail', '')}")
    return 0 if result["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
