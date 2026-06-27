"""
Issue 21M DBF packaging validation (v57.34).

Verifies quikmemo.dbf + sidecar co-locate in Output/quikmemo_uat_dbf/
and survive output hygiene. Does not re-run full batch.

Usage:
  python QLA_Migration/_validate_issue21m_dbf_packaging.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import dbf
import pandas as pd

SCRIPT_VERSION = "1.1"
ENGINE_VERSION = "v57.34"
EXPECTED_CSV_ROWS = 4380
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
UAT_DBF_DIR = OUTPUT / "quikmemo_uat_dbf"
CSV_PATH = OUTPUT / "quikmemo.csv"
BEFORE_DIR = OUTPUT / "_issue21m_before"


def _sidecar_paths(dbf_path: Path) -> list[Path]:
    stem = dbf_path.with_suffix("")
    candidates = [stem.with_suffix(".dbt"), stem.with_suffix(".fpt"), Path(str(dbf_path) + "t")]
    return [p for p in candidates if p.is_file()]


def main() -> int:
    print("=" * 72)
    print(f"ISSUE 21M DBF PACKAGING VALIDATION (script v{SCRIPT_VERSION}, engine {ENGINE_VERSION})")
    print("=" * 72)

    errors: list[str] = []
    from qla_core.quikmemo_dbf_generator import write_quikmemo_dbf
    from qla_core import run_logging as RL

    if not CSV_PATH.is_file():
        errors.append(f"Missing {CSV_PATH}")
        for e in errors:
            print(f"FAIL: {e}")
        return 1

    csv_rows_before = len(pd.read_csv(CSV_PATH, dtype=str))
    UAT_DBF_DIR.mkdir(parents=True, exist_ok=True)
    dbf_path = UAT_DBF_DIR / "quikmemo.dbf"

    info = write_quikmemo_dbf(str(CSV_PATH), str(dbf_path))
    sidecars = _sidecar_paths(dbf_path)

    print("\n--- DBF write ---")
    print(f"  DBF: {dbf_path} exists={dbf_path.is_file()} rows={info['dbf_rows']}")
    print(f"  Sidecars: {[str(p.name) for p in sidecars]}")
    if not dbf_path.is_file():
        errors.append("quikmemo.dbf not created")
    if not sidecars:
        errors.append("No .dbt/.fpt sidecar next to quikmemo.dbf")
    if dbf_path.parent.resolve() != UAT_DBF_DIR.resolve():
        errors.append("DBF not in quikmemo_uat_dbf/")
    for sc in sidecars:
        if sc.parent.resolve() != dbf_path.parent.resolve():
            errors.append(f"Sidecar {sc.name} not in same directory as DBF")

    print("\n--- DBF open / memo read ---")
    try:
        table = dbf.Table(str(dbf_path))
        table.open()
        dbf_rows = len(table)
        sample = table[0]
        memokey = sample.memokey
        memotext = (sample.memotext or "")[:80]
        table.close()
        print(f"  Open OK: rows={dbf_rows}, MEMOKEY={memokey!r}, MEMOTEXT={memotext!r}...")
        if dbf_rows != info["dbf_rows"]:
            errors.append(f"DBF row count {dbf_rows} != expected {info['dbf_rows']}")
        if not memotext.startswith("[PNOTE]") and not memotext.startswith("[ENS]"):
            errors.append("Sample MEMOTEXT missing [PNOTE]/[ENS] prefix")
    except Exception as exc:
        errors.append(f"DBF open failed: {exc}")

    print("\n--- Output hygiene simulation ---")
    reports = str(PROJECT_ROOT / "QLA_Migration" / "Reports")
    sandbox = str(PROJECT_ROOT / "plan_analysis" / "phase_r5_rate_loader" / "emitted_dbf")
    res = RL.relocate_non_csv(str(OUTPUT), reports, sandbox)
    dbf_after = dbf_path.is_file()
    sidecars_after = _sidecar_paths(dbf_path)
    print(f"  Hygiene moved {len(res['moved'])} file(s)")
    print(f"  After hygiene: DBF exists={dbf_after}, sidecars={[p.name for p in sidecars_after]}")
    if not dbf_after or not sidecars_after:
        errors.append("quikmemo_uat_dbf pair removed or split by output hygiene")

    csv_rows_after = len(pd.read_csv(CSV_PATH, dtype=str))
    print("\n--- CSV unchanged ---")
    print(f"  quikmemo.csv rows before={csv_rows_before} after={csv_rows_after}")
    if csv_rows_before != csv_rows_after:
        errors.append("quikmemo.csv row count changed")

    if csv_rows_after != EXPECTED_CSV_ROWS:
        errors.append(f"quikmemo.csv expected {EXPECTED_CSV_ROWS} rows, got {csv_rows_after}")

    print("\n--- Regression tables (vs before snapshot) ---")
    if BEFORE_DIR.is_dir():
        for name in ["quikmstr.csv", "quikridr.csv", "quikprmh.csv"]:
            b, a = BEFORE_DIR / name, OUTPUT / name
            if b.is_file() and a.is_file():
                bn, an = len(pd.read_csv(b, dtype=str)), len(pd.read_csv(a, dtype=str))
                ok = bn == an
                print(f"  {name}: {bn} -> {an} {'OK' if ok else 'CHANGED'}")
                if not ok:
                    errors.append(f"{name} row count changed")

    print("\n" + "=" * 72)
    if errors:
        print("RESULT: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
