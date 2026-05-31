#!/usr/bin/env python3
"""Phase P3C — Closed product catalog authority smoke validation."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))
RUNNER = os.path.join(ROOT, "plan_governance", "phase_p2_product_setup_runner", "product_setup_runner.py")
OUTPUT_DIR = os.path.join(ROOT, "plan_analysis", "phase_p3c_closed_product_authority")
EMITTED = os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv")
CATALOG = os.path.join(ROOT, "plan_governance", "product_catalog_crosswalk.csv")

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from qla_core.product_catalog_authority import load_closed_product_catalog, plan_contains_space


def main() -> int:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    proc = subprocess.run(
        [
            sys.executable, RUNNER,
            "--uat-overlay", "--closed-product-authority", "--strict-authority",
            "--emit", "--output-dir", os.path.join(ROOT, "QLA_Migration", "Output"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        return proc.returncode

    catalog = load_closed_product_catalog(CATALOG)
    df = pd.read_csv(EMITTED, dtype=str, keep_default_na=False)
    plans = [str(p).strip() for p in df["PLAN"].tolist()]
    outside = [p for p in plans if p not in catalog.authoritative_plan_set]
    spaced = [p for p in plans if plan_contains_space(p)]
    banned = {"1579 GPO", "0824 P DIS", "0823 960CH", "1579 G", "0824 P", "0823 9"}
    found_banned = sorted(set(plans) & banned)

    summary_path = os.path.join(OUTPUT_DIR, "closed_product_authority_summary.json")
    summary = {}
    if os.path.isfile(summary_path):
        with open(summary_path, encoding="utf-8") as fh:
            summary = json.load(fh)

    checks = {
        "rows": len(df),
        "columns": len(df.columns),
        "plans_outside_authoritative_set": len(outside),
        "plans_with_spaces": len(spaced),
        "banned_passthrough_plans_found": found_banned,
        "validation_passed": len(outside) == 0 and len(spaced) == 0 and not found_banned,
    }
    print("P3C_SMOKE_CHECKS:", json.dumps(checks, indent=2))
    print("SUMMARY_PATH:", summary_path)
    return 0 if checks["validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
