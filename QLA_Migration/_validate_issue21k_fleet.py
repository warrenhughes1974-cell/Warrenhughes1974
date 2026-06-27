"""Fleet-level Validation Agent checks — Issue 21K (read-only)."""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

CSV_PATH = REPO / "QLA_Migration" / "Output" / "quikridr.csv"
DBF_PATH = REPO / "QLA_Migration" / "Output" / "qladmin_issue21k" / "QUIKRIDR.DBF"
MANIFEST = REPO / "QLA_Migration" / "Output" / "qladmin_issue21k" / "issue21k_schema_migration_manifest.json"
TRACE_CSV = REPO / "Issue_Log_Items" / "Issue_21" / "Issue_21K_MUNIT_Precision_Trace.csv"
OUT_JSON = REPO / "Issue_Log_Items" / "Issue_21" / "Issue_21K_Validation_Evidence.json"


def num(s) -> float:
    try:
        return float(str(s).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def sub_mill(x: float) -> bool:
    return abs(x * 1000 - math.floor(x * 1000 + 1e-9)) > 1e-9


def close(a: float, b: float, tol: float = 1e-5) -> bool:
    return abs(a - b) <= tol


def main() -> int:
    import dbf

    from qladmin_core.qladmin_units_schema import ISSUE_21K_TABLES, munit_spec
    from qladmin_core.quikridr_dbf_writer import read_quikridr_munit

    evidence: dict = {"checks": {}, "failures": []}

    # --- Schema registry (six tables) ---
    schema_rows = []
    for table in ISSUE_21K_TABLES:
        schema_rows.append({"table": table, "expected_munit": munit_spec(table, after=True)})
    evidence["checks"]["schema_registry"] = schema_rows

    # --- QUIKRIDR physical structure ---
    table = dbf.Table(str(DBF_PATH))
    table.open()
    structure = [str(x) for x in table.structure()]
    evidence["checks"]["quikridr_structure"] = structure
    munit_line = next((s for s in structure if "MUNIT" in s.upper()), "")
    if "N(10,5)" not in munit_line.replace(" ", ""):
        evidence["failures"].append(f"QUIKRIDR MUNIT structure: {munit_line!r}")

    # Field order vs Help layout
    from qladmin_core.qladmin_units_schema import QUIKRIDR_DBF_LAYOUT

    expected_fields = [f["field"] for f in QUIKRIDR_DBF_LAYOUT]
    actual_fields = []
    for part in structure:
        actual_fields.append(part.split()[0].upper())
    if actual_fields != expected_fields:
        evidence["failures"].append(
            f"Field order mismatch expected {len(expected_fields)} got {len(actual_fields)}"
        )
    evidence["checks"]["field_order_match"] = actual_fields == expected_fields

    dbf_rows = []
    for rec in table:
        dbf_rows.append(
            {
                "MPOLICY": str(rec.mpolicy).strip(),
                "MPHASE": str(int(float(rec.mphase))),
                "MPLAN": str(rec.mplan).strip(),
                "MUNIT": float(rec.munit) if rec.munit is not None else 0.0,
                "MVPU": float(rec.mvpu) if rec.mvpu is not None else 0.0,
            }
        )
    table.close()

    # --- Reload counts / keys ---
    with CSV_PATH.open(encoding="latin1", newline="") as fh:
        csv_rows = list(csv.DictReader(fh))

    evidence["checks"]["csv_row_count"] = len(csv_rows)
    evidence["checks"]["dbf_row_count"] = len(dbf_rows)
    if len(csv_rows) != len(dbf_rows):
        evidence["failures"].append(f"Row count CSV {len(csv_rows)} != DBF {len(dbf_rows)}")
    if len(dbf_rows) != 7002:
        evidence["failures"].append(f"Expected 7002 DBF rows, got {len(dbf_rows)}")

    csv_keys = [(r["MPOLICY"].strip(), r["MPHASE"].strip()) for r in csv_rows]
    dbf_keys = [(r["MPOLICY"], r["MPHASE"]) for r in dbf_rows]
    csv_dupes = [k for k, c in Counter(csv_keys).items() if c > 1]
    dbf_dupes = [k for k, c in Counter(dbf_keys).items() if c > 1]
    evidence["checks"]["csv_duplicate_keys"] = len(csv_dupes)
    evidence["checks"]["dbf_duplicate_keys"] = len(dbf_dupes)
    if csv_dupes or dbf_dupes:
        evidence["failures"].append(f"Duplicate keys csv={len(csv_dupes)} dbf={len(dbf_dupes)}")

    # --- CSV vs DBF MUNIT alignment (fleet) ---
    dbf_index = {(r["MPOLICY"], r["MPHASE"]): r for r in dbf_rows}
    munit_mismatch = 0
    mvpu_mismatch = 0
    submill_csv = 0
    submill_preserved = 0
    frac_cent_ok = 0
    frac_cent_total = 0
    trunc_loss_avoided = 0

    for r in csv_rows:
        key = (r["MPOLICY"].strip(), r["MPHASE"].strip())
        csv_mu = num(r.get("MUNIT", ""))
        csv_vp = num(r.get("MVPU", ""))
        if sub_mill(csv_mu):
            submill_csv += 1
        if int(round(csv_mu * csv_vp * 100)) % 100 != 0:
            frac_cent_total += 1
        br = dbf_index.get(key)
        if not br:
            evidence["failures"].append(f"Missing DBF row for {key}")
            continue
        if not close(csv_mu, br["MUNIT"], 1e-5):
            munit_mismatch += 1
        if not close(csv_vp, br["MVPU"], 0.001):
            mvpu_mismatch += 1
        face = round(csv_mu * csv_vp, 2)
        dbf_face = round(br["MUNIT"] * br["MVPU"], 2)
        if abs(face - dbf_face) <= 0.009:
            if int(round(csv_mu * csv_vp * 100)) % 100 != 0:
                frac_cent_ok += 1
        if sub_mill(csv_mu) and close(csv_mu, br["MUNIT"], 1e-5):
            submill_preserved += 1
            trunc3 = math.floor(csv_mu * 1000 + 1e-9) / 1000
            if abs(trunc3 * csv_vp - face) >= 0.009:
                trunc_loss_avoided += 1

    evidence["checks"]["munit_mismatch_rows"] = munit_mismatch
    evidence["checks"]["mvpu_mismatch_rows"] = mvpu_mismatch
    evidence["checks"]["submill_csv_rows"] = submill_csv
    evidence["checks"]["submill_preserved_rows"] = submill_preserved
    evidence["checks"]["fractional_cent_total"] = frac_cent_total
    evidence["checks"]["fractional_cent_face_ok"] = frac_cent_ok
    evidence["checks"]["trunc_loss_avoided_rows"] = trunc_loss_avoided

    if munit_mismatch:
        evidence["failures"].append(f"MUNIT mismatch rows: {munit_mismatch}")
    if submill_csv != submill_preserved:
        evidence["failures"].append(
            f"Sub-mill preserve {submill_preserved}/{submill_csv}"
        )
    if frac_cent_total != frac_cent_ok:
        evidence["failures"].append(
            f"Fractional cent face ok {frac_cent_ok}/{frac_cent_total}"
        )

    # --- Trace policies ---
    traces = []
    for pol, phase, plan, exp_face in (
        ("010448806C", "2", "1708PA", 5752.96),
        ("010615191C", "2", "1708PA", 3745.99),
        ("010367438C", "2", "1708PA", 2464.99),
        ("010510671C", "1", "2665ST", 6034.59),
    ):
        row = read_quikridr_munit(str(DBF_PATH), pol, phase, mplan=plan)
        ok = row and abs(row["face"] - exp_face) <= 0.009
        traces.append({"policy": pol, "phase": phase, "plan": plan, "row": row, "pass": ok})
        if not ok:
            evidence["failures"].append(f"Trace fail {pol} ph{phase}")
    evidence["checks"]["trace_policies"] = traces

    # --- Primary example ---
    primary = read_quikridr_munit(str(DBF_PATH), "010448806C", 2, mplan="1708PA")
    evidence["checks"]["primary_010448806C"] = primary

    evidence["pass"] = len(evidence["failures"]) == 0
    OUT_JSON.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")

    print("=== Issue 21K fleet validation ===")
    print(f"csv_rows={len(csv_rows)} dbf_rows={len(dbf_rows)}")
    print(f"duplicate_keys csv={len(csv_dupes)} dbf={len(dbf_dupes)}")
    print(f"submill_preserved={submill_preserved}/{submill_csv}")
    print(f"frac_cent_ok={frac_cent_ok}/{frac_cent_total}")
    print(f"munit_mismatch={munit_mismatch}")
    print(f"primary={primary}")
    print(f"PASS={evidence['pass']}")
    print(f"Evidence: {OUT_JSON}")
    return 0 if evidence["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
