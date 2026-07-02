#!/usr/bin/env python3
"""
GUI subprocess runner for Phase R5 rate table generation.

Invoked from app.py (never requires manual CLI). Reuses the same rate_pipeline
and rate_dbf_writer code path as rate_loader_emit.py. Emits machine-parseable
stdout lines for the application console.

Stdout keys:
  RATE_LOADER_STATUS: SUCCESS | BLOCKED | FAILED
  RATE_LOADER_BLOCKERS: <int>
  RATE_TABLES_WRITTEN: <int>
  RATE_CSV_ROWS: <int>
  RATE_CSV_DIR: <path>
  RATE_DBF_DIR: <path or empty>
  RATE_CSV_MANIFEST: <path or empty>
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))

if DEFAULT_ROOT not in sys.path:
    sys.path.insert(0, DEFAULT_ROOT)

from qla_core import rate_dbf_writer as W
from qla_core import rate_pipeline as P

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


def _write_dbf_tables(res, emit_dir, manifest):
    for table, rows in res.factor_rows.items():
        path = os.path.join(emit_dir, f"{table}.dbf")
        n = W.write_factor_table(path, table, rows, overwrite=True)
        manifest.append({"kind": "factor", "table": table, "format": "dbf", "path": path, "rows": n})
    for key_table, rows in res.key_rows.items():
        path = os.path.join(emit_dir, f"{key_table}.dbf")
        n = W.write_key_table(path, key_table, rows, overwrite=True)
        manifest.append({"kind": "key", "table": key_table, "format": "dbf", "path": path, "rows": n})
    for member_table, rows in res.member_rows.items():
        path = os.path.join(emit_dir, f"{member_table}.dbf")
        n = W.write_member_table(path, member_table, rows, overwrite=True)
        manifest.append({"kind": "member", "table": member_table, "format": "dbf", "path": path, "rows": n})
    if res.quikuint_rows:
        path = os.path.join(emit_dir, "QuikUint.dbf")
        n = W.write_quikuint_table(path, res.quikuint_rows, overwrite=True)
        manifest.append({"kind": "interest", "table": "QuikUint", "format": "dbf", "path": path, "rows": n})
    if res.quikissc_rows:
        path = os.path.join(emit_dir, "QuikIssc.dbf")
        n = W.write_quikissc_table(path, res.quikissc_rows, overwrite=True)
        manifest.append({"kind": "surrender", "table": "QuikIssc", "format": "dbf", "path": path, "rows": n})


def _write_csv_tables(res, csv_dir, manifest):
    for table, rows in res.factor_rows.items():
        path = os.path.join(csv_dir, f"{table}.csv")
        n = W.write_factor_table_csv(path, table, rows, overwrite=True)
        manifest.append({"kind": "factor", "table": table, "format": "csv", "path": path, "rows": n})
    for key_table, rows in res.key_rows.items():
        path = os.path.join(csv_dir, f"{key_table}.csv")
        n = W.write_key_table_csv(path, key_table, rows, overwrite=True)
        manifest.append({"kind": "key", "table": key_table, "format": "csv", "path": path, "rows": n})
    for member_table, rows in res.member_rows.items():
        path = os.path.join(csv_dir, f"{member_table}.csv")
        n = W.write_member_table_csv(path, member_table, rows, overwrite=True)
        manifest.append({"kind": "member", "table": member_table, "format": "csv", "path": path, "rows": n})
    if res.quikuint_rows:
        path = os.path.join(csv_dir, "QuikUint.csv")
        n = W.write_quikuint_csv(path, res.quikuint_rows, overwrite=True)
        manifest.append({"kind": "interest", "table": "QuikUint", "format": "csv", "path": path, "rows": n})
    if res.quikissc_rows:
        path = os.path.join(csv_dir, "QuikIssc.csv")
        n = W.write_quikissc_csv(path, res.quikissc_rows, overwrite=True)
        manifest.append({"kind": "surrender", "table": "QuikIssc", "format": "csv", "path": path, "rows": n})


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

    if not os.path.isfile(config_path):
        print(f"RATE_LOADER_STATUS: FAILED")
        print(f"RATE_LOADER_ERROR: config not found: {config_path}")
        return 1

    try:
        res = P.run(config_path, repo_root)
        P.write_issue_reports(res, PHASE_DIR)
    except Exception as exc:
        print(f"RATE_LOADER_STATUS: FAILED")
        print(f"RATE_LOADER_ERROR: {exc}")
        return 1

    gate_ok = res.blocker_count == 0
    manifest = []
    emitted_csv = False
    emitted_dbf = False
    csv_manifest_path = ""

    if gate_ok and not args.dry_run:
        if args.emit_dbf:
            os.makedirs(dbf_dir, exist_ok=True)
            _write_dbf_tables(res, dbf_dir, manifest)
            emitted_dbf = True
        if args.emit_csv:
            os.makedirs(csv_dir, exist_ok=True)
            _write_csv_tables(res, csv_dir, manifest)
            emitted_csv = True
            csv_manifest_path = os.path.join(csv_dir, "rate_csv_manifest.csv")
            with open(csv_manifest_path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["KIND", "TABLE", "FILENAME", "ROWS", "NOTES"])
                for m in manifest:
                    if m.get("format") != "csv":
                        continue
                    w.writerow([
                        m["kind"], m["table"], os.path.basename(m["path"]), m["rows"],
                        "DBF column order preserved; append-ready for QLAdmin",
                    ])

    csv_rows = sum(m["rows"] for m in manifest if m.get("format") == "csv")
    status = "SUCCESS" if gate_ok else "BLOCKED"
    if not gate_ok:
        status = "BLOCKED"
    elif args.dry_run:
        status = "SUCCESS"
    elif (args.emit_csv or args.emit_dbf) and not manifest:
        status = "BLOCKED"

    print(f"RATE_LOADER_STATUS: {status}")
    print(f"RATE_LOADER_BLOCKERS: {res.blocker_count}")
    print(f"RATE_TABLES_WRITTEN: {len(manifest)}")
    print(f"RATE_CSV_ROWS: {csv_rows}")
    print(f"RATE_CSV_DIR: {csv_dir if emitted_csv else ''}")
    print(f"RATE_DBF_DIR: {dbf_dir if emitted_dbf else ''}")
    print(f"RATE_CSV_MANIFEST: {csv_manifest_path if emitted_csv else ''}")
    print(f"RATE_CONFIG: {config_path}")

    if res.blocker_count:
        for issue in res.issues:
            if issue.get("severity") == "BLOCKER":
                print(f"RATE_BLOCKER: {issue.get('id', '')} | {issue.get('detail', '')}")

    summary = P.build_summary(
        res, "R5 GUI EMIT", config_path,
        extra={
            "gate_passed": gate_ok,
            "emitted_csv": emitted_csv,
            "emitted_dbf": emitted_dbf,
            "csv_dir": csv_dir if emitted_csv else None,
            "dbf_dir": dbf_dir if emitted_dbf else None,
            "tables_written": len(manifest),
        },
    )
    print(f"RATE_SUMMARY_JSON: {json.dumps(summary)}")

    return 0 if status == "SUCCESS" else (2 if status == "BLOCKED" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
