"""
R5 GUARDED EMIT — writes QLAdmin rate factor + rate-key DBFs, but ONLY when the validation
gate passes:

    BLOCKER_COUNT == 0   (hard gate; otherwise nothing is written)

Emit is rollback-safe and ISOLATED: tables are written to a dedicated output directory via
qla_core.rate_dbf_writer (temp file + atomic replace). Source / reference DBFs are never
touched. Re-running republishes atomically.

Usage:
  python plan_analysis/phase_r5_rate_loader/rate_loader_emit.py            # DBF + CSV emit
  python plan_analysis/phase_r5_rate_loader/rate_loader_emit.py --dry-run  # validate only
  python plan_analysis/phase_r5_rate_loader/rate_loader_emit.py --csv-only # CSV to QLA_Migration only
"""
import os, sys, json, csv, argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from qla_core import rate_pipeline as P
from qla_core import rate_dbf_schema as S
from qla_core import rate_dbf_writer as W

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CONFIG = os.path.join(HERE, "rate_loader_config.json")
if not os.path.isfile(CONFIG):
    CONFIG = os.path.join(HERE, "rate_loader_config.example.json")
EMIT_DIR = os.path.join(HERE, "emitted_dbf")  # isolated, rollback-safe
MIGRATION_CSV_DIR = os.path.join(ROOT, "QLA_Migration", "Output", "rates")


def _write_dbf_manifest(res, manifest):
    for table, rows in res.factor_rows.items():
        path = os.path.join(EMIT_DIR, f"{table}.dbf")
        n = W.write_factor_table(path, table, rows, overwrite=True)
        manifest.append({"kind": "factor", "table": table, "format": "dbf",
                         "path": os.path.relpath(path, ROOT), "rows": n})
    for key_table, rows in res.key_rows.items():
        path = os.path.join(EMIT_DIR, f"{key_table}.dbf")
        n = W.write_key_table(path, key_table, rows, overwrite=True)
        manifest.append({"kind": "key", "table": key_table, "format": "dbf",
                         "path": os.path.relpath(path, ROOT), "rows": n})
    for member_table, rows in res.member_rows.items():
        path = os.path.join(EMIT_DIR, f"{member_table}.dbf")
        n = W.write_member_table(path, member_table, rows, overwrite=True)
        manifest.append({"kind": "member", "table": member_table, "format": "dbf",
                         "path": os.path.relpath(path, ROOT), "rows": n})
    if res.quikuint_rows:
        path = os.path.join(EMIT_DIR, "QuikUint.dbf")
        n = W.write_quikuint_table(path, res.quikuint_rows, overwrite=True)
        manifest.append({"kind": "interest", "table": "QuikUint", "format": "dbf",
                         "path": os.path.relpath(path, ROOT), "rows": n})
    if res.quikissc_rows:
        path = os.path.join(EMIT_DIR, "QuikIssc.dbf")
        n = W.write_quikissc_table(path, res.quikissc_rows, overwrite=True)
        manifest.append({"kind": "surrender", "table": "QuikIssc", "format": "dbf",
                         "path": os.path.relpath(path, ROOT), "rows": n})


