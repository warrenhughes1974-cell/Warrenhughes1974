"""
QLAdmin rate table emit — single code path for GUI (app.py) and CLI runners.

Runs rate_pipeline, writes factor/key/member CSVs to Output/rates/, and verifies
Issue #40 inherited CV plans (QuikCvs + QuikPlCv + member tables) on disk.
"""
from __future__ import annotations

import csv
import json
import os
from datetime import datetime

from qla_core import rate_dbf_schema as S
from qla_core import rate_dbf_writer as W
from qla_core import rate_pipeline as P
from qla_core import quikaint_closed_riders as QAINT

# Blockers that must not prevent CV / factor / key / member CSV emit.
PARTIAL_EMIT_BLOCKERS = frozenset({"V-UINT-PDINT", "V-ISSC-RATE", "V-ISSC-SL"})

MEMBER_TABLES = ("QuikPlGd", "QuikPlBd", "QuikPlUw", "QuikPlSt", "QuikPlNb")
CV_KEY_TABLE = "QuikPlCv"
CV_FACTOR_TABLE = "QuikCvs"


def _default_audit_csv(repo_root):
    return os.path.join(repo_root, "Issue_Log_Items", "Issue_40", "Issue_40_Fleet_CV_Inheritance_Audit.csv")


def load_inherited_cv_plans(audit_csv):
    if not os.path.isfile(audit_csv):
        return []
    plans = []
    with open(audit_csv, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("bucket") == "MISSING_INHERITED_CV":
                plans.append(row["ql_plan"].strip())
    return sorted(set(plans))


def partial_emit_allowed(res):
    if res.blocker_count == 0:
        return True
    blocker_ids = {i["id"] for i in res.issues if i.get("severity") == "BLOCKER"}
    return bool(blocker_ids) and blocker_ids.issubset(PARTIAL_EMIT_BLOCKERS)


def _plans_in_csv(path, plan_field="PLAN"):
    if not os.path.isfile(path):
        return set(), 0
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return {r.get(plan_field, "").strip() for r in rows if r.get(plan_field, "").strip()}, len(rows)


def verify_inherited_cv_package(csv_dir, required_plans):
    """Verify all inherited plans appear in QuikPlCv, QuikCvs, and member tables."""
    if not required_plans:
        return {"pass": True, "checks": [], "missing_by_table": {}}

    checks = []
    missing_by_table = {}
    targets = [
        (CV_KEY_TABLE, os.path.join(csv_dir, f"{CV_KEY_TABLE}.csv")),
        (CV_FACTOR_TABLE, os.path.join(csv_dir, f"{CV_FACTOR_TABLE}.csv")),
    ]
    for mt in MEMBER_TABLES:
        targets.append((mt, os.path.join(csv_dir, f"{mt}.csv")))

    for label, path in targets:
        found, total = _plans_in_csv(path)
        missing = [p for p in required_plans if p not in found]
        ok = not missing
        checks.append({
            "table": label,
            "path": path,
            "total_rows": total,
            "missing_plans": missing,
            "pass": ok,
        })
        if missing:
            missing_by_table[label] = missing

    return {
        "pass": all(c["pass"] for c in checks),
        "checks": checks,
        "missing_by_table": missing_by_table,
        "required_plans": required_plans,
    }


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
    qaint_entry = QAINT.emit_issue51_quikaint(emit_dir, overwrite=True, emit_csv=False, emit_dbf=True)
    manifest.append(qaint_entry)


def _write_csv_manifest(csv_dir, manifest):
    manifest_path = os.path.join(csv_dir, "rate_csv_manifest.csv")
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["KIND", "TABLE", "FILENAME", "ROWS", "NOTES"])
        for m in manifest:
            w.writerow([
                m["kind"], m["table"], os.path.basename(m["path"]), m["rows"],
                "DBF column order preserved; append-ready for QLAdmin",
            ])
    return manifest_path


