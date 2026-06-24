"""Phase 24 — Client balancing re-run (Item 16 dividend-on-deposit exclusion).

Re-evaluates Phase 23 rebalance-pending unbalanced death claims using
client-authorized GL exclusions (2023 / 603703R) sourced from PACTG account
fields on each claim activity window, with lifecycle 0038 clearing fallback.

Promotes BALANCED and MINOR_VARIANCE claims into post-rebalance UAT candidate
populations. Does NOT modify Phase 4-17 engines, Phase 6 engine, or app.py.
production_dbf_flag remains N.
"""

import json
import os
import shutil
from datetime import datetime, timezone

import pandas as pd

ROOT = r"C:\Users\warren\Documents\GitHub\Warrenhughes1974"
CONFIG_PATH = os.path.join(ROOT, "claims_analysis", "config", "client_issue_log_decision_rules.json")
RULES_PATH = os.path.join(ROOT, "claims_analysis", "config", "claim_family_balancing_rules_client.json")
P23_DIR = os.path.join(ROOT, "claims_analysis", "phase23_client_decision_application")
P4_DIR = os.path.join(ROOT, "claims_analysis", "phase4_claim_event_reconstruction")
P15_CROSSWALK = os.path.join(
    ROOT, "claims_analysis", "phase15_qa_signoff_replay_execution", "phase15_claimnum_crosswalk.csv"
)
PACTG_PATH = os.path.join(ROOT, "QLA_Migration", "Source", "PACTG_Accounting_Extract20260427.csv")
OUT_DIR = os.path.join(ROOT, "claims_analysis", "phase24_client_balancing_rerun")

TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
SNAP = "PHASE24-CLIENT-BALANCING-RERUN-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LINEAGE = "phase23_client_decision_application|phase24_client_balancing_rerun"
PROD_FLAG = "N"
BALANCE_TOLERANCE = 0.01
MINOR_VARIANCE = 100.0

PAYOUT_CODES = {"0094", "0567", "1900"}
GROSS_CODES = {"0530", "0519"}
OFFSET_CODES = {"0411", "0412"}


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


def format_code(value):
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if not digits:
        return ""
    return str(int(digits)).zfill(4)


def balancing_status(diff):
    ad = abs(diff)
    if ad <= BALANCE_TOLERANCE:
        return "BALANCED"
    if ad <= MINOR_VARIANCE:
        return "MINOR_VARIANCE"
    return "UNBALANCED"


def is_div_on_dep_row(row):
    credit_account = str(row.get("CREDIT_ACCOUNT", "")).strip()
    debit_account = str(row.get("DEBIT_ACCOUNT", "")).strip()
    credit_code = str(row.get("CREDIT_CODE", "")).strip()
    debit_code = str(row.get("DEBIT_CODE", "")).strip()

    if "603703" in debit_account or "603703" in credit_account:
        return True
    if credit_code in ("38", "038") and (
        debit_account.startswith("2023") or credit_account.startswith("2023")
    ):
        return True
    if debit_code == "310" and credit_code in ("38", "038") and (
        debit_account.startswith("2023") or credit_account.startswith("2023")
    ):
        return True
    return False


def load_pactg_for_policies(policy_numbers):
    cols = [
        "POLICY_NUMBER",
        "EFFECTIVE_DATE",
        "CREDIT_CODE",
        "DEBIT_CODE",
        "CREDIT_ACCOUNT",
        "DEBIT_ACCOUNT",
        "TRANS_AMOUNT     ",
    ]
    chunks = []
    for chunk in pd.read_csv(
        PACTG_PATH,
        usecols=cols,
        dtype=str,
        encoding="latin-1",
        chunksize=250000,
    ):
        chunk["POLICY_NUMBER"] = chunk["POLICY_NUMBER"].astype(str).str.strip()
        mask = chunk["POLICY_NUMBER"].isin(policy_numbers)
        if mask.any():
            chunks.append(chunk.loc[mask].copy())
    if not chunks:
        return pd.DataFrame(columns=cols)
    pactg = pd.concat(chunks, ignore_index=True)
    pactg["effective_date"] = pactg["EFFECTIVE_DATE"].astype(str).str.strip()
    pactg["trans_amount_parsed"] = pactg["TRANS_AMOUNT     "].apply(parse_amount)
    return pactg


def pactg_div_on_dep_exclusion(pactg, policy_number, date_from, date_to):
    sub = pactg[
        (pactg["POLICY_NUMBER"] == policy_number)
        & (pactg["effective_date"] >= date_from)
        & (pactg["effective_date"] <= date_to)
    ]
    total = 0.0
    matched_rows = 0
    for _, row in sub.iterrows():
        if is_div_on_dep_row(row):
            total += row["trans_amount_parsed"]
            matched_rows += 1
    return round(total, 2), matched_rows


