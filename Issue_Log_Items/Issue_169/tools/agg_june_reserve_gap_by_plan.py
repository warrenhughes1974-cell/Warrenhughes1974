import csv
from collections import defaultdict

targets = {"960 LP85-M", "SAL ADB", "619 SPS PU", "667 ART", "1595", "1596", "1596 667", "1596 L01"}
agg = defaultdict(lambda: {"rows": 0, "valx": 0.0, "qla": 0.0, "buckets": defaultdict(int)})
with open(r"docs\Valuation\analysis\reserve_gap_population.csv", encoding="utf-8-sig") as f:
    r = csv.DictReader(f)
    for row in r:
        p = row["plan"]
        if p not in targets:
            continue
        a = agg[p]
        a["rows"] += 1
        a["valx"] += float(row["valx_reserve"] or 0)
        a["qla"] += float(row["qla_reserve"] or 0)
        a["buckets"][row["bucket"]] += 1

for p in sorted(agg):
    a = agg[p]
    print(f"{p:<14} rows={a['rows']:>4} valx_total={a['valx']:>12,.2f} qla_total={a['qla']:>12,.2f}  buckets={dict(a['buckets'])}")
