#!/usr/bin/env python3
"""Generate business-reviewable claim examples from real pipeline artifacts (read-only)."""

import os
import re
from datetime import datetime, timezone

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
REPO = os.path.normpath(os.path.join(ROOT, ".."))
OUTPUT_DIR = SCRIPT_DIR

PATHS = {
    "hdr": os.path.join(ROOT, "phase4_claim_event_reconstruction", "claim_candidate_header.csv"),
    "fin": os.path.join(ROOT, "phase4_claim_event_reconstruction", "claim_candidate_financials.csv"),
    "p10": os.path.join(ROOT, "phase10b_quikclms_derivation_design", "quikclms_derivation_candidates.csv"),
    "rev_fin": os.path.join(ROOT, "phase6_family_balancing_intelligence", "revised_claim_financials.csv"),
    "deferred_claims": os.path.join(ROOT, "phase17_uat_governance_reporting", "deferred_governance_claims.csv"),
    "deferred_payments": os.path.join(ROOT, "phase17_uat_governance_reporting", "deferred_governance_payments.csv"),
    "orphan_wb": os.path.join(ROOT, "phase17_uat_governance_reporting", "orphan_review_workbench.csv"),
    "semantic": os.path.join(ROOT, "phase22_semantic_governance", "non_claim_accounting_activity_population.csv"),
    "quikclms": os.path.join(REPO, "QLA_Migration", "Output", "quikclms.csv"),
    "quikclmp": os.path.join(REPO, "QLA_Migration", "Output", "quikclmp.csv"),
    "uat_clms": os.path.join(ROOT, "phase17_uat_governance_reporting", "uat_candidate_quikclms.csv"),
}


def load(path):
    if not os.path.isfile(path):
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str).fillna("")
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def strip(v):
    return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).strip()


def rc_from_memotext(text):
    m = re.search(r"(RC-[A-Za-z0-9_-]+)", strip(text))
    return m.group(1) if m else ""


def hdr_index(hdr):
    return {strip(r.get("reconstructed_claim_id", "")): r.to_dict() for _, r in hdr.iterrows() if strip(r.get("reconstructed_claim_id", ""))}


def p10_index(p10):
    return {strip(r.get("reconstructed_claim_id", "")): r.to_dict() for _, r in p10.iterrows() if strip(r.get("reconstructed_claim_id", ""))}


def fin_index(fin):
    return {strip(r.get("reconstructed_claim_id", "")): r.to_dict() for _, r in fin.iterrows() if strip(r.get("reconstructed_claim_id", ""))}


def row(
    issue_category,
    policy_number,
    claim_id,
    claim_status,
    tx_codes,
    payment_amount,
    governance_status,
    reason_held_or_flagged,
    why_business_review_needed,
    recommended_business_question,
    current_uat_status,
    recommended_next_action,
    **extra,
):
    base = {
        "issue_category": issue_category,
        "policy_number": policy_number,
        "claim_id": claim_id,
        "claim_status": claim_status,
        "tx_codes": tx_codes,
        "payment_amount": payment_amount,
        "governance_status": governance_status,
        "reason_held_or_flagged": reason_held_or_flagged,
        "why_business_review_needed": why_business_review_needed,
        "recommended_business_question": recommended_business_question,
        "current_uat_status": current_uat_status,
        "recommended_next_action": recommended_next_action,
    }
    base.update(extra)
    return base


def examples_true_surrender(clms, hdr_idx, p10_idx, limit=5):
    surr = clms[clms["claimstat"].astype(str) == "99"].head(limit)
    out = []
    for _, r in surr.iterrows():
        rc = rc_from_memotext(r.get("memotext", ""))
        h = hdr_idx.get(rc, {})
        p = p10_idx.get(rc, {})
        tx = strip(h.get("claim_relevant_transaction_codes", ""))
        payout_evidence = [c for c in tx.split("|") if c.strip() in ("0560", "0561", "0090", "1020", "0567", "1900")]
        out.append(row(
            "TRUE_SURRENDER_VALIDATION",
            strip(r.get("mpolicy", "")),
            rc or strip(r.get("claimnum", "")),
            f"CLAIMSTAT=99 ({strip(p.get('mclaimstatus', 'SURRENDER'))})",
            tx,
            strip(r.get("mpaid", "")) or strip(r.get("netdb", "")),
            "UAT_EMITTED",
            f"Passed claim-domain gate: payout/benefit codes present ({'|'.join(payout_evidence) or 'see tx_codes'})",
            "Confirm this is a genuine policy surrender — not loan accounting.",
            "Does LifePRO show a real surrender/cash payout for this policy on this date?",
            "IN_UAT_IMPORT",
            "Validate in QLAdmin Claims tab; compare to LifePRO surrender history.",
            claimnum=strip(r.get("claimnum", "")),
            payout_evidence="|".join(payout_evidence),
            first_activity_date=strip(h.get("first_activity_date", "")),
            netdb=strip(r.get("netdb", "")),
        ))
    return out


