#!/usr/bin/env python3
"""
GUI subprocess runner for Phase R5 rate table generation.

Thin wrapper around qla_core.rate_emit (same path app.py uses in-process).
"""
from __future__ import annotations

import argparse
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))

if DEFAULT_ROOT not in sys.path:
    sys.path.insert(0, DEFAULT_ROOT)

from qla_core import rate_emit as RE

PHASE_DIR = os.path.join(DEFAULT_ROOT, "plan_analysis", "phase_r5_rate_loader")
DEFAULT_CONFIG = os.path.join(PHASE_DIR, "rate_loader_config.example.json")
DEFAULT_DBF_DIR = os.path.join(PHASE_DIR, "emitted_dbf")


def _resolve_config(config_arg: str) -> str:
    if config_arg and os.path.isfile(config_arg):
        return config_arg
    preferred = os.path.join(PHASE_DIR, "rate_loader_config.json")
    if os.path.isfile(preferred):
        return preferred
    if os.path.isfile(DEFAULT_CONFIG):
        return DEFAULT_CONFIG
    return config_arg or DEFAULT_CONFIG


def main() -> int:
    ap = argparse.ArgumentParser(description="R5 rate loader — GUI subprocess runner")
    ap.add_argument("--repo-root", default=DEFAULT_ROOT)
    ap.add_argument("--config", default="", help="rate loader config JSON")
    ap.add_argument("--csv-dir", default="", help="append-ready CSV output directory")
    ap.add_argument("--dbf-dir", default="", help="isolated sandbox DBF directory")
    ap.add_argument("--emit-csv", action="store_true", help="write append-ready CSV tables")
    ap.add_argument("--emit-dbf", action="store_true", help="write sandbox DBF tables")
    ap.add_argument("--dry-run", action="store_true", help="validate only; never write outputs")
    args = ap.parse_args()

    repo_root = os.path.normpath(args.repo_root)
    config_path = _resolve_config(args.config)
    csv_dir = os.path.normpath(args.csv_dir) if args.csv_dir else os.path.join(
        repo_root, "QLA_Migration", "Output", "rates",
    )
    dbf_dir = os.path.normpath(args.dbf_dir) if args.dbf_dir else DEFAULT_DBF_DIR

    result = RE.run_rate_emit(
        repo_root,
        config_path,
        csv_dir=csv_dir,
        dbf_dir=dbf_dir,
        emit_csv=args.emit_csv,
        emit_dbf=args.emit_dbf,
        dry_run=args.dry_run,
        phase_report_dir=PHASE_DIR,
    )
    sys.stdout.write(RE.format_runner_stdout(result))
    return result.get("return_code", 1)


if __name__ == "__main__":
    raise SystemExit(main())
