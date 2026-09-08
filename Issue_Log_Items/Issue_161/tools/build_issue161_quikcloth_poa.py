"""Issue #161 (amendment) — build QLA_Migration/Output/quikcloth.csv (POFA only).

QLAdmin Help (QLAdmin_Help.pdf, section 7.69, page 737) documents QuikCloth -
Client Other Record as the table that backs the Names tab "Other Information"
grid, keyed MPOLICY + MRELATION + MCLOTHID. This table has never been emitted
by the conversion (confirmed 0 rows in the live 6/30/2026 QLAdmin build).

Scope: derive quikcloth rows ONLY from the quikclid MRELATION=POFA population
already fixed under Issue #161 (LifePRO RELATE_CODE=PW). Does not invent rows
for ASGN/JINS/JOWN/LAPS or any other "Other Information" code not reported by
the client -- those stay in quikclid untouched and are out of scope here.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CLID = ROOT / "QLA_Migration" / "Output" / "quikclid.csv"
CLOTH = ROOT / "QLA_Migration" / "Output" / "quikcloth.csv"

FIELDS = ["MPOLICY", "MRELATION", "MCLOTHID"]

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
        clid_rows = list(reader)

    out_rows = []
    for row in clid_rows:
        rel = str(row.get("MRELATION") or "").strip().upper()
        if rel != "POFA":
            continue
        out_rows.append(
            {
                "MPOLICY": str(row.get("MPOLICY") or "").strip(),
                "MRELATION": "POFA",
                "MCLOTHID": row.get("MCLIENTID") or "",
            }
        )

    with CLOTH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(out_rows)

    print("Issue #161 quikcloth (Client Other Record) build")
    print(f"quikclid POFA rows read={len(out_rows)}")
    print(f"quikcloth rows written={len(out_rows)} -> {CLOTH}")

    for pol, cid in EXAMPLES:
        cid_padded_variants = {cid, cid.rjust(12), f"{cid:>12}"}
        hit = any(
            r["MPOLICY"] == pol and str(r["MCLOTHID"]).strip() == cid
            for r in out_rows
        )
        print(f"example {pol} / {cid}: {'OK' if hit else 'MISSING'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
