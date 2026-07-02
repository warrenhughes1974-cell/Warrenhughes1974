"""
Issue #34 — PFNDR MISWL readiness validation (planning only).

Validates PFNDR.VALUATION_DATE can populate MISWL for eligible QuikIsrr candidates.
Does NOT emit QuikIsrr.csv or modify production outputs.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PACTG = PROJECT_ROOT / "QLA_Migration" / "Source" / "PACTG_Accounting_Extract20260530.csv"
PFNDR = PROJECT_ROOT / "QLA_Migration" / "Source" / "PFNDR_FundHistory_Extract_20260530.csv"
OUT_DIR = PROJECT_ROOT / "Issue_Log_Items" / "Issue_34" / "output" / "QuikIsrr_PFNDR_Readiness"

HOLD = {"9010780411"}
ISWL_MPLANS = {"1658C1", "1658CS", "1659C2", "1659CR", "1659CS", "1659SR", "1669SR", "1679CS"}
CMAP = {
    "658 CEN I": "1658C1", "658 CEN SD": "1658CS", "659 CEN II": "1659C2",
    "659 CEN SR": "1659CR", "659 CEN SD": "1659CS", "659 SR GD": "1659SR",
    "669 SR GD": "1669SR", "679 CEN SD": "1679CS",
}
EXPECTED = {"rows": 3623, "policies": 636, "amount": 1217593.55}


def norm(v: str) -> str:
    s = (v or "").strip()
    return "" if s and set(s) == {"-"} else s


def norm_date(v: str) -> str:
    d = re.sub(r"[^0-9]", "", norm(v))
    return d[:8] if len(d) >= 8 else ""


def norm_policy(v: str) -> str:
    return re.sub(r"[^0-9]", "", norm(v))


def parse_amount(v: str) -> float | None:
    s = norm(v)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def is_dash_row(policy: str, val_date: str) -> bool:
    return (not policy) or set(policy) == {"-"} or (not val_date) or set(val_date.replace("0", "")) == set("-")


def load_candidates() -> list[dict]:
    rows = []
    with open(PACTG, encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f)
        cols = {c.strip(): c for c in reader.fieldnames or []}

        def g(raw, n):
            c = cols.get(n)
            return norm(raw.get(c, "")) if c else ""

        for raw in reader:
            dc = re.sub(r"[^0-9]", "", g(raw, "DEBIT_CODE"))
            if not dc or str(int(dc)) != "561":
                continue
            pol = norm_policy(g(raw, "POLICY_NUMBER"))
            mplan = CMAP.get(g(raw, "PLAN_CODE"), "") or CMAP.get(g(raw, "PRODUCT_ID"), "")
            if mplan not in ISWL_MPLANS:
                continue
            if g(raw, "REVERSAL_CODE") == "Y":
                continue
            if pol in HOLD:
                continue
            amt = parse_amount(g(raw, "TRANS_AMOUNT"))
            eff = norm_date(g(raw, "EFFECTIVE_DATE"))
            rows.append({
                "policy_number": pol,
                "mplan": mplan,
                "msurrdate": eff,
                "msurramt": amt,
                "benefit_seq": g(raw, "BENEFIT_SEQ"),
            })
    return rows


def load_pfndr() -> tuple[list[dict], dict]:
    """Return PFNDR rows and policy -> sorted list of (val_date, benefit_seq, record_seq)."""
    pfndr_rows = []
    by_policy: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    blank_pol = blank_date = dash_skipped = 0
    key_counter: Counter = Counter()

    with open(PFNDR, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = [c.strip() for c in reader.fieldnames or []]
        col_map = {c: c for c in reader.fieldnames}
        # normalize trailing spaces in headers
        norm_cols = {}
        for c in reader.fieldnames or []:
            norm_cols[c.strip()] = c

        for raw in reader:
            pol = norm_policy(raw.get(norm_cols.get("POLICY_NUMBER", "POLICY_NUMBER"), ""))
            bseq = norm(raw.get(norm_cols.get("BENEFIT_SEQ", "BENEFIT_SEQ"), ""))
            vdate = norm_date(raw.get(norm_cols.get("VALUATION_DATE", "VALUATION_DATE"), ""))
            rseq = norm(raw.get(norm_cols.get("RECORD_SEQ", "RECORD_SEQ"), ""))

            if is_dash_row(pol, vdate):
                dash_skipped += 1
                continue
            if not pol:
                blank_pol += 1
                continue
            if not vdate:
                blank_date += 1
                continue

            key_counter[(pol, bseq, vdate, rseq)] += 1
            entry = {"policy_number": pol, "benefit_seq": bseq, "valuation_date": vdate, "record_seq": rseq}
            pfndr_rows.append(entry)
            by_policy[pol].append((vdate, bseq, rseq))

    # dedupe policy valuations to unique dates (keep all benefit_seq variants for tie detection)
    struct = {
        "columns": cols,
        "row_count": len(pfndr_rows),
        "dash_header_rows_skipped": dash_skipped,
        "blank_policy": blank_pol,
        "blank_valuation_date": blank_date,
        "duplicate_keys": sum(1 for k, v in key_counter.items() if v > 1),
        "duplicate_key_rows": sum(v - 1 for v in key_counter.values() if v > 1),
    }
    return pfndr_rows, by_policy, struct, key_counter


def pick_miswl(val_dates: list[str], msurrdate: str) -> tuple[str | None, str]:
    """Return (miswl_date, status). status: MATCHED | ONLY_EARLIER | NO_HISTORY"""
    if not val_dates:
        return None, "NO_HISTORY"
    uniq = sorted(set(val_dates))
    on_or_after = [d for d in uniq if d >= msurrdate]
    if on_or_after:
        return on_or_after[0], "MATCHED"
    if uniq:
        return None, "ONLY_EARLIER"
    return None, "NO_HISTORY"


def main() -> int:
    if not PFNDR.is_file():
        print("FAIL — PFNDR not found")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pfndr_size = PFNDR.stat().st_size

    candidates = load_candidates()
    pols = {c["policy_number"] for c in candidates}
    total_amt = sum(c["msurramt"] for c in candidates if c["msurramt"] is not None)

    count_ok = len(candidates) == EXPECTED["rows"] and len(pols) == EXPECTED["policies"]
    amt_ok = abs(total_amt - EXPECTED["amount"]) < 0.02

    pfndr_rows, by_policy, pstruct, key_counter = load_pfndr()

    matched = []
    unmatched = []
    dup_candidates = []
    policy_coverage = defaultdict(lambda: {"candidate_rows": 0, "matched": 0, "unmatched": 0,
                                           "only_earlier": 0, "no_history": 0})

    miswl_dist: Counter = Counter()
    only_earlier = 0
    no_history = 0
    dup_tie_count = 0

    for c in candidates:
        pol = c["policy_number"]
        ms = c["msurrdate"]
        policy_coverage[pol]["candidate_rows"] += 1

        dates = [t[0] for t in by_policy.get(pol, [])]
        miswl, status = pick_miswl(dates, ms)

        # duplicate PFNDR tie: multiple rows same min date
        dup_pfndr_rows = 0
        if miswl:
            dup_pfndr_rows = sum(1 for t in by_policy.get(pol, []) if t[0] == miswl)
            if dup_pfndr_rows > 1:
                dup_tie_count += 1

        rec = {
            **c,
            "miswl": miswl or "",
            "match_status": status,
            "pfndr_policy_rows": len(by_policy.get(pol, [])),
            "pfndr_unique_valuation_dates": len(set(dates)),
            "pfndr_dup_rows_at_miswl": dup_pfndr_rows,
        }

        if status == "MATCHED":
            matched.append(rec)
            policy_coverage[pol]["matched"] += 1
            miswl_dist[miswl] += 1
            if dup_pfndr_rows > 1:
                dup_candidates.append(rec)
        else:
            unmatched.append(rec)
            policy_coverage[pol]["unmatched"] += 1
            if status == "ONLY_EARLIER":
                only_earlier += 1
                policy_coverage[pol]["only_earlier"] += 1
            else:
                no_history += 1
                policy_coverage[pol]["no_history"] += 1

    match_rate = len(matched) / len(candidates) * 100 if candidates else 0
    matched_pols = {r["policy_number"] for r in matched}
    unmatched_pols = pols - matched_pols

    # policies with any PFNDR history
    pfndr_policies = set(by_policy.keys())
    candidate_pols_no_pfndr = pols - pfndr_policies

    # MISWL validation on matched
    miswl_valid = all(r["miswl"] >= r["msurrdate"] for r in matched if r["miswl"])

    # recommendation logic
    if not count_ok or not amt_ok:
        rec_status = "BLOCKED"
        rec_reason = "Candidate population mismatch vs expected 3623/636/$1,217,593.55"
    elif match_rate >= 95.0:
        rec_status = "READY FOR DEVELOPMENT"
        rec_reason = f"PFNDR MISWL match rate {match_rate:.1f}% meets readiness threshold (>=95%)"
    elif match_rate >= 80.0:
        rec_status = "READY AFTER SME CONFIRMATION"
        rec_reason = f"PFNDR match rate {match_rate:.1f}% — SME must confirm exception-file handling for {len(unmatched)} unmatched rows"
    else:
        rec_status = "BLOCKED"
        rec_reason = f"PFNDR match rate {match_rate:.1f}% too low — {no_history} no history, {only_earlier} only earlier dates; need PFNDRDET/historical PFNDR or MISWL fallback decision"

    summary = {
        "readiness_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "validation_pass": "PFNDR Readiness Agent — MISWL source validation (PFNDR present)",
        "pfndr_available": True,
        "pfndr_path": str(PFNDR),
        "pfndr_size_bytes": pfndr_size,
        "pfndr_encoding": "utf-8-sig",
        "pfndr_structure": pstruct,
        "candidate_population": {
            "rows": len(candidates),
            "policies": len(pols),
            "gross_amount": round(total_amt, 2),
            "expected_rows": EXPECTED["rows"],
            "expected_policies": EXPECTED["policies"],
            "expected_amount": EXPECTED["amount"],
            "count_match": count_ok,
            "amount_match": amt_ok,
        },
        "match_results": {
            "matched_rows": len(matched),
            "unmatched_rows": len(unmatched),
            "match_rate_pct": round(match_rate, 2),
            "matched_policies": len(matched_pols),
            "unmatched_policies": len(unmatched_pols),
            "only_earlier_pfndr_rows": only_earlier,
            "no_pfndr_policy_history_rows": no_history,
            "candidate_policies_with_no_pfndr_at_all": len(candidate_pols_no_pfndr),
            "duplicate_pfndr_tie_candidates": dup_tie_count,
        },
        "miswl_validation": {
            "all_matched_miswl_gte_msurrdate": miswl_valid,
            "miswl_from_pfndr_valuation_date_only": True,
            "one_selected_row_per_candidate": True,
            "no_estimated_dates": True,
            "top_miswl_dates": dict(miswl_dist.most_common(15)),
        },
        "issue_34_status": rec_status,
        "recommendation_reason": rec_reason,
    }

    fields_match = ["policy_number", "mplan", "msurrdate", "msurramt", "benefit_seq",
                    "miswl", "match_status", "pfndr_policy_rows", "pfndr_unique_valuation_dates",
                    "pfndr_dup_rows_at_miswl"]
    fields_unmatch = fields_match
    fields_dup = fields_match
    fields_pol = ["policy_number", "candidate_rows", "matched", "unmatched", "only_earlier", "no_history",
                  "has_pfndr_history", "pfndr_valuation_dates"]

    def write_csv(name, rows, fields):
        with open(OUT_DIR / name, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)

    write_csv("quikisrr_pfndr_matches.csv", matched, fields_match)
    write_csv("quikisrr_pfndr_unmatched.csv", unmatched, fields_unmatch)
    write_csv("quikisrr_pfndr_duplicate_candidates.csv", dup_candidates, fields_dup)

    pol_rows = []
    for pol in sorted(pols):
        pc = policy_coverage[pol]
        dates = sorted(set(t[0] for t in by_policy.get(pol, [])))
        pol_rows.append({
            "policy_number": pol,
            **pc,
            "has_pfndr_history": pol in pfndr_policies,
            "pfndr_valuation_dates": "|".join(dates[:20]) + ("..." if len(dates) > 20 else ""),
        })
    write_csv("quikisrr_pfndr_policy_coverage.csv", pol_rows, fields_pol)

    with open(OUT_DIR / "quikisrr_pfndr_readiness_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    if not count_ok or not amt_ok:
        print("WARNING: candidate count mismatch — investigate before proceeding")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
