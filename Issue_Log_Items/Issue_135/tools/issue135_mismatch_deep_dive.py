#!/usr/bin/env python3
"""Issue #135 Phase B reverse-engineering — AVAILABLE_MISMATCH deep dive only.

Read-only evidence builder. Does not mutate Output.
Separates CLAIMSTAT=2 death mismatches from shell/PS/no-death cases,
classifies multiplicity / missing / loan / clearing / unexplained with
signed PACTG debit/credit relationships where available.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TOOLS))

from issue135_cso_pactg_recon import (  # noqa: E402
    TOLERANCE,
    _account_family,
    _money,
    _strip,
    classify_claim_row,
    is_reversed_date,
    load_output_claims,
    resolve_pactg,
    stream_pactg_for_policies,
)

EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
DEFAULT_CLMS = ROOT / "QLA_Migration" / "Output" / "quikclms.csv"
DEFAULT_CLMP = ROOT / "QLA_Migration" / "Output" / "quikclmp.csv"
DEFAULT_CSO = ROOT / "docs" / "Claims" / "CSO Life claims summary - 2017 - 2025.xlsx"

# Economic payout codes / accounts (signed analysis)
PAYOUT_DEBIT_CODES = {"0094", "0090"}
PAYOUT_CREDIT_CODES = {"6001", "6038"}  # funding / interest-on-DB in check
CLEARING_ACCT_FAMILIES = {"2032", "2031", "2039"}
LOAN_ACCT_FAMILIES = {"1017", "7046"}
LOAN_DEBIT_CODES = {"0412", "0451"}
REINSTATE_ACCT = {"1015", "2031", "2039", "6044"}
INTRACO_ACCT = {"2019"}
DIV_EXCLUDE_CODES = {"6037", "0310", "0641"}
DIV_EXCLUDE_ACCT = {"2023"}


def _signed_net(rows: list[dict], predicate) -> float:
    """Net using signed amounts: credit-side funding positive as economic source;
    debit payouts negative as economic use. For residual analysis we keep abs
    and direction markers separately — here return sum of signed amounts where
    predicate matches, using +trans for credit-dominant rows and -trans for debit.
    """
    total = 0.0
    for r in rows:
        if not predicate(r):
            continue
        amt = float(r["trans_amount"])
        # Prefer credit as + when credit code is economic; debit payout as -
        dr = r["debit_code"]
        cr = r["credit_code"]
        if dr in PAYOUT_DEBIT_CODES or _account_family(r["debit_account"]) in (
            "1058",
        ):
            total -= abs(amt)
        elif cr in PAYOUT_CREDIT_CODES or _account_family(r["credit_account"]) in (
            "1058",
        ):
            total += abs(amt)
        else:
            # unclassified direction: keep positive abs for presence only
            total += 0.0
    return round(total, 2)


def analyze_pactg_layers(rows: list[dict]) -> dict:
    """Compute signed / presence metrics for mismatch classification."""
    open_rows = [r for r in rows if not is_reversed_date(r.get("date_reversed", ""))]
    rev_rows = [r for r in rows if is_reversed_date(r.get("date_reversed", ""))]

    by_layer_abs: dict[str, float] = defaultdict(float)
    by_layer_signed: dict[str, float] = defaultdict(float)
    by_layer_n: dict[str, int] = defaultdict(int)

    payout_debit_sum = 0.0
    payout_debit_n = 0
    payout_debit_dates: list[str] = []
    clearing_sum = 0.0
    clearing_n = 0
    loan_sum = 0.0
    loan_n = 0
    funding_sum = 0.0
    funding_n = 0
    interest_in_check = 0.0
    reinstate_markers = 0
    intraco_markers = 0
    div_exclude = 0.0

    # Distinct payout event keys: (eff_date, amount, debit_code)
    payout_events = []

    for r in open_rows:
        layer = r.get("layer_class", "unclassified")
        amt = abs(float(r["trans_amount"]))
        by_layer_abs[layer] += amt
        by_layer_n[layer] += 1
        dr = r["debit_code"]
        cr = r["credit_code"]
        dra = _account_family(r["debit_account"])
        cra = _account_family(r["credit_account"])

        # Economic cash payout: 0094/0090 on either side, or 1058 cash account.
        # LifePRO often credits 1058 with credit_code 0094 (clearing 2032 -> cash).
        is_payout = (
            dr in PAYOUT_DEBIT_CODES
            or cr in PAYOUT_DEBIT_CODES
            or dra == "1058"
            or cra == "1058"
            or layer
            in (
                "payout_death_claim_payment",
                "payout_cash_death_claim",
                "payout_related",
            )
        )
        if is_payout:
            payout_debit_sum += amt
            payout_debit_n += 1
            payout_debit_dates.append(_strip(r.get("effective_date", "")))
            payout_events.append(
                {
                    "effective_date": _strip(r.get("effective_date", "")),
                    "amount": round(float(r["trans_amount"]), 2),
                    "debit_code": dr,
                    "credit_code": cr,
                    "debit_account": r["debit_account"],
                    "credit_account": r["credit_account"],
                    "layer_class": layer,
                }
            )
            by_layer_signed["payout_death"] -= amt
        if cra in CLEARING_ACCT_FAMILIES or dra in CLEARING_ACCT_FAMILIES:
            clearing_sum += amt
            clearing_n += 1
            by_layer_signed["clearing"] += amt if cra in CLEARING_ACCT_FAMILIES else -amt
        if dra in LOAN_ACCT_FAMILIES or cra in LOAN_ACCT_FAMILIES or dr in LOAN_DEBIT_CODES:
            loan_sum += amt
            loan_n += 1
            by_layer_signed["loan"] += amt
        if cr in {"6001"} or cra.startswith("6001") if False else cr.startswith("6001"):
            funding_sum += amt
            funding_n += 1
            by_layer_signed["funding_db"] += amt
        if cr.startswith("6038") or dr == "0630":
            interest_in_check += amt
            by_layer_signed["interest_in_check"] += amt
        if dra in REINSTATE_ACCT or cra in REINSTATE_ACCT or cr.startswith("6044"):
            reinstate_markers += 1
        if dra in INTRACO_ACCT or cra in INTRACO_ACCT or "1058000256" in (
            re.sub(r"[^0-9]", "", r["debit_account"]),
            re.sub(r"[^0-9]", "", r["credit_account"]),
        ):
            intraco_markers += 1
        if cr.startswith("6037") or dra in DIV_EXCLUDE_ACCT or cra in DIV_EXCLUDE_ACCT:
            div_exclude += amt

    # Multiplicity from payout event clustering by amount
    amt_counts = Counter(round(abs(e["amount"]), 2) for e in payout_events)
    dominant_amt = None
    dominant_mult = 0
    if amt_counts:
        dominant_amt, dominant_mult = amt_counts.most_common(1)[0]

    # Unique calendar dates of payout debits
    unique_payout_dates = sorted({d for d in payout_debit_dates if d})

    return {
        "open_row_count": len(open_rows),
        "reversal_row_count": len(rev_rows),
        "reversal_abs_sum": round(sum(abs(float(r["trans_amount"])) for r in rev_rows), 2),
        "layer_abs_json": json.dumps({k: round(v, 2) for k, v in sorted(by_layer_abs.items())}),
        "layer_n_json": json.dumps(dict(sorted(by_layer_n.items()))),
        "payout_debit_sum": round(payout_debit_sum, 2),
        "payout_debit_n": payout_debit_n,
        "payout_unique_dates": len(unique_payout_dates),
        "payout_dates": "|".join(unique_payout_dates[:8]),
        "clearing_sum": round(clearing_sum, 2),
        "clearing_n": clearing_n,
        "loan_sum": round(loan_sum, 2),
        "loan_n": loan_n,
        "funding_sum": round(funding_sum, 2),
        "funding_n": funding_n,
        "interest_in_check": round(interest_in_check, 2),
        "reinstate_markers": reinstate_markers,
        "intraco_markers": intraco_markers,
        "div_exclude_sum": round(div_exclude, 2),
        "dominant_payout_amount": dominant_amt if dominant_amt is not None else "",
        "dominant_payout_multiplicity": dominant_mult,
        "payout_events_json": json.dumps(payout_events[:20]),
        "signed_layer_json": json.dumps(
            {k: round(v, 2) for k, v in sorted(by_layer_signed.items())}
        ),
    }


def classify_mismatch(
    cso_paid: float,
    death_mpaid: float,
    death_claimstats: str,
    payee_sum: float,
    pactg: dict,
    non_death_families: str,
) -> tuple[str, str, str]:
    """Return (evidence_class, hold_flag, note).

    evidence_class is a fine-grained Phase B label.
    hold_flag = HOLD/UNEXPLAINED when not proven.
    """
    residual = round(cso_paid - death_mpaid, 2)
    stats = set(x for x in death_claimstats.split("|") if x)
    is_stat2 = stats == {"2"} or ("2" in stats and "1" not in stats)
    is_stat1_only = stats == {"1"}

    # Shell / non-death should not appear in AVAILABLE_MISMATCH; guard anyway
    if not stats and non_death_families:
        return (
            "SHELL_OR_PS_NOT_DEATH",
            "HOLD",
            "No death CLAIMSTAT; non-death families present — exclude from death MPAID rules",
        )

    ratio = (death_mpaid / cso_paid) if cso_paid > 0 else None
    mult = pactg.get("dominant_payout_multiplicity") or 0
    dom_amt = pactg.get("dominant_payout_amount")
    try:
        dom_amt_f = float(dom_amt) if dom_amt != "" and dom_amt is not None else None
    except (TypeError, ValueError):
        dom_amt_f = None

    # x3 reinstatement / triple economic count
    if ratio is not None and abs(ratio - 3.0) <= 0.02:
        if pactg.get("reinstate_markers", 0) > 0 or mult >= 3 or pactg.get("payout_debit_n", 0) >= 3:
            return (
                "MULTIPLICITY_X3_REINSTATEMENT",
                "CANDIDATE",
                "Death MPAID ≈ 3× CSO; PACTG shows reinstate markers and/or ≥3 payout legs",
            )
        return (
            "MULTIPLICITY_X3_RATIO_ONLY",
            "HOLD",
            "MPAID ≈ 3× CSO but PACTG reinstate/payout multiplicity not confirmed",
        )

    # x2 duplicate
    if ratio is not None and abs(ratio - 2.0) <= 0.02:
        if pactg.get("intraco_markers", 0) > 0 or mult >= 2 or pactg.get("clearing_n", 0) >= 2:
            return (
                "MULTIPLICITY_X2_DUPLICATE_OR_CLEARING",
                "CANDIDATE",
                "Death MPAID ≈ 2× CSO; PACTG shows duplicate payout and/or clearing duplication",
            )
        return (
            "MULTIPLICITY_X2_RATIO_ONLY",
            "HOLD",
            "MPAID ≈ 2× CSO but PACTG duplicate/clearing evidence thin",
        )

    # Missing death payment — prefer PACTG economic payout evidence over loan-only.
    if abs(death_mpaid) <= TOLERANCE and cso_paid > 0:
        if pactg.get("payout_debit_n", 0) > 0:
            note = "Header MPAID=0 but open PACTG economic payout (0094/1058) exists — emit/path gap"
            if pactg.get("loan_n", 0) > 0:
                note += "; loan layers also present (loan residual context)"
            return (
                "MISSING_DEATH_MPAID_BUT_PACTG_PAYOUT",
                "CANDIDATE",
                note,
            )
        if pactg.get("loan_n", 0) > 0:
            return (
                "MISSING_DEATH_PAYMENT_LOAN_RESIDUAL",
                "CANDIDATE",
                "CSO>0, death MPAID=0; loan layers present, no open economic payout",
            )
        if pactg.get("funding_n", 0) > 0:
            return (
                "MISSING_DEATH_MPAID_FUNDING_ONLY",
                "HOLD",
                "Funding layers without open payout; do not invent payee",
            )
        return (
            "MISSING_DEATH_PAYMENT",
            "HOLD",
            "CSO>0 and death MPAID=0; no strong PACTG payout path",
        )

    # Header vs payee
    if abs(payee_sum - death_mpaid) > TOLERANCE:
        if abs(payee_sum - cso_paid) <= TOLERANCE:
            return (
                "HEADER_PAYEE_MISALIGN_PAYEE_MATCHES_CSO",
                "CANDIDATE",
                "Payee sum == CSO; header MPAID does not — header correction candidate",
            )
        if abs(death_mpaid - cso_paid) <= TOLERANCE:
            return (
                "HEADER_PAYEE_MISALIGN_HEADER_MATCHES_CSO",
                "CANDIDATE",
                "Header matches CSO; payee sum does not — payee correction candidate",
            )
        return (
            "HEADER_PAYEE_MISALIGN_BOTH_OFF",
            "HOLD",
            "Header and payee disagree with each other and CSO",
        )

    # Clearing duplication without exact x2 ratio
    if pactg.get("clearing_n", 0) >= 2 and ratio is not None and ratio > 1.05:
        return (
            "CLEARING_DUPLICATION_SUSPECT",
            "HOLD",
            "Multiple clearing legs with overstated MPAID; not exact x2/x3",
        )

    # Loan residual (partial): death MPAID short of CSO by loan-ish amount
    if residual > TOLERANCE and pactg.get("loan_n", 0) > 0:
        loan = float(pactg.get("loan_sum") or 0)
        if abs(residual - loan) <= 1.0 or (loan > 0 and abs(residual) <= loan + 1.0):
            return (
                "LOAN_RESIDUAL_SHORTFALL",
                "HOLD",
                "Death MPAID short of CSO with loan layers near residual — needs payee/loan net rule",
            )

    # Interest in check already in MPAID (should stay; MINTAMT=0)
    if abs(residual) > TOLERANCE and float(pactg.get("interest_in_check") or 0) > 0:
        return (
            "INTEREST_IN_CHECK_RESIDUAL",
            "HOLD",
            "Interest-on-DB layers present; keep interest in check/MPAID path, MINTAMT stays 0",
        )

    # Near-CSO with dominant payout == CSO but header overstated
    if (
        dom_amt_f is not None
        and abs(dom_amt_f - cso_paid) <= TOLERANCE
        and death_mpaid > cso_paid + TOLERANCE
        and mult >= 2
    ):
        return (
            "MULTIPLICITY_FROM_REPEATED_PAYOUT_AMT",
            "CANDIDATE",
            f"Dominant open payout amount equals CSO ({dom_amt_f}); header counts {mult}x",
        )

    # CLAIMSTAT nuance
    if is_stat1_only:
        return (
            "CLAIMSTAT_1_PENDING_RESIDUAL",
            "HOLD",
            "Death header is CLAIMSTAT=1 (pending); residual held pending status/money rule",
        )

    if is_stat2:
        return (
            "UNEXPLAINED_RESIDUAL_CLAIMSTAT2",
            "HOLD/UNEXPLAINED",
            "CLAIMSTAT=2 death residual not force-fit; insufficient repeated PACTG rule proof",
        )

    return (
        "UNEXPLAINED_RESIDUAL",
        "HOLD/UNEXPLAINED",
        "Residual not force-fit; hold pending further PACTG proof",
    )


def main() -> int:
    recon_path = EVIDENCE / "issue135_cso_output_recon.csv"
    if not recon_path.is_file():
        raise SystemExit(f"Missing {recon_path}; run issue135_cso_pactg_recon.py first")

    recon = pd.read_csv(recon_path, dtype=str, keep_default_na=False)
    mism = recon[recon["population"] == "AVAILABLE_MISMATCH"].copy()
    no_death = recon[recon["population"] == "IN_OUTPUT_NO_DEATH_HEADER"].copy()

    # Reload claims for CLAIMSTAT=2 filter detail
    clms, clmp, payee_meta = load_output_claims(DEFAULT_CLMS, DEFAULT_CLMP)
    clms["_family"] = clms.apply(classify_claim_row, axis=1)

    digits = set(mism["policy_digits"].tolist())
    pactg_path = resolve_pactg(None)
    print(f"Streaming PACTG for {len(digits)} mismatch policies from {pactg_path} ...")
    buckets = stream_pactg_for_policies(pactg_path, digits)

    rows_out = []
    for _, r in mism.iterrows():
        pol = _strip(r["mpolicy"])
        dig = _strip(r["policy_digits"])
        cso_paid = _money(r["cso_total_paid"])
        death_mpaid = _money(r["death_mpaid"])
        payee_sum = _money(r["payee_sum_mamount"])
        claimstats = _strip(r["death_claimstats"])
        pactg_metrics = analyze_pactg_layers(buckets.get(dig, []))
        eclass, hold, note = classify_mismatch(
            cso_paid,
            death_mpaid,
            claimstats,
            payee_sum,
            pactg_metrics,
            _strip(r.get("non_death_families", "")),
        )
        stats = set(x for x in claimstats.split("|") if x)
        death_stat2 = "Y" if "2" in stats else "N"
        death_stat1 = "Y" if "1" in stats else "N"
        ratio = round(death_mpaid / cso_paid, 4) if cso_paid else ""
        rows_out.append(
            {
                "mpolicy": pol,
                "policy_digits": dig,
                "population": "AVAILABLE_MISMATCH",
                "death_claimstats": claimstats,
                "is_claimstat_2_death": death_stat2,
                "is_claimstat_1_death": death_stat1,
                "cso_total_paid": cso_paid,
                "death_mpaid": death_mpaid,
                "payee_sum_mamount": payee_sum,
                "residual_cso_minus_death_mpaid": round(cso_paid - death_mpaid, 2),
                "mpaid_over_cso_ratio": ratio,
                "non_death_families": _strip(r.get("non_death_families", "")),
                "prior_proposed_rule_class": _strip(r.get("proposed_rule_class", "")),
                "evidence_class": eclass,
                "hold_flag": hold,
                "evidence_note": note,
                "is_teacher_death": _strip(r.get("is_teacher_death", "N")),
                **pactg_metrics,
            }
        )

    deep = pd.DataFrame(rows_out)

    # No-death / shell / PS separation artifact (the 32)
    no_death_out = []
    for _, r in no_death.iterrows():
        no_death_out.append(
            {
                "mpolicy": _strip(r["mpolicy"]),
                "population": "IN_OUTPUT_NO_DEATH_HEADER",
                "cso_total_paid": _money(r["cso_total_paid"]),
                "non_death_families": _strip(r.get("non_death_families", "")),
                "non_death_mpaid_sum_DO_NOT_ADD_TO_CSO": _money(
                    r.get("non_death_mpaid_sum_DO_NOT_ADD_TO_CSO", 0)
                ),
                "payee_sum_mamount": _money(r.get("payee_sum_mamount", 0)),
                "separation_note": (
                    "Excluded from death CLAIMSTAT=2 mismatch Phase B rules; "
                    "do not sum PS/surrender/shell with CSO Total_Paid"
                ),
                "evidence_class": "NO_DEATH_SHELL_OR_PS",
                "hold_flag": "SEPARATE_WORKSTREAM",
            }
        )
    no_death_df = pd.DataFrame(no_death_out)

    # Frequency tables
    class_counts = Counter(deep["evidence_class"])
    hold_counts = Counter(deep["hold_flag"])
    stat2_counts = Counter(
        deep.loc[deep["is_claimstat_2_death"] == "Y", "evidence_class"]
    )

    examples = {}
    for cls, n in class_counts.most_common():
        sample = deep[deep["evidence_class"] == cls].head(5)
        examples[cls] = {
            "count": int(n),
            "policies": sample["mpolicy"].tolist(),
            "hold_flags": sample["hold_flag"].tolist(),
            "ratios": sample["mpaid_over_cso_ratio"].tolist(),
            "residuals": sample["residual_cso_minus_death_mpaid"].tolist(),
        }

    # Candidate rules that are repeated AND not HOLD — for Phase B code gate
    candidate = deep[deep["hold_flag"] == "CANDIDATE"]
    candidate_by_class = Counter(candidate["evidence_class"])
    # A class is "implementable" only if >= 5 repeated cases AND no client choice pending
    # User instruction: only if supported by repeated PACTG and no unanswered client choice.
    # Multiplicity corrections change MPAID/payee — client-facing money choice still open
    # per Planning Q2 (hold unresolved). So we do NOT auto-implement amount changes.
    implementable = {}
    for cls, n in candidate_by_class.items():
        # Require strong repeated evidence
        if n < 5:
            implementable[cls] = {
                "count": int(n),
                "safe_to_implement_phase_b_code": False,
                "reason": "Fewer than 5 repeated cases",
            }
            continue
        # Multiplicity / missing / header changes alter claim money — Planning locked
        # unresolved residual = Hold, and teacher cases need client confirmation path.
        # Without an explicit approved emit rule beyond MINTAMT=0, keep evidence-only.
        implementable[cls] = {
            "count": int(n),
            "safe_to_implement_phase_b_code": False,
            "reason": (
                "Repeated PACTG pattern exists (ratio + clearing/reinstatement/"
                "0094-1058 legs). Correction mechanism is still ambiguous: "
                "scale header MPAID vs dedupe quikclmp payees vs exclude "
                "reinstatement/clearing loops in emit. Do not force "
                "MPAID=Total_Paid without an approved audit-reasoned path. "
                "Needs Development approval for the chosen mechanism."
            ),
        }

    summary = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "issue": 135,
        "phase": "B_REVERSE_ENGINEERING",
        "available_mismatch_count": int(len(deep)),
        "claimstat_2_mismatch_count": int((deep["is_claimstat_2_death"] == "Y").sum()),
        "claimstat_1_mismatch_count": int((deep["is_claimstat_1_death"] == "Y").sum()),
        "no_death_shell_ps_separated": int(len(no_death_df)),
        "evidence_class_counts": dict(class_counts),
        "hold_flag_counts": dict(hold_counts),
        "claimstat_2_class_counts": dict(stat2_counts),
        "examples_by_class": examples,
        "candidate_class_counts": dict(candidate_by_class),
        "phase_b_code_implementability": implementable,
        "phase_b_code_change": False,
        "phase_b_code_change_reason": (
            "No Phase B production claim-amount rule implemented. x2 (17) and x3 (22) "
            "have repeated PACTG proof, but the emit correction mechanism is unresolved "
            "(header scale vs payee dedupe vs exclude reinstatement/clearing loops). "
            "Forcing MPAID=Total_Paid without that path is disallowed. Missing-death "
            "PACTG payout cases are few (<5) and need the same mechanism choice."
        ),
        "mintamt_remains_zero": True,
        "eric_gaps_untouched": True,
        "pactg_path": str(pactg_path),
    }

    deep_path = EVIDENCE / "issue135_phase_b_mismatch_deep_dive.csv"
    sep_path = EVIDENCE / "issue135_no_death_shell_ps_separated.csv"
    sum_path = EVIDENCE / "issue135_phase_b_reverse_eng_summary.json"
    md_path = EVIDENCE / "issue135_phase_b_reverse_eng_report.md"

    deep.to_csv(deep_path, index=False, encoding="utf-8")
    no_death_df.to_csv(sep_path, index=False, encoding="utf-8")
    sum_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Markdown report
    lines = [
        "# Issue #135 — Phase B Reverse-Engineering Report",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Scope",
        "",
        "- Population: **AVAILABLE_MISMATCH only** (61).",
        "- Separated: **IN_OUTPUT_NO_DEATH_HEADER** (32) — shell/PS/disbursement; not death CLAIMSTAT=2 rules.",
        "- Eric supply gaps (459): untouched; not conversion failures.",
        "- `MINTAMT` remains 0.00 (Phase A).",
        "- No production claim-amount code change in this pass.",
        "",
        "## Separation",
        "",
        f"| Bucket | Count |",
        f"|---|---:|",
        f"| AVAILABLE_MISMATCH (death headers vs CSO) | {summary['available_mismatch_count']} |",
        f"| … with CLAIMSTAT containing 2 | {summary['claimstat_2_mismatch_count']} |",
        f"| … with CLAIMSTAT containing 1 | {summary['claimstat_1_mismatch_count']} |",
        f"| NO_DEATH_SHELL_OR_PS (separated) | {summary['no_death_shell_ps_separated']} |",
        "",
        "## Evidence class frequencies (61 mismatches)",
        "",
        "| Evidence class | Count | Hold | Example policies |",
        "|---|---:|---|---|",
    ]
    for cls, meta in examples.items():
        holds = ",".join(sorted(set(meta["hold_flags"])))
        pols = "; ".join(meta["policies"][:3])
        lines.append(f"| {cls} | {meta['count']} | {holds} | {pols} |")

    lines.extend(
        [
            "",
            "## Hold vs candidate",
            "",
            "| Hold flag | Count |",
            "|---|---:|",
        ]
    )
    for k, v in hold_counts.most_common():
        lines.append(f"| {k} | {v} |")

    lines.extend(
        [
            "",
            "## Phase B code decision",
            "",
            f"**Code change implemented:** `{summary['phase_b_code_change']}`",
            "",
            summary["phase_b_code_change_reason"],
            "",
            "### Candidate classes (not auto-implemented)",
            "",
        ]
    )
    if not implementable:
        lines.append("_No CANDIDATE classes in this pass._")
    else:
        lines.append("| Class | Count | Safe to implement? | Reason |")
        lines.append("|---|---:|---|---|")
        for cls, meta in implementable.items():
            lines.append(
                f"| {cls} | {meta['count']} | {meta['safe_to_implement_phase_b_code']} | {meta['reason']} |"
            )

    lines.extend(
        [
            "",
            "## Teacher case refresh",
            "",
            "| Policy | CSO | Death MPAID | Ratio | Evidence class | Hold |",
            "|---|---:|---:|---:|---|---|",
        ]
    )
    teachers = deep[deep["is_teacher_death"] == "Y"]
    for _, t in teachers.iterrows():
        lines.append(
            f"| {t['mpolicy']} | {float(t['cso_total_paid']):.2f} | {float(t['death_mpaid']):.2f} | "
            f"{t['mpaid_over_cso_ratio']} | {t['evidence_class']} | {t['hold_flag']} |"
        )

    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- `{deep_path.name}` — per-policy deep dive",
            f"- `{sep_path.name}` — 32 no-death/shell/PS separation",
            f"- `{sum_path.name}` — machine summary",
            "",
            "## Safeguards preserved",
            "",
            "- CSO Total_Paid is policy-level; never sum death + PS.",
            "- Do not set MPAID=Total_Paid without PACTG evidence + audit reason.",
            "- Unexplained → HOLD/UNEXPLAINED.",
            "- Preserve #134 MEMOTEXT, #78/#84/#85 payee/header, Item 16/18, MPOLICY/MPREM.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "available_mismatch_count": summary["available_mismatch_count"],
        "claimstat_2_mismatch_count": summary["claimstat_2_mismatch_count"],
        "no_death_shell_ps_separated": summary["no_death_shell_ps_separated"],
        "evidence_class_counts": summary["evidence_class_counts"],
        "hold_flag_counts": summary["hold_flag_counts"],
        "phase_b_code_change": summary["phase_b_code_change"],
    }, indent=2))
    print(f"Wrote {deep_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
