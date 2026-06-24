"""Phase 23 — Client Issue Log Decision Application (Items 14-19).

Applies client-authorized business decisions (recorded 2026-06-11) to the
Phase 17 UAT governance populations. Produces refreshed UAT candidate CSVs
and decision artifacts. Does NOT modify Phase 4-17 engines, app.py, or any
prior phase outputs. production_dbf_flag remains N (no production DBFs).
"""

import json
import os
from datetime import datetime, timezone

import pandas as pd

ROOT = r"C:\Users\warren\Documents\GitHub\Warrenhughes1974"
CONFIG_PATH = os.path.join(ROOT, "claims_analysis", "config", "client_issue_log_decision_rules.json")
P17_DIR = os.path.join(ROOT, "claims_analysis", "phase17_uat_governance_reporting")
P15_CROSSWALK = os.path.join(ROOT, "claims_analysis", "phase15_qa_signoff_replay_execution", "phase15_claimnum_crosswalk.csv")
P4_LIFECYCLE = os.path.join(ROOT, "claims_analysis", "phase4_claim_event_reconstruction", "claim_candidate_lifecycle.csv")
P7C_LAYERS = os.path.join(ROOT, "claims_analysis", "phase7c_death_claim_decomposition", "death_claim_component_layers.csv")
OUT_DIR = os.path.join(ROOT, "claims_analysis", "phase23_client_decision_application")

TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
SNAP = "PHASE23-CLIENT-DECISION-APPLICATION-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LINEAGE = "phase17_uat_governance|phase23_client_decision_application"
PROD_FLAG = "N"


def load_inputs():
    data = {
        "uat_clms": pd.read_csv(os.path.join(P17_DIR, "uat_candidate_quikclms.csv"), dtype=str),
        "uat_clmp": pd.read_csv(os.path.join(P17_DIR, "uat_candidate_quikclmp.csv"), dtype=str),
        "def_claims": pd.read_csv(os.path.join(P17_DIR, "deferred_governance_claims.csv"), dtype=str),
        "def_payments": pd.read_csv(os.path.join(P17_DIR, "deferred_governance_payments.csv"), dtype=str),
        "surrender_wb": pd.read_csv(os.path.join(P17_DIR, "surrender_review_workbench.csv"), dtype=str),
        "crosswalk": pd.read_csv(P15_CROSSWALK, dtype=str),
        "lifecycle": pd.read_csv(P4_LIFECYCLE, dtype=str),
        "layers": pd.read_csv(P7C_LAYERS, dtype=str),
    }
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        data["cfg"] = json.load(fh)
    return data


def claim_codes_map(lifecycle):
    grouped = lifecycle.groupby("reconstructed_claim_id")["source_transaction_code"].apply(
        lambda s: set(str(c).strip() for c in s.dropna())
    )
    return grouped.to_dict()


def next_claimnum_factory(crosswalk, uat_clms):
    nums = []
    for series in (crosswalk["prototype_claimnum"], uat_clms["prototype_claimnum"]):
        for v in series.dropna():
            v = str(v).strip()
            if v.startswith("CLM") and v[3:].isdigit():
                nums.append(int(v[3:]))
    counter = {"n": max(nums) if nums else 0}

    def make():
        counter["n"] += 1
        return "CLM%07d" % counter["n"]

    return make


def lookup_claimnum(crosswalk_map, claim_id, make_new):
    existing = crosswalk_map.get(claim_id)
    if existing and str(existing).strip().startswith("CLM"):
        return str(existing).strip(), "PHASE15_CROSSWALK"
    return make_new(), "PHASE23_ASSIGNED"


