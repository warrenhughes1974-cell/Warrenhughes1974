#!/usr/bin/env python3
"""
Phase R7B — Promote rate variation flags into main quikplan output path.

Applies R7A-derived PLANVALOPT / *VARY* flags to QLA_Migration/Output/quikplan.csv
and writes integration audit artifacts.

Usage:
  python plan_analysis/phase_r7b_quikplan_rate_variation_integration/run_r7b_integration.py

  # Regenerate quikplan via product setup, then integrate:
  python plan_governance/phase_p2_product_setup_runner/product_setup_runner.py --emit
  python plan_analysis/phase_r7b_quikplan_rate_variation_integration/run_r7b_integration.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from qla_core.quikplan_rate_variation_flags import (
    RateVariationEnrichmentConfig,
    integrate_quikplan_file,
)

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_QUIKPLAN = os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv")


def main() -> int:
    ap = argparse.ArgumentParser(description="R7B quikplan rate variation integration")
    ap.add_argument("--quikplan", default=DEFAULT_QUIKPLAN, help="Main quikplan.csv path")
    ap.add_argument("--skip-write", action="store_true", help="Audit only; do not overwrite quikplan.csv")
    ap.add_argument("--regenerate-quikplan", action="store_true", help="Run product setup conversion first")
    args = ap.parse_args()

    if args.regenerate_quikplan:
        import subprocess
        runner = os.path.join(ROOT, "plan_governance", "phase_p2_product_setup_runner", "product_setup_runner.py")
        print("Running product setup conversion...")
        rc = subprocess.call([sys.executable, runner, "--emit"], cwd=ROOT)
        if rc != 0:
            print(f"Product setup failed (exit {rc})")
            return rc

    if not os.path.isfile(args.quikplan):
        print(f"ERROR: quikplan not found: {args.quikplan}")
        return 1

    cfg = RateVariationEnrichmentConfig.from_env_and_defaults(ROOT)
    cfg.integration_audit_dir = HERE
    result = integrate_quikplan_file(
        args.quikplan,
        config=cfg,
        repo_root=ROOT,
        write_back=not args.skip_write,
        write_audit=True,
    )

    report = {
        "quikplan_rows": len(result.enriched_rows),
        "plans_updated": result.plans_updated,
        "planvalopt_y": result.planvalopt_y,
        "field_diffs": len(result.field_diffs),
        "validation_blockers": result.validation_blockers,
        "validation": result.validation_checks,
        "quikplan_path": args.quikplan,
        "audit_dir": HERE,
    }
    print(json.dumps({k: v for k, v in report.items() if k != "validation"}, indent=2))
    for chk in result.validation_checks:
        if chk["STATUS"] == "FAIL":
            print(f"  FAIL: {chk['CHECK_NAME']} — {chk['DETAILS']}")
    return 1 if result.validation_blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
