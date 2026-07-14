from dbfread import DBF
from collections import Counter
from pathlib import Path
import csv

table = DBF(r"docs/QUIKLOAN.DBF", load=True, ignore_missing_memofile=True)
print("fields:")
for f in table.fields:
    dec = getattr(f, "decimal_count", 0)
    print(f"  {f.name:12} {f.type} {f.length}.{dec}")
print("total rows", len(table))

pols = Counter()
for r in table:
    p = str(r.get("MPOLICY", "")).strip()
    pols[p] += 1
print("unique policies", len(pols))
print("max rows/policy", max(pols.values()) if pols else 0)
print("policies with >1 row", sum(1 for v in pols.values() if v > 1))
print("top multi:", pols.most_common(15))

rows = [dict(r) for r in table if "14560K" in str(r.get("MPOLICY", "")).upper()]
print("14560K count", len(rows))


def sk(r):
    return (str(r.get("MLOANDATE") or ""), str(r.get("MLOANIDT") or ""), float(r.get("MLOANBAL") or 0))


rows.sort(key=sk)
cols = [
    "MPOLICY",
    "MLOANPRIN",
    "MLOANBAL",
    "MLOANINT",
    "MLOANINTX",
    "MLOANIDT",
    "MLOANDATE",
    "MLOANACCR",
    "MLOANBILL",
]
for r in rows:
    print({k: r.get(k) for k in cols})

out = Path(r"Issue_Log_Items/Issue_54/evidence")
out.mkdir(parents=True, exist_ok=True)
with (out / "issue54_docs_quikloan_14560K.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k) for k in cols})

# fleet multi-row summary
with (out / "issue54_docs_quikloan_multirow_summary.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["metric", "value"])
    w.writerow(["total_rows", len(table)])
    w.writerow(["unique_policies", len(pols)])
    w.writerow(["policies_with_gt1_row", sum(1 for v in pols.values() if v > 1)])
    w.writerow(["max_rows_per_policy", max(pols.values()) if pols else 0])
    w.writerow(["policy_14560K_rows", len(rows)])
