"""Build Issue #55 UAT QUIKRIDR package (sample policies only)."""
from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from qladmin_core.quikridr_dbf_writer import read_quikridr_munit, write_quikridr_dbf
SRC = REPO / "QLA_Migration" / "Output" / "quikridr.csv"
OUT_DIR = REPO / "QLA_Migration" / "Staging" / "issue55_quikridr_uat"
UAT_ISSUE = REPO / "Issue_Log_Items" / "Issue_55" / "uat"
TV = REPO / "QLA_Migration" / "Output" / "Test_Validation"
POLS = {"018495BC", "018499CC", "018510C"}
EXPECTED = {
    ("018495BC", 1): 0.00001,
    ("018495BC", 2): 0.53,
    ("018499CC", 1): 0.00001,
    ("018499CC", 2): 1.05,
    ("018510C", 1): 0.00001,
    ("018510C", 2): 0.647,
}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    UAT_ISSUE.mkdir(parents=True, exist_ok=True)
    TV.mkdir(parents=True, exist_ok=True)

    rows = []
    with open(SRC, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        for row in reader:
            if (row.get("MPOLICY") or "").strip() in POLS:
                rows.append(row)

    csv_path = OUT_DIR / "quikridr_issue55_samples.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    shutil.copy2(csv_path, UAT_ISSUE / "quikridr_issue55_samples.csv")
    shutil.copy2(csv_path, TV / "quikridr_issue55_samples.csv")

    dbf_path = OUT_DIR / "QUIKRIDR.DBF"
    info = write_quikridr_dbf(str(csv_path), str(dbf_path))
    shutil.copy2(dbf_path, UAT_ISSUE / "QUIKRIDR.DBF")

    print("Wrote", info)
    print("CSV rows:", len(rows))
    ok = True
    print("=== verify ===")
    for (pol, ph), exp in EXPECTED.items():
        rec = read_quikridr_munit(str(dbf_path), pol, ph)
        got = None if not rec else round(float(rec["MUNIT"]), 5)
        face = None if not rec else rec["face"]
        match = got == round(exp, 5)
        ok = ok and match
        status = "PASS" if match else "FAIL"
        print(f"{pol} P{ph}: MUNIT={got} face={face} expected={exp} {status}")
    print("OVERALL", "PASS" if ok else "FAIL")
    print("DBF:", dbf_path.resolve())
    print("Also:", UAT_ISSUE / "QUIKRIDR.DBF")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
