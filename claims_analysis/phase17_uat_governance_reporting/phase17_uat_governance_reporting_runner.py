#!/usr/bin/env python3
"""
Phase 17 — UAT candidate segmentation & business governance reporting orchestrator.

Runs Phase 17A-17F in sequence. Does NOT modify stable engines or app.py.
"""

import argparse
import logging
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_OUTPUT = os.path.join(ROOT, "phase17_uat_governance_reporting")

logger = logging.getLogger("phase17_runner")


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
    parser = argparse.ArgumentParser(description="Phase 17 UAT governance reporting orchestrator.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    os.makedirs(args.output, exist_ok=True)

    scripts = [
        "uat_candidate_segmentation_engine.py",
        "deferred_governance_segmentation_engine.py",
        "business_exclusion_logging_engine.py",
        "representative_issue_examples_engine.py",
        "executive_governance_reporting_engine.py",
        "business_review_workbench_engine.py",
    ]
    for script in scripts:
        if not run_script(script, args.output, args.verbose):
            return 1

    summary_path = os.path.join(args.output, "phase17_execution_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 17 UAT Candidate Segmentation & Business Governance Reporting — Complete ===",
            "",
            "Sub-phases executed:",
            "  17A — UAT candidate segmentation",
            "  17B — Deferred governance population segmentation",
            "  17C — Business-facing exclusion logging",
            "  17D — Representative issue examples",
            "  17E — Executive/UAT governance reporting",
            "  17F — Business review workbench preparation",
            "",
            f"Output: {os.path.abspath(args.output)}",
            "Go-live target: 2026-09-01 (UAT preparation phase)",
            "Stable Phase 4-16 engines NOT modified",
            "app.py NOT modified",
            "production_dbf_flag=N on all outputs",
            "No production DBFs generated",
        ]) + "\n")

    print("Phase 17 orchestration complete.")
    print(f"Output: {os.path.abspath(args.output)}")
    print(f"  {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
