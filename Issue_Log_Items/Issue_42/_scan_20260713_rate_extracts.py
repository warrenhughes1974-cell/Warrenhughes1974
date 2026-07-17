"""Read-only inventory: Issue #42 + Eric 2026-07-13 gap IDs vs new Source extracts."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"c:\Users\warren\Documents\GitHub\Warrenhughes1974")
SRC = ROOT / "QLA_Migration" / "Source"
OUT = ROOT / "Issue_Log_Items" / "Issue_42" / "evidence_20260713_rate_gap_scan.csv"

FOCUS = {
    "L01 10Y": {"NP", "RV"},
    "L01 10Y LT": {"NP", "RV", "PR", "CV"},
    "L10 LP9595": {"NP", "RV", "CV", "PR"},
    "L10 LP95": {"NP", "RV", "CV", "PR"},
    "L17": {"CV", "NP", "RV", "PR"},
    "L17 1": {"CV", "NP", "RV", "PR"},
    "L17 2+": {"CV", "NP", "RV", "PR"},
    "960 LP85-8": {"CV", "NP", "RV", "PR", "DV"},
    "960 LP85-M": {"CV", "NP", "RV", "PR", "DV"},
    "0824 P DTH": {"NP", "RV", "PR", "DB"},
    "L10 GPO OL": {"NP", "RV", "PR", "DB"},
    "L10 GPO": {"NP", "RV", "PR"},
}

TOKENS = ["L01 10Y", "L10 LP95", "L17", "LP85-8", "0824 P DTH", "L10 GPO"]

FILES = {
    "PAAGERAT_20260713": SRC / "PAAGERAT_AttainedAge_Rates_Extract_20260713.csv",
    "PAAGERAT_20260630": SRC / "PAAGERAT_AttainedAge_Rates_Extract_20260630.csv",
    "PDAGE_20260713": SRC / "PDAGE_AgeDuration_Rates_Extract_20260713.csv",
    "PDAGE_20260630": SRC / "PDAGE_AgeDuration_Rates_Extract_20260630.csv",
    "Rate_Table_Txt": SRC / "Rate_Table_Extract_Txt.txt",
}


def scan(path: Path, label: str):
    counts: dict[tuple[str, str], int] = defaultdict(int)
    cov_types: dict[str, set[str]] = defaultdict(set)
    token_hits: dict[str, set[str]] = defaultdict(set)
    n = 0
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            n += 1
            cov = (row.get("COVERAGE_ID") or "").strip()
            typ = (row.get("TYPE_CODE") or "").strip()
            if not cov or cov.startswith("-"):
                continue
            for tok in TOKENS:
                if tok in cov:
                    token_hits[tok].add(cov)
            if cov in FOCUS:
                counts[(cov, typ)] += 1
                cov_types[cov].add(typ)
    print(f"\n=== {label} rows={n:,} ===")
    rows = []
    for cov in sorted(FOCUS):
        types = sorted(cov_types.get(cov, []))
        wanted = FOCUS[cov]
        if not types:
            print(f"  {cov!r}: ABSENT")
            for t in sorted(wanted):
                rows.append(
                    {
                        "extract": label,
                        "coverage_id": cov,
                        "type_code": t,
                        "row_count": 0,
                        "status": "ABSENT",
                    }
                )
            continue
        parts = []
        all_types = sorted(set(list(wanted) + types))
        for t in all_types:
            c = counts.get((cov, t), 0)
            if c or t in wanted:
                parts.append(f"{t}={c}")
                status = "PRESENT" if c > 0 else "MISSING_TYPE"
                rows.append(
                    {
                        "extract": label,
                        "coverage_id": cov,
                        "type_code": t,
                        "row_count": c,
                        "status": status,
                    }
                )
        print(f"  {cov!r}: {' '.join(parts)}  [types: {','.join(types)}]")
    print("  Token discovery:")
    for tok in TOKENS:
        ids = sorted(token_hits.get(tok, []))
        print(f"    {tok}: {ids if ids else '(none)'}")
    return rows


all_rows = []
for label, path in FILES.items():
    if not path.exists():
        print(f"MISSING {path}")
        continue
    all_rows.extend(scan(path, label))

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(
        f, fieldnames=["extract", "coverage_id", "type_code", "row_count", "status"]
    )
    w.writeheader()
    w.writerows(all_rows)
print(f"\nWrote {OUT}")
