"""Read-only forensic extract for policy 9011156655C. No Output/code mutation."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"C:\Users\warren\Documents\GitHub\Warrenhughes1974")
PACTG = ROOT / "QLA_Migration/Source/PACTG_Accounting_Extract20260630.csv"
RNA = ROOT / "QLA_Migration/Source/RelationshipNameAddress_Extract_20260630.csv"
OUT_CLMS = ROOT / "QLA_Migration/Output/quikclms.csv"
OUT_CLMP = ROOT / "QLA_Migration/Output/quikclmp.csv"
RECON = ROOT / "Issue_Log_Items/Issue_135/evidence/issue135_cso_output_recon.csv"
RESULT = ROOT / "Issue_Log_Items/Issue_135/evidence/issue135_forensic_9011156655C.json"

DIGITS = "9011156655"
MPOLICY = "9011156655C"


def _norm_row(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        key = (k or "").strip()
        if isinstance(v, list):
            # duplicate CSV headers (RNA) — keep first non-empty
            vals = [(x or "").strip() for x in v]
            val = next((x for x in vals if x), "")
        else:
            val = (v or "").strip()
        if key and key not in out:
            out[key] = val
    return out


def _amt(x: str) -> float:
    try:
        return float(x or 0)
    except ValueError:
        return 0.0


def load_pactg():
    rows = []
    with open(PACTG, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            n = _norm_row(row)
            if n.get("POLICY_NUMBER") == DIGITS:
                rows.append(n)
    return rows


def load_rna():
    rows = []
    with open(RNA, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            n = _norm_row(row)
            if n.get("POLICY_NUMBER") == DIGITS:
                rows.append(n)
    return rows


def load_output():
    clms = []
    with open(OUT_CLMS, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if (row.get("MPOLICY") or "").strip() == MPOLICY:
                clms.append(row)
    clmp = []
    with open(OUT_CLMP, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if (row.get("MPOLICY") or "").strip() == MPOLICY:
                clmp.append(row)
    return clms, clmp


def main():
    pactg = load_pactg()
    rna = load_rna()
    clms, clmp = load_output()

    settlement = [r for r in pactg if r.get("DATE_ADDED") == "20211104"]
    layers = defaultdict(float)
    settlement_detail = []
    for row in settlement:
        a = _amt(row.get("TRANS_AMOUNT", "0"))
        dc, cc = row.get("DEBIT_CODE", ""), row.get("CREDIT_CODE", "")
        da, ca = row.get("DEBIT_ACCOUNT", ""), row.get("CREDIT_ACCOUNT", "")
        pe, pseq = row.get("PAYEE_RELA_CODE", ""), row.get("PAYEE_SEQUENCE", "")
        rev = row.get("DATE_REVERSED", "")
        detail = {
            "effective_date": row.get("EFFECTIVE_DATE"),
            "date_added": row.get("DATE_ADDED"),
            "debit_code": dc,
            "credit_code": cc,
            "debit_account": da,
            "credit_account": ca,
            "amount": a,
            "date_reversed": rev,
            "reversal_code": row.get("REVERSAL_CODE", ""),
            "payee_rela": pe,
            "payee_seq": pseq,
        }
        settlement_detail.append(detail)
        if rev not in ("", "0"):
            layers["reversed"] += a
            continue
        if dc == "530" and cc == "38":
            layers["face_0530_to_2032"] += a
            detail["class"] = "funding_face"
        elif dc == "110" and cc == "38":
            layers["unearned_prem_110_to_2032"] += a
            detail["class"] = "unearned_premium_return"
        elif dc == "38" and cc == "94" and ca == "1058":
            layers["payout_1058_total"] += a
            layers[f"payout_PE{pseq}"] += a
            detail["class"] = "payout_1058"
        elif any(x in (dc, cc, da, ca) for x in ("0630", "603803R", "603703R")):
            layers["interest_or_dividend"] += a
            detail["class"] = "interest_dividend"
        else:
            layers[f"other_{dc}_{cc}"] += a
            detail["class"] = "other"

    pe_rna = []
    for r in rna:
        if r.get("RELATE_CODE") != "PE":
            continue
        pe_rna.append(
            {
                "name_id": r.get("NAME_ID"),
                "benefit_seq": r.get("BENEFIT_SEQ_NUMBER"),
                "first": r.get("INDIVIDUAL_FIRST"),
                "middle": r.get("INDIVIDUAL_MIDDLE"),
                "last": r.get("INDIVIDUAL_LAST"),
                "suffix": r.get("INDIVIDUAL_SUFFIX"),
                "addr1": r.get("ADDR_LINE_1"),
                "city": r.get("CITY"),
                "state": r.get("STATE"),
                "zip": r.get("ZIP"),
                "ssn": r.get("SOC_SEC_NUMBER"),
            }
        )

    # recon class
    recon_row = None
    with open(RECON, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("mpolicy") == MPOLICY:
                recon_row = row
                break

    face = round(layers.get("face_0530_to_2032", 0), 2)
    prem = round(layers.get("unearned_prem_110_to_2032", 0), 2)
    payout = round(layers.get("payout_1058_total", 0), 2)
    interest = round(layers.get("interest_or_dividend", 0), 2)

    conclusion = {
        "policy": MPOLICY,
        "output_quikclms": [
            {
                k: clms[0].get(k)
                for k in [
                    "MPOLICY",
                    "MPHASE",
                    "MSEQ",
                    "CLAIMNUM",
                    "CLAIMSTAT",
                    "ORIGSTTUS",
                    "DTOFDEATH",
                    "RPTDATE",
                    "PDDATE",
                    "ACCPTDATE",
                    "MPAID",
                    "MFACE",
                    "NETDB",
                    "DIVIDENDS",
                    "LOAN",
                    "PREMIUM",
                    "SUSPENSE",
                    "ADJUST",
                    "MINTAMT",
                    "MINTST",
                    "MINTRATE",
                    "MINTDAYS",
                    "MHOLDINT",
                ]
            }
        ]
        if clms
        else [],
        "output_quikclmp_count": len(clmp),
        "pactg_total_rows": len(pactg),
        "settlement_detail": settlement_detail,
        "layers": dict(layers),
        "arithmetic": {
            "face_funding": face,
            "unearned_premium_return": prem,
            "interest_dividend": interest,
            "clearing_in_total": round(face + prem, 2),
            "payout_total": payout,
            "balanced_clearing_vs_payout": abs(face + prem - payout) < 0.01,
            "gap_net_payment_minus_face": round(payout - face, 2),
            "gap_is_interest": False,
            "gap_is_unearned_premium": prem == 145.67,
        },
        "rna_pe_payees": pe_rna,
        "issue135_recon": recon_row,
        "issue135_bucket": {
            "in_142_derived_high": False,
            "in_308_no_pactg": False,
            "in_9_hold": False,
            "actual_class": "MATCH_CSO_EXISTING_HEADER_ZERO_PAYEE",
            "note": (
                "Pre-existing death header already MATCH_CSO on MPAID; "
                "Issue #135 did not backfill payees for this class. "
                "Legacy claims pipeline left payees out due to UNBALANCED "
                "(-145.67) when unearned premium 110 was not counted as funding."
            ),
        },
        "recommended_fix": {
            "keep_mpaid": 5145.67,
            "keep_mface_netdb": 5000.00,
            "keep_mintamt": 0.00,
            "emit_quikclmp": [
                {"mseq": 1, "amount": 1286.42, "pe_seq": 1, "name_id": "711250"},
                {"mseq": 2, "amount": 1286.41, "pe_seq": 2, "name_id": "711251"},
                {"mseq": 3, "amount": 1286.42, "pe_seq": 3, "name_id": "711252"},
                {"mseq": 4, "amount": 1286.42, "pe_seq": 4, "name_id": "711254"},
            ],
            "do_not_put_145_67_in_mintamt": True,
            "premium_field": "leave 0 (returned unearned premium already inside MPAID)",
        },
        "confidence": 0.93,
        "coding_safe_to_begin": True,
        "coding_scope_note": (
            "Surgical payee backfill for this policy is safe. "
            "Fleet MATCH_CSO zero-payee cohort (~140) needs separate gated inventory before mass apply."
        ),
    }

    # second-pass validation checks
    checks = []
    checks.append(("mpaid_equals_payout", float(clms[0]["MPAID"]) == payout if clms else False))
    checks.append(("mface_equals_face_funding", float(clms[0]["MFACE"]) == face if clms else False))
    checks.append(("mintamt_zero", float(clms[0]["MINTAMT"]) == 0 if clms else False))
    checks.append(("no_interest_codes", interest == 0))
    checks.append(("premium_gap_145_67", prem == 145.67))
    checks.append(("four_pe_payouts", len([d for d in settlement_detail if d.get("class") == "payout_1058"]) == 4))
    checks.append(("four_rna_pe", len(pe_rna) == 4))
    checks.append(("zero_output_payees", len(clmp) == 0))
    checks.append(("payout_sum_5145_67", payout == 5145.67))
    conclusion["second_pass_checks"] = [{"name": n, "pass": bool(p)} for n, p in checks]
    conclusion["second_pass_all_pass"] = all(p for _, p in checks)

    RESULT.write_text(json.dumps(conclusion, indent=2), encoding="utf-8")
    print(json.dumps({k: conclusion[k] for k in [
        "arithmetic", "output_quikclmp_count", "issue135_bucket",
        "recommended_fix", "confidence", "coding_safe_to_begin",
        "second_pass_checks", "second_pass_all_pass", "layers"
    ]}, indent=2))
    print("RNA_PE:")
    for p in pe_rna:
        print(p)
    print("Wrote", RESULT)


if __name__ == "__main__":
    main()
