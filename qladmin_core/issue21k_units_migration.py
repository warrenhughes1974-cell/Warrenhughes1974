#!/usr/bin/env python3
"""Issue 21K — QLAdmin MUNIT precision schema migration (N(*,3) → N(*,5)).

Not a LifePRO conversion change. Operates on QLAdmin DBF tables only.

Usage:
  python qladmin_core/issue21k_units_migration.py --reload-quikridr
  python qladmin_core/issue21k_units_migration.py --migrate-dir C:\\QLAdmin\\Data
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from qladmin_core.qladmin_dbf_layout import migrate_dbf_widen_units, read_table_spec, widen_units_field_in_spec
from qladmin_core.qladmin_units_schema import (
    ISSUE_21K_TABLES,
    UNITS_DECIMALS_AFTER,
    UNITS_DECIMALS_BEFORE,
    UNITS_FIELD,
    schema_before_after,
)
from qladmin_core.quikridr_dbf_writer import read_quikridr_munit, write_quikridr_dbf

DEFAULT_CSV = REPO / "QLA_Migration" / "Output" / "quikridr.csv"
DEFAULT_OUT = REPO / "QLA_Migration" / "Output" / "qladmin_issue21k"
MANIFEST_NAME = "issue21k_schema_migration_manifest.json"


def _migrate_table_in_dir(table: str, data_dir: Path, out_dir: Path) -> dict:
    """Migrate one table if source DBF exists in data_dir."""
    src = data_dir / f"{table}.DBF"
    if not src.is_file():
        src = data_dir / f"{table.lower()}.dbf"
    if not src.is_file():
        return {"table": table, "status": "SKIPPED", "reason": "source DBF not found"}

    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / src.name
    backup = out_dir / f"{src.stem}_before_{UNITS_DECIMALS_BEFORE}dp{src.suffix}"

    if not backup.exists():
        import shutil

        shutil.copy2(src, backup)

    result = migrate_dbf_widen_units(str(src), str(dst), field_name=UNITS_FIELD, new_decimals=UNITS_DECIMALS_AFTER)
    result["table"] = table
    result["status"] = "MIGRATED"
    result["backup"] = str(backup)
    return result


def run_reload_quikridr(csv_path: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    dbf_path = out_dir / "QUIKRIDR.DBF"
    info = write_quikridr_dbf(str(csv_path), str(dbf_path))
    spec = read_table_spec(str(dbf_path))

    trace = read_quikridr_munit(str(dbf_path), "010448806C", 2, mplan="1708PA")
    return {
        "action": "reload_quikridr",
        "csv_path": str(csv_path),
        "dbf_path": str(dbf_path),
        "rows": info["dbf_rows"],
        "munit_field_spec": "MUNIT N(10,5)",
        "structure": spec,
        "trace_010448806C_pua": trace,
    }


def run_migrate_dir(data_dir: Path, out_dir: Path) -> list[dict]:
    results = []
    for table in ISSUE_21K_TABLES:
        results.append(_migrate_table_in_dir(table, data_dir, out_dir))
    return results


def build_schema_report() -> list[dict]:
    rows = []
    for table in ISSUE_21K_TABLES:
        before, after = schema_before_after(table)
        rows.append({"table": table, "units_before": before, "units_after": after})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue 21K QLAdmin MUNIT precision migration")
    parser.add_argument("--reload-quikridr", action="store_true", help="Reload QUIKRIDR from conversion CSV")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="quikridr.csv path")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT), help="Output directory")
    parser.add_argument("--migrate-dir", help="Directory containing production QLAdmin DBFs to widen")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    manifest: dict = {
        "issue": "21K",
        "units_field": UNITS_FIELD,
        "decimals_before": UNITS_DECIMALS_BEFORE,
        "decimals_after": UNITS_DECIMALS_AFTER,
        "tables": ISSUE_21K_TABLES,
        "schema_before_after": build_schema_report(),
        "actions": [],
    }

    if args.reload_quikridr:
        if not Path(args.csv).is_file():
            print(f"ERROR: CSV not found: {args.csv}", file=sys.stderr)
            return 1
        reload_result = run_reload_quikridr(Path(args.csv), out_dir)
        manifest["actions"].append(reload_result)
        print("QUIKRIDR reload:", reload_result["rows"], "rows ->", reload_result["dbf_path"])
        trace = reload_result.get("trace_010448806C_pua")
        if trace:
            print(
                f"  010448806C PUA: MUNIT={trace['MUNIT']} MVPU={trace['MVPU']} face=${trace['face']:.2f}"
            )

    if args.migrate_dir:
        mig = run_migrate_dir(Path(args.migrate_dir), out_dir / "migrated")
        manifest["actions"].extend(mig)
        for r in mig:
            print(f"{r['table']}: {r['status']}")

    if not args.reload_quikridr and not args.migrate_dir:
        parser.print_help()
        return 1

    manifest_path = out_dir / MANIFEST_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Manifest:", manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
