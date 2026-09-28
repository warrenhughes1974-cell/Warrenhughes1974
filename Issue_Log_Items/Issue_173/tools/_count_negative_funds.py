"""Read-only counts for Issue 173. Does not write Output."""
import csv
from collections import Counter
from pathlib import Path

root = Path(".")
exc_path = root / "QLA_Migration/Reports/issue155_iswl_seed_exceptions_20260630.csv"
pf_path = root / "QLA_Migration/Source/PFNDR_FundHistory_Extract_20260630.csv"
qw_path = root / "QLA_Migration/Output/QuikIswl.csv"

reasons = Counter()
floor_pols = set()
with exc_path.open(newline="", encoding="latin1") as f:
    for row in csv.DictReader(f):
        reasons[row["REASON"]] += 1
        if row["REASON"] == "NEGATIVE_FLOORED_ZERO":
            floor_pols.add(row["MPOLICY"])

pf = {}
dup_pf = 0
with pf_path.open(newline="", encoding="latin1") as f:
    reader = csv.DictReader(f)
    reader.fieldnames = [(h or "").strip() for h in (reader.fieldnames or [])]
    for row in reader:
        cleaned = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
        pol = cleaned.get("POLICY_NUMBER") or ""
        if not pol:
            continue
        key = pol if pol.endswith("C") else pol + "C"
        try:
            bal = float((cleaned.get("FUND_BALANCE") or "0").replace(",", "") or 0)
        except ValueError:
            continue
        if key in pf:
            dup_pf += 1
        pf[key] = bal

last = {}
rows_n = 0
with qw_path.open(newline="", encoding="latin1") as f:
    for row in csv.DictReader(f):
        rows_n += 1
        pol = (row.get("MPOLICY") or "").strip()
        ann = (row.get("MLASTANNV") or "").strip()
        prev = last.get(pol)
        if prev is None or ann >= prev[0]:
            last[pol] = (ann, row.get("MACCTBAL") or "")

neg_end = []
pos_unchanged = 0
zero_match = 0
for pol, (ann, acct_s) in last.items():
    fund = pf.get(pol)
    if fund is None:
        continue
    try:
        acct = float(acct_s)
    except ValueError:
        continue
    if fund < -0.005:
        neg_end.append((fund, pol, acct, ann))
    elif abs(acct - fund) <= 0.011:
        pos_unchanged += 1
    if abs(fund) <= 0.011 and abs(acct) <= 0.011:
        zero_match += 1

neg_end.sort()
floor_but_positive_end = [p for p in floor_pols if pf.get(p, 0) >= -0.005]
print("pfndr_policies", len(pf))
print("pfndr_duplicate_rows", dup_pf)
print("quikiswl_rows", rows_n)
print("quikiswl_policies", len(last))
print("exception_reasons", dict(reasons))
print("floor_policies", len(floor_pols))
print("ending_negative_in_output", len(neg_end))
print("floor_policies_whose_lifepro_end_is_not_negative", len(floor_but_positive_end))
print("positive_or_zero_already_tied", pos_unchanged)
print("both_zero", zero_match)
print("most_negative")
for fund, pol, acct, ann in neg_end[:8]:
    print(f"  {pol} lifepro {fund:.2f} ql {acct} date {ann}")
for pol in ("9010713704C", "9010713705C", "9010713707C", "9010779727C"):
    ann, acct = last.get(pol, ("", ""))
    print("trace", pol, "ql", acct, "ann", ann, "lifepro", pf.get(pol))
