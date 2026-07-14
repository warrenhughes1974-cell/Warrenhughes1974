"""Audit docs QuikActg.dbf vs QuikLoan.dbf for Loan History source hypothesis."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from dbfread import DBF

OUT = Path("Issue_Log_Items/Issue_54/evidence")
OUT.mkdir(parents=True, exist_ok=True)

actg = DBF(r"docs/QuikActg.dbf", load=True, ignore_missing_memofile=True)
loan = DBF(r"docs/QUIKLOAN.DBF", load=True, ignore_missing_memofile=True)

print("=== QuikActg schema ===")
for f in actg.fields:
    print(f"  {f.name:12} {f.type} {f.length}.{getattr(f, 'decimal_count', 0)}")
print("rows", len(actg))

# sample first 3
print("\n=== QuikActg sample rows ===")
for i, r in enumerate(actg):
    if i >= 3:
        break
    print(dict(r))

# field population
keys = [f.name for f in actg.fields]
nonblank = Counter()
for r in actg:
    for k in keys:
        v = r.get(k)
        if v is None:
            continue
        s = str(v).strip()
        if s and s not in {".", "0", "0.0", "0.00"}:
            nonblank[k] += 1

print("\n=== Non-blank/nonzero counts ===")
for k in keys:
    print(f"  {k}: {nonblank[k]}/{len(actg)}")

# MLOAN / MLOANINT values
mloan = Counter(str(r.get("MLOAN", "")).strip() for r in actg)
mloanint = Counter(str(r.get("MLOANINT", "")).strip() for r in actg)
print("\n=== MLOAN distinct (top 20) ===")
print(mloan.most_common(20))
print("=== MLOANINT distinct (top 20) ===")
print(mloanint.most_common(20))

# Does Actg have MPOLICY?
has_mpolicy = "MPOLICY" in keys
print("\nhas MPOLICY?", has_mpolicy)
print("index-like fields present:", [k for k in keys if k in {"MCOMP", "MPLAN", "MPOLICY", "MDATE", "MAMOUNT"}])

# QuikLoan 14560K
loan_row = [dict(r) for r in loan if "14560K" in str(r.get("MPOLICY", "")).upper()]
print("\n=== QuikLoan 14560K ===")
print(loan_row)

# Try join paths: no policy on actg — check if any plan on loan side
# QuikLoan has no MPLAN. Look for companion master?
print("\nQuikLoan fields:", [f.name for f in loan.fields])
print("QuikActg unique MCOMP", len({str(r.get("MCOMP", "")).strip() for r in actg}))
print("QuikActg unique MPLAN", len({str(r.get("MPLAN", "")).strip() for r in actg}))
print("QuikActg total rows", len(actg))
print("QuikLoan total rows", len(loan))

# Write summary
with (OUT / "issue54_quikactg_vs_quikloan_audit.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["metric", "value"])
    w.writerow(["quikactg_rows", len(actg)])
    w.writerow(["quikactg_has_mpolicy", has_mpolicy])
    w.writerow(["quikactg_unique_mplan", len({str(r.get("MPLAN", "")).strip() for r in actg})])
    w.writerow(["quikloan_rows", len(loan)])
    w.writerow(["quikloan_14560K_rows", len(loan_row)])
    w.writerow(["join_on_policy_possible", False])
    w.writerow(
        [
            "quikactg_grain",
            "plan-level GL chart (MCOMP+MPLAN); MLOAN/MLOANINT are account numbers not txn amounts",
        ]
    )
    w.writerow(
        [
            "loan_history_grid_in_quikactg",
            "NO — no Transaction/Date/Amount/Balance; no policy key; not multi-row policy history",
        ]
    )

# dump actg rows that have MLOAN or MLOANINT populated
with (OUT / "issue54_quikactg_loan_account_rows.csv").open("w", newline="", encoding="utf-8") as f:
    cols = ["MCOMP", "MPLAN", "MLOAN", "MLOANINT"]
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in actg:
        row = {k: str(r.get(k, "")).strip() for k in cols}
        if row["MLOAN"] or row["MLOANINT"]:
            w.writerow(row)

print("\nWrote evidence CSVs")