def examples_orphan_payments(deferred_pay, hdr_idx, limit=5):
    out = []
    seen_policies = set()
    for _, r in deferred_pay.iterrows():
        pol = strip(r.get("reconstructed_claim_id", "")).split("-")[1] if "RC-" in strip(r.get("reconstructed_claim_id", "")) else ""
        if not pol:
            continue
        # derive policy from RC-9010150910-...
        m = re.search(r"RC-(\d+)-", strip(r.get("reconstructed_claim_id", "")))
        pol_num = m.group(1) if m else pol
        key = (pol_num, strip(r.get("reconstructed_claim_id", "")))
        if key in seen_policies:
            continue
        seen_policies.add(key)
        out.append(row(
            "DEFERRED_ORPHAN_PAYMENTS",
            pol_num,
            strip(r.get("reconstructed_claim_id", "")),
            "Payment only — parent claim blocked",
            "",
            strip(r.get("mamount", "")),
            strip(r.get("governance_status", "")),
            f"{strip(r.get('blocker_category', ''))}: {strip(r.get('orphan_issue', ''))} / parent {strip(r.get('parent_blocker_type', ''))}",
            "Payment exists in LifePRO but cannot link to an approved UAT claim header.",
            "Should this payment stand alone, or does the parent claim need to be fixed first?",
            "DEFERRED_NOT_IN_UAT",
            strip(r.get("remediation_recommendation", "BUSINESS_REVIEW")),
            payment_stage_id=strip(r.get("canonical_payment_stage_id", "")),
            deferred_category=strip(r.get("deferred_category", "")),
        ))
        if len(out) >= limit:
            break
    return out


def examples_unbalanced(deferred_claims, hdr_idx, p10_idx, rev_fin_idx, limit=5):
    sub = deferred_claims[deferred_claims["blocker_category"].astype(str).str.contains("BALANCING", na=False)]
    out = []
    for _, r in sub.head(limit).iterrows():
        rc = strip(r.get("reconstructed_claim_id", ""))
        h = hdr_idx.get(rc, {})
        p = p10_idx.get(rc, {})
        rf = rev_fin_idx.get(rc, {})
        residual = strip(p.get("mresidual", "")) or strip(rf.get("residual_amount", "")) or strip(rf.get("balancing_residual", ""))
        out.append(row(
            "UNBALANCED_CLAIMS",
            strip(h.get("policy_number", "")) or rc.split("-")[1] if rc.startswith("RC-") else "",
            rc,
            strip(p.get("mclaimstatus", "")) or strip(h.get("claim_family", "")),
            strip(h.get("claim_relevant_transaction_codes", "")),
            strip(p.get("mpaid", "")) or strip(p.get("mnetamt", "")),
            strip(r.get("governance_status", "")),
            f"{strip(r.get('deferred_category', ''))}: financial components do not balance ({strip(p.get('mbalancingstatus', 'UNBALANCED'))})",
            "Claim was reconstructed but debits/credits or payout components do not tie out.",
            "Is the imbalance expected (e.g., loan offset, tax withholding) or a missing transaction?",
            "DEFERRED_NOT_IN_UAT",
            "BUSINESS_REVIEW — confirm expected accounting before re-opening for conversion.",
            imbalance_amount=residual,
            reconciliation_status=strip(r.get("reconciliation_status", "")),
            prototype_claimnum=strip(r.get("prototype_claimnum", "")),
        ))
        if len(out) >= limit:
            break
    return out


