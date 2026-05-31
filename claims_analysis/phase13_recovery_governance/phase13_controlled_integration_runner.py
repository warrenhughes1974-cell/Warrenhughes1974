#!/usr/bin/env python3
"""
Phase 13 — Controlled enterprise integration orchestrator.

Runs Phase 13A-13D engines in sequence without modifying stable engines or app.py.
"""

import argparse
import logging
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_OUTPUT = os.path.join(ROOT, "phase13_controlled_enterprise_integration")

logger = logging.getLogger("phase13_runner")


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
    parser = argparse.ArgumentParser(description="Phase 13 controlled integration orchestrator.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    os.makedirs(args.output, exist_ok=True)

    scripts = [
        "trustee_payment_recovery_engine.py",
        "balancing_remediation_workflow_engine.py",
        "orphan_resolution_governance_engine.py",
        "app_integration_planning_engine.py",
    ]
    for script in scripts:
        if not run_script(script, args.output, args.verbose):
            return 1

    summary_path = os.path.join(args.output, "phase13_controlled_integration_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("=== Phase 13 Controlled Enterprise Integration — Run Complete ===\n\n")
        fh.write("Sub-phases executed:\n")
        fh.write("  13A — Trustee payment recovery governance\n")
        fh.write("  13B — Balancing remediation workflow\n")
        fh.write("  13C — Orphan resolution governance\n")
        fh.write("  13D — app.py integration planning (no code changes)\n\n")
        fh.write(f"Output directory: {os.path.abspath(args.output)}\n")
        fh.write("production_dbf_flag=N on all outputs\n")
        fh.write("app.py NOT modified\n")

    print("Phase 13 orchestration complete.")
    print(f"Output: {os.path.abspath(args.output)}")
    print(f"  {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
