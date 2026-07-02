"""
Issue #34 — QUIKISRR Decision Review deep profile (planning only).

Second-pass PACTG analysis for the Decision Review:
- Reversal / void indicators (REVERSAL_CODE, DATE_REVERSED, CODER_REVERSED)
- Same-policy / same-date duplicate patterns on 0561
- Full-surrender (0560) chain proximity to 0561 rows
- Credit-code distribution on 0561 (0013 surrender clearing validation)
- Related code volumes: 0560/0562-0565/1020/0090/0092 fleet + ISWL
- TERM_REASON distribution
- Annual recurring same-amount pattern detection

Does NOT emit QuikIsrr.csv or modify production outputs.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PACTG = PROJECT_ROOT / "QLA_Migration" / "Source" / "PACTG_Accounting_Extract20260530.csv"
OUT_DIR = PROJECT_ROOT / "Issue_Log_Items" / "Issue_34" / "output" / "QuikIsrr_Decision_Review"

GOV_POLICIES = {"9010776027", "9010780411", "9010780591", "9011072813", "9011107796"}
ISWL_MPLANS = {"1658C1", "1658CS", "1659C2", "1659CR", "1659CS", "1659SR", "1669SR", "1679CS"}
COVERAGE_TO_MPLAN = {
    "658 CEN I": "1658C1",
    "658 CEN SD": "1658CS",
    "659 CEN II": "1659C2",
    "659 CEN SR": "1659CR",
    "659 CEN SD": "1659CS",
    "659 SR GD": "1659SR",
    "669 SR GD": "1669SR",
    "679 CEN SD": "1679CS",
}
WATCH_CODES = {"560", "561", "562", "563", "564", "565", "1020", "90", "92", "13"}


def norm(v: str) -> str:
    s = (v or "").strip()
    if not s or set(s) == {"-"}:
        return ""
    return s


def norm_code(v: str) -> str:
    s = norm(v)
    if not s:
        return ""
    d = re.sub(r"[^0-9]", "", s)
    return str(int(d)) if d else s.upper()


def norm_date(v: str) -> str:
    s = norm(v)
    d = re.sub(r"[^0-9]", "", s)
    return d[:8] if len(d) >= 8 else ""


def amt(v: str) -> float | None:
    s = norm(v)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows_561: list[dict] = []
    fleet_debit_counts: Counter = Counter()
    iswl_debit_counts: Counter = Counter()
    policy_560_dates: dict[str, list[str]] = defaultdict(list)
    policy_code_rows: dict[str, Counter] = defaultdict(Counter)  # policy -> debit code counts
    policy_mplans: dict[str, set] = defaultdict(set)

    with open(PACTG, encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f)
        cols = {c.strip(): c for c in reader.fieldnames or []}

        def g(raw, name):
            c = cols.get(name)
            return raw.get(c, "") if c else ""

        for raw in reader:
            pol = re.sub(r"[^0-9]", "", norm(g(raw, "POLICY_NUMBER")))
            if not pol:
                continue
            dc = norm_code(g(raw, "DEBIT_CODE"))
            cc = norm_code(g(raw, "CREDIT_CODE"))
            pc = norm(g(raw, "PLAN_CODE"))
            mplan = COVERAGE_TO_MPLAN.get(pc, "")
            if mplan:
                policy_mplans[pol].add(mplan)
            if dc:
                fleet_debit_counts[dc] += 1
                policy_code_rows[pol][dc] += 1
                if mplan in ISWL_MPLANS:
                    iswl_debit_counts[dc] += 1
            if dc == "560":
                policy_560_dates[pol].append(norm_date(g(raw, "EFFECTIVE_DATE")))
            if dc == "561":
                rows_561.append({
                    "policy": pol,
                    "mplan": mplan,
                    "plan_code": pc,
                    "eff": norm_date(g(raw, "EFFECTIVE_DATE")),
                    "amount": amt(g(raw, "TRANS_AMOUNT")),
                    "credit_code": cc,
                    "reversal_code": norm(g(raw, "REVERSAL_CODE")),
                    "date_reversed": norm_date(g(raw, "DATE_REVERSED")),
                    "time_reversed": norm(g(raw, "TIME_REVERSED")),
                    "coder_reversed": norm(g(raw, "CODER_REVERSED")),
                    "control_number": norm(g(raw, "CONTROL_NUMBER")),
                    "offset_control": norm(g(raw, "OFFSET_CONTROL_NUM")),
                    "record_seq": norm(g(raw, "RECORD_SEQUENCE")),
                    "benefit_seq": norm(g(raw, "BENEFIT_SEQ")),
                    "date_added": norm_date(g(raw, "DATE_ADDED")),
                    "term_reason": norm(g(raw, "TERM_REASON")),
                    "description": norm(g(raw, "DESCRIPTION")),
                    "adj_or_pay": norm(g(raw, "ADJ_OR_PAY_HIST")),
                    "duration": norm(g(raw, "DURATION")),
                })

    iswl = [r for r in rows_561 if r["mplan"] in ISWL_MPLANS]

    # --- Reversal indicators ---
    reversed_rows = [r for r in iswl if r["reversal_code"] or r["date_reversed"] or r["coder_reversed"]]
    reversal_code_dist = Counter(r["reversal_code"] for r in iswl)

    # --- Credit code distribution on 561 ---
    credit_dist = Counter(r["credit_code"] for r in iswl)

    # --- Same policy+date groups ---
    by_pol_date: dict[tuple, list[dict]] = defaultdict(list)
    for r in iswl:
        by_pol_date[(r["policy"], r["eff"])].append(r)
    multi_same_date = {k: v for k, v in by_pol_date.items() if len(v) > 1}
    exact_dup_groups = []
    distinct_same_date_groups = []
    for k, grp in multi_same_date.items():
        sigs = Counter((r["amount"], r["control_number"], r["record_seq"], r["benefit_seq"]) for r in grp)
        if any(c > 1 for c in sigs.values()):
            exact_dup_groups.append((k, grp, sigs))
        else:
            distinct_same_date_groups.append((k, grp))
    # same date+amount but different control numbers (suspicious but not identical)
    same_date_amt_groups = []
    for k, grp in multi_same_date.items():
        amts = Counter(r["amount"] for r in grp)
        if any(c > 1 for c in amts.values()):
            same_date_amt_groups.append((k, grp))

    # --- 560 proximity ---
    after_560 = []
    same_day_560 = []
    for r in iswl:
        dates_560 = [d for d in policy_560_dates.get(r["policy"], []) if d]
        if not dates_560:
            continue
        min560 = min(dates_560)
        if r["eff"] and r["eff"] > min560:
            after_560.append({**r, "first_560_date": min560})
        elif r["eff"] and r["eff"] == min560:
            same_day_560.append({**r, "first_560_date": min560})
    policies_with_560 = {r["policy"] for r in iswl if policy_560_dates.get(r["policy"])}

    # --- Annual recurring pattern (same month-day, same amount, consecutive years) ---
    by_policy: dict[str, list[dict]] = defaultdict(list)
    for r in iswl:
        by_policy[r["policy"]].append(r)
    recurring_policies = 0
    recurring_rows = 0
    for pol, grp in by_policy.items():
        mmdd_amt = Counter((r["eff"][4:8], r["amount"]) for r in grp if r["eff"])
        rec = sum(c for c in mmdd_amt.values() if c >= 3)
        if rec:
            recurring_policies += 1
            recurring_rows += rec

    # --- Zero / negative / missing ---
    zero_amt = [r for r in iswl if r["amount"] is not None and r["amount"] == 0]
    neg_amt = [r for r in iswl if r["amount"] is not None and r["amount"] < 0]
    none_amt = [r for r in iswl if r["amount"] is None]
    no_date = [r for r in iswl if not r["eff"]]

    # --- TERM_REASON distribution ---
    term_dist = Counter(r["term_reason"] for r in iswl)

    # --- Description distribution ---
    desc_dist = Counter(r["description"] for r in iswl)

    # --- Governance policies detail ---
    gov_rows = [r for r in iswl if r["policy"] in GOV_POLICIES]

    # --- 561 count per policy distribution ---
    per_policy = Counter(r["policy"] for r in iswl)
    per_policy_hist = Counter(per_policy.values())

    summary = {
        "iswl_561_rows": len(iswl),
        "iswl_561_policies": len(per_policy),
        "iswl_561_total_amount": round(sum(r["amount"] for r in iswl if r["amount"] is not None), 2),
        "fleet_debit_code_counts_watchlist": {c: fleet_debit_counts.get(c, 0) for c in sorted(WATCH_CODES)},
        "iswl_debit_code_counts_watchlist": {c: iswl_debit_counts.get(c, 0) for c in sorted(WATCH_CODES)},
        "reversal_indicators": {
            "rows_with_any_reversal_marker": len(reversed_rows),
            "reversal_code_distribution": dict(reversal_code_dist),
        },
        "credit_code_distribution_on_561": dict(credit_dist.most_common()),
        "data_quality": {
            "zero_amount": len(zero_amt),
            "negative_amount": len(neg_amt),
            "missing_amount": len(none_amt),
            "missing_effective_date": len(no_date),
        },
        "same_policy_date": {
            "groups_with_multiple_561_same_date": len(multi_same_date),
            "rows_in_those_groups": sum(len(v) for v in multi_same_date.values()),
            "exact_duplicate_signature_groups": len(exact_dup_groups),
            "same_date_same_amount_groups": len(same_date_amt_groups),
            "distinct_same_date_groups": len(distinct_same_date_groups),
        },
        "full_surrender_proximity": {
            "iswl_561_policies_with_any_560": len(policies_with_560),
            "iswl_561_rows_after_first_560_date": len(after_560),
            "iswl_561_rows_same_day_as_560": len(same_day_560),
        },
        "recurring_annual_pattern": {
            "policies_with_same_mmdd_same_amount_3plus_years": recurring_policies,
            "rows_in_recurring_patterns": recurring_rows,
        },
        "term_reason_distribution": dict(term_dist.most_common()),
        "description_distribution_top20": dict(desc_dist.most_common(20)),
        "per_policy_561_count_histogram": {str(k): v for k, v in sorted(per_policy_hist.items())},
        "governance_policies": {
            p: {
                "rows": sum(1 for r in gov_rows if r["policy"] == p),
                "reversal_marked": sum(1 for r in gov_rows if r["policy"] == p and (r["reversal_code"] or r["date_reversed"])),
            }
            for p in sorted(GOV_POLICIES)
        },
    }

    with open(OUT_DIR / "quikisrr_decision_review_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    def dump_csv(name: str, rows: list[dict], extra: list[str] | None = None):
        fields = ["policy", "mplan", "eff", "amount", "credit_code", "reversal_code",
                  "date_reversed", "coder_reversed", "control_number", "offset_control",
                  "record_seq", "benefit_seq", "date_added", "term_reason", "description",
                  "adj_or_pay", "duration"] + (extra or [])
        with open(OUT_DIR / name, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)

    dump_csv("quikisrr_561_reversal_marked.csv", reversed_rows)
    dump_csv("quikisrr_561_after_560.csv", after_560, ["first_560_date"])
    dump_csv("quikisrr_561_same_day_560.csv", same_day_560, ["first_560_date"])
    flat_dups = [r for _, grp, _ in exact_dup_groups for r in grp]
    dump_csv("quikisrr_561_exact_duplicate_groups.csv", flat_dups)
    flat_same = [r for _, grp in same_date_amt_groups for r in grp]
    dump_csv("quikisrr_561_same_date_amount_groups.csv", flat_same)
    dump_csv("quikisrr_561_governance_rows.csv", gov_rows)

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
