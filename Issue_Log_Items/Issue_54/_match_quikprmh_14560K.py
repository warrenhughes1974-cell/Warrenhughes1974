"""Match docs/quikprmh.dbf for 14560K to Loan History screenshot."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from dbfread import DBF

OUT = Path("Issue_Log_Items/Issue_54/evidence")
OUT.mkdir(parents=True, exist_ok=True)

# Screenshot visible rows (from Loan History - 14560K)
SCREEN = [
    ("Loans Granted", "1991-10-31", 0.71, -3.22),
    ("Loans Granted", "1991-11-29", 0.71, -2.51),
    ("Loans Granted", "1991-12-31", 0.71, -1.80),
    ("Interest Added", "1991-12-31", 0.65, -1.15),
    ("Loan Payments", "1991-12-31", 2.69, -3.84),
    ("Loans Granted", "1992-01-31", 0.71, -3.13),
    ("Loans Granted", "1992-02-29", 0.71, -2.42),
    ("Loans Granted", "1992-03-31", 0.71, -1.71),
    ("Loans Granted", "1992-04-30", 0.71, -1.00),
    ("Loans Granted", "1992-05-31", 0.71, -0.29),
    ("Loans Granted", "1992-06-30", 0.71, 0.42),
    ("Loans Granted", "1992-07-31", 0.71, 1.13),
    ("Loans Granted", "1992-08-31", 0.71, 1.84),
    ("Interest Added", "1992-09-22", 0.78, 2.62),
    ("Loan Payments", "1992-09-22", 2.85, -0.23),
    ("Loans Granted", "1992-09-30", 0.71, 0.48),
    ("Loans Granted", "1992-10-31", 0.71, 1.19),
    ("Loans Granted", "1992-11-30", 0.71, 1.90),
    ("Loans Granted", "1992-12-31", 0.71, 2.61),
    ("Interest Added", "1992-12-31", 0.05, 2.66),
    ("Loan Payments", "1992-12-31", 0.18, 2.48),
    ("Loans Granted", "1993-01-31", 0.71, 3.19),
    ("Interest Added", "1993-02-22", 0.03, 3.22),
    ("Loan Payments - Div", "1993-02-22", 2.95, 0.27),
    ("Loans Granted", "1993-02-28", 0.71, 0.98),
    ("Loans Granted", "1993-03-31", 0.71, 1.69),
    ("Loans Granted", "1993-04-30", 0.71, 2.40),
    ("Loans Granted", "1993-05-31", 0.71, 3.11),
    ("Loans Granted", "1993-06-30", 0.71, 3.82),
    ("Loans Granted", "1993-07-31", 0.71, 4.53),
    ("Loans Granted", "1993-08-31", 0.71, 5.24),
    ("Interest Added", "1993-09-22", 0.21, 5.45),
    ("Loan Payments", "1993-09-22", 2.85, 2.60),
    ("Loans Granted", "1993-09-30", 0.71, 3.31),
    ("Loans Granted", "1993-10-31", 0.71, 4.02),
    ("Loans Granted", "1993-11-30", 0.71, 4.73),
    ("Loans Granted", "1993-12-31", 0.71, 5.44),
    ("Interest Added", "1993-12-31", 0.09, 5.53),
    ("Loan Payments", "1993-12-31", 0.33, 5.20),
    ("Loans Granted", "1994-01-31", 0.71, 5.91),
]

print("Opening quikprmh (large)...")
table = DBF(r"docs/quikprmh.dbf", ignore_missing_memofile=True)
print("fields:")
for f in table.fields:
    print(f"  {f.name:12} {f.type} {f.length}.{getattr(f, 'decimal_count', 0)}")

rows = []
for r in table:
    pol = str(r.get("MPOLICY", "")).strip().upper()
    if "14560K" in pol:
        rows.append(dict(r))

print(f"\n14560K quikprmh rows: {len(rows)}")
if not rows:
    # try variants
    print("No exact 14560K — scanning sample of policies containing 14560...")
    sample = []
    for i, r in enumerate(table):
        if i > 50000:
            break
        pol = str(r.get("MPOLICY", ""))
        if "14560" in pol:
            sample.append(pol)
    print("sample hits", Counter(sample).most_common(10))
else:
    # print field names from first row
    cols = list(rows[0].keys())
    print("columns:", cols)

    # write all rows
    out_path = OUT / "issue54_quikprmh_14560K.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in cols})
    print("wrote", out_path)

    # show first 15 and look for amount/date-like fields
    print("\n=== First 15 rows ===")
    for r in rows[:15]:
        print({k: r.get(k) for k in cols})

    # amount-ish fields
    numericish = []
    for k in cols:
        vals = [r.get(k) for r in rows[:50]]
        if any(isinstance(v, (int, float)) for v in vals):
            numericish.append(k)
    print("\nnumeric-ish fields:", numericish)

    # Try match screenshot amounts in any numeric field
    screen_amts = {round(a, 2) for _, _, a, _ in SCREEN}
    screen_bals = {round(b, 2) for _, _, _, b in SCREEN}
    print("\n=== Amount match scan ===")
    for k in numericish:
        vals = []
        for r in rows:
            try:
                vals.append(round(float(r.get(k) or 0), 2))
            except Exception:
                pass
        hit_amt = sum(1 for v in vals if v in screen_amts)
        hit_bal = sum(1 for v in vals if v in screen_bals)
        if hit_amt or hit_bal:
            print(f"  {k}: amount_hits={hit_amt} balance_hits={hit_bal} distinct={len(set(vals))} sample={vals[:10]}")

    # date fields
    print("\n=== Date-like sample ===")
    for k in cols:
        if "DATE" in k.upper() or k.upper() in {"MDATE", "MPDATE", "MEFFDATE", "MTRANDATE"}:
            print(k, [rows[i].get(k) for i in range(min(5, len(rows)))])
