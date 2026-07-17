"""Inventory Issue #42 + Eric residual IDs vs wired 20260714 Source extracts."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"c:\Users\warren\Documents\GitHub\Warrenhughes1974")
SRC = ROOT / "QLA_Migration" / "Source"
OUT = ROOT / "Issue_Log_Items" / "Issue_42" / "evidence_20260714_rate_gap_scan.csv"
OUT_SUMMARY = ROOT / "Issue_Log_Items" / "Issue_42" / "evidence_20260714_rate_gap_summary.json"

FOCUS = {
    "L01 10Y": {"NP", "RV", "NN", "PN", "CV", "PR"},
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

# Client/screenshot critical checks for pending-business closeout
CRITICAL = [
    ("L01 10Y", "NP"),
    ("L01 10Y", "RV"),
    ("L10 LP9595", "NP"),
    ("L10 LP9595", "RV"),
    ("L17", "CV"),
    ("960 LP85-8", "CV"),
    ("0824 P DTH", "NP"),
    ("L10 GPO OL", "NP"),
]

FILES = {
    "PAAGERAT_20260714": SRC / "PAAGERAT_AttainedAge_Rates_Extract_20260714.csv",
    "PDAGE_20260714": SRC / "PDAGE_AgeDuration_Rates_Extract_20260714.csv",
    "Rate_Table_Txt": SRC / "Rate_Table_Extract_Txt.txt",
}


def scan(path: Path, label: str):
    counts: dict[tuple[str, str], int] = defaultdict(int)
    cov_types: dict[str, set[str]] = defaultdict(set)
    n = 0
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            n += 1
            cov = (row.get("COVERAGE_ID") or "").strip()
            typ = (row.get("TYPE_CODE") or "").strip()
            if not cov or cov.startswith("-"):
                continue
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
        print(f"  {cov!r}: {', '.join(parts)}")
    return rows, counts


def union_available(all_counts: dict[str, dict[tuple[str, str], int]]):
    """True if any extract has rows for (cov, type)."""
    avail = {}
    for cov, typ in CRITICAL:
        total = 0
        sources = []
        for label, counts in all_counts.items():
            c = counts.get((cov, typ), 0)
            if c:
                total += c
                sources.append(f"{label}:{c}")
        avail[(cov, typ)] = {"total_rows_across_extracts": total, "sources": sources}
    return avail


def main() -> None:
    import sys

    sys.path.insert(0, str(ROOT))
    from qla_core.plan_source_paths import paagerat_extract, pdage_extract

    print("Wired paths:")
    print("  pdage   =", pdage_extract())
    print("  paagerat=", paagerat_extract())

    all_rows = []
    all_counts = {}
    for label, path in FILES.items():
        if not path.is_file():
            print(f"MISSING FILE: {path}")
            continue
        rows, counts = scan(path, label)
        all_rows.extend(rows)
        all_counts[label] = counts

    avail = union_available(all_counts)
    print("\n=== CRITICAL union (Rate_Table + PDAGE + PAAGERAT) ===")
    still_missing = []
    newly_present = []
    for cov, typ in CRITICAL:
        info = avail[(cov, typ)]
        status = "PRESENT" if info["total_rows_across_extracts"] > 0 else "MISSING"
        print(f"  {cov}|{typ}: {status} {info['sources'] or ['none']}")
        if status == "MISSING":
            still_missing.append({"coverage_id": cov, "type_code": typ})
        else:
            newly_present.append(
                {
                    "coverage_id": cov,
                    "type_code": typ,
                    "sources": info["sources"],
                    "total": info["total_rows_across_extracts"],
                }
            )

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["extract", "coverage_id", "type_code", "row_count", "status"],
        )
        w.writeheader()
        w.writerows(all_rows)

    summary = {
        "wired_pdage": pdage_extract(),
        "wired_paagerat": paagerat_extract(),
        "critical_present": newly_present,
        "critical_still_missing": still_missing,
        "evidence_csv": str(OUT),
    }
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"\nStill missing critical: {len(still_missing)}")
    for m in still_missing:
        print(f"  - {m['coverage_id']}|{m['type_code']}")


if __name__ == "__main__":
    main()
