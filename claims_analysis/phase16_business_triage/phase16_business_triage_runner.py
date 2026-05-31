#!/usr/bin/env python3
"""
Phase 16 — Business triage & targeted remediation governance orchestrator.

Runs Phase 16A-16F in sequence. Does NOT modify stable engines or app.py.
"""

import argparse
import logging
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_OUTPUT = os.path.join(ROOT, "phase16_business_triage_remediation")

logger = logging.getLogger("phase16_runner")


def run_script(script_name, output_dir, verbose):
    script_path = os.path.join(SCRIPT_DIR, script_name)
    cmd = [sys.executable, script_path, "--output", output_dir]
    if verbose:
        cmd.append("--verbose")
    logger.info("Running %s", script_name)
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        logger.error("%s failed with exit code %s", script_name, result.returncode)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Phase 16 business triage orchestrator.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    os.makedirs(args.output, exist_ok=True)

    scripts = [
        "remaining_orphan_triage_engine.py",
        "surrender_offset_business_triage_engine.py",
        "parent_claim_remediation_prioritization_engine.py",
        "production_readiness_forecast_engine.py",
        "qa_uat_business_review_package_engine.py",
        "phase16_decision_checkpoint_engine.py",
    ]
    for script in scripts:
        if not run_script(script, args.output, args.verbose):
            return 1

    summary_path = os.path.join(args.output, "phase16_execution_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 16 Business Triage & Targeted Remediation Governance — Complete ===",
            "",
            "Sub-phases executed:",
            "  16A — Remaining orphan root-cause triage",
            "  16B — Surrender offset business triage workbench",
            "  16C — Parent-claim remediation prioritization",
            "  16D — Production readiness threshold forecasting",
            "  16E — QA/UAT business review packages",
            "  16F — Pre-production decision checkpoint",
            "",
            f"Output: {os.path.abspath(args.output)}",
            "Stable Phase 4-15 engines NOT modified",
            "app.py NOT modified",
            "production_dbf_flag=N on all outputs",
            "No production DBFs generated",
        ]) + "\n")

    print("Phase 16 orchestration complete.")
    print(f"Output: {os.path.abspath(args.output)}")
    print(f"  {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
