#!/usr/bin/env python3
"""
Phase 14 — Controlled rule refinement & authorized rerun orchestrator.

Runs Phase 14A-14E in sequence. Does NOT modify stable engines or app.py.
"""

import argparse
import logging
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_OUTPUT = os.path.join(ROOT, "phase14_controlled_rule_refinement")

logger = logging.getLogger("phase14_runner")


def run_script(script_name, output_dir, verbose):
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, script_name), "--output", output_dir]
    if verbose:
        cmd.append("--verbose")
    logger.info("Running %s", script_name)
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Phase 14 authorized rerun orchestrator.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    os.makedirs(args.output, exist_ok=True)

    scripts = [
        "trustee_authorized_rerun_engine.py",
        "authorized_balancing_rerun_engine.py",
        "surrender_offset_triage_engine.py",
        "orphan_authorized_rerun_engine.py",
        "app_authorization_prep_engine.py",
    ]
    for script in scripts:
        if not run_script(script, args.output, args.verbose):
            return 1

    summary_path = os.path.join(args.output, "phase14_authorized_rerun_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 14 Controlled Rule Refinement & Authorized Re-run — Complete ===",
            "",
            "Sub-phases executed:",
            "  14A — Trustee gating refinement (QA subset)",
            "  14B — Lifecycle balancing replay authorization",
            "  14C — Surrender offset business triage",
            "  14D — Orphan resolution rerun analysis",
            "  14E — app.py authorization prep (no code changes)",
            "",
            f"Output: {os.path.abspath(args.output)}",
            "Stable engines NOT modified",
            "app.py NOT modified",
            "production_dbf_flag=N on all outputs",
        ]) + "\n")

    print("Phase 14 orchestration complete.")
    print(f"Output: {os.path.abspath(args.output)}")
    print(f"  {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
