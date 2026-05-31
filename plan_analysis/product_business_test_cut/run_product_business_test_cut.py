#!/usr/bin/env python3
"""
Phase PRODUCT-CUT-1 — Product Business Test Cut packaging and validation.

Usage:
  python plan_analysis/product_business_test_cut/run_product_business_test_cut.py

  python plan_analysis/product_business_test_cut/run_product_business_test_cut.py --regenerate
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)

from qla_core.product_business_test_cut import CUT_LABEL, CUT_VERSION, run_product_cut_validation


def _run(cmd: list[str], label: str) -> int:
    print(f"\n=== {label} ===")
    rc = subprocess.call(cmd, cwd=ROOT)
    if rc != 0:
        print(f"WARNING: {label} exited {rc}")
    return rc


def regenerate_outputs() -> int:
    rc = 0
    rc |= _run([
        sys.executable,
        os.path.join(ROOT, "plan_governance", "phase_p2_product_setup_runner", "product_setup_runner.py"),
        "--uat-overlay", "--closed-product-authority", "--strict-authority",
        "--emit", "--output-dir", os.path.join(ROOT, "QLA_Migration", "Output"),
    ], "Product Setup (P3C quikplan)")

    rc |= _run([
        sys.executable,
        os.path.join(ROOT, "plan_analysis", "phase_p3e_quikridr_authority_alignment",
                     "phase_p3e_quikridr_authority_runner.py"),
        "--quikridr", os.path.join(ROOT, "QLA_Migration", "Output", "quikridr.csv"),
        "--quikplan", os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv"),
        "--ppben", os.path.join(ROOT, "QLA_Migration", "Source", "PPBEN.csv"),
        "--master-crosswalk", os.path.join(ROOT, "Master_Crosswalk.csv"),
        "--product-catalog", os.path.join(ROOT, "plan_governance", "product_catalog_crosswalk.csv"),
        "--closed-mplan-authority", "--emit",
    ], "quikridr MPLAN alignment (P3E)")

    rc |= _run([
        sys.executable,
        os.path.join(ROOT, "plan_analysis", "phase_r7b_quikplan_rate_variation_integration",
                     "run_r7b_integration.py"),
    ], "Rate variation flags (R7B)")

    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description=f"{CUT_VERSION} {CUT_LABEL}")
    ap.add_argument("--regenerate", action="store_true", help="Regenerate quikplan/quikridr then validate")
    ap.add_argument("--output-dir", default=HERE, help="Validation output directory")
    args = ap.parse_args()

    if args.regenerate:
        regenerate_outputs()

    result = run_product_cut_validation(ROOT, args.output_dir)
    report = {
        "cut_version": result["cut_version"],
        "cut_label": result["cut_label"],
        "quikplan_rows": result["quikplan_rows"],
        "planvalopt_y": result["planvalopt_y"],
        "validation_blockers": result["validation_blockers"],
        "summary": os.path.relpath(result["summary"], ROOT),
    }
    print(json.dumps(report, indent=2))
    for chk in result["checks"]:
        if chk["STATUS"] == "FAIL":
            print(f"  FAIL: {chk['CHECK_NAME']} — {chk['DETAILS']}")
    return 1 if result["validation_blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
