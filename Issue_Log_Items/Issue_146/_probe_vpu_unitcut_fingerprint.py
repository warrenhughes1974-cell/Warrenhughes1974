"""Read-only probe: for Value Per Unit mismatches in docs/Valuation File Comparison Research.xlsx,
fingerprint the unit-cut set (has QuikIsrr rows) against PPOLC billing reason / annual premium,
and profile the zero-VPU set by status and plan."""
import csv
from pathlib import Path
from collections import Counter, defaultdict
import openpyxl

root = Path(r"C:\Users\warren\Documents\GitHub\Warrenhughes1974")
out = root / "QLA_Migration" / "Output"
src = root / "QLA_Migration" / "Source"

wb = openpyxl.load_workbook(root / "docs" / "Valuation File Comparison Research.xlsx",
                            read_only=True, data_only=True)
ws = wb["Value Per Unit"]
mism, zero = set(), set()
for i, row in enumerate(ws.iter_rows(values_only=True), 1):
    if i == 1 or not row or row[1] is None:
        continue
    try:
        d = float(row[4] or 0)
        ql = float(row[3] or 0)
    except Exception:
        continue
    if abs(d) <= 0.01:
        continue
    p = str(row[1]).strip().replace(".0", "")
    mism.add(p)
    if abs(ql) < 0.01:
        zero.add(p)

isrr = defaultdict(list)
with (out / "quikisrr.csv").open(newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        p = (row.get("MPOLICY") or "").strip().rstrip("C")
        isrr[p].append((row.get("MSURRDATE"), float(row.get("MSURRAMT") or 0)))

cut = [p for p in mism if p in isrr]
print("mismatch policies with ISRR rows:", len(cut))

info = {}
with (src / "PPOLC_PolicyMaster_Extract_20260630.csv").open(newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        p = (row.get("POLICY_NUMBER") or "").strip()
        if p in cut:
            info[p] = {
                "br": (row.get("BILLING_REASON") or "").strip(),
                "ann": float(row.get("ANNUAL_PREMIUM") or 0),
            }

br_count = Counter()
print("policy       bill_rsn  annprem  n0561  amts=prem  distinct_monthdays")
for p in sorted(cut):
    i = info.get(p, {})
    rows = isrr[p]
    amts = [a for _, a in rows]
    ann = i.get("ann", 0)
    match = sum(1 for a in amts if abs(a - ann) < 0.51)
    mds = set(d[4:] for d, _ in rows if d)
    br = i.get("br", "?") or "(blank)"
    br_count[br] += 1
    print(f"{p:<12} {br:<8} {ann:>8.2f} {len(rows):>5} {match:>6}/{len(rows):<4} {len(mds):>4}")
print("billing reasons:", dict(br_count))

stat, plans = Counter(), Counter()
with (out / "quikmstr.csv").open(newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        p = (row.get("MPOLICY") or "").strip().rstrip("C")
        if p in zero:
            stat[(row.get("MSTATUS") or "").strip()] += 1
with (out / "quikridr.csv").open(newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        p = (row.get("MPOLICY") or "").strip().rstrip("C")
        if p in zero and str(row.get("MPHASE") or "").strip() == "1":
            plans[(row.get("MPLAN") or "").strip()] += 1
print("ZERO-VPU quikmstr MSTATUS dist:", dict(stat))
print("ZERO-VPU phase-1 plans:", dict(plans))
