#!/usr/bin/env python3
"""Phase 15 — QA sign-off & controlled prototype replay orchestrator."""

import argparse
import logging
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_OUTPUT = os.path.join(ROOT, "phase15_qa_signoff_replay_execution")

logger = logging.getLogger("phase15_runner")


def run_script(script_name, output_dir, verbose):
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, script_name), "--output", output_dir]
    if verbose:
        cmd.append("--verbose")
    logger.info("Running %s", script_name)
    return subprocess.run(cmd, cwd=ROOT).returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Phase 15 authorized replay orchestrator.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    os.makedirs(args.output, exist_ok=True)

    scripts = [
        "trustee_qa_signoff_engine.py",
        "authorized_phase11_rerun_engine.py",
        "phase15_post_replay_governance_engine.py",
    ]
    for script in scripts:
        if not run_script(script, args.output, args.verbose):
            return 1

    summary = os.path.join(args.output, "phase15_execution_summary.txt")
    with open(summary, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 15 QA Sign-off & Controlled Prototype Replay — Complete ===",
            "",
            "15A — Trustee QA sign-off simulation",
            "15B — Authorized Phase 11 replay (overlay wrapper)",
            "15C/D/E — Governance delta, readiness, pre-integration validation",
            "",
            f"Output: {os.path.abspath(args.output)}",
            "Stable engines NOT modified",
            "app.py NOT modified",
            "production_dbf_flag=N",
        ]) + "\n")

    print("Phase 15 orchestration complete.")
    print(f"Output: {os.path.abspath(args.output)}")
    print(f"  {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
