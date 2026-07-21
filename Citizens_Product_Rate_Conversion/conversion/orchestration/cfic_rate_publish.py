"""Publish CFIC rate rows to the CSV-only QLAdmin load package."""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from citizens_paths import LOAD_PACKAGE_TABLES, OUTPUT_RATES, REPORTS
from engine_import import rate_dbf_writer


def _import_writer():
    return rate_dbf_writer()


def pad_plan_field(rows: list[dict], field: str = "PLAN") -> list[dict]:
    out = []
    for row in rows:
        r = dict(row)
        if field in r and r[field]:
            r[field] = str(r[field]).strip()[:6].ljust(6)
        out.append(r)
    return out


def publish_rate_csvs(
    factor_rows: dict[str, list[dict]],
    key_rows: dict[str, list[dict]],
    member_rows: dict[str, list[dict]],
    *,
    output_dir: Path = OUTPUT_RATES,
    overwrite: bool = True,
    drop_empty: bool = True,
) -> list[dict]:
    """Write PascalCase Quik*.csv files; return manifest entries."""
    W = _import_writer()
    output_dir.mkdir(parents=True, exist_ok=True)
    sanitize_output_dir(output_dir)

    if drop_empty:
        factor_rows = {k: v for k, v in factor_rows.items() if v}
        key_rows = {k: v for k, v in key_rows.items() if v}
        member_rows = {k: v for k, v in member_rows.items() if v}

    factor_rows = {k: pad_plan_field(v) for k, v in factor_rows.items()}
    key_rows = {k: pad_plan_field(v) for k, v in key_rows.items()}
    member_rows = {k: pad_plan_field(v) for k, v in member_rows.items()}

    manifest = W.emit_all_rate_tables_csv(
        factor_rows, key_rows, member_rows, str(output_dir), overwrite=overwrite
    )
    return [
        {
            "kind": m["kind"],
            "table": m["table"],
            "format": "csv",
            "path": m["path"],
            "rows": m["rows"],
        }
        for m in manifest
    ]


def sanitize_output_dir(output_dir: Path) -> int:
    """Remove all CSVs from load package folder before a fresh publish."""
    if not output_dir.exists():
        return 0
    removed = 0
    for path in output_dir.glob("*.csv"):
        path.unlink()
        removed += 1
    return removed


def audit_output_folder(output_dir: Path = OUTPUT_RATES) -> list[str]:
    """Return list of policy violations (non-Quik CSVs, wrong casing, etc.)."""
    issues: list[str] = []
    if not output_dir.exists():
        return issues
    seen_lower: set[str] = set()
    for path in sorted(output_dir.iterdir()):
        if not path.is_file():
            issues.append(f"non-file entry: {path.name}")
            continue
        if path.suffix.lower() != ".csv":
            issues.append(f"non-CSV file: {path.name}")
            continue
        lower = path.name.lower()
        if lower in seen_lower:
            continue
        seen_lower.add(lower)
        stem = path.stem
        if stem != stem[:1].upper() + stem[1:]:
            issues.append(f"filename not PascalCase table name: {path.name}")
        if stem not in LOAD_PACKAGE_TABLES:
            issues.append(f"unexpected table in load package: {path.name}")
    return issues


def write_manifest(
    manifest: list[dict],
    *,
    wave: str,
    plans: list[str],
    notes: str = "",
    reports_dir: Path = REPORTS,
) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = reports_dir / "rate_csv_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["KIND", "TABLE", "FILENAME", "ROWS", "WAVE", "PLANS", "NOTES"])
        plan_s = ";".join(plans)
        for m in manifest:
            if m.get("format") != "csv":
                continue
            w.writerow([
                m["kind"],
                m["table"],
                Path(m["path"]).name,
                m["rows"],
                wave,
                plan_s,
                notes or "DBF column order preserved; append-ready for QLAdmin",
            ])
    return manifest_path


def write_emit_summary(
    *,
    wave: str,
    plans: list[str],
    manifest: list[dict],
    validation_pass: bool | None,
    audit_issues: list[str],
    extra: dict | None = None,
    reports_dir: Path = REPORTS,
) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    summary_path = reports_dir / "emit_summary.json"
    payload = {
        "program": "Citizens_Product_Rate_Conversion",
        "wave": wave,
        "plans": plans,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "output_dir": str(OUTPUT_RATES),
        "csv_tables_written": sum(1 for m in manifest if m.get("format") == "csv"),
        "total_rows_written": sum(m["rows"] for m in manifest if m.get("format") == "csv"),
        "validation_pass": validation_pass,
        "output_audit_clean": len(audit_issues) == 0,
        "output_audit_issues": audit_issues,
        "tables": [
            {"kind": m["kind"], "table": m["table"], "rows": m["rows"]}
            for m in manifest
            if m.get("format") == "csv"
        ],
    }
    if extra:
        payload.update(extra)
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return summary_path


def clean_legacy_output(legacy_dir: Path) -> int:
    """Remove deprecated lowercase draft folder contents."""
    if not legacy_dir.exists():
        return 0
    removed = 0
    for path in legacy_dir.glob("*.csv"):
        path.unlink()
        removed += 1
    return removed
