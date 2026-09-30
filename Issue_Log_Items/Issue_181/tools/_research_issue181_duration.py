"""Issue 181 Discovery — read-only duration alignment check for 658/659.

Compares LifePRO VALX 6/30/2026 per-unit reserves on 658/659 coverages with
the QuikTvs terminal grid at policy year t-1, t, and t+1. Writes a CSV under
Issue_181/evidence. No Output or rate changes.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "docs" / "Valuation" / "analysis"))
import valx_layout as VL  # noqa: E402

RATES = ROOT / "QLA_Migration" / "Output" / "rates"
OUT = ROOT / "QLA_Migration" / "Output"
EVID = ROOT / "Issue_Log_Items" / "Issue_181" / "evidence"


def _s(v):
    return str(v or "").strip()


def load_grid(table, pfx):
    grid = defaultdict(dict)
    with (RATES / f"{table}.csv").open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            plan = _s(r["PLAN"])
            if not (plan.startswith("1658") or plan.startswith("1659")):
                continue
            if _s(r["EFFDATE"]) != "19000101":
                continue
            key = (plan, _s(r["GENDER"]), _s(r["UWCLASS"]), int(_s(r["AGE"]) or 0))
            cntl = int(_s(r["CNTL"]) or 0)
            for i in range(10):
                v = _s(r.get(f"{pfx}{i}"))
                if v:
                    try:
                        grid[key][cntl * 10 + i] = float(v)
                    except ValueError:
                        pass
    return grid


def load_riders():
    out = {}
    with (OUT / "quikridr.csv").open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if _s(r.get("MPHASE")) not in ("1", "01"):
                continue
            out[_s(r["MPOLICY"])] = r
    return out


def policy_year(issue: date, val: date) -> int:
    years = val.year - issue.year
    if (val.month, val.day) < (issue.month, issue.day):
        years -= 1
    return years + 1


def main() -> int:
    tv = load_grid("QuikTvs", "TV")
    np_ = load_grid("QuikNps", "NP")
    riders = load_riders()
    recs = [r for r in VL.read_records() if _s(r["PLAN_ID"]).startswith(("658", "659"))]
    rows = []
    tally = Counter()
    for r in recs:
        units = r["NUMBER_OF_UNITS"] or 0
        if not units:
            tally["zero_units"] += 1
            continue
        pol = _s(r["POLICY_NUMBER"]) + "C"
        rid = riders.get(pol)
        if rid is None:
            tally["no_quikridr"] += 1
            continue
        plan = _s(rid["MPLAN"])
        key = (plan, _s(rid["MSEX"]), _s(rid["MUWCLASS"]), int(float(_s(rid["MAGE"]) or 0)))
        g = tv.get(key)
        if not g:
            tally["no_grid"] += 1
            continue
        t = policy_year(r["ISSUE_DATE"], r["VALUATION_DATE"])
        per = {
            "RV_T_1": (r["RV_T_1"] or 0) / units,
            "RV_T": (r["RV_T"] or 0) / units,
            "MEAN_NL": (r["MEAN_NL_RESERVE"] or 0) / units,
        }
        slots = {d: g.get(t + d) for d in (-2, -1, 0, 1)}
        match = {}
        for name, val in per.items():
            hit = [d for d, sv in slots.items() if sv is not None and abs(sv - val) <= 0.01]
            match[name] = hit[0] if hit else None
            tally[f"{name}@{match[name]}"] += 1
        nps = np_.get(key, {})
        rows.append({
            "POLICY": pol,
            "LP_PLAN": _s(r["PLAN_ID"]),
            "QL_PLAN": plan,
            "SEX": key[1],
            "UW": key[2],
            "AGE": key[3],
            "ISSUE": r["ISSUE_DATE"].isoformat(),
            "YEAR_T": t,
            "UNITS": units,
            "RV_T_1_PU": round(per["RV_T_1"], 4),
            "RV_T_PU": round(per["RV_T"], 4),
            "MEAN_NL_PU": round(per["MEAN_NL"], 4),
            "TV_t-2": slots[-2],
            "TV_t-1": slots[-1],
            "TV_t": slots[0],
            "TV_t+1": slots[1],
            "NP_t-1": nps.get(t - 1),
            "NP_t": nps.get(t),
            "RV_T_matches": match["RV_T"],
            "RV_T_1_matches": match["RV_T_1"],
            "MEAN_NL_matches": match["MEAN_NL"],
        })
    EVID.mkdir(parents=True, exist_ok=True)
    out = EVID / "issue181_valx_vs_quiktvs_20260630.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("rows", len(rows), "->", out)
    for k, v in sorted(tally.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
