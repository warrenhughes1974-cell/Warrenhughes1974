"""Validation — Issue 21K MUNIT N(10,5) precision (QLAdmin Core + conversion CSV)."""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
CSV_PATH = REPO / "QLA_Migration" / "Output" / "quikridr.csv"
DBF_PATH = REPO / "QLA_Migration" / "Output" / "qladmin_issue21k" / "QUIKRIDR.DBF"

TRACE_POLICIES = (
    ("010448806C", "2", "1708PA", 5752.96),
    ("010615191C", "2", "1708PA", 3745.99),
    ("010367438C", "2", "1708PA", 2464.99),
)


def _num(s: str) -> float:
    return float(str(s).replace(",", "").strip() or 0)


def validate_csv_precision() -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not CSV_PATH.is_file():
        return False, [f"Missing {CSV_PATH}"]

    with CSV_PATH.open(encoding="latin1", newline="") as fh:
        rows = list(csv.DictReader(fh))

    pol_rows = [r for r in rows if (r.get("MPOLICY") or "").strip() == "010448806C"]
    pua = next((r for r in pol_rows if (r.get("MPLAN") or "").strip() == "1708PA"), None)
    if not pua:
        errors.append("010448806C / 1708PA row missing in CSV")
    elif _num(pua.get("MUNIT", "")) != 5.75296:
        errors.append(f"CSV MUNIT expected 5.75296 got {pua.get('MUNIT')}")

    submill = 0
    for r in rows:
        mu = _num(r.get("MUNIT", ""))
        if abs(mu * 1000 - math.floor(mu * 1000 + 1e-9)) > 1e-9:
            submill += 1
    if submill < 1000:
        errors.append(f"Expected 1000+ sub-mill MUNIT rows, got {submill}")

    return len(errors) == 0, errors


def validate_dbf_reload() -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not DBF_PATH.is_file():
        return False, [f"Missing {DBF_PATH} — run issue21k_units_migration.py --reload-quikridr"]

    try:
        import dbf
    except ImportError:
        return False, ["dbf module not installed"]

    from qladmin_core.quikridr_dbf_writer import read_quikridr_munit

    spec = dbf.Table(str(DBF_PATH)).structure()
    spec_parts = spec if isinstance(spec, list) else str(spec).split(";")
    munit_part = next((p for p in spec_parts if "MUNIT" in str(p).upper()), "")
    if "N(10,5)" not in str(munit_part).replace(" ", ""):
        errors.append(f"MUNIT not N(10,5) in structure: {munit_part!r}")

    trace = read_quikridr_munit(str(DBF_PATH), "010448806C", 2, mplan="1708PA")
    if not trace:
        errors.append("010448806C MPHASE 2 / 1708PA not found in DBF")
    else:
        if abs(trace["MUNIT"] - 5.75296) > 1e-5:
            errors.append(f"DBF MUNIT expected 5.75296 got {trace['MUNIT']}")
        if abs(trace["face"] - 5752.96) > 0.009:
            errors.append(f"DBF face expected 5752.96 got {trace['face']}")

    for pol, phase, plan, expected_face in TRACE_POLICIES:
        row = read_quikridr_munit(str(DBF_PATH), pol, phase, mplan=plan)
        if not row:
            errors.append(f"Missing DBF row {pol} ph{phase} {plan}")
        elif abs(row["face"] - expected_face) > 0.009:
            errors.append(f"{pol} face expected {expected_face} got {row['face']}")

    table = dbf.Table(str(DBF_PATH))
    table.open()
    try:
        if len(table) < 7000:
            errors.append(f"Expected ~7002 DBF rows, got {len(table)}")
    finally:
        table.close()

    return len(errors) == 0, errors


def main() -> int:
    ok = True
    csv_ok, csv_err = validate_csv_precision()
    print("--- CSV precision ---")
    print("PASS" if csv_ok else "FAIL")
    for e in csv_err:
        print(" ", e)
    ok = ok and csv_ok

    dbf_ok, dbf_err = validate_dbf_reload()
    print("--- QUIKRIDR DBF reload (N10,5) ---")
    print("PASS" if dbf_ok else "FAIL")
    for e in dbf_err:
        print(" ", e)
    ok = ok and dbf_ok

    print("=== OVERALL:", "PASS" if ok else "FAIL", "===")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