def examples_semantic_hold(semantic, limit=5):
    out = []
    # diverse patterns: annual 0412, 0411|0412, multi-year same policy
    picks = []
    if not semantic.empty:
        annual = semantic[semantic.get("annual_recurrence_flag", pd.Series(dtype=str)).astype(str).str.upper() == "Y"]
        if not annual.empty:
            pol = strip(annual.iloc[0].get("policy_number", ""))
            picks.extend(annual[annual["policy_number"].astype(str) == pol].head(2).to_dict("records"))
        mixed = semantic[semantic["transaction_codes"].astype(str).str.contains("0411", na=False)]
        if not mixed.empty:
            picks.append(mixed.iloc[0].to_dict())
        only412 = semantic[semantic["transaction_codes"].astype(str) == "0412"]
        if not only412.empty:
            picks.append(only412.iloc[len(only412) // 2].to_dict())
    seen = set()
    for item in picks:
        rc = strip(item.get("reconstructed_claim_id", ""))
        if rc in seen:
            continue
        seen.add(rc)
        out.append(row(
            "SEMANTIC_REVIEW_HOLDS",
            strip(item.get("policy_number", "")),
            rc,
            f"{strip(item.get('claim_family', ''))} / {strip(item.get('lifecycle_status', ''))}",
            strip(item.get("transaction_codes", "")),
            strip(item.get("mintamt", "")),
            strip(item.get("governance_status", "")),
            strip(item.get("reason_excluded", "")).replace("|", "; "),
            "Only borrowed-money accounting codes — no death/surrender payout activity.",
            "Can you confirm this is loan capitalization/maintenance and should NOT appear as a QLAdmin claim?",
            "SEMANTIC_HOLD_NOT_IN_UAT",
            "Accept hold; route to future QuikLoan workstream if loan history is required.",
            activity_class=strip(item.get("activity_class", "")),
            first_activity_date=strip(item.get("first_activity_date", "")),
            annual_recurrence_flag=strip(item.get("annual_recurrence_flag", "")),
        ))
        if len(out) >= limit:
            break
    # pad from head if needed
    if len(out) < limit:
        for _, item in semantic.head(limit).iterrows():
            rc = strip(item.get("reconstructed_claim_id", ""))
            if rc in seen:
                continue
            seen.add(rc)
            out.append(row(
                "SEMANTIC_REVIEW_HOLDS",
                strip(item.get("policy_number", "")),
                rc,
                f"{strip(item.get('claim_family', ''))} / {strip(item.get('lifecycle_status', ''))}",
                strip(item.get("transaction_codes", "")),
                strip(item.get("mintamt", "")),
                strip(item.get("governance_status", "")),
                strip(item.get("reason_excluded", "")).replace("|", "; "),
                "Loan accounting activity quarantined from QUIKCLMS.",
                "Should this ever be a claim, or strictly loan accounting?",
                "SEMANTIC_HOLD_NOT_IN_UAT",
                "Confirm hold; document for QuikLoan planning.",
                activity_class=strip(item.get("activity_class", "")),
                first_activity_date=strip(item.get("first_activity_date", "")),
                annual_recurrence_flag=strip(item.get("annual_recurrence_flag", "")),
            ))
            if len(out) >= limit:
                break
    return out


def examples_missing_claims(deferred_claims, hdr_idx, emit_rc_ids, semantic_ids, limit=5):
    sub = deferred_claims[
        deferred_claims["deferred_category"].astype(str).str.contains("RECONCILIATION", na=False)
        | deferred_claims["blocker_category"].astype(str).str.contains("RECONCILIATION", na=False)
    ]
    out = []
    for _, r in sub.head(limit).iterrows():
        rc = strip(r.get("reconstructed_claim_id", ""))
        h = hdr_idx.get(rc, {})
        tx = strip(h.get("claim_relevant_transaction_codes", ""))
        has_death = any(c in tx for c in ("0530", "0094", "0038", "0630"))
        out.append(row(
            "POTENTIAL_MISSING_CLAIMS",
            strip(h.get("policy_number", "")) or (rc.split("-")[1] if rc.startswith("RC-") else ""),
            rc,
            strip(h.get("claim_family", "")),
            tx,
            "",
            strip(r.get("governance_status", "")),
            f"{strip(r.get('deferred_category', ''))}: {strip(r.get('blocker_category', ''))} — not emitted to UAT",
            "LifePRO may show death/claim activity but conversion deferred pending reconciliation review.",
            "Should this policy have a claim in QLAdmin? If yes, what is missing to approve it?",
            "DEFERRED_NOT_IN_UAT",
            "Business decision: remediate and re-run, or accept exclusion with documented reason.",
            reconciliation_status=strip(r.get("reconciliation_status", "")),
            death_benefit_pattern="Y" if has_death else "N",
            prototype_claimnum=strip(r.get("prototype_claimnum", "")),
            confidence_indicator="MEDIUM" if has_death else "LOW",
        ))
    return out


def examples_payee(clmp, clms, hdr_idx, limit=5):
    out = []
    # pick varied payees with meaningful amounts
    sub = clmp.copy()
    sub["_amt"] = pd.to_numeric(sub.get("mamount", 0), errors="coerce").fillna(0)
    sub = sub.sort_values("_amt", ascending=False)
    seen = set()
    for _, p in sub.iterrows():
        pol = strip(p.get("mpolicy", ""))
        if pol in seen:
            continue
        seen.add(pol)
        # find matching claim
        match = clms[clms["mpolicy"].astype(str) == pol]
        rc = ""
        claim_type = ""
        claimnum = ""
        if not match.empty:
            m0 = match.iloc[0]
            rc = rc_from_memotext(m0.get("memotext", ""))
            claimnum = strip(m0.get("claimnum", ""))
            h = hdr_idx.get(rc, {})
            claim_type = strip(h.get("claim_family", "")) or f"CLAIMSTAT={strip(m0.get('claimstat', ''))}"
        out.append(row(
            "PAYEE_BENEFICIARY_VALIDATION",
            pol,
            rc or claimnum,
            claim_type or "PAYMENT",
            strip(h.get("claim_relevant_transaction_codes", "")) if h else "",
            strip(p.get("mamount", "")),
            "UAT_EMITTED",
            f"Payment emitted to payee {strip(p.get('mpayname', ''))} — no governance block.",
            f"Is payee '{strip(p.get('mpayname', ''))}' correct for ${strip(p.get('mamount', ''))} on policy {pol}?",
            "Is the payee correct for this policy and claim type?",
            "IN_UAT_IMPORT",
            "Compare MPAYNAME and MAMOUNT in QLAdmin to LifePRO payment history.",
            payee_name=strip(p.get("mpayname", "")),
            payee_city=strip(p.get("mpaycity", "")),
            payee_state=strip(p.get("mpayst", "")),
            payment_date=strip(p.get("mpmtdate", "")),
            claimnum=claimnum,
        ))
        if len(out) >= limit:
            break
    return out


def build_review_examples(rows):
    """Wider format for claims_business_review_examples.csv with narrative fields."""
    review = []
    for r in rows:
        review.append({
            "issue_category": r["issue_category"],
            "example_rank": len([x for x in review if x["issue_category"] == r["issue_category"]]) + 1,
            "policy_number": r["policy_number"],
            "claim_id": r["claim_id"],
            "claimnum": r.get("claimnum", ""),
            "claim_status": r["claim_status"],
            "transaction_codes": r["tx_codes"],
            "payment_amount": r["payment_amount"],
            "payee_name": r.get("payee_name", ""),
            "governance_status": r["governance_status"],
            "current_uat_status": r["current_uat_status"],
            "reason_held_or_flagged": r["reason_held_or_flagged"],
            "scenario_summary": r["why_business_review_needed"],
            "recommended_business_question": r["recommended_business_question"],
            "recommended_next_action": r["recommended_next_action"],
            "payout_evidence": r.get("payout_evidence", ""),
            "imbalance_amount": r.get("imbalance_amount", ""),
            "annual_recurrence_flag": r.get("annual_recurrence_flag", ""),
            "first_activity_date": r.get("first_activity_date", ""),
            "production_dbf_flag": "N",
        })
    return review


def write_summary(rows):
    lines = [
        "Claims Conversion — Business Review Examples",
        "=" * 60,
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "Source: Real LifePRO pipeline artifacts (no fabricated examples)",
        "",
        "HOW TO USE THIS FILE",
        "-" * 30,
        "Each section below corresponds to an issue category in the CSV outputs.",
        "Use these examples in UAT review meetings, issue logs, and business sign-off discussions.",
        "",
    ]
    categories = [
        ("TRUE_SURRENDER_VALIDATION", "Real surrenders in UAT — confirm they are genuine"),
        ("DEFERRED_ORPHAN_PAYMENTS", "Payments blocked because parent claim is not approved"),
        ("UNBALANCED_CLAIMS", "Claims deferred because financial components do not tie out"),
        ("SEMANTIC_REVIEW_HOLDS", "Loan accounting quarantined from QUIKCLMS"),
        ("POTENTIAL_MISSING_CLAIMS", "Expected claim activity deferred — should it exist in QLAdmin?"),
        ("PAYEE_BENEFICIARY_VALIDATION", "Emitted payments — validate payee and amount"),
    ]
    for cat, desc in categories:
        cat_rows = [r for r in rows if r["issue_category"] == cat]
        lines.extend([
            "",
            cat.upper().replace("_", " "),
            "-" * 40,
            desc,
            f"Examples provided: {len(cat_rows)}",
            "",
        ])
        for i, r in enumerate(cat_rows, 1):
            lines.extend([
                f"  Example {i}: Policy {r['policy_number']}",
                f"    Claim: {r['claim_id']}",
                f"    Status: {r['current_uat_status']} | {r['governance_status']}",
                f"    Why review: {r['why_business_review_needed']}",
                f"    Question: {r['recommended_business_question']}",
                f"    Action: {r['recommended_next_action']}",
                "",
            ])
    lines.extend([
        "OUTPUT FILES",
        "-" * 30,
        "claims_business_review_examples.csv — full review workbook format",
        "claims_issue_log_examples.csv — issue-log ready columns",
        "",
        "production_dbf_flag=N | UAT governance only",
    ])
    return "\n".join(lines)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    hdr = load(PATHS["hdr"])
    p10 = load(PATHS["p10"])
    fin = load(PATHS["fin"])
    rev_fin = load(PATHS["rev_fin"])
    deferred_claims = load(PATHS["deferred_claims"])
    deferred_pay = load(PATHS["deferred_payments"])
    semantic = load(PATHS["semantic"])
    clms = load(PATHS["quikclms"])
    clmp = load(PATHS["quikclmp"])

    hdr_idx = hdr_index(hdr)
    p10_idx = p10_index(p10)
    rev_fin_idx = {strip(r.get("reconstructed_claim_id", "")): r.to_dict() for _, r in rev_fin.iterrows()} if not rev_fin.empty else fin_index(fin)

    emit_rc = {rc_from_memotext(r.get("memotext", "")) for _, r in clms.iterrows()}
    emit_rc.discard("")
    semantic_ids = set(semantic.get("reconstructed_claim_id", pd.Series(dtype=str)).astype(str)) if not semantic.empty else set()

    all_rows = []
    all_rows.extend(examples_true_surrender(clms, hdr_idx, p10_idx, 5))
    all_rows.extend(examples_orphan_payments(deferred_pay, hdr_idx, 5))
    all_rows.extend(examples_unbalanced(deferred_claims, hdr_idx, p10_idx, rev_fin_idx, 5))
    all_rows.extend(examples_semantic_hold(semantic, 5))
    all_rows.extend(examples_missing_claims(deferred_claims, hdr_idx, emit_rc, semantic_ids, 5))
    all_rows.extend(examples_payee(clmp, clms, hdr_idx, 5))

    issue_cols = [
        "issue_category", "policy_number", "claim_id", "claim_status", "tx_codes",
        "payment_amount", "governance_status", "reason_held_or_flagged",
        "why_business_review_needed", "recommended_business_question",
        "current_uat_status", "recommended_next_action",
    ]
    issue_df = pd.DataFrame(all_rows)
    for c in issue_cols:
        if c not in issue_df.columns:
            issue_df[c] = ""
    issue_df = issue_df[issue_cols]

    review_df = pd.DataFrame(build_review_examples(all_rows))

    issue_path = os.path.join(OUTPUT_DIR, "claims_issue_log_examples.csv")
    review_path = os.path.join(OUTPUT_DIR, "claims_business_review_examples.csv")
    summary_path = os.path.join(OUTPUT_DIR, "claims_business_review_examples_summary.txt")

    issue_df.to_csv(issue_path, index=False)
    review_df.to_csv(review_path, index=False)
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write(write_summary(all_rows))

    print(f"ISSUE_LOG_EXAMPLES: {len(issue_df)} rows -> {issue_path}")
    print(f"REVIEW_EXAMPLES: {len(review_df)} rows -> {review_path}")
    print(f"SUMMARY: {summary_path}")
    print("BY_CATEGORY:", issue_df.groupby("issue_category").size().to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
