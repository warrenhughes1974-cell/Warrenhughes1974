"""Join docs/VaxLife_QLAdmin_VPUNITDIFFERENCES.txt to 0561 / VB recon. Read-only."""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LISTING = ROOT / "docs" / "VaxLife_QLAdmin_VPUNITDIFFERENCES.txt"
EVID = Path(__file__).resolve().parent / "evidence"
VB_RECON = EVID / "issue145b_vb_population_recon.csv"
ISRR = ROOT / "QLA_Migration" / "Output" / "QuikIsrr.csv"
PPOLC = ROOT / "QLA_Migration" / "Source" / "PPOLC_PolicyMaster_Extract_20260630.csv"

GOLD = ("9010815236", "9011050114", "9011069610")
SCOPE_146 = ("9010761639", "9010760840")


def npol(v: str) -> str:
    return re.sub(r"[^0-9]", "", (v or "").strip())


def namt(v: str) -> float | None:
    s = (v or "").strip().replace(",", "")
    if not s or set(s.replace(".", "")) <= {"-", " "}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def close(a, b, tol=0.002) -> bool:
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) <= tol


def parse_listing():
    rows = []
    with LISTING.open(encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            if i == 1:
                continue
            parts = [p.strip() for p in line.rstrip("\n").split("\t")]
            if len(parts) < 5:
                continue
            pol = npol(parts[1])
            if not pol:
                continue
            rows.append({
                "line": i,
                "group": parts[0].strip(),
                "policy": pol,
                "valx_units": namt(parts[2]),
                "qla_live_units": namt(parts[3]),
                "listed_diff": namt(parts[4]),
            })
    return rows


def load_vb_recon():
    by = {}
    with VB_RECON.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pol = npol(row.get("policy", ""))
            by[pol] = {
                "billing_reason": (row.get("billing_reason") or "").strip(),
                "lp_units": namt(row.get("lp_units", "")),
                "qla_munit": namt(row.get("qla_munit", "")),
                "n_0561": int(float(row.get("n_0561_unrev") or 0)),
                "sum_0561": namt(row.get("sum_0561", "")) or 0.0,
                "unit_impact_0561": namt(row.get("unit_impact_0561", "")) or 0.0,
                "counterfactual": namt(row.get("counterfactual_qla_units", "")),
                "vanish_flag": (row.get("vanish_flag") or "").strip(),
            }
    return by


def load_isrr_sums():
    sums = defaultdict(float)
    counts = defaultdict(int)
    with ISRR.open(newline="", encoding="latin-1", errors="replace") as f:
        for row in csv.DictReader(f):
            pol = npol(row.get("MPOLICY", ""))
            amt = namt(row.get("MSURRAMT", ""))
            if not pol or amt is None:
                continue
            sums[pol] += amt
            counts[pol] += 1
    return sums, counts


def load_billing():
    br = {}
    with PPOLC.open(newline="", encoding="latin-1", errors="replace") as f:
        for row in csv.DictReader(f):
            pol = npol(row.get("POLICY_NUMBER", ""))
            if pol:
                br[pol] = (row.get("BILLING_REASON") or "").strip().upper()
    return br


def main():
    listing = parse_listing()
    vb = load_vb_recon()
    isrr_sum, isrr_n = load_isrr_sums()
    billing = load_billing()

    joined = []
    for r in listing:
        pol = r["policy"]
        rec = vb.get(pol)
        if rec:
            n561 = rec["n_0561"]
            s561 = rec["sum_0561"]
            impact = rec["unit_impact_0561"]
            lp = rec["lp_units"]
            munit = rec["qla_munit"]
            cf = rec["counterfactual"]
            br = rec["billing_reason"] or billing.get(pol, "")
            vanish = rec["vanish_flag"]
        else:
            s561 = isrr_sum.get(pol, 0.0)
            n561 = isrr_n.get(pol, 0)
            impact = s561 / 1000.0
            lp = r["valx_units"]
            munit = None
            cf = (lp - impact) if lp is not None else None
            br = billing.get(pol, "")
            vanish = ""

        qla = r["qla_live_units"]
        valx = r["valx_units"]
        listed = r["listed_diff"]
        computed_diff = (valx - qla) if valx is not None and qla is not None else None
        qla_vs_cf = (qla - cf) if qla is not None and cf is not None else None
        qla_eq_cf = close(qla, cf, 0.002)
        listed_eq_impact = close(listed, impact, 0.002)
        valx_eq_lp = close(valx, lp, 0.002) if lp is not None else False

        if pol in GOLD:
            bucket = "145B_GOLD"
        elif pol in SCOPE_146:
            bucket = "146"
        elif br == "VB":
            bucket = "145B_VB"
        elif n561:
            bucket = "146_OTHER"
        else:
            bucket = "NO_0561"

        joined.append({
            **r,
            "billing_reason": br,
            "vanish_flag": vanish,
            "is_vb": br == "VB",
            "bucket": bucket,
            "lp_or_seed_units": lp,
            "conversion_munit": munit,
            "n_0561": n561,
            "sum_0561": round(s561, 6),
            "unit_impact_0561": round(impact, 6),
            "counterfactual_units": None if cf is None else round(cf, 6),
            "computed_valx_minus_qla": None if computed_diff is None else round(computed_diff, 6),
            "qla_live_minus_counterfactual": None if qla_vs_cf is None else round(qla_vs_cf, 6),
            "qla_matches_counterfactual": qla_eq_cf,
            "listed_diff_matches_0561_impact": listed_eq_impact,
            "valx_matches_lp_units": valx_eq_lp,
        })

    n = len(joined)
    match_cf = sum(1 for r in joined if r["qla_matches_counterfactual"])
    match_diff = sum(1 for r in joined if r["listed_diff_matches_0561_impact"])
    pos_diff = [r for r in joined if (r["listed_diff"] or 0) > 0.0005]
    neg_diff = [r for r in joined if (r["listed_diff"] or 0) < -0.0005]
    pos_match = sum(1 for r in pos_diff if r["qla_matches_counterfactual"])

    by_bucket = defaultdict(int)
    bucket_match = defaultdict(int)
    for r in joined:
        by_bucket[r["bucket"]] += 1
        if r["qla_matches_counterfactual"]:
            bucket_match[r["bucket"]] += 1

    golds = {r["policy"]: r for r in joined if r["policy"] in GOLD or r["policy"] in SCOPE_146}
    misses = [r for r in joined if not r["qla_matches_counterfactual"]]

    summary = {
        "source": str(LISTING.relative_to(ROOT)).replace("\\", "/"),
        "columns": "Group | Policy | ValxLife units | QLAdmin live units | Diff",
        "listing_rows": n,
        "qla_live_equals_seed_minus_0561_over_1000": {
            "match": match_cf,
            "miss": n - match_cf,
            "tol": 0.002,
        },
        "listed_diff_equals_0561_over_1000": {
            "match": match_diff,
            "miss": n - match_diff,
            "note": "Fails when Valx units already reduced (e.g. 9010815236 Valx=24.30594 not 25).",
        },
        "positive_diff_rows": {
            "count": len(pos_diff),
            "qla_matches_counterfactual": pos_match,
        },
        "negative_diff_rows": len(neg_diff),
        "by_bucket": {
            k: {"rows": by_bucket[k], "qla_matches_counterfactual": bucket_match[k]}
            for k in sorted(by_bucket)
        },
        "golds": {
            p: {
                "valx_units": golds[p]["valx_units"],
                "qla_live_units": golds[p]["qla_live_units"],
                "listed_diff": golds[p]["listed_diff"],
                "sum_0561": golds[p]["sum_0561"],
                "unit_impact_0561": golds[p]["unit_impact_0561"],
                "counterfactual_units": golds[p]["counterfactual_units"],
                "qla_matches_counterfactual": golds[p]["qla_matches_counterfactual"],
                "bucket": golds[p]["bucket"],
            }
            for p in list(GOLD) + list(SCOPE_146)
            if p in golds
        },
        "miss_sample": [
            {
                "policy": r["policy"],
                "bucket": r["bucket"],
                "valx": r["valx_units"],
                "qla_live": r["qla_live_units"],
                "diff": r["listed_diff"],
                "sum_0561": r["sum_0561"],
                "counterfactual": r["counterfactual_units"],
            }
            for r in misses[:25]
        ],
        "conclusion": (
            "This listing is live QLAdmin units after anniversary, not conversion MUNIT. "
            "On the 145B golds, live QLA units equal LifePRO units minus unreversed 0561/1000."
        ),
    }

    EVID.mkdir(exist_ok=True)
    out_csv = EVID / "issue145b_vpunit_listing_join.csv"
    fields = list(joined[0].keys())
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(joined)

    out_json = EVID / "issue145b_vpunit_listing_summary.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"wrote {out_csv}")
    print(f"wrote {out_json}")


if __name__ == "__main__":
    main()
