"""Match docs/QUIKBENH.DBF for 14560K to Loan History screenshot."""
from __future__ import annotations

import csv
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from dbfread import DBF

OUT = Path("Issue_Log_Items/Issue_54/evidence")
OUT.mkdir(parents=True, exist_ok=True)

# Visible Loan History screenshot rows (14560K)
SCREEN = [
    ("Loans Granted", date(1991, 10, 31), 0.71, -3.22),
    ("Loans Granted", date(1991, 11, 29), 0.71, -2.51),
    ("Loans Granted", date(1991, 12, 31), 0.71, -1.80),
    ("Interest Added", date(1991, 12, 31), 0.65, -1.15),
    ("Loan Payments", date(1991, 12, 31), 2.69, -3.84),
    ("Loans Granted", date(1992, 1, 31), 0.71, -3.13),
    ("Loans Granted", date(1992, 2, 29), 0.71, -2.42),
    ("Loans Granted", date(1992, 3, 31), 0.71, -1.71),
    ("Loans Granted", date(1992, 4, 30), 0.71, -1.00),
    ("Loans Granted", date(1992, 5, 31), 0.71, -0.29),
    ("Loans Granted", date(1992, 6, 30), 0.71, 0.42),
    ("Loans Granted", date(1992, 7, 31), 0.71, 1.13),
    ("Loans Granted", date(1992, 8, 31), 0.71, 1.84),
    ("Interest Added", date(1992, 9, 22), 0.78, 2.62),
    ("Loan Payments", date(1992, 9, 22), 2.85, -0.23),
    ("Loans Granted", date(1992, 9, 30), 0.71, 0.48),
    ("Loans Granted", date(1992, 10, 31), 0.71, 1.19),
    ("Loans Granted", date(1992, 11, 30), 0.71, 1.90),
    ("Loans Granted", date(1992, 12, 31), 0.71, 2.61),
    ("Interest Added", date(1992, 12, 31), 0.05, 2.66),
    ("Loan Payments", date(1992, 12, 31), 0.18, 2.48),
    ("Loans Granted", date(1993, 1, 31), 0.71, 3.19),
    ("Interest Added", date(1993, 2, 22), 0.03, 3.22),
    ("Loan Payments - Div", date(1993, 2, 22), 2.95, 0.27),
    ("Loans Granted", date(1993, 2, 28), 0.71, 0.98),
    ("Loans Granted", date(1993, 3, 31), 0.71, 1.69),
    ("Loans Granted", date(1993, 4, 30), 0.71, 2.40),
    ("Loans Granted", date(1993, 5, 31), 0.71, 3.11),
    ("Loans Granted", date(1993, 6, 30), 0.71, 3.82),
    ("Loans Granted", date(1993, 7, 31), 0.71, 4.53),
    ("Loans Granted", date(1993, 8, 31), 0.71, 5.24),
    ("Interest Added", date(1993, 9, 22), 0.21, 5.45),
    ("Loan Payments", date(1993, 9, 22), 2.85, 2.60),
    ("Loans Granted", date(1993, 9, 30), 0.71, 3.31),
    ("Loans Granted", date(1993, 10, 31), 0.71, 4.02),
    ("Loans Granted", date(1993, 11, 30), 0.71, 4.73),
    ("Loans Granted", date(1993, 12, 31), 0.71, 5.44),
    ("Interest Added", date(1993, 12, 31), 0.09, 5.53),
    ("Loan Payments", date(1993, 12, 31), 0.33, 5.20),
    ("Loans Granted", date(1994, 1, 31), 0.71, 5.91),
]

print("Opening QUIKBENH...")
table = DBF(r"docs/QUIKBENH.DBF", ignore_missing_memofile=True)
print("fields:")
for f in table.fields:
    print(f"  {f.name:12} {f.type} {f.length}.{getattr(f, 'decimal_count', 0)}")

rows = []
for r in table:
    if "14560K" in str(r.get("MPOLICY", "")).upper():
        rows.append(dict(r))

print(f"\n14560K quikbenh rows: {len(rows)}")
if not rows:
    raise SystemExit("no rows")

cols = list(rows[0].keys())
print("columns:", cols)
print("MBENTYP counts:", Counter(str(r.get("MBENTYP", "")).strip() for r in rows))

# sort by date
def as_date(v):
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    if v is None:
        return date.min
    s = str(v).strip()
    if len(s) == 8 and s.isdigit():
        return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    return date.min


rows.sort(key=lambda r: (as_date(r.get("MDATE")), str(r.get("MBENTYP", "")), float(r.get("MBEN") or 0)))

out_csv = OUT / "issue54_quikbenh_14560K.csv"
with out_csv.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k) for k in cols})
print("wrote", out_csv)

print("\n=== First 25 rows ===")
for r in rows[:25]:
    print(
        as_date(r.get("MDATE")),
        repr(str(r.get("MBENTYP", "")).strip()),
        r.get("MBEN"),
        {k: r.get(k) for k in cols if k not in {"MPOLICY", "MBENTYP", "MDATE", "MBEN"}},
    )

print("\n=== Rows overlapping screenshot date window 1991-10 to 1994-01 ===")
win = [
    r
    for r in rows
    if date(1991, 10, 1) <= as_date(r.get("MDATE")) <= date(1994, 1, 31)
]
print("count", len(win))
for r in win[:60]:
    print(as_date(r.get("MDATE")), repr(str(r.get("MBENTYP", "")).strip()), float(r.get("MBEN") or 0))

# Match screen rows on date+amount
print("\n=== Screenshot match (date + amount) ===")
benh_keys = Counter()
for r in rows:
    d = as_date(r.get("MDATE"))
    try:
        amt = round(abs(float(r.get("MBEN") or 0)), 2)
    except Exception:
        continue
    benh_keys[(d, amt)] += 1

matched = 0
partial = []
for typ, d, amt, bal in SCREEN:
    key = (d, round(amt, 2))
    key_neg = (d, round(-amt, 2))
    # also try signed as stored
    hits = benh_keys.get(key, 0) + benh_keys.get((d, round(float(amt), 2)), 0)
    # signed variants already covered by abs above
    same_day = [r for r in rows if as_date(r.get("MDATE")) == d]
    amt_hit = any(abs(abs(float(r.get("MBEN") or 0)) - amt) < 0.005 for r in same_day)
    if amt_hit:
        matched += 1
        types = [str(r.get("MBENTYP", "")).strip() for r in same_day if abs(abs(float(r.get("MBEN") or 0)) - amt) < 0.005]
        print(f"  MATCH {typ} {d} {amt} -> MBENTYP={types}")
    else:
        same_day_amts = [(str(r.get("MBENTYP", "")).strip(), float(r.get("MBEN") or 0)) for r in same_day]
        partial.append((typ, d, amt, same_day_amts))

print(f"matched {matched}/{len(SCREEN)}")
print("unmatched sample:")
for u in partial[:12]:
    print(" ", u)

# Does running balance exist as cumulative MBEN by type?
print("\n=== All MBENTYP labels/values for policy ===")
for typ, n in Counter(str(r.get("MBENTYP", "")).strip() for r in rows).most_common():
    amts = [float(r.get("MBEN") or 0) for r in rows if str(r.get("MBENTYP", "")).strip() == typ]
    print(f"  typ={typ!r} n={n} amt_min={min(amts):.2f} max={max(amts):.2f} sample={amts[:5]}")
