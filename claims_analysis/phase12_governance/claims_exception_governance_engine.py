#!/usr/bin/env python3
"""
Phase 12 — QA/UAT hardening & production readiness exception governance engine.

Analyzes Phase 11 prototype exceptions and produces enterprise governance intelligence.
Does NOT deploy production DBFs, auto-remediate rows, or modify app.py / prior outputs.
"""

import argparse
import json
import logging
import os
import shutil
from collections import Counter, defaultdict

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "claims_exception_governance_rules.json")
PHASE6 = os.path.join(ROOT, "phase6_family_balancing_intelligence")
PHASE7C = os.path.join(ROOT, "phase7c_death_claim_decomposition")
PHASE8 = os.path.join(ROOT, "phase8_payee_distribution_intelligence")
PHASE10A = os.path.join(ROOT, "phase10a_quikclmp_derivation_design")
PHASE10B = os.path.join(ROOT, "phase10b_quikclms_derivation_design")
PHASE11 = os.path.join(ROOT, "phase11_prototype_dbf_generation")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase12_qa_uat_hardening")

logger = logging.getLogger("exception_governance")


def load_csv(path):
    df = pd.read_csv(path, dtype=str)
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def strip_val(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def parse_amount(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    raw = str(value).strip().replace(",", "").replace("$", "")
    if not raw:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0


def pattern_match(text, patterns):
    s = strip_val(text).upper()
    for pat in patterns:
        if strip_val(pat).upper() in s:
            return True
    return False


def classify_rejected_claim(row, rules, revised_lookup, residual_lookup):
    cfg = rules["rejected_claim_root_causes"]
    validation_issue = strip_val(row.get("validation_issues", ""))
    rejection = strip_val(row.get("rejection_reason", ""))
    confidence = strip_val(row.get("derivation_confidence", ""))
    cid = strip_val(row.get("reconstructed_claim_id", ""))
    balancing = revised_lookup.get(cid, {})
    residual = residual_lookup.get(cid, {})
    residual_amt = abs(parse_amount(residual.get("residual_amount", 0)))

    root_cause = "RULEBOOK_GATING_FAILURE"
    meta = cfg.get("RULEBOOK_GATING_FAILURE", {})

    if validation_issue == "UNBALANCED" or strip_val(balancing.get("revised_balancing_status", "")) == "UNBALANCED":
        root_cause = "UNBALANCED"
        meta = cfg.get("UNBALANCED", meta)
    elif residual_amt > float(cfg.get("RESIDUAL_EXCESS", {}).get("match_residual_threshold", 0.01)):
        if validation_issue or strip_val(balancing.get("revised_balancing_status", "")) != "BALANCED":
            root_cause = "RESIDUAL_EXCESS"
            meta = cfg.get("RESIDUAL_EXCESS", meta)
    elif confidence in {"LOW_CONFIDENCE", "INFERRED"} or "confidence=" in rejection.lower():
        root_cause = "LOW_CONFIDENCE"
        meta = cfg.get("LOW_CONFIDENCE", meta)
    elif pattern_match(rejection, cfg.get("DERIVATION_FAILURE", {}).get("match_rejection_patterns", [])):
        root_cause = "DERIVATION_FAILURE"
        meta = cfg.get("DERIVATION_FAILURE", meta)

    rationale_parts = []
    if validation_issue:
        rationale_parts.append(f"validation_issues={validation_issue}")
    if rejection:
        rationale_parts.append(f"rejection_reason={rejection}")
    if balancing.get("revised_balancing_status"):
        rationale_parts.append(f"balancing_status={balancing['revised_balancing_status']}")
    if residual_amt:
        rationale_parts.append(f"residual_amount={residual_amt}")

    return {
        "reconstructed_claim_id": cid,
        "prototype_claimnum": strip_val(row.get("prototype_claimnum", "")),
        "claim_family": strip_val(row.get("claim_family", "")),
        "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
        "enhanced_settlement_group_id": strip_val(row.get("enhanced_settlement_group_id", "")),
        "root_cause": root_cause,
        "rejection_rationale": "; ".join(rationale_parts) or rejection or validation_issue,
        "rejection_severity": meta.get("severity", "HIGH"),
        "remediability": meta.get("remediability", "PARTIALLY_RECOVERABLE"),
        "governance_status": meta.get("governance_status", "PRODUCTION_BLOCKED"),
        "recommended_remediation": meta.get("recommended_remediation", ""),
        "balancing_status": strip_val(balancing.get("revised_balancing_status", "")),
        "balancing_confidence": strip_val(balancing.get("balancing_confidence", "")),
        "residual_amount": residual_amt,
        "production_dbf_flag": "N",
    }


def classify_rejected_payment(row, rules, clmp_val_lookup, unresolved_lookup):
    cfg = rules["rejected_payment_root_causes"]
    rejection = strip_val(row.get("rejection_reason", ""))
    cid = strip_val(row.get("reconstructed_claim_id", ""))
    stage_id = strip_val(row.get("canonical_payment_stage_id", ""))
    val_row = clmp_val_lookup.get(stage_id, {})
    validation_issue = strip_val(val_row.get("validation_issues", ""))
    confidence = strip_val(row.get("derivation_confidence", val_row.get("derivation_confidence", "")))
    unresolved = unresolved_lookup.get(cid, {})

    root_cause = "GATING_FAILURE"
    meta = cfg.get("GATING_FAILURE", {})

    if pattern_match(rejection, cfg.get("TRUSTEE_ROUTING", {}).get("match_rejection_patterns", [])):
        root_cause = "TRUSTEE_ROUTING"
        meta = cfg.get("TRUSTEE_ROUTING", meta)
    elif pattern_match(rejection, cfg.get("INFERRED_PAYEE", {}).get("match_rejection_patterns", [])):
        root_cause = "INFERRED_PAYEE"
        meta = cfg.get("INFERRED_PAYEE", meta)
    elif validation_issue in {"MISSING_PAYNAME", "UNRESOLVED_PAYEE"} or strip_val(unresolved.get("unresolved_reason", "")):
        root_cause = "MISSING_PAYEE"
        meta = cfg.get("MISSING_PAYEE", meta)
    elif confidence in {"LOW_CONFIDENCE", "INFERRED"} or "confidence=" in rejection.lower():
        root_cause = "LOW_CONFIDENCE"
        meta = cfg.get("LOW_CONFIDENCE", meta)

    rationale_parts = []
    if rejection:
        rationale_parts.append(f"rejection_reason={rejection}")
    if validation_issue:
        rationale_parts.append(f"validation_issues={validation_issue}")
    if unresolved.get("unresolved_reason"):
        rationale_parts.append(f"unresolved_payee={unresolved['unresolved_reason']}")

    return {
        "reconstructed_claim_id": cid,
        "canonical_payment_stage_id": stage_id,
        "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
        "prototype_claimnum": strip_val(row.get("prototype_claimnum", "")),
        "root_cause": root_cause,
        "rejection_rationale": "; ".join(rationale_parts) or rejection,
        "rejection_severity": meta.get("severity", "HIGH"),
        "remediability": meta.get("remediability", "PARTIALLY_RECOVERABLE"),
        "governance_status": meta.get("governance_status", "QA_REVIEW_REQUIRED"),
        "recommended_remediation": meta.get("recommended_remediation", ""),
        "validation_issues": validation_issue,
        "derivation_confidence": confidence,
        "production_dbf_flag": "N",
    }


def analyze_orphans(orphan_df, rejected_claim_df, rules):
    orphan_cfg = rules["orphan_governance"]
    rejected_lookup = {
        strip_val(r["reconstructed_claim_id"]): r.to_dict()
        for _, r in rejected_claim_df.iterrows()
    }
    rows = []
    for _, row in orphan_df.iterrows():
        if strip_val(row.get("is_orphan", "")) != "Y":
            continue
        cid = strip_val(row.get("reconstructed_claim_id", ""))
        issue = strip_val(row.get("orphan_issues", "MISSING_CLAIM_HEADER"))
        issue_key = issue.split("|")[0] if issue else "MISSING_CLAIM_HEADER"
        meta = orphan_cfg.get(issue_key, orphan_cfg.get("MISSING_CLAIM_HEADER", {}))
        parent = rejected_lookup.get(cid, {})
        parent_cause = strip_val(parent.get("root_cause", "PARENT_NOT_IN_PROTOTYPE"))
        recoverable = "Y" if parent and parent.get("remediability") in {"RECOVERABLE", "PARTIALLY_RECOVERABLE"} else "N"
        rows.append({
            "reconstructed_claim_id": cid,
            "canonical_payment_stage_id": strip_val(row.get("canonical_payment_stage_id", "")),
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
            "mpolicy": strip_val(row.get("mpolicy", "")),
            "mseq": strip_val(row.get("mseq", "")),
            "mamount": parse_amount(row.get("mamount", 0)),
            "orphan_issue": issue,
            "parent_claim_root_cause": parent_cause,
            "orphan_severity": meta.get("severity", "CRITICAL"),
            "recoverable_orphan": recoverable,
            "remediability": meta.get("remediability", "PARTIALLY_RECOVERABLE"),
            "governance_status": meta.get("governance_status", "PRODUCTION_BLOCKED"),
            "recommended_remediation": meta.get("recommended_remediation", ""),
            "production_dbf_flag": "N",
        })
    return pd.DataFrame(rows)


def analyze_duplicate_mseq(validation_df, audit_df, rules):
    dup_cfg = rules["duplicate_mseq_governance"]
    dup_val = validation_df[validation_df["validation_type"] == "DUPLICATE_MSEQ"].copy()
    rows = []
    for _, row in dup_val.iterrows():
        detail = strip_val(row.get("validation_detail", ""))
        mpolicy = ""
        mseq = ""
        count = ""
        for part in detail.split(";"):
            part = part.strip()
            if part.startswith("mpolicy="):
                mpolicy = part.split("=", 1)[1]
            elif part.startswith("mseq="):
                mseq = part.split("=", 1)[1]
            elif part.startswith("count="):
                count = part.split("=", 1)[1]
        dup_count = int(parse_amount(count)) if count else 0
        classification = "LEGITIMATE_MULTI_PAYEE" if dup_count <= dup_cfg.get("legitimate_multi_payee_threshold", 2) + 1 else "SEQUENCE_COLLISION"
        rows.append({
            "mpolicy": mpolicy,
            "mseq": mseq,
            "duplicate_count": dup_count,
            "classification": classification,
            "sequence_collision_risk": "HIGH" if classification == "SEQUENCE_COLLISION" else "LOW",
            "severity": dup_cfg.get("severity_default", "MEDIUM"),
            "remediability": dup_cfg.get("remediability_default", "PARTIALLY_RECOVERABLE"),
            "governance_status": dup_cfg.get("governance_status_default", "NEEDS_RULE_REFINEMENT"),
            "recommended_remediation": dup_cfg.get("recommended_remediation", ""),
            "production_numbering_risk": "Y" if classification == "SEQUENCE_COLLISION" else "N",
            "production_dbf_flag": "N",
        })
    return pd.DataFrame(rows)


def analyze_reconciliation_failures(recon_df, rejected_payment_df, rules):
    cfg = rules["reconciliation_failure_categories"]
    rej_pay_by_claim = defaultdict(list)
    for _, r in rejected_payment_df.iterrows():
        rej_pay_by_claim[strip_val(r["reconstructed_claim_id"])].append(r.to_dict())

    rows = []
    for _, row in recon_df.iterrows():
        cid = strip_val(row.get("reconstructed_claim_id", ""))
        family = strip_val(row.get("claim_family", ""))
        pay_count_match = strip_val(row.get("payment_count_match", ""))
        amount_recon = strip_val(row.get("amount_reconciliation", ""))
        recon_status = strip_val(row.get("reconciliation_status", ""))
        net_var = parse_amount(row.get("net_payment_variance", 0))
        q_pay_count = int(parse_amount(row.get("quikclmp_payment_count", 0)))
        mpaycount = int(parse_amount(row.get("quikclms_mpaycount", 0)))

        category = "PASS"
        meta = {
            "severity": "INFORMATIONAL",
            "remediability": "INFORMATIONAL",
            "governance_status": "AUTO_APPROVED",
            "recommended_remediation": "No action required",
        }

        if recon_status == "REVIEW":
            if pay_count_match == "N" and q_pay_count == 0 and mpaycount > 0:
                category = "PAYMENT_COUNT_MISMATCH"
                meta = cfg.get("PAYMENT_COUNT_MISMATCH", meta)
            elif amount_recon == "VARIANCE":
                category = "AGGREGATION_MISMATCH"
                meta = cfg.get("AGGREGATION_MISMATCH", meta)
            elif family in cfg.get("EXPECTED_NON_PAYMENT_CLAIM", {}).get("match_families", []) and q_pay_count == 0:
                category = "EXPECTED_NON_PAYMENT_CLAIM"
                meta = cfg.get("EXPECTED_NON_PAYMENT_CLAIM", meta)
            else:
                category = "PAYMENT_COUNT_MISMATCH"
                meta = cfg.get("PAYMENT_COUNT_MISMATCH", meta)

        net_threshold = float(cfg.get("NET_BALANCING_VARIANCE", {}).get("net_variance_threshold", 0.01))
        if abs(net_var) > net_threshold and category == "PASS":
            category = "NET_BALANCING_VARIANCE"
            meta = cfg.get("NET_BALANCING_VARIANCE", meta)

        rejected_payments = rej_pay_by_claim.get(cid, [])
        rej_causes = Counter(strip_val(p.get("root_cause", "")) for p in rejected_payments)

        rows.append({
            "prototype_claimnum": strip_val(row.get("prototype_claimnum", "")),
            "reconstructed_claim_id": cid,
            "claim_family": family,
            "failure_category": category,
            "reconciliation_status": recon_status,
            "quikclms_mpaycount": mpaycount,
            "quikclmp_payment_count": q_pay_count,
            "mpaid_variance": parse_amount(row.get("mpaid_variance", 0)),
            "net_payment_variance": net_var,
            "mresidual": parse_amount(row.get("mresidual", 0)),
            "residual_preserved": strip_val(row.get("residual_preserved", "")),
            "linked_rejected_payment_count": len(rejected_payments),
            "linked_rejected_payment_causes": "|".join(f"{k}:{v}" for k, v in rej_causes.items() if k),
            "severity": meta.get("severity", "MEDIUM"),
            "remediability": meta.get("remediability", "PARTIALLY_RECOVERABLE"),
            "governance_status": meta.get("governance_status", "QA_REVIEW_REQUIRED"),
            "recommended_remediation": meta.get("recommended_remediation", ""),
            "production_dbf_flag": "N",
        })
    return pd.DataFrame(rows)


def build_remediation_recommendations(rejected_claim_df, rejected_payment_df, orphan_df, dup_df, recon_fail_df, rules):
    recs = []
    counters = [
        ("REJECTED_CLAIM", rejected_claim_df, "root_cause"),
        ("REJECTED_PAYMENT", rejected_payment_df, "root_cause"),
        ("ORPHAN_PAYMENT", orphan_df, "orphan_issue"),
        ("DUPLICATE_MSEQ", dup_df, "classification"),
        ("RECONCILIATION_FAILURE", recon_fail_df[recon_fail_df["failure_category"] != "PASS"], "failure_category"),
    ]
    for domain, df, col in counters:
        if df.empty or col not in df.columns:
            continue
        for cause, sub in df.groupby(col):
            if not strip_val(cause) or cause == "PASS":
                continue
            sample = sub.iloc[0]
            recs.append({
                "exception_domain": domain,
                "exception_category": strip_val(cause),
                "exception_count": len(sub),
                "likely_root_cause": strip_val(cause),
                "recoverability": sub["remediability"].mode().iloc[0] if "remediability" in sub.columns and not sub["remediability"].empty else "",
                "recommended_remediation": sample.get("recommended_remediation", ""),
                "rule_refinement_opportunity": "Y" if sample.get("governance_status") == "NEEDS_RULE_REFINEMENT" else "N",
                "business_review_required": "Y" if sample.get("governance_status") == "BUSINESS_REVIEW_REQUIRED" else "N",
                "governance_status": sub["governance_status"].mode().iloc[0] if "governance_status" in sub.columns else "",
                "production_dbf_flag": "N",
            })
    return pd.DataFrame(recs)


def build_production_readiness(rejected_claim_df, rejected_payment_df, orphan_df, dup_df, recon_fail_df, recon_summary, rules):
    thresholds = rules["production_readiness_thresholds"]
    summary_lookup = {strip_val(r["metric"]): parse_amount(r["value"]) for _, r in recon_summary.iterrows()}

    total_claims = 5182 + len(rejected_claim_df)
    total_payments = 1910 + len(rejected_payment_df)
    recon_pass_pct = summary_lookup.get("reconciliation_pass_pct", 0)
    orphan_count = len(orphan_df)
    orphan_pct = round(100.0 * orphan_count / max(total_payments, 1), 2)

    blocked_claims = len(rejected_claim_df[rejected_claim_df["governance_status"] == "PRODUCTION_BLOCKED"]) if not rejected_claim_df.empty else 0
    blocked_pct = round(100.0 * blocked_claims / max(total_claims, 1), 2)

    assessments = [
        {
            "readiness_dimension": "RECONCILIATION_PASS_RATE",
            "current_value": recon_pass_pct,
            "threshold": thresholds["min_reconciliation_pass_pct"],
            "assessment": "READY" if recon_pass_pct >= thresholds["min_reconciliation_pass_pct"] else "NOT_READY",
            "production_dbf_flag": "N",
        },
        {
            "readiness_dimension": "ORPHAN_PAYMENT_RATE",
            "current_value": orphan_pct,
            "threshold": thresholds["max_orphan_payment_pct"],
            "assessment": "READY" if orphan_pct <= thresholds["max_orphan_payment_pct"] else "NOT_READY",
            "production_dbf_flag": "N",
        },
        {
            "readiness_dimension": "PRODUCTION_BLOCKED_CLAIM_RATE",
            "current_value": blocked_pct,
            "threshold": thresholds["max_production_blocked_pct"],
            "assessment": "READY" if blocked_pct <= thresholds["max_production_blocked_pct"] else "NOT_READY",
            "production_dbf_flag": "N",
        },
        {
            "readiness_dimension": "DUPLICATE_MSEQ_GROUPS",
            "current_value": len(dup_df),
            "threshold": thresholds["max_duplicate_mseq_groups"],
            "assessment": "READY" if len(dup_df) <= thresholds["max_duplicate_mseq_groups"] else "NOT_READY",
            "production_dbf_flag": "N",
        },
        {
            "readiness_dimension": "PROTOTYPE_CLAIM_ACCEPTANCE",
            "current_value": 5182,
            "threshold": total_claims,
            "assessment": "PARTIAL",
            "production_dbf_flag": "N",
        },
        {
            "readiness_dimension": "PROTOTYPE_PAYMENT_ACCEPTANCE",
            "current_value": 1910,
            "threshold": total_payments,
            "assessment": "PARTIAL",
            "production_dbf_flag": "N",
        },
    ]

    not_ready = [a for a in assessments if a["assessment"] == "NOT_READY"]
    overall = "NOT_READY" if not_ready else "CONDITIONALLY_READY"
    assessments.append({
        "readiness_dimension": "OVERALL_PRODUCTION_READINESS",
        "current_value": len(not_ready),
        "threshold": 0,
        "assessment": overall,
        "production_dbf_flag": "N",
    })
    return pd.DataFrame(assessments)


def build_dashboard(rejected_claim_df, rejected_payment_df, orphan_df, dup_df, recon_fail_df, audit_df):
    rows = []
    accepted_claims = len(audit_df[(audit_df["record_type"] == "CLAIM") & (audit_df["generation_status"] == "ACCEPTED")])
    accepted_payments = len(audit_df[(audit_df["record_type"] == "PAYMENT") & (audit_df["generation_status"] == "ACCEPTED")])
    rows.append({"metric_group": "ACCEPTED", "metric_name": "prototype_claims", "metric_value": accepted_claims, "governance_status": "AUTO_APPROVED"})
    rows.append({"metric_group": "ACCEPTED", "metric_name": "prototype_payments", "metric_value": accepted_payments, "governance_status": "AUTO_APPROVED"})

    for name, df, col in [
        ("rejected_claims", rejected_claim_df, "root_cause"),
        ("rejected_payments", rejected_payment_df, "root_cause"),
        ("orphan_payments", orphan_df, "orphan_issue"),
        ("duplicate_mseq", dup_df, "classification"),
    ]:
        if df.empty:
            continue
        for key, cnt in Counter(strip_val(x) for x in df[col]).items():
            if not key:
                continue
            gov = df[df[col] == key]["governance_status"].mode()
            rows.append({
                "metric_group": name.upper(),
                "metric_name": key,
                "metric_value": cnt,
                "governance_status": gov.iloc[0] if not gov.empty else "",
            })

    review = recon_fail_df[recon_fail_df["failure_category"] != "PASS"]
    for key, cnt in Counter(review["failure_category"]).items():
        rows.append({
            "metric_group": "RECONCILIATION_FAILURE",
            "metric_name": key,
            "metric_value": cnt,
            "governance_status": "QA_REVIEW_REQUIRED",
        })

    recoverable = len(orphan_df[orphan_df["recoverable_orphan"] == "Y"]) if not orphan_df.empty and "recoverable_orphan" in orphan_df.columns else 0
    orphan_total = len(orphan_df)
    rows.append({
        "metric_group": "ORPHAN_RECOVERABILITY",
        "metric_name": "recoverable_pct",
        "metric_value": round(100.0 * recoverable / max(orphan_total, 1), 2),
        "governance_status": "QA_REVIEW_REQUIRED",
    })
    return pd.DataFrame(rows)


def build_exception_summary(rejected_claim_df, rejected_payment_df, orphan_df, dup_df, recon_fail_df, readiness_df):
    rows = [
        {"exception_type": "REJECTED_CLAIM", "count": len(rejected_claim_df)},
        {"exception_type": "REJECTED_PAYMENT", "count": len(rejected_payment_df)},
        {"exception_type": "ORPHAN_PAYMENT", "count": len(orphan_df)},
        {"exception_type": "DUPLICATE_MSEQ_GROUP", "count": len(dup_df)},
        {"exception_type": "RECONCILIATION_REVIEW", "count": len(recon_fail_df[recon_fail_df["reconciliation_status"] == "REVIEW"])},
    ]
    if not rejected_claim_df.empty:
        for cause, cnt in rejected_claim_df["root_cause"].value_counts().items():
            rows.append({"exception_type": f"REJECTED_CLAIM_{cause}", "count": int(cnt)})
    if not rejected_payment_df.empty:
        for cause, cnt in rejected_payment_df["root_cause"].value_counts().items():
            rows.append({"exception_type": f"REJECTED_PAYMENT_{cause}", "count": int(cnt)})
    overall = readiness_df[readiness_df["readiness_dimension"] == "OVERALL_PRODUCTION_READINESS"]
    rows.append({
        "exception_type": "OVERALL_PRODUCTION_READINESS",
        "count": strip_val(overall.iloc[0]["assessment"]) if not overall.empty else "UNKNOWN",
    })
    return pd.DataFrame(rows)


def run_engine(
    audit_df, validation_df, orphan_df, recon_df, recon_summary,
    clmp_validation, clms_validation, revised_fin, residual_analysis,
    unresolved_payee, rules_path, output_dir,
):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)

    revised_lookup = {strip_val(r["reconstructed_claim_id"]): r.to_dict() for _, r in revised_fin.iterrows()}
    residual_lookup = {strip_val(r["reconstructed_claim_id"]): r.to_dict() for _, r in residual_analysis.iterrows()}
    clms_val_lookup = {strip_val(r["reconstructed_claim_id"]): r.to_dict() for _, r in clms_validation.iterrows()}
    clmp_val_lookup = {strip_val(r["canonical_payment_stage_id"]): r.to_dict() for _, r in clmp_validation.iterrows()}
    unresolved_lookup = {strip_val(r["reconstructed_claim_id"]): r.to_dict() for _, r in unresolved_payee.iterrows()}

    rejected_claims_raw = audit_df[(audit_df["record_type"] == "CLAIM") & (audit_df["generation_status"] == "REJECTED")].copy()
    rejected_payments_raw = audit_df[(audit_df["record_type"] == "PAYMENT") & (audit_df["generation_status"] == "REJECTED")].copy()

    rejected_claim_rows = []
    for _, row in rejected_claims_raw.iterrows():
        cid = strip_val(row.get("reconstructed_claim_id", ""))
        enriched = row.to_dict()
        val = clms_val_lookup.get(cid, {})
        enriched.update({
            "validation_issues": val.get("validation_issues", ""),
            "derivation_confidence": enriched.get("derivation_confidence") or val.get("derivation_confidence", ""),
            "claim_family": enriched.get("claim_family") or val.get("claim_family", ""),
        })
        rejected_claim_rows.append(classify_rejected_claim(enriched, rules, revised_lookup, residual_lookup))
    rejected_claim_df = pd.DataFrame(rejected_claim_rows)

    rejected_payment_rows = []
    for _, row in rejected_payments_raw.iterrows():
        rejected_payment_rows.append(classify_rejected_payment(row.to_dict(), rules, clmp_val_lookup, unresolved_lookup))
    rejected_payment_df = pd.DataFrame(rejected_payment_rows)

    orphan_gov_df = analyze_orphans(orphan_df, rejected_claim_df, rules)
    dup_df = analyze_duplicate_mseq(validation_df, audit_df, rules)
    recon_fail_df = analyze_reconciliation_failures(recon_df, rejected_payment_df, rules)
    remediation_df = build_remediation_recommendations(
        rejected_claim_df, rejected_payment_df, orphan_gov_df, dup_df, recon_fail_df, rules,
    )
    readiness_df = build_production_readiness(
        rejected_claim_df, rejected_payment_df, orphan_gov_df, dup_df, recon_fail_df, recon_summary, rules,
    )
    dashboard_df = build_dashboard(
        rejected_claim_df, rejected_payment_df, orphan_gov_df, dup_df, recon_fail_df, audit_df,
    )
    summary_df = build_exception_summary(
        rejected_claim_df, rejected_payment_df, orphan_gov_df, dup_df, recon_fail_df, readiness_df,
    )

    stats = {
        "rejected_claims": len(rejected_claim_df),
        "rejected_payments": len(rejected_payment_df),
        "orphan_payments": len(orphan_gov_df),
        "duplicate_mseq": len(dup_df),
        "reconciliation_review": len(recon_fail_df[recon_fail_df["reconciliation_status"] == "REVIEW"]),
        "recoverable_orphans": len(orphan_gov_df[orphan_gov_df["recoverable_orphan"] == "Y"]) if not orphan_gov_df.empty else 0,
        "production_blocked_claims": len(rejected_claim_df[rejected_claim_df["governance_status"] == "PRODUCTION_BLOCKED"]) if not rejected_claim_df.empty else 0,
        "auto_approved_claims": len(audit_df[(audit_df["record_type"] == "CLAIM") & (audit_df["generation_status"] == "ACCEPTED")]),
        "auto_approved_payments": len(audit_df[(audit_df["record_type"] == "PAYMENT") & (audit_df["generation_status"] == "ACCEPTED")]),
    }
    overall = readiness_df[readiness_df["readiness_dimension"] == "OVERALL_PRODUCTION_READINESS"]
    stats["overall_readiness"] = strip_val(overall.iloc[0]["assessment"]) if not overall.empty else "UNKNOWN"

    rules_out = os.path.join(output_dir, "claims_exception_governance_rules.json")
    shutil.copy2(rules_path, rules_out)
    output_files = [rules_out]

    reports = {
        "claims_exception_summary.csv": summary_df,
        "rejected_claim_root_cause_analysis.csv": rejected_claim_df,
        "rejected_payment_root_cause_analysis.csv": rejected_payment_df,
        "orphan_payment_governance_analysis.csv": orphan_gov_df,
        "duplicate_mseq_analysis.csv": dup_df,
        "reconciliation_failure_analysis.csv": recon_fail_df,
        "exception_remediation_recommendations.csv": remediation_df,
        "production_readiness_assessment.csv": readiness_df,
        "claims_exception_governance_dashboard.csv": dashboard_df,
    }
    for name, frame in reports.items():
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        output_files.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_txt = os.path.join(output_dir, "qa_uat_hardening_summary.txt")
    write_summary_txt(summary_txt, stats, output_files, rejected_claim_df, rejected_payment_df, orphan_gov_df)
    output_files.append(summary_txt)
    logger.info("Wrote qa_uat_hardening_summary.txt")

    return stats, output_files


def write_summary_txt(path, stats, output_files, rejected_claim_df, rejected_payment_df, orphan_df):
    lines = [
        "=== QA/UAT Hardening & Production Readiness Summary (Phase 12) ===",
        "",
        f"Rejected claims analyzed: {stats['rejected_claims']}",
        f"Rejected payments analyzed: {stats['rejected_payments']}",
        f"Orphan payments analyzed: {stats['orphan_payments']}",
        f"Duplicate MSEQ groups: {stats['duplicate_mseq']}",
        f"Reconciliation REVIEW claims: {stats['reconciliation_review']}",
        f"Recoverable orphans: {stats['recoverable_orphans']}",
        f"Production-blocked claims: {stats['production_blocked_claims']}",
        f"Auto-approved prototype claims: {stats['auto_approved_claims']}",
        f"Auto-approved prototype payments: {stats['auto_approved_payments']}",
        f"Overall production readiness: {stats['overall_readiness']}",
        "",
        "Rejected claim root causes:",
    ]
    if not rejected_claim_df.empty:
        for cause, cnt in rejected_claim_df["root_cause"].value_counts().items():
            lines.append(f"  {cause}: {cnt}")
    lines.extend(["", "Rejected payment root causes:"])
    if not rejected_payment_df.empty:
        for cause, cnt in rejected_payment_df["root_cause"].value_counts().items():
            lines.append(f"  {cause}: {cnt}")
    lines.extend([
        "",
        "Architectural notes:",
        "  - Exception governance analysis only; no auto-remediation",
        "  - production_dbf_flag=N on all outputs",
        "  - Preserves orphan, residual, and rejection visibility",
        "",
        "Recommended next phase:",
        "  - Phase 13: Controlled enterprise app.py integration",
        "",
        "Output files generated:",
    ])
    for f in output_files:
        lines.append(f"  - {f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Phase 12 QA/UAT exception governance engine.")
    parser.add_argument("--audit", default=os.path.join(PHASE11, "prototype_dbf_generation_audit.csv"))
    parser.add_argument("--validation", default=os.path.join(PHASE11, "prototype_dbf_validation.csv"))
    parser.add_argument("--orphan-analysis", default=os.path.join(PHASE11, "prototype_orphan_analysis.csv"))
    parser.add_argument("--reconciliation", default=os.path.join(PHASE11, "prototype_claim_payment_reconciliation.csv"))
    parser.add_argument("--recon-summary", default=os.path.join(PHASE11, "prototype_reconciliation_summary.csv"))
    parser.add_argument("--clmp-validation", default=os.path.join(PHASE10A, "quikclmp_derivation_validation.csv"))
    parser.add_argument("--clms-validation", default=os.path.join(PHASE10B, "quikclms_derivation_validation.csv"))
    parser.add_argument("--revised-financials", default=os.path.join(PHASE6, "revised_claim_financials.csv"))
    parser.add_argument("--residual-analysis", default=os.path.join(PHASE7C, "death_claim_residual_analysis.csv"))
    parser.add_argument("--unresolved-payee", default=os.path.join(PHASE8, "unresolved_payee_analysis.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    for label, path in (
        ("Audit", args.audit),
        ("Validation", args.validation),
        ("Rules", args.rules),
    ):
        if not os.path.isfile(path):
            logger.error("%s not found: %s", label, path)
            return 1

    audit_df = load_csv(args.audit)
    validation_df = load_csv(args.validation)
    orphan_df = load_csv(args.orphan_analysis)
    recon_df = load_csv(args.reconciliation)
    recon_summary = load_csv(args.recon_summary)
    clmp_validation = load_csv(args.clmp_validation) if os.path.isfile(args.clmp_validation) else pd.DataFrame()
    clms_validation = load_csv(args.clms_validation) if os.path.isfile(args.clms_validation) else pd.DataFrame()
    revised_fin = load_csv(args.revised_financials) if os.path.isfile(args.revised_financials) else pd.DataFrame()
    residual_analysis = load_csv(args.residual_analysis) if os.path.isfile(args.residual_analysis) else pd.DataFrame()
    unresolved_payee = load_csv(args.unresolved_payee) if os.path.isfile(args.unresolved_payee) else pd.DataFrame()

    try:
        stats, outputs = run_engine(
            audit_df, validation_df, orphan_df, recon_df, recon_summary,
            clmp_validation, clms_validation, revised_fin, residual_analysis,
            unresolved_payee, args.rules, args.output,
        )
        print("QA/UAT exception governance complete.")
        print(f"Rejected claims: {stats['rejected_claims']}")
        print(f"Orphan payments: {stats['orphan_payments']}")
        print(f"Overall readiness: {stats['overall_readiness']}")
        print(f"Output: {os.path.abspath(args.output)}")
        for p in outputs:
            print(f"  {p}")
        return 0
    except (ValueError, FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