def lifecycle_amounts(lifecycle, claim_id):
    sub = lifecycle[lifecycle["reconstructed_claim_id"] == claim_id].copy()
    sub["code"] = sub["source_transaction_code"].apply(format_code)
    sub["amount"] = sub["trans_amount"].apply(parse_amount)

    gross = round(float(sub.loc[sub["code"].isin(GROSS_CODES), "amount"].sum()), 2)
    interest = round(float(sub.loc[sub["code"] == "0630", "amount"].sum()), 2)
    offsets = round(float(sub.loc[sub["code"].isin(OFFSET_CODES), "amount"].sum()), 2)
    payout = round(float(sub.loc[sub["code"].isin(PAYOUT_CODES), "amount"].sum()), 2)
    clearing = round(float(sub.loc[sub["code"] == "0038", "amount"].sum()), 2)
    net = round(gross + interest - offsets, 2)
    return {
        "gross": gross,
        "interest": interest,
        "loan_offsets": offsets,
        "payout": payout,
        "clearing_0038": clearing,
        "net_payment": net,
    }


def next_claimnum_factory(crosswalk, uat_clms):
    nums = []
    for series in (crosswalk["prototype_claimnum"], uat_clms["prototype_claimnum"]):
        for value in series.dropna():
            value = str(value).strip()
            if value.startswith("CLM") and value[3:].isdigit():
                nums.append(int(value[3:]))
    counter = {"n": max(nums) if nums else 0}

    def make():
        counter["n"] += 1
        return "CLM%07d" % counter["n"]

    return make


def lookup_claimnum(crosswalk_map, claim_id, make_new):
    existing = crosswalk_map.get(claim_id)
    if existing and str(existing).strip().startswith("CLM"):
        return str(existing).strip(), "PHASE15_CROSSWALK"
    return make_new(), "PHASE24_ASSIGNED"


