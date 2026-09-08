"""Issue #161 — scoped remap: quikclid.MRELATION PW → POFA.

Reads QLA_Migration/Output/quikclid.csv and updates only MRELATION when the
current value is PW. Does not add/remove rows or touch any other column.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CLID = ROOT / "QLA_Migration" / "Output" / "quikclid.csv"

EXAMPLES = (
    ("9010442216C", "712072"),
    ("9010451650C", "712326"),
    ("9011045619C", "591432"),
)


def main() -> int:
    if not CLID.is_file():
        print(f"FAIL: missing {CLID}")
        return 1

    with CLID.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        if not fields:
            print("FAIL: quikclid.csv has no header")
            return 1
        rows = list(reader)

    changed = 0
    samples: list[str] = []
    for row in rows:
        rel = str(row.get("MRELATION") or "").strip().upper()
        if rel != "PW":
            continue
        row["MRELATION"] = "POFA"
        changed += 1
        if len(samples) < 6:
            pol = str(row.get("MPOLICY") or "").strip()
            cid = str(row.get("MCLIENTID") or "").strip()
            samples.append(f"  MPOLICY={pol} MCLIENTID={cid} BEFORE=PW AFTER=POFA")

    with CLID.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)

    print("Issue #161 POA MRELATION remap")
    print(f"rows_read={len(rows)}")
    print(f"MRELATION PW->POFA changed={changed}")
    if samples:
        print("sample changes:")
        for line in samples:
            print(line)
    for pol, cid in EXAMPLES:
        hit = False
        for row in rows:
            if str(row.get("MPOLICY") or "").strip() != pol:
                continue
            if str(row.get("MCLIENTID") or "").strip() != cid:
                continue
            if str(row.get("MRELATION") or "").strip().upper() == "POFA":
                hit = True
                break
        print(f"example {pol} / {cid}: {'POFA' if hit else 'MISSING'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
