import csv
from pathlib import Path

ROOT = Path(r"c:\Users\warren\Documents\GitHub\Warrenhughes1974")
mc = ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
pc = ROOT / "QLA_Migration" / "Mapping" / "product_catalog_crosswalk.csv"
qp = ROOT / "QLA_Migration" / "Output" / "quikplan.csv"

want = [
    "DISCHO2475",
    "DISCHO29",
    "DISCHO247C",
    "DISCHO25",
    "DISCHO70",
    "670 GL858",
    "670 GL8588",
    "670 GL85-8",
    "L05 10Y LT",
    "0822 960PO",
    "665 STME95",
    "619 SPS PU",
    "619 DT SP",
    "L10 LP95",
    "L10 LP9595",
    "ZERO",
    "L10ZERO",
    "ZERO LIFE",
]

print("=== Master exact ===")
with open(mc, newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        old = (row.get("Old_Value") or "").strip()
        new = (row.get("New_Value") or "").strip()
        if old in want:
            print(f"{old!r} -> {new!r}")

print("\n=== Catalog exact ===")
with open(pc, newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        cid = (row.get("lifepro_coverage_id") or "").strip()
        if cid in want:
            print(
                cid,
                "emit=",
                (row.get("ql_plan_code") or "").strip(),
                "xwalk=",
                (row.get("crosswalk_ql_plan_code") or "").strip(),
                "descr=",
                (row.get("ql_plan_description") or "").strip(),
                "status=",
                (row.get("mapping_status") or "").strip(),
            )

plans = [
    "9DIS25",
    "9DIS24",
    "9DS24C",
    "9DIS29",
    "DISCHO29",
    "9DIS70",
    "170588",
    "170858",
    "5L0510",
    "9POADB",
    "2665ST",
    "7619PU",
    "719SDT",
    "5L0110",
]
print("\n=== quikplan ===")
with open(qp, newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        p = (row.get("PLAN") or "").strip()
        if p in plans:
            print(
                p,
                "|",
                (row.get("FORM") or "").strip(),
                "|",
                (row.get("DESCR") or row.get("PLANNAME") or "").strip(),
            )
