"""Build primary (PAAGERAT) vs secondary (Rate_Table) inventory tables."""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEC = ROOT / "QLA_Migration" / "Source" / "Rate_Table_Extract_Txt.txt"
PRI = ROOT / "QLA_Migration" / "Source" / "PAAGERAT_AttainedAge_Rates_Extract_20260630.csv"
EVID = Path(__file__).resolve().parent / "evidence"
OUT = EVID / "issue48_primary_secondary_rate_inventory.csv"
OUT_SUM = EVID / "issue48_primary_secondary_type_summary.csv"


def scan(path: Path) -> Counter:
    c: Counter = Counter()
    with path.open(encoding="utf-8", errors="replace") as f:
        f.readline()
        f.readline()
        for line in f:
            p = [x.strip() for x in line.split(",")]
            if len(p) >= 2:
                c[(p[0], p[1])] += 1
    return c


def main() -> None:
    sec = scan(SEC)
    pri = scan(PRI)
    all_keys = sorted(set(sec) | set(pri), key=lambda x: (x[0], x[1]))
    rows = []
    for cov, tc in all_keys:
        s = sec.get((cov, tc), 0)
        p = pri.get((cov, tc), 0)
        if s and p:
            loc = "BOTH"
        elif s:
            loc = "SECONDARY_ONLY"
        else:
            loc = "PRIMARY_ONLY"
        rows.append(
            {
                "coverage_id": cov,
                "type_code": tc,
                "secondary_rate_table_rows": s,
                "primary_paagerat_rows": p,
                "present_in": loc,
            }
        )

    EVID.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "coverage_id",
                "type_code",
                "secondary_rate_table_rows",
                "primary_paagerat_rows",
                "present_in",
            ],
        )
        w.writeheader()
        w.writerows(rows)

    ts: dict = defaultdict(
        lambda: {
            "sec_keys": 0,
            "pri_keys": 0,
            "sec_rows": 0,
            "pri_rows": 0,
            "both": 0,
            "sec_only": 0,
            "pri_only": 0,
        }
    )
    for r in rows:
        t = r["type_code"]
        d = ts[t]
        if r["secondary_rate_table_rows"]:
            d["sec_keys"] += 1
            d["sec_rows"] += r["secondary_rate_table_rows"]
        if r["primary_paagerat_rows"]:
            d["pri_keys"] += 1
            d["pri_rows"] += r["primary_paagerat_rows"]
        if r["present_in"] == "BOTH":
            d["both"] += 1
        elif r["present_in"] == "SECONDARY_ONLY":
            d["sec_only"] += 1
        else:
            d["pri_only"] += 1

    with OUT_SUM.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "type_code",
                "secondary_coverage_count",
                "primary_coverage_count",
                "secondary_rows",
                "primary_rows",
                "both",
                "secondary_only",
                "primary_only",
            ],
        )
        w.writeheader()
        for t in sorted(ts):
            d = ts[t]
            w.writerow(
                {
                    "type_code": t,
                    "secondary_coverage_count": d["sec_keys"],
                    "primary_coverage_count": d["pri_keys"],
                    "secondary_rows": d["sec_rows"],
                    "primary_rows": d["pri_rows"],
                    "both": d["both"],
                    "secondary_only": d["sec_only"],
                    "primary_only": d["pri_only"],
                }
            )

    print(f"inventory_rows={len(rows)}")
    print(f"secondary_keys={len(sec)} primary_keys={len(pri)}")
    print(f"wrote {OUT}")
    print(f"wrote {OUT_SUM}")
    print("--- TYPE SUMMARY ---")
    for t in sorted(ts):
        d = ts[t]
        print(
            f"{t}: sec_cov={d['sec_keys']} pri_cov={d['pri_keys']} "
            f"sec_rows={d['sec_rows']} pri_rows={d['pri_rows']} "
            f"both={d['both']} sec_only={d['sec_only']} pri_only={d['pri_only']}"
        )


if __name__ == "__main__":
    main()
