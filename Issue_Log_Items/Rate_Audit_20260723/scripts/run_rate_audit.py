"""Exhaustive source-to-package-to-QLAdmin rate audit.

This is an evidence generator, not a converter. It runs the existing rate
pipeline in an audit sandbox, builds the expected QLAdmin rate package in
memory, compares it to `QLA_Migration/Output/rates`, and optionally compares
the package to a post-load QLAdmin export directory.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core import quikaint_closed_riders as QAINT
from qla_core import rate_dbf_schema as S
from qla_core import rate_member_setup as MB
from qla_core import rate_pipeline as P


AUDIT_DIR = ROOT / "Issue_Log_Items" / "Rate_Audit_20260723"
EVIDENCE_DIR = AUDIT_DIR / "evidence"
REPORTS_DIR = AUDIT_DIR / "reports"
DEFAULT_CONFIG = ROOT / "plan_analysis" / "phase_r5_rate_loader" / "rate_loader_config.json"
DEFAULT_OUTPUT_RATES = ROOT / "QLA_Migration" / "Output" / "rates"
DEFAULT_TEST_VALIDATION_RATES = ROOT / "QLA_Migration" / "Output" / "Test_Validation" / "rates"
DEFAULT_QLA_EXPORT = ROOT / "QLA_Migration" / "QLAdmin_Export" / "rates"

FACTOR_TABLES = tuple(S.PREFIX.keys())
KEY_TABLES = tuple(sorted(set(S.KEY_TABLE.values())))
MEMBER_TABLES = ("QuikPlGd", "QuikPlUw", "QuikPlBd", "QuikPlSt", "QuikPlNb")
SPECIAL_TABLES = ("QuikUint", "QuikAint", "QuikIssc", "QuikUwpo")

FACTOR_KEYS = ("PLAN", "AGE", "CNTL", "GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE")
KEY_BASE = ("PLAN", "GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE")
PRIMARY_KEYS = {
    **{t: FACTOR_KEYS for t in FACTOR_TABLES},
    **{t: KEY_BASE for t in KEY_TABLES},
    "QuikPlGd": ("PLAN", "GDCODE"),
    "QuikPlUw": ("PLAN", "UWCODE"),
    "QuikPlBd": ("PLAN", "BDCODE"),
    "QuikPlSt": ("PLAN", "ISSCNTRY", "ISSUEST"),
    "QuikPlNb": ("PLAN", "ISSCNTRY", "ISSUEST", "EFFDATE"),
    "QuikUint": ("MPLAN", "MEFFDATE"),
    "QuikAint": ("MPLAN", "MEFFDATE"),
    "QuikIssc": ("PLAN", "AGE", "GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST"),
    "QuikUwpo": ("UWCODE",),
}


@dataclass
class TableComparison:
    table: str
    status: str
    expected_rows: int
    actual_rows: int
    missing_rows: int = 0
    extra_rows: int = 0
    duplicate_actual_keys: int = 0
    mismatched_cells: int = 0
    schema_status: str = "PASS"
    note: str = ""


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def ensure_dirs() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict]) -> int:
    count = 0
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)
            count += 1
    return count


def audit_config_path(config_path: Path) -> Path:
    cfg = read_json(config_path)
    cfg.setdefault("issue42_pdage_missfill", {})
    pdage = cfg["issue42_pdage_missfill"]
    if pdage.get("enabled", False):
        pdage["staging_merged_csv"] = rel(EVIDENCE_DIR / "audit_rate_table_pdage_missfill_merged.csv")
    out = EVIDENCE_DIR / "audit_rate_loader_config.json"
    write_json(out, cfg)
    return out


def field_defs(table: str) -> list[tuple]:
    if table in FACTOR_TABLES:
        return S.factor_table_fields(table)
    if table in KEY_TABLES:
        return S.key_table_fields(table)
    if table in MEMBER_TABLES:
        return S.member_table_fields(table)
    if table == "QuikUint":
        return S.quikuint_fields()
    if table == "QuikAint":
        return S.quikaint_fields()
    if table == "QuikIssc":
        return S.quikissc_fields()
    if table == "QuikUwpo":
        return S.quikuwpo_fields()
    raise KeyError(f"No schema known for table {table}")


def field_order(table: str) -> list[str]:
    return [f[0] for f in field_defs(table)]


def field_types(table: str) -> dict[str, str]:
    return {f[0]: f[1] for f in field_defs(table)}


def csv_cell(v: object, field_type: str) -> str:
    if v is None:
        return ""
    if field_type == "L":
        s = str(v).strip().upper()
        if s in ("Y", "T", "TRUE", "1"):
            return "Y"
        if s in ("N", "F", "FALSE", "0"):
            return "N"
        return ""
    if field_type == "N":
        s = str(v).strip()
        if s == "":
            return ""
        try:
            num = float(s)
        except ValueError:
            return s
        if num.is_integer():
            return str(int(num)) if "." not in s else s.rstrip("0").rstrip(".")
        return s.rstrip("0").rstrip(".")
    return str(v).strip()


def normalize_row(table: str, row: dict) -> dict[str, str]:
    types = field_types(table)
    return {name: csv_cell(row.get(name, ""), types[name]) for name in field_order(table)}


def row_key(table: str, row: dict) -> tuple[str, ...]:
    return tuple((row.get(f, "") or "").strip() for f in PRIMARY_KEYS[table])


def expected_tables(res) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for table, rows in res.factor_rows.items():
        out[table] = [normalize_row(table, r) for r in rows]
    for table, rows in res.key_rows.items():
        out[table] = [normalize_row(table, r) for r in rows if (r.get("PLAN") or "").strip()]
    for table, rows in res.member_rows.items():
        rows2 = rows
        if table.startswith("QuikPl"):
            rows2 = [r for r in rows if (r.get("PLAN") or "").strip()]
        out[table] = [normalize_row(table, r) for r in rows2]
    out["QuikUint"] = [normalize_row("QuikUint", r) for r in res.quikuint_rows]
    out["QuikIssc"] = [normalize_row("QuikIssc", r) for r in res.quikissc_rows]
    out["QuikAint"] = [normalize_row("QuikAint", r) for r in QAINT.build_issue51_quikaint_rows()]
    uwpo_rows = MB.build_quikuwpo_rows(res.member_rows, key_rows=res.key_rows)
    out["QuikUwpo"] = [normalize_row("QuikUwpo", r) for r in uwpo_rows]
    return {k: v for k, v in sorted(out.items())}


def read_csv_table(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def read_dbf_table(path: Path) -> list[dict]:
    try:
        import dbf
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(f"DBF reader unavailable: {exc}") from exc
    rows = []
    table = dbf.Table(str(path))
    table.open()
    try:
        names = list(table.field_names)
        for rec in table:
            row = {}
            for name in names:
                val = rec[name]
                if val is None:
                    row[name] = ""
                elif hasattr(val, "strftime"):
                    row[name] = val.strftime("%Y%m%d")
                else:
                    row[name] = str(val).strip()
            rows.append(row)
    finally:
        table.close()
    return rows


def read_external_table(table: str, directory: Path) -> tuple[list[dict], str]:
    csv_path = directory / f"{table}.csv"
    dbf_path = directory / f"{table}.dbf"
    if csv_path.is_file():
        return read_csv_table(csv_path), rel(csv_path)
    if dbf_path.is_file():
        return read_dbf_table(dbf_path), rel(dbf_path)
    lower_csv = directory / f"{table.lower()}.csv"
    lower_dbf = directory / f"{table.lower()}.dbf"
    if lower_csv.is_file():
        return read_csv_table(lower_csv), rel(lower_csv)
    if lower_dbf.is_file():
        return read_dbf_table(lower_dbf), rel(lower_dbf)
    return [], ""


def index_rows(table: str, rows: list[dict]) -> tuple[dict[tuple, dict], Counter]:
    idx: dict[tuple, dict] = {}
    dup = Counter()
    for raw in rows:
        row = normalize_row(table, raw)
        key = row_key(table, row)
        if key in idx:
            dup[key] += 1
            continue
        idx[key] = row
    return idx, dup


def compare_tables(
    label: str,
    expected: dict[str, list[dict]],
    actual_dir: Path,
    mismatch_path: Path,
) -> list[TableComparison]:
    comparisons: list[TableComparison] = []
    rows_out = []
    for table, exp_rows in expected.items():
        try:
            actual_rows, actual_source = read_external_table(table, actual_dir)
        except Exception as exc:
            comparisons.append(TableComparison(table, "FAIL", len(exp_rows), 0, note=str(exc)))
            rows_out.append({
                "comparison": label,
                "table": table,
                "key": "",
                "field": "",
                "expected": "",
                "actual": "",
                "issue": f"READ_ERROR: {exc}",
            })
            continue

        if not actual_source:
            comparisons.append(TableComparison(table, "FAIL", len(exp_rows), 0, missing_rows=len(exp_rows), note="missing table"))
            continue

        expected_header = field_order(table)
        actual_header = list(read_csv_table(Path(actual_source) if Path(actual_source).is_absolute() else ROOT / actual_source)[0].keys()) if actual_source.lower().endswith(".csv") and actual_rows else expected_header
        schema_status = "PASS" if actual_header == expected_header else "FAIL"

        exp_idx, exp_dup = index_rows(table, exp_rows)
        act_idx, act_dup = index_rows(table, actual_rows)
        missing = sorted(set(exp_idx) - set(act_idx))
        extra = sorted(set(act_idx) - set(exp_idx))
        mismatch_count = 0
        compare_fields = [f for f in expected_header if f not in PRIMARY_KEYS[table]]

        for key in sorted(set(exp_idx) & set(act_idx)):
            exp_row = exp_idx[key]
            act_row = act_idx[key]
            for fld in compare_fields:
                if exp_row.get(fld, "") != act_row.get(fld, ""):
                    mismatch_count += 1
                    rows_out.append({
                        "comparison": label,
                        "table": table,
                        "key": "|".join(key),
                        "field": fld,
                        "expected": exp_row.get(fld, ""),
                        "actual": act_row.get(fld, ""),
                        "issue": "CELL_MISMATCH",
                    })

        for key in missing[:10000]:
            rows_out.append({
                "comparison": label,
                "table": table,
                "key": "|".join(key),
                "field": "",
                "expected": "ROW_PRESENT",
                "actual": "ROW_MISSING",
                "issue": "MISSING_ROW",
            })
        for key in extra[:10000]:
            rows_out.append({
                "comparison": label,
                "table": table,
                "key": "|".join(key),
                "field": "",
                "expected": "ROW_ABSENT",
                "actual": "ROW_PRESENT",
                "issue": "EXTRA_ROW",
            })
        for key, n in act_dup.items():
            rows_out.append({
                "comparison": label,
                "table": table,
                "key": "|".join(key),
                "field": "",
                "expected": "UNIQUE_KEY",
                "actual": f"{n + 1}_ROWS",
                "issue": "DUPLICATE_ACTUAL_KEY",
            })
        if schema_status != "PASS":
            rows_out.append({
                "comparison": label,
                "table": table,
                "key": "",
                "field": "HEADER",
                "expected": "|".join(expected_header),
                "actual": "|".join(actual_header),
                "issue": "SCHEMA_MISMATCH",
            })

        status = "PASS"
        if missing or extra or mismatch_count or act_dup or exp_dup or schema_status != "PASS":
            status = "FAIL"
        comparisons.append(TableComparison(
            table=table,
            status=status,
            expected_rows=len(exp_rows),
            actual_rows=len(actual_rows),
            missing_rows=len(missing),
            extra_rows=len(extra),
            duplicate_actual_keys=sum(act_dup.values()),
            mismatched_cells=mismatch_count,
            schema_status=schema_status,
            note=actual_source,
        ))

    write_csv(
        mismatch_path,
        ["comparison", "table", "key", "field", "expected", "actual", "issue"],
        rows_out,
    )
    return comparisons


def write_table_summary(path: Path, comparisons: list[TableComparison]) -> None:
    write_csv(
        path,
        [
            "table", "status", "expected_rows", "actual_rows", "missing_rows",
            "extra_rows", "duplicate_actual_keys", "mismatched_cells",
            "schema_status", "note",
        ],
        [c.__dict__ for c in comparisons],
    )


def flatten_expected_cells(path: Path, expected: dict[str, list[dict]]) -> int:
    def rows():
        for table, table_rows in expected.items():
            keys = PRIMARY_KEYS[table]
            for row in table_rows:
                key = "|".join(row.get(k, "") for k in keys)
                for field in field_order(table):
                    if field in keys:
                        continue
                    yield {
                        "table": table,
                        "key": key,
                        "field": field,
                        "expected_value": row.get(field, ""),
                    }
    return write_csv(path, ["table", "key", "field", "expected_value"], rows())


def write_expected_row_ledger(path: Path, expected: dict[str, list[dict]]) -> int:
    rows = []
    all_fields = [
        "table", "primary_key", "PLAN", "MPLAN", "AGE", "CNTL", "GENDER",
        "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE", "MEFFDATE",
        "factor_values_populated",
        "row_json",
    ]
    for table, table_rows in expected.items():
        value_prefix = S.PREFIX.get(table)
        factor_fields = [f"{value_prefix}{i}" for i in range(10)] if value_prefix else []
        for row in table_rows:
            rows.append({
                "table": table,
                "primary_key": "|".join(row.get(k, "") for k in PRIMARY_KEYS[table]),
                "PLAN": row.get("PLAN", ""),
                "MPLAN": row.get("MPLAN", ""),
                "AGE": row.get("AGE", ""),
                "CNTL": row.get("CNTL", ""),
                "GENDER": row.get("GENDER", ""),
                "UWCLASS": row.get("UWCLASS", ""),
                "BAND": row.get("BAND", ""),
                "ISSCNTRY": row.get("ISSCNTRY", ""),
                "ISSUEST": row.get("ISSUEST", ""),
                "EFFDATE": row.get("EFFDATE", ""),
                "MEFFDATE": row.get("MEFFDATE", ""),
                "factor_values_populated": sum(1 for f in factor_fields if row.get(f, "") != ""),
                "row_json": json.dumps(row, sort_keys=True),
            })
    return write_csv(path, all_fields, rows)


def source_inventory(config_path: Path, cfg: dict) -> list[dict]:
    entries = [
        ("rate_loader_config", str(config_path), "Config authority"),
        ("source_rate_extract", cfg.get("source_rate_extract", ""), "Rate_Table direct CV/DB/DV/NP/RV/PR/NF/SL source"),
        ("paagerat_pr_extract", cfg.get("paagerat_pr_extract", ""), "PAAGERAT PR/BP/NF/COI/GCOI/DB source"),
        ("pdage_extract", cfg.get("pdage_extract", ""), "PDAGE miss-fill source"),
        ("pdint_extract", cfg.get("pdint_extract", ""), "PDINT declared interest header"),
        ("pdinttbl_extract", cfg.get("pdinttbl_extract", ""), "PDINTTBL declared interest tiers"),
        ("pcovrsgt_csv", cfg.get("pcovrsgt_csv", ""), "Segment hierarchy"),
        ("pcovr_csv", cfg.get("pcovr_csv", ""), "Coverage hierarchy"),
        ("psegt_csv", cfg.get("psegt_csv", ""), "Product segment source"),
        ("plan_form_crosswalk", cfg.get("plan_form_crosswalk", ""), "Coverage to QLA plan"),
        ("cso_mortality_crosswalk", cfg.get("cso_mortality_crosswalk", ""), "Fallback assumption authority"),
        ("cso_valuation_setup", cfg.get("cso_valuation_setup", ""), "QuikPlCv/QuikPlTv assumption authority"),
        ("assumption_mapping_csv", cfg.get("assumption_mapping_csv", ""), "Legacy assumption map"),
        ("issue40_cv_inheritance", (cfg.get("issue40_cv_inheritance") or {}).get("fleet_audit_csv", ""), "Inherited CV manifest"),
        ("non_cv_rate_inheritance", (cfg.get("non_cv_rate_inheritance") or {}).get("manifest_csv", ""), "Inherited NP/RV/DV/DB manifest"),
        ("shared_rate_candidates", (cfg.get("shared_rate_candidates") or {}).get("candidate_csv", ""), "Shared rate candidate manifest"),
        ("quikaing_parallel", "PFSA_Annuity_interest/QUIKAING.DBF", "Parallel annuity guaranteed-interest DBF, not main pipeline"),
    ]
    out = []
    for name, raw, role in entries:
        p = Path(raw or "")
        path = p if p.is_absolute() else ROOT / p
        out.append({
            "source_name": name,
            "path": raw,
            "exists": "Y" if raw and path.exists() else "N",
            "bytes": path.stat().st_size if raw and path.exists() and path.is_file() else "",
            "role": role,
        })
    return out


def table_inventory(expected: dict[str, list[dict]], output_dir: Path, qla_dir: Path | None) -> list[dict]:
    rows = []
    for table, exp_rows in expected.items():
        out_rows, out_source = read_external_table(table, output_dir)
        qla_rows, qla_source = ([], "")
        if qla_dir:
            qla_rows, qla_source = read_external_table(table, qla_dir)
        rows.append({
            "table": table,
            "category": table_category(table),
            "expected_rows": len(exp_rows),
            "output_rows": len(out_rows) if out_source else "",
            "output_present": "Y" if out_source else "N",
            "qla_export_rows": len(qla_rows) if qla_source else "",
            "qla_export_present": "Y" if qla_source else "N",
            "qla_export_path": qla_source,
        })
    return rows


def table_category(table: str) -> str:
    if table in FACTOR_TABLES:
        return "factor"
    if table in KEY_TABLES:
        return "key"
    if table in MEMBER_TABLES:
        return "member"
    if table in ("QuikUint", "QuikAint"):
        return "interest"
    if table == "QuikIssc":
        return "surrender"
    if table == "QuikUwpo":
        return "uw_class"
    return "other"


def cv_value_at(rows: list[dict], plan: str, gender: str, age: int, duration: int) -> str:
    cntl = f"{duration // 10:02d}"
    col = f"CV{duration % 10}"
    for row in rows:
        if (
            row.get("PLAN", "").strip() == plan
            and row.get("GENDER", "").strip() == gender
            and int(row.get("AGE", "-1") or -1) == age
            and row.get("CNTL", "").strip() == cntl
        ):
            return row.get(col, "").strip()
    return ""


def family_controls(expected: dict[str, list[dict]], output_dir: Path, qla_dir: Path | None, res) -> list[dict]:
    controls = []

    def add(check_id: str, area: str, status: str, detail: str) -> None:
        controls.append({"check_id": check_id, "area": area, "status": status, "detail": detail})

    output_cvs, _ = read_external_table("QuikCvs", output_dir)
    issue98_checks = [
        ("RA-CV-098-01", 3, "0.06", "17085M M/14 .06 at duration 3"),
        ("RA-CV-098-02", 85, "975.61", "17085M M/14 975.61 at duration 85"),
        ("RA-CV-098-03", 86, "1000.00", "17085M M/14 1000 at duration 86"),
    ]
    for cid, dur, exp, desc in issue98_checks:
        actual = cv_value_at(output_cvs, "17085M", "M", 14, dur)
        ok = normalize_numeric_text(actual) == normalize_numeric_text(exp)
        add(cid, "CV", "PASS" if ok else "FAIL", f"{desc}; expected={exp}; actual={actual or '(blank)'}")

    blocker_ids = sorted({i.get("id", "") for i in res.issues if i.get("severity") == "BLOCKER"})
    add(
        "RA-GATE-001",
        "pipeline",
        "PASS" if not blocker_ids else "FAIL",
        f"Pipeline blockers: {', '.join(blocker_ids) if blocker_ids else 'none'}",
    )
    add(
        "RA-UINT-001",
        "interest",
        "PASS" if "V-UINT-PDINT" not in blocker_ids else "FAIL",
        "QuikUint PDINTTBL dependency clear" if "V-UINT-PDINT" not in blocker_ids else "QuikUint PDINTTBL dependency blocker present",
    )
    add(
        "RA-COI-001",
        "coi",
        "PASS" if not (output_dir / "QuikPlCoi.csv").exists() and not (output_dir / "QuikPlGcoi.csv").exists() else "FAIL",
        "No forbidden QuikPlCoi/QuikPlGcoi companion files",
    )
    add_manifest_control(add, output_dir)
    add(
        "RA-AING-001",
        "annuity_interest",
        "PASS" if (AUDIT_DIR / "QuikAing_Scope_Decision.md").is_file() else "WARN",
        (
            "QuikAing documented as separate follow-up scope"
            if (AUDIT_DIR / "QuikAing_Scope_Decision.md").is_file()
            else "QuikAing is not emitted by the main QLA_Migration/Output/rates pipeline; classify as follow-up or out of scope"
        ),
    )
    add(
        "RA-QLA-001",
        "qla_export",
        "PASS" if qla_dir and qla_dir.is_dir() else "PENDING",
        f"QLAdmin export directory: {rel(qla_dir) if qla_dir else '(not provided)'}",
    )
    add_test_validation_control(add, output_dir)
    return controls


def add_manifest_control(add, output_dir: Path) -> None:
    manifest = output_dir / "rate_csv_manifest.csv"
    if not manifest.is_file():
        add("RA-MANIFEST-001", "manifest", "WARN", "rate_csv_manifest.csv is missing from Output/rates")
        return
    diffs = []
    with manifest.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            table = (row.get("TABLE") or "").strip()
            rows_s = (row.get("ROWS") or "").strip()
            filename = (row.get("FILENAME") or f"{table}.csv").strip()
            if not table or not rows_s:
                continue
            path = output_dir / filename
            if not path.is_file():
                diffs.append(f"{filename}: listed but missing")
                continue
            try:
                listed = int(rows_s)
            except ValueError:
                diffs.append(f"{filename}: nonnumeric manifest rows {rows_s}")
                continue
            actual = max(0, sum(1 for _ in path.open(encoding="utf-8-sig", newline="")) - 1)
            if listed != actual:
                diffs.append(f"{filename}: manifest {listed} actual {actual}")
    add(
        "RA-MANIFEST-001",
        "manifest",
        "PASS" if not diffs else "WARN",
        "rate_csv_manifest row counts match current CSVs" if not diffs else "; ".join(diffs[:20]),
    )


def normalize_numeric_text(value: str) -> str:
    s = (value or "").strip()
    if not s:
        return ""
    try:
        return f"{float(s):.2f}"
    except ValueError:
        return s


def add_test_validation_control(add, output_dir: Path) -> None:
    if not DEFAULT_TEST_VALIDATION_RATES.is_dir():
        add("RA-TV-001", "test_validation", "WARN", "Output/Test_Validation/rates is absent")
        return
    diffs = []
    for src in sorted(output_dir.glob("*.csv")):
        dst = DEFAULT_TEST_VALIDATION_RATES / src.name
        if not dst.is_file():
            continue
        if src.read_bytes() != dst.read_bytes():
            diffs.append(src.name)
    manifest = DEFAULT_TEST_VALIDATION_RATES.parent / "manifest.txt"
    manifest_text = manifest.read_text(encoding="utf-8") if manifest.is_file() else ""
    rate_files = [p.name for p in DEFAULT_TEST_VALIDATION_RATES.glob("*.csv")]
    status = "PASS" if not diffs else "WARN"
    detail = f"{len(rate_files)} Test_Validation rate files; stale/different vs Output: {', '.join(diffs) if diffs else 'none'}"
    if manifest_text and len(rate_files) > manifest_text.count("rates/"):
        status = "WARN"
        detail += "; folder appears broader than manifest"
    add("RA-TV-001", "test_validation", status, detail)


def write_executive_summary(
    path: Path,
    package_summary: list[TableComparison],
    qla_summary: list[TableComparison] | None,
    controls: list[dict],
) -> None:
    package_fail = [x for x in package_summary if x.status != "PASS"]
    qla_fail = [x for x in qla_summary or [] if x.status != "PASS"]
    control_fail = [x for x in controls if x["status"] == "FAIL"]
    control_pending = [x for x in controls if x["status"] == "PENDING"]
    qla_status = "NOT RUN - export not provided" if qla_summary is None else ("PASS" if not qla_fail else "FAIL")
    lines = [
        "# Rate Audit Executive Summary",
        "",
        "## Result",
        "",
        f"- Source-to-package parity: {'PASS' if not package_fail else 'FAIL'}",
        f"- Package-to-QLAdmin export parity: {qla_status}",
        f"- Family controls: {'PASS' if not control_fail else 'FAIL'}",
        "",
        "## Key Counts",
        "",
        f"- Package tables checked: {len(package_summary)}",
        f"- Package table failures: {len(package_fail)}",
        f"- QLAdmin table failures: {len(qla_fail)}" if qla_summary is not None else "- QLAdmin table failures: pending export",
        f"- Failed controls: {len(control_fail)}",
        f"- Pending controls: {len(control_pending)}",
        "",
        "## Blocking Findings",
        "",
    ]
    if package_fail or qla_fail or control_fail:
        for item in package_fail[:25]:
            lines.append(f"- Package `{item.table}`: {item.status}; missing={item.missing_rows}; extra={item.extra_rows}; mismatches={item.mismatched_cells}; {item.note}")
        for item in qla_fail[:25]:
            lines.append(f"- QLAdmin `{item.table}`: {item.status}; missing={item.missing_rows}; extra={item.extra_rows}; mismatches={item.mismatched_cells}; {item.note}")
        for item in control_fail[:25]:
            lines.append(f"- Control `{item['check_id']}`: {item['detail']}")
    else:
        lines.append("- None.")
    lines.extend([
        "",
        "## Evidence Files",
        "",
        "- `evidence/source_inventory.csv`",
        "- `evidence/rate_table_inventory.csv`",
        "- `evidence/canonical_expected_rows.csv`",
        "- `evidence/canonical_expected_cells.csv`",
        "- `evidence/package_table_summary.csv`",
        "- `evidence/package_mismatches.csv`",
        "- `evidence/qla_table_summary.csv` and `evidence/qla_mismatches.csv` when a QLAdmin export is provided",
        "- `evidence/family_controls.csv`",
        "",
        "## Acceptance Gate",
        "",
        "Do not claim loaded QLAdmin rates are correct until package parity and QLAdmin export parity both pass, with any exceptions explicitly waived.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run exhaustive rate audit")
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--output-rates", type=Path, default=DEFAULT_OUTPUT_RATES)
    ap.add_argument("--qla-export", type=Path, default=None, help="Post-load QLAdmin export folder (CSV or DBF)")
    ap.add_argument("--skip-cell-ledger", action="store_true", help="Skip large canonical_expected_cells.csv")
    args = ap.parse_args(argv)

    ensure_dirs()
    cfg_path = audit_config_path(args.config)
    cfg = read_json(cfg_path)

    res = P.run(str(cfg_path), str(ROOT))
    P.write_issue_reports(res, str(EVIDENCE_DIR))
    summary = P.build_summary(res, "RATE_AUDIT", rel(cfg_path))
    write_json(EVIDENCE_DIR / "pipeline_summary.json", summary)

    expected = expected_tables(res)
    write_csv(
        EVIDENCE_DIR / "source_inventory.csv",
        ["source_name", "path", "exists", "bytes", "role"],
        source_inventory(cfg_path, cfg),
    )
    qla_dir = args.qla_export if args.qla_export else (DEFAULT_QLA_EXPORT if DEFAULT_QLA_EXPORT.is_dir() else None)
    write_csv(
        EVIDENCE_DIR / "rate_table_inventory.csv",
        ["table", "category", "expected_rows", "output_rows", "output_present", "qla_export_rows", "qla_export_present", "qla_export_path"],
        table_inventory(expected, args.output_rates, qla_dir),
    )
    write_expected_row_ledger(EVIDENCE_DIR / "canonical_expected_rows.csv", expected)
    if not args.skip_cell_ledger:
        flatten_expected_cells(EVIDENCE_DIR / "canonical_expected_cells.csv", expected)

    package_summary = compare_tables(
        "expected_vs_output",
        expected,
        args.output_rates,
        EVIDENCE_DIR / "package_mismatches.csv",
    )
    write_table_summary(EVIDENCE_DIR / "package_table_summary.csv", package_summary)

    qla_summary = None
    if qla_dir and qla_dir.is_dir():
        qla_summary = compare_tables(
            "output_vs_qla_export",
            {table: read_external_table(table, args.output_rates)[0] for table in expected},
            qla_dir,
            EVIDENCE_DIR / "qla_mismatches.csv",
        )
        write_table_summary(EVIDENCE_DIR / "qla_table_summary.csv", qla_summary)
    else:
        write_csv(
            EVIDENCE_DIR / "qla_table_summary.csv",
            ["table", "status", "expected_rows", "actual_rows", "missing_rows", "extra_rows", "duplicate_actual_keys", "mismatched_cells", "schema_status", "note"],
            [TableComparison(t, "PENDING", len(rows), 0, note="QLAdmin export not provided").__dict__ for t, rows in expected.items()],
        )
        write_csv(EVIDENCE_DIR / "qla_mismatches.csv", ["comparison", "table", "key", "field", "expected", "actual", "issue"], [])

    controls = family_controls(expected, args.output_rates, qla_dir, res)
    write_csv(EVIDENCE_DIR / "family_controls.csv", ["check_id", "area", "status", "detail"], controls)
    write_executive_summary(REPORTS_DIR / "Rate_Audit_Executive_Summary.md", package_summary, qla_summary, controls)

    package_fail = sum(1 for c in package_summary if c.status != "PASS")
    qla_fail = 0 if qla_summary is None else sum(1 for c in qla_summary if c.status != "PASS")
    control_fail = sum(1 for c in controls if c["status"] == "FAIL")
    print("RATE AUDIT COMPLETE")
    print(f"Evidence: {rel(EVIDENCE_DIR)}")
    print(f"Report: {rel(REPORTS_DIR / 'Rate_Audit_Executive_Summary.md')}")
    print(f"Package table failures: {package_fail}")
    print(f"QLAdmin export: {'provided' if qla_summary is not None else 'pending'}; failures: {qla_fail if qla_summary is not None else 'pending'}")
    print(f"Control failures: {control_fail}")
    return 1 if package_fail or qla_fail or control_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