def run_rate_emit(
    repo_root,
    config_path,
    csv_dir=None,
    dbf_dir=None,
    emit_csv=True,
    emit_dbf=False,
    dry_run=False,
    phase_report_dir=None,
    verify_inherited=True,
):
    """
    Run pipeline and emit rate tables.

    Returns dict with keys used by app.py rate loader UI:
      status, blockers, tables, csv_rows, csv_dir, dbf_dir, csv_manifest, config,
      partial_emit, inherited_plans, inherited_verify, messages, return_code
    """
    repo_root = os.path.normpath(repo_root)
    config_path = os.path.normpath(config_path)
    csv_dir = os.path.normpath(csv_dir or os.path.join(repo_root, "QLA_Migration", "Output", "rates"))
    dbf_dir = os.path.normpath(dbf_dir or os.path.join(repo_root, "plan_analysis", "phase_r5_rate_loader", "emitted_dbf"))
    phase_report_dir = phase_report_dir or os.path.join(repo_root, "plan_analysis", "phase_r5_rate_loader")
    messages = []

    if not os.path.isfile(config_path):
        return {
            "status": "FAILED",
            "error": f"config not found: {config_path}",
            "blockers": "",
            "tables": "0",
            "csv_rows": "0",
            "csv_dir": "",
            "dbf_dir": "",
            "csv_manifest": "",
            "config": config_path,
            "messages": [f"config not found: {config_path}"],
            "return_code": 1,
        }

    try:
        res = P.run(config_path, repo_root)
        P.write_issue_reports(res, phase_report_dir)
    except Exception as exc:
        return {
            "status": "FAILED",
            "error": str(exc),
            "blockers": "",
            "tables": "0",
            "csv_rows": "0",
            "csv_dir": "",
            "dbf_dir": "",
            "csv_manifest": "",
            "config": config_path,
            "messages": [f"pipeline error: {exc}"],
            "return_code": 1,
        }

    gate_ok = res.emit_ready
    partial = partial_emit_allowed(res)
    can_emit = (gate_ok or partial) and not dry_run

    manifest = []
    emitted_csv = False
    emitted_dbf = False
    csv_manifest_path = ""

    if can_emit:
        if emit_dbf:
            os.makedirs(dbf_dir, exist_ok=True)
            _write_dbf_tables(res, dbf_dir, manifest)
            emitted_dbf = True
        if emit_csv:
            os.makedirs(csv_dir, exist_ok=True)
            csv_manifest = W.emit_all_rate_tables_csv(
                res.factor_rows, res.key_rows, res.member_rows, csv_dir, overwrite=True,
            )
            manifest.extend(csv_manifest)
            emitted_csv = True
            qaint_entry = QAINT.emit_issue51_quikaint(csv_dir, overwrite=True)
            manifest.append(qaint_entry)
            messages.append(
                f"Issue #51 QuikAint stubs: {qaint_entry['rows']} row(s) "
                f"({', '.join(QAINT.CLOSED_RIDER_MPLANS)})"
            )
            csv_manifest_path = _write_csv_manifest(csv_dir, manifest)
            if partial and not gate_ok:
                messages.append(
                    f"Partial CSV emit: {res.blocker_count} non-CV blocker(s) ignored "
                    f"({', '.join(sorted({i['id'] for i in res.issues if i.get('severity') == 'BLOCKER'}))})"
                )

    inherited_plans = sorted({e["issuing_plan"] for e in res.cv_inheritance_manifest})
    inherited_verify = None
    if verify_inherited and emitted_csv:
        inherited_verify = verify_inherited_cv_package(csv_dir, inherited_plans)
        if inherited_plans:
            if inherited_verify["pass"]:
                messages.append(
                    f"Issue #40 inherited CV verify PASS: {len(inherited_plans)} plans "
                    f"({', '.join(inherited_plans)})"
                )
            else:
                missing = inherited_verify.get("missing_by_table", {})
                messages.append(f"Issue #40 inherited CV verify FAIL: {missing}")

    csv_rows = sum(m["rows"] for m in manifest if m.get("format") == "csv" or "rows" in m)
    quikcvs_rows = len(res.factor_rows.get(CV_FACTOR_TABLE, []))
    quikplcv_rows = len(res.key_rows.get(CV_KEY_TABLE, []))

    if dry_run:
        status = "SUCCESS"
    elif can_emit and manifest:
        if inherited_verify and not inherited_verify.get("pass", True):
            status = "BLOCKED"
        elif gate_ok or partial:
            status = "SUCCESS"
        else:
            status = "BLOCKED"
    elif res.blocker_count:
        status = "BLOCKED"
    else:
        status = "BLOCKED"

    for issue in res.issues:
        if issue.get("severity") == "BLOCKER":
            messages.append(f"BLOCKER {issue.get('id', '')}: {issue.get('detail', '')}")

    if inherited_plans:
        inh_status = dict(res.cv_inheritance_status)
        messages.append(
            f"Inherited CV emit: {inh_status.get('IN_SCOPE', 0)} rows across "
            f"{len(inherited_plans)} issuing plan(s)"
        )

    result = {
        "status": status,
        "blockers": str(res.blocker_count),
        "tables": str(len(manifest)),
        "csv_rows": str(csv_rows),
        "csv_dir": csv_dir if emitted_csv else "",
        "dbf_dir": dbf_dir if emitted_dbf else "",
        "csv_manifest": csv_manifest_path if emitted_csv else "",
        "config": config_path,
        "partial_emit": partial and not gate_ok,
        "gate_ok": gate_ok,
        "inherited_plans": inherited_plans,
        "inherited_verify": inherited_verify,
        "quikcvs_rows": quikcvs_rows,
        "quikplcv_rows": quikplcv_rows,
        "messages": messages,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "return_code": 0 if status == "SUCCESS" else (2 if status == "BLOCKED" else 1),
    }
    return result


def format_runner_stdout(result):
    """Machine-parseable lines for subprocess compatibility."""
    lines = [
        f"RATE_LOADER_STATUS: {result.get('status', 'UNKNOWN')}",
        f"RATE_LOADER_BLOCKERS: {result.get('blockers', '')}",
        f"RATE_TABLES_WRITTEN: {result.get('tables', '0')}",
        f"RATE_CSV_ROWS: {result.get('csv_rows', '0')}",
        f"RATE_CSV_DIR: {result.get('csv_dir', '')}",
        f"RATE_DBF_DIR: {result.get('dbf_dir', '')}",
        f"RATE_CSV_MANIFEST: {result.get('csv_manifest', '')}",
        f"RATE_CONFIG: {result.get('config', '')}",
        f"RATE_INHERITED_PLANS: {len(result.get('inherited_plans') or [])}",
        f"RATE_QUIKCVS_ROWS: {result.get('quikcvs_rows', 0)}",
        f"RATE_QUIKPLCV_ROWS: {result.get('quikplcv_rows', 0)}",
    ]
    iv = result.get("inherited_verify") or {}
    lines.append(f"RATE_ISSUE40_VERIFY: {'PASS' if iv.get('pass') else 'FAIL' if iv else 'SKIP'}")
    if result.get("partial_emit"):
        lines.append("RATE_PARTIAL_EMIT: Y")
    for msg in result.get("messages") or []:
        lines.append(f"RATE_LOG: {msg}")
    return "\n".join(lines) + "\n"