def base_clms_row(claim_id, claimnum, segment, explanation, extra=None):
    row = {
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
    if extra:
        row.update(extra)
    return row


def main():
    data = load_inputs()
    cfg = data["cfg"]
    uat_clms = data["uat_clms"].copy()
    uat_clmp = data["uat_clmp"].copy()
    def_claims = data["def_claims"]
    def_payments = data["def_payments"]
    surrender_wb = data["surrender_wb"]

    before = {
        "uat_claims": len(uat_clms),
        "uat_payments": len(uat_clmp),
        "deferred_claims": len(def_claims),
        "deferred_payments": len(def_payments),
        "surrender_queue": len(surrender_wb),
    }

    codes_by_claim = claim_codes_map(data["lifecycle"])
    crosswalk_map = dict(
        zip(data["crosswalk"]["reconstructed_claim_id"], data["crosswalk"]["prototype_claimnum"])
    )
    make_new_claimnum = next_claimnum_factory(data["crosswalk"], uat_clms)

    audit_rows = []
    new_clms_rows = []
    new_clmp_rows = []

    uat_claim_ids = set(uat_clms["reconstructed_claim_id"])
    promoted_claim_ids = set()

    # ---- Item 16: explicit claim promotions -------------------------------
    item16 = cfg["item16_unbalanced_claims"]
    for claim_id in item16["client_approved_uat_claims"]:
        if claim_id in uat_claim_ids:
            audit_rows.append({"item": "16", "action": "ALREADY_IN_UAT", "entity": claim_id, "detail": "No promotion needed"})
            continue
        claimnum, src = lookup_claimnum(crosswalk_map, claim_id, make_new_claimnum)
        new_clms_rows.append(base_clms_row(
            claim_id, claimnum, "CLIENT_AUTHORIZED_UAT",
            "Client decision Item 16: approved for UAT with 2023/603703R dividend-on-deposit "
            "excluded from DB balancing.",
        ))
        promoted_claim_ids.add(claim_id)
        audit_rows.append({"item": "16", "action": "PROMOTED_TO_UAT", "entity": claim_id, "detail": f"claimnum={claimnum} ({src})"})

    for spec in item16["header_only_claims"]:
        claim_id = spec["reconstructed_claim_id"]
        if claim_id in uat_claim_ids:
            audit_rows.append({"item": "16", "action": "ALREADY_IN_UAT", "entity": claim_id, "detail": "Header-only flag recorded"})
        else:
            claimnum, src = lookup_claimnum(crosswalk_map, claim_id, make_new_claimnum)
            new_clms_rows.append(base_clms_row(
                claim_id, claimnum, "CLIENT_AUTHORIZED_HEADER_ONLY",
                f"Client decision Item 16: convert header only — status {spec['claim_status']} "
                f"{spec['status_date']}, amount {spec['amount']}, no financial history.",
            ))
            promoted_claim_ids.add(claim_id)
            audit_rows.append({"item": "16", "action": "PROMOTED_HEADER_ONLY", "entity": claim_id, "detail": f"claimnum={claimnum} ({src}); CLAIMSTAT={spec['claimstat']}; amount={spec['amount']}"})

    # ---- Item 16: global rebalance-pending marker --------------------------
    rebalance = def_claims[
        (
            def_claims["deferred_category"].fillna("").str.contains("UNBALANCED", case=False)
            | def_claims["blocker_category"].fillna("").str.contains("BALANCING", case=False)
        )
        & ~def_claims["reconstructed_claim_id"].isin(promoted_claim_ids)
        & ~def_claims["reconstructed_claim_id"].isin(
            [s["reconstructed_claim_id"] for s in item16["header_only_claims"]]
        )
    ].copy()
    rebalance["rebalance_rule"] = "EXCLUDE_GL_2023_603703R_FROM_DB_BALANCING"
    rebalance["rebalance_status"] = "REBALANCE_PENDING"
    rebalance["audit_timestamp"] = TS
    rebalance["rollback_snapshot_id"] = SNAP
    audit_rows.append({"item": "16", "action": "MARKED_REBALANCE_PENDING", "entity": f"{len(rebalance)} deferred unbalanced claims", "detail": "Await balancing engine re-run with 2023/603703R exclusion"})

    # ---- Item 15: standalone orphan payments -------------------------------
    item15 = cfg["item15_orphan_payments"]
    standalone_headers = []
    seen_parents = set()
    for _, pay in def_payments.iterrows():
        parent_id = pay["reconstructed_claim_id"]
        claimnum, src = lookup_claimnum(crosswalk_map, parent_id, make_new_claimnum)

        if parent_id not in seen_parents and parent_id not in uat_claim_ids and parent_id not in promoted_claim_ids:
            seen_parents.add(parent_id)
            family = "DEATH_CLAIM" if "DEATH_CLAIM" in parent_id else ("SURRENDER_CLAIM" if "SURRENDER_CLAIM" in parent_id else "DISBURSEMENT_CLAIM")
            header = base_clms_row(
                parent_id, claimnum, "CLIENT_STANDALONE_PAYMENT_HEADER",
                "Client decision Item 15: minimal claim header for standalone orphan payment(s). "
                f"CLAIMSTAT={item15['standalone_claimstat']} ({item15['standalone_mclaimstatus']}); "
                "no claim-level financial history.",
            )
            standalone_headers.append({
                "audit_timestamp": TS,
                "rollback_snapshot_id": SNAP,
                "production_dbf_flag": PROD_FLAG,
                "reconstructed_claim_id": parent_id,
                "prototype_claimnum": claimnum,
                "claimnum_source": src,
                "claim_family": family,
                "claimstat": item15["standalone_claimstat"],
                "mclaimstatus": item15["standalone_mclaimstatus"],
                "header_type": "STANDALONE_MINIMAL",
                "financial_history": "PAYMENTS_ONLY",
                "rulebook_lineage": LINEAGE,
            })
            new_clms_rows.append(header)

        new_clmp_rows.append({
            "audit_timestamp": TS,
            "rollback_snapshot_id": SNAP,
            "production_dbf_flag": PROD_FLAG,
            "record_type": "QUIKCLMP",
            "reconstructed_claim_id": parent_id,
            "canonical_payment_stage_id": pay.get("canonical_payment_stage_id", ""),
            "derivation_candidate_id": pay.get("derivation_candidate_id", ""),
            "prototype_claimnum": claimnum,
            "replay_source": "CLIENT_DECISION",
            "uat_segment": "CLIENT_AUTHORIZED_STANDALONE",
            "governance_status": "UAT_CLEARED",
            "business_review_required": "N",
            "replay_authorization_status": "CLIENT_AUTHORIZED",
            "generation_status": "ACCEPTED",
            "mamount": pay.get("mamount", ""),
            "blocker_category": "NONE",
            "business_explanation": "Client decision Item 15: orphan payment converts standalone under minimal settled header.",
            "orphan_impact": "RESOLVED_STANDALONE",
            "reconciliation_impact": "CLIENT_ACCEPTED",
            "replay_eligibility": "UAT_READY",
            "remediation_recommendation": "NONE",
            "rulebook_lineage": LINEAGE,
        })

    audit_rows.append({"item": "15", "action": "PROMOTED_STANDALONE_PAYMENTS", "entity": f"{len(new_clmp_rows)} payments", "detail": f"{len(standalone_headers)} minimal headers created; CLAIMSTAT={item15['standalone_claimstat']}"})

    # ---- Item 14: surrender queue triage ------------------------------------
    item14 = cfg["item14_surrender_validation"]
    payout_codes = set(item14["approved_payout_evidence_codes"])
    loan_codes = set(item14["loan_only_codes"])
    triage_rows = []
    surrender_promotions = 0
    for _, row in surrender_wb.iterrows():
        claim_id = row["reconstructed_claim_id"]
        codes = codes_by_claim.get(claim_id, set())
        if codes and codes.issubset(loan_codes):
            disposition = item14["loan_only_disposition"]
        elif codes & payout_codes:
            disposition = item14["pattern_match_disposition"]
        else:
            disposition = item14["insufficient_evidence_disposition"]
        triage_rows.append({
            "audit_timestamp": TS,
            "rollback_snapshot_id": SNAP,
            "production_dbf_flag": PROD_FLAG,
            "reconstructed_claim_id": claim_id,
            "claim_family": row.get("claim_family", ""),
            "blocker_category": row.get("blocker_category", ""),
            "transaction_codes": "|".join(sorted(codes)) if codes else "",
            "triage_disposition": disposition,
            "decision_basis": "Client Item 14: approved surrender patterns only; loan-only excluded",
            "rulebook_lineage": LINEAGE,
        })
        if disposition == item14["pattern_match_disposition"] and claim_id not in uat_claim_ids and claim_id not in promoted_claim_ids:
            claimnum, src = lookup_claimnum(crosswalk_map, claim_id, make_new_claimnum)
            new_clms_rows.append(base_clms_row(
                claim_id, claimnum, "CLIENT_PATTERN_CLEARED",
                "Client decision Item 14: matches approved surrender payout pattern; cleared "
                "best-effort per client instruction (client to flag exceptions).",
            ))
            promoted_claim_ids.add(claim_id)
            surrender_promotions += 1

    triage_df = pd.DataFrame(triage_rows)
    counts14 = triage_df["triage_disposition"].value_counts().to_dict()
    audit_rows.append({"item": "14", "action": "SURRENDER_TRIAGE", "entity": f"{len(triage_df)} queue items", "detail": f"{counts14}; promoted={surrender_promotions}"})

    # ---- Item 18: combined claim amounts ------------------------------------
    item18 = cfg["item18_combined_claim_amounts"]
    layers = data["layers"].copy()
    layers["layer_total_num"] = pd.to_numeric(layers["layer_total"], errors="coerce").fillna(0.0)
    combine = layers[layers["layer_name"].isin(item18["combine_layers"])]
    pivot = combine.pivot_table(
        index=["reconstructed_claim_id", "policy_number"],
        columns="layer_name", values="layer_total_num", aggfunc="sum",
    ).reset_index().fillna(0.0)
    for layer in item18["combine_layers"]:
        if layer not in pivot.columns:
            pivot[layer] = 0.0
    pivot["combined_claim_amount"] = pivot[item18["combine_layers"]].sum(axis=1).round(2)
    has_loan = pivot[(pivot.get("offset", 0) != 0) | (pivot.get("interest", 0) != 0)].copy()
    has_loan["audit_timestamp"] = TS
    has_loan["rollback_snapshot_id"] = SNAP
    has_loan["production_dbf_flag"] = PROD_FLAG
    has_loan["adjustment_rule"] = "DB_PLUS_LOAN_PAYOUT_PLUS_LOAN_INTEREST"
    has_loan["rulebook_lineage"] = LINEAGE
    audit_rows.append({"item": "18", "action": "COMBINED_AMOUNT_ADJUSTMENTS", "entity": f"{len(has_loan)} claims with loan components", "detail": "Adjusted amount = payout + offset + interest layers"})

    # ---- Item 19: payee overrides -------------------------------------------
    payee_rows = []
    for ovr in cfg["item19_payee_overrides"]:
        payee_rows.append({
            "audit_timestamp": TS,
            "rollback_snapshot_id": SNAP,
            "production_dbf_flag": PROD_FLAG,
            "reconstructed_claim_id": ovr["reconstructed_claim_id"],
            "prototype_claimnum": ovr["prototype_claimnum"],
            "policy_number": ovr["policy_number"],
            "mamount": ovr["mamount"],
            "old_payee": ovr["old_payee"],
            "new_payee": ovr["new_payee"],
            "override_status": "CLIENT_AUTHORIZED",
            "apply_at": "UAT_EMIT_MPAYNAME",
            "reason": ovr["reason"],
            "rulebook_lineage": LINEAGE,
        })
        audit_rows.append({"item": "19", "action": "PAYEE_OVERRIDE", "entity": ovr["policy_number"], "detail": f"{ovr['old_payee']} -> {ovr['new_payee']} (${ovr['mamount']})"})

    # ---- Assemble refreshed populations -------------------------------------
    new_clms_df = pd.DataFrame(new_clms_rows)
    refreshed_clms = pd.concat([uat_clms, new_clms_df[uat_clms.columns.intersection(new_clms_df.columns)]], ignore_index=True)
    new_clmp_df = pd.DataFrame(new_clmp_rows)
    refreshed_clmp = pd.concat([uat_clmp, new_clmp_df[uat_clmp.columns.intersection(new_clmp_df.columns)]], ignore_index=True)

    after = {
        "uat_claims": len(refreshed_clms),
        "uat_payments": len(refreshed_clmp),
        "standalone_headers": len(standalone_headers),
        "surrender_promotions": surrender_promotions,
        "rebalance_pending": len(rebalance),
        "amount_adjustments": len(has_loan),
        "payee_overrides": len(payee_rows),
    }

    # ---- Write outputs -------------------------------------------------------
    outputs = {
        "uat_candidate_quikclms_refreshed.csv": refreshed_clms,
        "uat_candidate_quikclmp_refreshed.csv": refreshed_clmp,
        "standalone_claim_headers.csv": pd.DataFrame(standalone_headers),
        "surrender_triage_results.csv": triage_df,
        "rebalance_pending_unbalanced_claims.csv": rebalance,
        "combined_claim_amount_adjustments.csv": has_loan,
        "payee_override_application.csv": pd.DataFrame(payee_rows),
        "phase23_decision_audit_log.csv": pd.DataFrame(audit_rows).assign(
            audit_timestamp=TS, rollback_snapshot_id=SNAP, production_dbf_flag=PROD_FLAG
        ),
    }
    for name, df in outputs.items():
        df.to_csv(os.path.join(OUT_DIR, name), index=False)

    summary_lines = [
        "=== Phase 23 Client Decision Application Summary ===",
        "",
        f"Rollback snapshot: {SNAP}",
        f"Decision source: {cfg['source_document']}",
        "",
        "BEFORE (Phase 17 baseline):",
        f"  UAT candidate claims:    {before['uat_claims']}",
        f"  UAT candidate payments:  {before['uat_payments']}",
        f"  Deferred claims:         {before['deferred_claims']}",
        f"  Deferred payments:       {before['deferred_payments']}",
        f"  Surrender review queue:  {before['surrender_queue']}",
        "",
        "AFTER (client decisions applied):",
        f"  UAT candidate claims:    {after['uat_claims']} (+{after['uat_claims'] - before['uat_claims']})",
        f"  UAT candidate payments:  {after['uat_payments']} (+{after['uat_payments'] - before['uat_payments']})",
        f"  Standalone headers:      {after['standalone_headers']} (Item 15, CLAIMSTAT=3 SETTLED)",
        f"  Surrender promotions:    {after['surrender_promotions']} (Item 14 pattern-cleared)",
        f"  Surrender triage:        {counts14}",
        f"  Rebalance pending:       {after['rebalance_pending']} (Item 16 global 2023 exclusion awaits engine re-run)",
        f"  Amount adjustments:      {after['amount_adjustments']} (Item 18 DB+loan+interest)",
        f"  Payee overrides:         {after['payee_overrides']} (Item 19)",
        "",
        "production_dbf_flag=N — UAT staging artifacts only. No production DBFs.",
        "Phase 4-17 engines NOT modified. app.py NOT modified.",
    ]
    with open(os.path.join(OUT_DIR, "phase23_execution_summary.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(summary_lines) + "\n")

    print("\n".join(summary_lines))


if __name__ == "__main__":
    main()