def _write_csv_manifest(res, csv_dir, manifest):
    for table, rows in res.factor_rows.items():
        path = os.path.join(csv_dir, f"{table}.csv")
        n = W.write_factor_table_csv(path, table, rows, overwrite=True)
        manifest.append({"kind": "factor", "table": table, "format": "csv",
                         "path": os.path.relpath(path, ROOT), "rows": n})
    for key_table, rows in res.key_rows.items():
        path = os.path.join(csv_dir, f"{key_table}.csv")
        n = W.write_key_table_csv(path, key_table, rows, overwrite=True)
        manifest.append({"kind": "key", "table": key_table, "format": "csv",
                         "path": os.path.relpath(path, ROOT), "rows": n})
    for member_table, rows in res.member_rows.items():
        path = os.path.join(csv_dir, f"{member_table}.csv")
        n = W.write_member_table_csv(path, member_table, rows, overwrite=True)
        manifest.append({"kind": "member", "table": member_table, "format": "csv",
                         "path": os.path.relpath(path, ROOT), "rows": n})
    if res.quikuint_rows:
        path = os.path.join(csv_dir, "QuikUint.csv")
        n = W.write_quikuint_csv(path, res.quikuint_rows, overwrite=True)
        manifest.append({"kind": "interest", "table": "QuikUint", "format": "csv",
                         "path": os.path.relpath(path, ROOT), "rows": n})
    if res.quikissc_rows:
        path = os.path.join(csv_dir, "QuikIssc.csv")
        n = W.write_quikissc_csv(path, res.quikissc_rows, overwrite=True)
        manifest.append({"kind": "surrender", "table": "QuikIssc", "format": "csv",
                         "path": os.path.relpath(path, ROOT), "rows": n})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="validate only; never write outputs")
    ap.add_argument("--csv-only", action="store_true", help="write CSV only (skip DBF emit)")
    ap.add_argument("--no-csv", action="store_true", help="skip CSV emit to QLA_Migration/Output/rates")
    ap.add_argument("--csv-dir", default=MIGRATION_CSV_DIR,
                    help="CSV output directory (default: QLA_Migration/Output/rates)")
    args = ap.parse_args()

    cfg = json.load(open(CONFIG, encoding="utf-8"))
    res = P.run(CONFIG, ROOT)
    P.write_issue_reports(res, HERE)

    manifest = []
    emitted_dbf = False
    emitted_csv = False
    gate_ok = res.blocker_count == 0

    if gate_ok and not args.dry_run:
        if not args.csv_only:
            os.makedirs(EMIT_DIR, exist_ok=True)
            _write_dbf_manifest(res, manifest)
            emitted_dbf = True
        if not args.no_csv:
            os.makedirs(args.csv_dir, exist_ok=True)
            _write_csv_manifest(res, args.csv_dir, manifest)
            emitted_csv = True

    manifest_path = os.path.join(HERE, "emit_manifest.csv")
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["KIND", "TABLE", "FORMAT", "PATH", "ROWS"])
        for m in manifest:
            w.writerow([m["kind"], m["table"], m.get("format", ""), m["path"], m["rows"]])

    if emitted_csv:
        csv_manifest = os.path.join(args.csv_dir, "rate_csv_manifest.csv")
        with open(csv_manifest, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["KIND", "TABLE", "FILENAME", "ROWS", "NOTES"])
            for m in manifest:
                if m.get("format") != "csv":
                    continue
                w.writerow([
                    m["kind"], m["table"], os.path.basename(m["path"]), m["rows"],
                    "DBF column order preserved; append-ready for QLAdmin",
                ])

    summary = P.build_summary(
        res, "R5 GUARDED EMIT", cfg["source_rate_extract"],
        extra={
            "gate": {"rule": "BLOCKER_COUNT == 0", "blocker_count": res.blocker_count,
                     "passed": gate_ok},
            "emitted_dbf": emitted_dbf,
            "emitted_csv": emitted_csv,
            "emit_dir": os.path.relpath(EMIT_DIR, ROOT) if emitted_dbf else None,
            "csv_dir": os.path.relpath(args.csv_dir, ROOT) if emitted_csv else None,
            "tables_written": len(manifest),
            "csv_tables_written": sum(1 for m in manifest if m.get("format") == "csv"),
            "total_rows_written": sum(m["rows"] for m in manifest),
            "note": ("CSV outputs use confirmed DBF field order for QLAdmin append. "
                     "EFFDATE/ISSCNTRY/ISSUEST + actuarial assumptions remain configurable "
                     "placeholders; isolated rollback-safe output, source DBFs untouched."),
        })
    json.dump(summary, open(os.path.join(HERE, "emit_summary.json"), "w", encoding="utf-8"), indent=2)
    print(json.dumps(summary, indent=2))
    if not gate_ok:
        print(f"\nEMIT BLOCKED: {res.blocker_count} blocker(s). No outputs written.")


if __name__ == "__main__":
    main()
