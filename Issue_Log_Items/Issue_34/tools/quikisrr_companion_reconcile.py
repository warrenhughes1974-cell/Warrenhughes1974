"""
Issue #34 — QUIKISRR companion table reconciliation (planning only).

Matches the eligible ISWL 0561 candidate set (unreversed, 8 MPLANs,
9010780411 hold excluded) against existing claims-pipeline outputs:
  QLA_Migration/Output/quikclms.csv
  QLA_Migration/Output/quikclmp.csv
  QLA_Migration/Output/quikbenf.csv

Match levels:
  A policy-only (quikclms)
  B policy+date  (clms RPTDATE/PDDATE; clmp MCHKDATE/MPMTDATE)
  C policy+amount (clms MPAID/NETDB; clmp MAMOUNT/MGROSS)
  D policy+date+amount (exact event-level)

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
OUT_DIR = PROJECT_ROOT / "Issue_Log_Items" / "Issue_34" / "output" / "QuikIsrr_Companion_Reconciliation"

HOLD_POLICIES = {"9010780411"}
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
DATE_TOLERANCE_DAYS = 45  # payout usually posts days/weeks after the event


def norm(v: str) -> str:
    s = (v or "").strip()
    return "" if s and set(s) == {"-"} else s


def norm_date(v: str) -> str:
    d = re.sub(r"[^0-9]", "", norm(v))
    return d[:8] if len(d) >= 8 else ""


def to_ord(yyyymmdd: str) -> int | None:
    if len(yyyymmdd) != 8:
        return None
    import datetime
    try:
        return datetime.date(int(yyyymmdd[:4]), int(yyyymmdd[4:6]), int(yyyymmdd[6:8])).toordinal()
    except ValueError:
        return None


def to_cents(v: str) -> int | None:
    s = norm(v)
    if not s:
        return None
    try:
        return round(float(s) * 100)
    except ValueError:
        return None


def xwalk(pactg_policy: str) -> str:
    return pactg_policy[1:] + "C" if len(pactg_policy) == 10 and pactg_policy.startswith("9") else pactg_policy


def load_eligible_561() -> list[dict]:
    rows = []
    with open(PACTG, encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f)
        cols = {c.strip(): c for c in reader.fieldnames or []}

        def g(raw, n):
            c = cols.get(n)
            return norm(raw.get(c, "")) if c else ""

        for raw in reader:
            dcd = re.sub(r"[^0-9]", "", g(raw, "DEBIT_CODE"))
            if not dcd or str(int(dcd)) != "561":
                continue
            pol = re.sub(r"[^0-9]", "", g(raw, "POLICY_NUMBER"))
            mplan = COVERAGE_TO_MPLAN.get(g(raw, "PLAN_CODE"), "") or COVERAGE_TO_MPLAN.get(g(raw, "PRODUCT_ID"), "")
            if mplan not in ISWL_MPLANS:
                continue
            if g(raw, "REVERSAL_CODE") == "Y":
                continue
            if pol in HOLD_POLICIES:
                continue
            rows.append({
                "policy_number": pol,
                "mpolicy": xwalk(pol),
                "mplan": mplan,
                "effective_date": norm_date(g(raw, "EFFECTIVE_DATE")),
                "trans_amount": norm(g(raw, "TRANS_AMOUNT")),
                "amount_cents": to_cents(g(raw, "TRANS_AMOUNT")),
            })
    return rows


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    eligible = load_eligible_561()
    total_amt = sum(r["amount_cents"] for r in eligible) / 100.0
    print(f"eligible 561: {len(eligible)} rows / {len({r['policy_number'] for r in eligible})} policies / ${total_amt:,.2f}")

    # --- load companions ---
    def load(path):
        with open(PROJECT_ROOT / path, encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    clms = load("QLA_Migration/Output/quikclms.csv")
    clmp = load("QLA_Migration/Output/quikclmp.csv")
    benf = load("QLA_Migration/Output/quikbenf.csv")

    clms_by_pol = defaultdict(list)
    for r in clms:
        fam = "UNPARSED"
        m = re.search(r"\|([A-Z_]+)\|[A-Z]+$", r.get("MEMOTEXT", ""))
        if m:
            fam = m.group(1)
        clms_by_pol[r["MPOLICY"].strip()].append({
            "family": fam,
            "claimnum": r.get("CLAIMNUM", ""),
            "claimstat": r.get("CLAIMSTAT", ""),
            "rptdate": norm_date(r.get("RPTDATE", "")),
            "pddate": norm_date(r.get("PDDATE", "")),
            "mpaid_cents": to_cents(r.get("MPAID", "")),
            "netdb_cents": to_cents(r.get("NETDB", "")),
            "mseq": r.get("MSEQ", ""),
        })

    clmp_by_pol = defaultdict(list)
    for r in clmp:
        clmp_by_pol[r["MPOLICY"].strip()].append({
            "mamount_cents": to_cents(r.get("MAMOUNT", "")),
            "mgross_cents": to_cents(r.get("MGROSS", "")),
            "mchkdate": norm_date(r.get("MCHKDATE", "")),
            "mpmtdate": norm_date(r.get("MPMTDATE", "")),
            "mseq": r.get("MSEQ", ""),
        })

    benf_pols = {r["MPOLICY"].strip() for r in benf}

    # --- match each eligible row ---
    results = []
    for r in eligible:
        mp = r["mpolicy"]
        eff = r["effective_date"]
        eff_ord = to_ord(eff)
        amt = r["amount_cents"]

        c_rows = clms_by_pol.get(mp, [])
        p_rows = clmp_by_pol.get(mp, [])

        policy_in_clms = bool(c_rows)
        policy_in_clmp = bool(p_rows)
        policy_in_benf = mp in benf_pols

        def date_hits(rows, keys):
            hits = 0
            for cr in rows:
                for k in keys:
                    o = to_ord(cr[k]) if cr[k] else None
                    if o is not None and eff_ord is not None and abs(o - eff_ord) <= DATE_TOLERANCE_DAYS:
                        hits += 1
                        break
            return hits

        def amt_hits(rows, keys):
            hits = 0
            for cr in rows:
                if any(cr[k] is not None and cr[k] == amt for k in keys):
                    hits += 1
            return hits

        def date_amt_hits(rows, dkeys, akeys):
            hits = 0
            for cr in rows:
                dok = False
                for k in dkeys:
                    o = to_ord(cr[k]) if cr[k] else None
                    if o is not None and eff_ord is not None and abs(o - eff_ord) <= DATE_TOLERANCE_DAYS:
                        dok = True
                        break
                aok = any(cr[k] is not None and cr[k] == amt for k in akeys)
                if dok and aok:
                    hits += 1
            return hits

        clms_date = date_hits(c_rows, ["rptdate", "pddate"])
        clms_amt = amt_hits(c_rows, ["mpaid_cents", "netdb_cents"])
        clms_exact = date_amt_hits(c_rows, ["rptdate", "pddate"], ["mpaid_cents", "netdb_cents"])
        clmp_date = date_hits(p_rows, ["mchkdate", "mpmtdate"])
        clmp_amt = amt_hits(p_rows, ["mamount_cents", "mgross_cents"])
        clmp_exact = date_amt_hits(p_rows, ["mchkdate", "mpmtdate"], ["mamount_cents", "mgross_cents"])

        exact_total = clms_exact + clmp_exact
        if exact_total == 1:
            cls = "EXACT_MATCH"
        elif exact_total > 1:
            cls = "AMBIGUOUS_MULTIPLE"
        elif (clms_date and clms_amt) or (clmp_date and clmp_amt):
            cls = "STRONG_MATCH"  # date hit + amount hit on different rows
        elif clms_amt or clmp_amt or clms_date or clmp_date:
            cls = "WEAK_PARTIAL"
        elif policy_in_clms or policy_in_clmp:
            cls = "POLICY_ONLY"
        else:
            cls = "NO_MATCH"

        results.append({
            **{k: r[k] for k in ("policy_number", "mpolicy", "mplan", "effective_date", "trans_amount")},
            "in_quikclms": policy_in_clms,
            "in_quikclmp": policy_in_clmp,
            "in_quikbenf": policy_in_benf,
            "clms_families": "|".join(sorted({c["family"] for c in c_rows})) if c_rows else "",
            "clms_date_hits": clms_date,
            "clms_amount_hits": clms_amt,
            "clms_exact_hits": clms_exact,
            "clmp_date_hits": clmp_date,
            "clmp_amount_hits": clmp_amt,
            "clmp_exact_hits": clmp_exact,
            "classification": cls,
        })

    by_cls = Counter(r["classification"] for r in results)
    pols_no_companion = {r["policy_number"] for r in results if not r["in_quikclms"] and not r["in_quikclmp"]}
    pols_in_clms = {r["policy_number"] for r in results if r["in_quikclms"]}

    # family composition of matched policies
    fam_of_matched = Counter()
    for r in results:
        if r["in_quikclms"]:
            fam_of_matched[r["clms_families"]] += 1

    summary = {
        "reconcile_date": "2026-07-02",
        "eligible_561_rows": len(results),
        "eligible_policies": len({r["policy_number"] for r in results}),
        "eligible_total_amount": round(total_amt, 2),
        "companion_sources": {
            "quikclms": {"path": "QLA_Migration/Output/quikclms.csv", "rows": len(clms)},
            "quikclmp": {"path": "QLA_Migration/Output/quikclmp.csv", "rows": len(clmp)},
            "quikbenf": {"path": "QLA_Migration/Output/quikbenf.csv", "rows": len(benf)},
            "quikbene_quikbenh": "NOT FOUND anywhere in repo",
        },
        "quikclms_family_composition": dict(Counter(
            re.search(r"\|([A-Z_]+)\|[A-Z]+$", r.get("MEMOTEXT", "")).group(1)
            if re.search(r"\|([A-Z_]+)\|[A-Z]+$", r.get("MEMOTEXT", "")) else "UNPARSED"
            for r in clms
        ).most_common()),
        "quikclms_partial_surrender_family_rows": 0,
        "match_classification": dict(by_cls.most_common()),
        "rows_policy_in_quikclms": sum(1 for r in results if r["in_quikclms"]),
        "rows_policy_in_quikclmp": sum(1 for r in results if r["in_quikclmp"]),
        "rows_policy_in_quikbenf": sum(1 for r in results if r["in_quikbenf"]),
        "policies_with_no_companion_rows": len(pols_no_companion),
        "clms_families_on_matched_rows": dict(fam_of_matched.most_common()),
        "date_tolerance_days": DATE_TOLERANCE_DAYS,
        "claim_sequence_note": "quikclms MSEQ = 0 on all 2,114 rows; quikclmp MSEQ = payment sequence 1-9 per claim, not per partial withdrawal",
        "benefit_code_8_note": "quikbenf schema is beneficiary splits (MPOLICY/MBENFID/MTYPE/MRELATION/MSPLIT) - no benefit code field; QuikBene/QuikBenh not present in repo",
    }

    with open(OUT_DIR / "quikisrr_companion_reconciliation_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    fields = list(results[0].keys())

    def dump(name, rows):
        with open(OUT_DIR / name, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for r in rows:
                w.writerow(r)

    dump("quikisrr_companion_exact_matches.csv",
         [r for r in results if r["classification"] in ("EXACT_MATCH", "STRONG_MATCH")])
    dump("quikisrr_companion_policy_only_matches.csv",
         [r for r in results if r["classification"] in ("POLICY_ONLY", "WEAK_PARTIAL")])
    dump("quikisrr_companion_missing_matches.csv",
         [r for r in results if r["classification"] == "NO_MATCH"])
    dump("quikisrr_companion_ambiguous_matches.csv",
         [r for r in results if r["classification"] == "AMBIGUOUS_MULTIPLE"])

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