def base_clms_row(claim_id, claimnum, segment, explanation):
    return {
        "audit_timestamp": TS,
        "rollback_snapshot_id": SNAP,
        "production_dbf_flag": PROD_FLAG,
        "record_type": "QUIKCLMS",
        "reconstructed_claim_id": claim_id,
        "prototype_claimnum": claimnum,
        "derivation_candidate_id": "QDC-" + claim_id,
        "replay_source": "CLIENT_DECISION",
        "uat_segment": segment,
        "governance_status": "UAT_CLEARED",
        "business_review_required": "N",
        "replay_authorization_status": "CLIENT_AUTHORIZED",
        "reconciliation_status": "CLIENT_ACCEPTED",
        "generation_status": "ACCEPTED",
        "blocker_category": "NONE",
        "business_explanation": explanation,
        "orphan_impact": "NONE",
        "reconciliation_impact": "CLIENT_ACCEPTED",
        "replay_eligibility": "UAT_READY",
        "remediation_recommendation": "NONE",
        "rulebook_lineage": LINEAGE,
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    with open(CONFIG_PATH, encoding="utf-8") as fh:
        client_cfg = json.load(fh)
    with open(RULES_PATH, encoding="utf-8") as fh:
        rules = json.load(fh)

    pending = pd.read_csv(os.path.join(P23_DIR, "rebalance_pending_unbalanced_claims.csv"), dtype=str)
    refreshed_clms = pd.read_csv(os.path.join(P23_DIR, "uat_candidate_quikclms_refreshed.csv"), dtype=str)
    refreshed_clmp = pd.read_csv(os.path.join(P23_DIR, "uat_candidate_quikclmp_refreshed.csv"), dtype=str)
    headers = pd.read_csv(os.path.join(P4_DIR, "claim_candidate_header.csv"), dtype=str)
    lifecycle = pd.read_csv(os.path.join(P4_DIR, "claim_candidate_lifecycle.csv"), dtype=str)
    crosswalk = pd.read_csv(P15_CROSSWALK, dtype=str)

    lifecycle = lifecycle[~lifecycle["lifecycle_event_type"].eq("CLAIM_SETTLEMENT")].copy()

    claim_ids = set(pending["reconstructed_claim_id"])
    header_sub = headers[headers["reconstructed_claim_id"].isin(claim_ids)].copy()
    policies = set(header_sub["policy_number"].astype(str).str.strip())
    pactg = load_pactg_for_policies(policies)

    crosswalk_map = dict(
        zip(crosswalk["reconstructed_claim_id"], crosswalk["prototype_claimnum"])
    )
    make_new_claimnum = next_claimnum_factory(crosswalk, refreshed_clms)
    uat_claim_ids = set(refreshed_clms["reconstructed_claim_id"])

    before_uat_claims = len(refreshed_clms)
    result_rows = []
    promoted_rows = []
    audit_rows = []

    for _, header in header_sub.iterrows():
        claim_id = header["reconstructed_claim_id"]
        policy_number = str(header["policy_number"]).strip()
        date_from = str(header["first_activity_date"]).strip()
        date_to = str(header["latest_activity_date"]).strip()

        amounts = lifecycle_amounts(lifecycle, claim_id)
        pactg_excl, pactg_rows = pactg_div_on_dep_exclusion(pactg, policy_number, date_from, date_to)
        clearing_excl = amounts["clearing_0038"]
        if pactg_excl > 0:
            div_excl = pactg_excl
            excl_source = "PACTG_GL_2023_603703R"
        elif clearing_excl > 0:
            div_excl = clearing_excl
            excl_source = "LIFECYCLE_0038_FALLBACK"
        else:
            div_excl = 0.0
            excl_source = "NONE"

        adjusted_payout = round(amounts["payout"] - div_excl, 2)
        diff_raw = round(amounts["net_payment"] - amounts["payout"], 2)
        diff_adj = round(amounts["net_payment"] - adjusted_payout, 2)
        status = balancing_status(diff_adj)

        result_rows.append({
            "audit_timestamp": TS,
            "rollback_snapshot_id": SNAP,
            "production_dbf_flag": PROD_FLAG,
            "reconstructed_claim_id": claim_id,
            "policy_number": policy_number,
            "claim_family": header.get("claim_family", "DEATH_CLAIM"),
            "activity_window": f"{date_from}-{date_to}",
            "gross_component": amounts["gross"],
            "interest_component": amounts["interest"],
            "loan_offsets": amounts["loan_offsets"],
            "net_payment": amounts["net_payment"],
            "payout_total": amounts["payout"],
            "clearing_0038_total": clearing_excl,
            "pactg_div_on_dep_excluded": pactg_excl,
            "pactg_div_rows_matched": pactg_rows,
            "div_on_dep_excluded": div_excl,
            "exclusion_source": excl_source,
            "adjusted_payout": adjusted_payout,
            "balancing_difference_raw": diff_raw,
            "balancing_difference_adjusted": diff_adj,
            "rebalance_status": status,
            "rebalance_rule": "EXCLUDE_GL_2023_603703R_FROM_DB_BALANCING",
            "promotion_eligible": "Y" if status in ("BALANCED", "MINOR_VARIANCE") else "N",
            "rulebook_lineage": LINEAGE,
        })

        if status in ("BALANCED", "MINOR_VARIANCE") and claim_id not in uat_claim_ids:
            claimnum, src = lookup_claimnum(crosswalk_map, claim_id, make_new_claimnum)
            explanation = (
                "Client decision Item 16 rebalance: dividend-on-deposit (2023/603703R) excluded "
                f"from DB balancing ({excl_source}); post-adjustment status {status} "
                f"(diff={diff_adj})."
            )
            promoted_rows.append(
                base_clms_row(claim_id, claimnum, "CLIENT_REBALANCE_CLEARED", explanation)
            )
            audit_rows.append({
                "action": "PROMOTED_POST_REBALANCE",
                "entity": claim_id,
                "detail": f"status={status}; diff_adj={diff_adj}; excl={div_excl}; claimnum={claimnum} ({src})",
            })
        elif status in ("BALANCED", "MINOR_VARIANCE"):
            audit_rows.append({
                "action": "ALREADY_IN_UAT",
                "entity": claim_id,
                "detail": f"status={status}; diff_adj={diff_adj}",
            })
        else:
            audit_rows.append({
                "action": "REMAINS_DEFERRED",
                "entity": claim_id,
                "detail": f"status={status}; diff_adj={diff_adj}; excl={div_excl}",
            })

    results_df = pd.DataFrame(result_rows)
    promoted_df = pd.DataFrame(promoted_rows)
    remaining_df = pending[
        pending["reconstructed_claim_id"].isin(
            results_df.loc[results_df["promotion_eligible"] == "N", "reconstructed_claim_id"]
        )
    ].copy()
    remaining_df["rebalance_status"] = "REBALANCE_REMAINING_UNBALANCED"
    remaining_df["audit_timestamp"] = TS
    remaining_df["rollback_snapshot_id"] = SNAP

    cleared_df = results_df[results_df["promotion_eligible"] == "Y"].copy()

    post_clms = refreshed_clms.copy()
    if not promoted_df.empty:
        post_clms = pd.concat(
            [post_clms, promoted_df[post_clms.columns.intersection(promoted_df.columns)]],
            ignore_index=True,
        )

    shutil.copy2(RULES_PATH, os.path.join(OUT_DIR, "claim_family_balancing_rules_client.json"))

    outputs = {
        "client_rebalance_results.csv": results_df,
        "rebalance_promoted_claims.csv": promoted_df,
        "rebalance_cleared_claims.csv": cleared_df,
        "rebalance_remaining_deferred.csv": remaining_df,
        "uat_candidate_quikclms_post_rebalance.csv": post_clms,
        "uat_candidate_quikclmp_post_rebalance.csv": refreshed_clmp.copy(),
        "phase24_rebalance_audit_log.csv": pd.DataFrame(audit_rows).assign(
            audit_timestamp=TS,
            rollback_snapshot_id=SNAP,
            production_dbf_flag=PROD_FLAG,
            rulebook_lineage=LINEAGE,
        ),
    }
    for name, frame in outputs.items():
        frame.to_csv(os.path.join(OUT_DIR, name), index=False)

    status_counts = results_df["rebalance_status"].value_counts().to_dict()
    excl_sources = results_df["exclusion_source"].value_counts().to_dict()
    summary_lines = [
        "=== Phase 24 Client Balancing Re-run Summary ===",
        "",
        f"Rollback snapshot: {SNAP}",
        f"Decision source: {client_cfg['source_document']}",
        f"Rules file: {RULES_PATH}",
        "",
        f"Rebalance queue (Phase 23 pending): {len(pending)}",
        f"Post-rebalance status counts: {status_counts}",
        f"Exclusion source counts: {excl_sources}",
        "",
        "BEFORE (Phase 23 refreshed UAT):",
        f"  UAT candidate claims:    {before_uat_claims}",
        "",
        "AFTER (client rebalance promotions):",
        f"  Newly promoted claims:   {len(promoted_df)}",
        f"  Remaining deferred:      {len(remaining_df)}",
        f"  UAT candidate claims:    {len(post_clms)} (+{len(post_clms) - before_uat_claims})",
        "",
        "production_dbf_flag=N — UAT staging artifacts only. No production DBFs.",
        "Phase 4-17 engines NOT modified. app.py NOT modified.",
    ]
    summary_path = os.path.join(OUT_DIR, "phase24_execution_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(summary_lines) + "\n")

    report_lines = [
        "# Phase 24 — Client Balancing Re-run Report",
        "",
        f"**Run date:** {TS[:10]}",
        f"**Rollback snapshot:** `{SNAP}`",
        f"**Authority:** Client Item 16 — exclude `2023` / `603703R` dividend-on-deposit from DB balancing",
        "",
        "## Results",
        "",
        f"| Metric | Count |",
        f"|---|---:|",
        f"| Rebalance queue | {len(pending)} |",
        f"| BALANCED after GL exclusion | {status_counts.get('BALANCED', 0)} |",
        f"| MINOR_VARIANCE after GL exclusion | {status_counts.get('MINOR_VARIANCE', 0)} |",
        f"| Still UNBALANCED | {status_counts.get('UNBALANCED', 0)} |",
        f"| Promoted to UAT | {len(promoted_df)} |",
        f"| Remaining deferred | {len(remaining_df)} |",
        "",
        "## UAT population",
        "",
        f"| Population | Phase 23 refreshed | Post-rebalance | Change |",
        f"|---|---:|---:|---:|",
        f"| UAT candidate claims | {before_uat_claims} | **{len(post_clms)}** | **+{len(post_clms) - before_uat_claims}** |",
        f"| UAT candidate payments | {len(refreshed_clmp)} | {len(refreshed_clmp)} | 0 |",
        "",
        "## Exclusion mechanics",
        "",
        "- Primary: PACTG `CREDIT_ACCOUNT` / `DEBIT_ACCOUNT` rows matching `2023` or `603703R` on claim activity window",
        "- Fallback: lifecycle `0038` clearing total when no PACTG GL rows detected",
        f"- Source mix: `{excl_sources}`",
        "",
        "## Remaining risk",
        "",
        f"- {status_counts.get('UNBALANCED', 0)} claims remain unbalanced after GL exclusion (partial payouts, multi-beneficiary splits, or non-dividend distortion).",
        "- These stay in `rebalance_remaining_deferred.csv` for business review.",
        "",
        "**Safety:** `production_dbf_flag=N`. No engine or `app.py` changes.",
    ]
    report_path = os.path.join(OUT_DIR, "client_balancing_rerun_report.md")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(report_lines) + "\n")

    print("\n".join(summary_lines))
    print(f"\nReport: {report_path}")


if __name__ == "__main__":
    main()
