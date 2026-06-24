"""Headless claims UAT emit harness (Phase 25).

Invokes app.py Phase 21 emit without running full conversion or Phase 17 pipeline.
Intended for subprocess use by phase25_uat_emit_refresh_runner.py.
"""

import argparse
import os
import shutil
import sys

import tkinter as tk

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import QLAdminEnterpriseIntegrationSuite  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Headless claims UAT emit (Phase 25).")
    parser.add_argument("--uat-clms", required=True)
    parser.add_argument("--uat-clmp", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--staging-dir", default="")
    args = parser.parse_args()

    os.environ.setdefault("QLA_VALIDATE_CLAIMS_MPOLICY", "0")
    os.environ.setdefault("QLA_CLAIMS_UAT_EMIT", "1")
    os.environ.setdefault("QLA_CLAIMS_ORCHESTRATE", "0")
    os.environ.setdefault("QLA_SEMANTIC_GOVERNANCE_HOLD", "1")
    os.environ.setdefault("QLA_GENERATE_UAT_CLAIMS_DBF", "0")

    output_dir = os.path.normpath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    staging_dir = os.path.normpath(args.staging_dir) if args.staging_dir else os.path.join(
        output_dir, "claims_uat_staging"
    )
    os.makedirs(staging_dir, exist_ok=True)

    for table_key, source in (("quikclms", args.uat_clms), ("quikclmp", args.uat_clmp)):
        if not os.path.isfile(source):
            print(f"ERROR: missing UAT source for {table_key}: {source}")
            return 1
        dest = os.path.join(staging_dir, f"{table_key}.csv")
        shutil.copy2(source, dest)
        print(f"STAGED {table_key}: {dest} <- {source}")

    root = tk.Tk()
    root.withdraw()
    app = QLAdminEnterpriseIntegrationSuite(root)

    if "Out" in app.path_vars:
        app.path_vars["Out"][0].set(output_dir)

    app.CLAIMS_ORCHESTRATION["uat_quikclms_source"] = os.path.normpath(args.uat_clms)
    app.CLAIMS_ORCHESTRATION["uat_quikclmp_source"] = os.path.normpath(args.uat_clmp)

    emit_result = app._emit_uat_claims_to_main_output(staging_dir)  # noqa: SLF001

    if not emit_result:
        print("ERROR: emit returned no result")
        return 1

    emitted = emit_result.get("emitted", {})
    for table_key in ("quikclms", "quikclmp"):
        info = emitted.get(table_key)
        if info:
            print(f"EMITTED {table_key}: {info['row_count']} rows -> {info['dest_path']}")
        else:
            print(f"EMITTED {table_key}: NONE")

    print(f"HOLD_COUNT={emit_result.get('hold_count', 0)}")
    print(f"VALIDATION_OK={emit_result.get('validation_ok')}")
    print(f"OUTPUT_DIR={emit_result.get('output_dir')}")
    print(f"MANIFEST={emit_result.get('manifest_path')}")
    return 0 if emit_result.get("validation_ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
