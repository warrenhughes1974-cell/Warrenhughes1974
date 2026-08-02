#!/usr/bin/env python3
"""Issue #135 — generate fresh claims UAT DBFs from verified Output CSVs + short names."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "QLA_Migration" / "Output"
STAGING = ROOT / "QLA_Migration" / "Staging" / "claims_uat_dbf"
GEN = ROOT / "claims_analysis" / "phase19_uat_emitted_csv_dbf" / "uat_emitted_csv_dbf_generator.py"


def main() -> int:
    clms = OUT / "quikclms.csv"
    clmp = OUT / "quikclmp.csv"
    if not clms.is_file() or not clmp.is_file():
        print("FAIL: missing Output quikclms/quikclmp")
        return 2

    STAGING.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(GEN),
        "--clms-csv",
        str(clms),
        "--clmp-csv",
        str(clmp),
        "--output-dir",
        str(STAGING),
        "--run-mode",
        "UAT",
    ]
    print("RUN", " ".join(cmd))
    rc = subprocess.call(cmd)
    if rc != 0:
        print("FAIL: generator rc=", rc)
        return rc

    # Short-name aliases for QLAdmin load (byte copies of phase19 outputs)
    pairs = [
        ("QUIKCLMS_PHASE19_UAT.DBF", "QUIKCLMS.DBF"),
        ("QUIKCLMS_PHASE19_UAT.DBT", "QUIKCLMS.DBT"),
        ("QUIKCLMP_PHASE19_UAT.DBF", "QUIKCLMP.DBF"),
    ]
    for src_name, dst_name in pairs:
        src = STAGING / src_name
        dst = STAGING / dst_name
        if not src.is_file():
            print("FAIL: missing generated", src)
            return 3
        shutil.copy2(src, dst)
        print("copied", src_name, "->", dst_name)

    # Ensure no QUIKCLMP.DBT
    clmp_dbt = STAGING / "QUIKCLMP.DBT"
    if clmp_dbt.exists():
        clmp_dbt.unlink()
        print("removed unexpected QUIKCLMP.DBT")
    phase_dbt = STAGING / "QUIKCLMP_PHASE19_UAT.DBT"
    if phase_dbt.exists():
        # generator typically does not create payee DBT; remove if present
        phase_dbt.unlink()
        print("removed QUIKCLMP_PHASE19_UAT.DBT")

    print("DBF_GENERATE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
