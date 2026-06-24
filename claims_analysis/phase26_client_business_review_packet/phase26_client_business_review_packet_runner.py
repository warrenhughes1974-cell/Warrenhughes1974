"""Phase 26 — Client business-review packet (post-UAT sign-off queue).

Assembles the remaining deferred populations for client decision after
Phase 23–25 UAT emit/DBF validation:
  - 126 death claims still UNBALANCED after dividend-on-deposit rebalance
  - 21 surrender queue items with insufficient payout evidence

Does NOT modify app.py, conversion engines, or UAT populations.
production_dbf_flag remains N.
"""

import os
from datetime import datetime, timezone

import pandas as pd

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
P23 = os.path.join(ROOT, "claims_analysis", "phase23_client_decision_application")
P24 = os.path.join(ROOT, "claims_analysis", "phase24_client_balancing_rerun")
P17 = os.path.join(ROOT, "claims_analysis", "phase17_uat_governance_reporting")
P4 = os.path.join(ROOT, "claims_analysis", "phase4_claim_event_reconstruction")
P15 = os.path.join(
    ROOT, "claims_analysis", "phase15_qa_signoff_replay_execution", "phase15_claimnum_crosswalk.csv"
)
OUT = os.path.join(ROOT, "claims_analysis", "phase26_client_business_review_packet")
DOCS = os.path.join(ROOT, "docs", "claims_conversion_reference")

TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
SNAP = "PHASE26-CLIENT-BUSINESS-REVIEW-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LINEAGE = "phase24_client_balancing_rerun|phase25_uat_emit_refresh|phase26_client_business_review_packet"
PROD = "N"


def strip(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def pick_unbalanced_examples(unbal_df):
    """Curated policy examples across distortion patterns for client review."""
    df = unbal_df.copy()
    df["diff_abs"] = pd.to_numeric(df["balancing_difference_adjusted"], errors="coerce").abs()
    picks = []

    def add(label, row):
        picks.append({
            "example_label": label,
            "policy_number": strip(row.get("policy_number", "")),
            "prototype_claimnum": strip(row.get("prototype_claimnum", "")),
            "reconstructed_claim_id": strip(row.get("reconstructed_claim_id", "")),
            "first_activity_date": strip(row.get("first_activity_date", "")),
            "distortion_pattern": strip(row.get("distortion_pattern", "")),
            "net_payment": strip(row.get("net_payment", "")),
            "payout_total": strip(row.get("payout_total", "")),
            "div_on_dep_excluded": strip(row.get("div_on_dep_excluded", "")),
            "balancing_difference_adjusted": strip(row.get("balancing_difference_adjusted", "")),
            "transaction_codes": strip(row.get("transaction_codes", "")),
            "client_review_note": label,
        })

    partial = df[df["distortion_pattern"] == "PARTIAL_PAYOUT_MULTI_PAYEE_OR_INCOMPLETE"]
    div_var = df[df["distortion_pattern"] == "DIV_ON_DEP_EXCLUDED_STILL_VARIANCE"]

    if not partial.empty:
        add("Large partial payout — benefit far exceeds recorded payout", partial.nlargest(1, "diff_abs").iloc[0])
        add("Large partial payout — second high-variance case", partial.nlargest(2, "diff_abs").iloc[1])
        add("Mid-size partial payout — typical multi-payee split", partial.iloc[partial["diff_abs"].sub(40000).abs().idxmin()])
        add("Smallest remaining variance — near tolerance", partial.nsmallest(1, "diff_abs").iloc[0])
    if not div_var.empty:
        add("Post-exclusion variance — clearing/payout timing distortion", div_var.iloc[0])
        add("Post-exclusion variance — div-on-dep excluded but gap remains", div_var.iloc[min(1, len(div_var) - 1)])

    # Zero-payout funded claim if present
    zero_pay = df[pd.to_numeric(df["payout_total"], errors="coerce").fillna(0) == 0]
    if not zero_pay.empty:
        add("Funded claim with no payout rows in extract", zero_pay.iloc[0])

    return pd.DataFrame(picks)


def pick_surrender_policy_summary(surr_df):
    """One row per policy with chain count for client review."""
    rows = []
    grouped = surr_df.groupby("policy_number", sort=True)
    for policy, sub in grouped:
        rows.append({
            "policy_number": policy,
            "surrender_chain_count": len(sub),
            "transaction_codes": strip(sub.iloc[0].get("transaction_codes", "")),
            "sample_claim_id": strip(sub.iloc[0].get("reconstructed_claim_id", "")),
            "first_activity_date_earliest": min(strip(r) for r in sub["first_activity_date"] if strip(r)),
            "first_activity_date_latest": max(strip(r) for r in sub["first_activity_date"] if strip(r)),
            "blocker_category": strip(sub.iloc[0].get("blocker_category", "")),
            "client_review_note": (
                f"{len(sub)} surrender chain(s); codes {strip(sub.iloc[0].get('transaction_codes', ''))} "
                "only — no approved payout evidence (1020/0560/0094/1900/0567)"
            ),
        })
    return pd.DataFrame(rows)


def format_unbalanced_examples_md(examples_df):
    lines = [
        "### Representative policy examples — unbalanced death claims",
        "",
        "Use these LifePRO policy numbers when validating in source accounting or QLAdmin.",
        "",
        "| Policy | Claim # | Activity date | Pattern | Net benefit | Payout total | Div-on-dep excluded | Remaining gap | Codes |",
        "|---|---|---|---|---:|---:|---:|---:|---|",
    ]
    for _, r in examples_df.iterrows():
        lines.append(
            f"| **{r['policy_number']}** | {r['prototype_claimnum']} | {r['first_activity_date']} | "
            f"{r['distortion_pattern'].replace('_', ' ').title()[:40]} | ${r['net_payment']} | ${r['payout_total']} | "
            f"${r['div_on_dep_excluded']} | ${r['balancing_difference_adjusted']} | {r['transaction_codes']} |"
        )
    lines.extend([
        "",
        "**How to read these:**",
    ])
    by_label = {strip(r.get("example_label", "")): strip(r.get("policy_number", "")) for _, r in examples_df.iterrows()}
    bullets = []
    p1 = by_label.get("Large partial payout — benefit far exceeds recorded payout")
    p2 = by_label.get("Large partial payout — second high-variance case")
    if p1 and p2:
        bullets.append(f"- **{p1}** / **{p2}** — large death benefits with payouts well below net (likely multi-beneficiary or incomplete payout chain in extract).")
    mid = by_label.get("Mid-size partial payout — typical multi-payee split")
    if mid:
        bullets.append(f"- **{mid}** — mid-size partial payout; benefit exceeds recorded payout after div-on-dep exclusion.")
    div1 = by_label.get("Post-exclusion variance — clearing/payout timing distortion")
    if div1:
        bullets.append(f"- **{div1}** — div-on-dep excluded but payout/clearing layers still do not tie out.")
    zero = by_label.get("Funded claim with no payout rows in extract")
    if zero:
        bullets.append(f"- **{zero}** — funded death claim with **$0** payout rows in LifePRO extract (header-only candidate?).")
    small = by_label.get("Smallest remaining variance — near tolerance")
    if small:
        bullets.append(f"- **{small}** — smallest remaining gap; closest to passing balance check.")
    lines.extend(bullets)
    lines.append("")
    return "\n".join(lines)


def format_surrender_examples_md(summary_df, surr_df):
    lines = [
        "### Representative policies — surrender insufficient evidence",
        "",
        "Five policies account for all **21** deferred surrender chains. Each shows code **0561** (partial surrender / total cash) "
        "but **no** approved payout evidence codes from Item 14.",
        "",
        "| Policy | Chains in queue | Date range | Codes seen | Sample claim id |",
        "|---|---:|---|---|---|",
    ]
    for _, r in summary_df.iterrows():
        date_range = r["first_activity_date_earliest"]
        if r["first_activity_date_latest"] != r["first_activity_date_earliest"]:
            date_range = f"{r['first_activity_date_earliest']} – {r['first_activity_date_latest']}"
        lines.append(
            f"| **{r['policy_number']}** | {r['surrender_chain_count']} | {date_range} | "
            f"{r['transaction_codes']} | `{r['sample_claim_id']}` |"
        )
    lines.extend([
        "",
        "**Policy notes for client review:**",
        "- **9011072813** — 8 annual surrender chains (2018–2025); recurring 0561-only activity.",
        "- **9011107796** — 9 annual chains (2018–2026); same pattern.",
        "- **9010776027** — 2 chains (2018, 2019).",
        "- **9010780411**, **9010780591** — single-chain policies.",
        "",
        "Full chain detail: `surrender_review_workbook.csv` (filter by `policy_number`).",
        "",
    ])
    return "\n".join(lines)


def classify_unbalanced(row):
    net = float(row.get("net_payment_num", 0) or 0)
    payout = float(row.get("payout_total_num", 0) or 0)
    adj_payout = float(row.get("adjusted_payout_num", 0) or 0)
    diff = float(row.get("balancing_difference_adjusted_num", 0) or 0)
    if payout < net - 0.01:
        return "PARTIAL_PAYOUT_MULTI_PAYEE_OR_INCOMPLETE"
    if payout > net + 0.01 and adj_payout <= net + 0.01:
        return "DIV_ON_DEP_EXCLUDED_STILL_VARIANCE"
    if abs(diff) <= 100:
        return "MINOR_VARIANCE_NEAR_TOLERANCE"
    return "OTHER_ACCOUNTING_DISTORTION"


def surrender_question(row):
    codes = strip(row.get("transaction_codes", ""))
    if not codes:
        return "No payout evidence codes in claim transaction history — is this a true surrender or loan/accounting activity?"
    return "Transaction history lacks approved surrender payout pattern (1020/0560/0094/1900/0567) — approve for UAT or exclude?"


def main():
    os.makedirs(OUT, exist_ok=True)

    remaining = pd.read_csv(os.path.join(P24, "rebalance_remaining_deferred.csv"), dtype=str)
    rebalance = pd.read_csv(os.path.join(P24, "client_rebalance_results.csv"), dtype=str)
    surrender = pd.read_csv(os.path.join(P23, "surrender_triage_results.csv"), dtype=str)
    surrender_wb = pd.read_csv(os.path.join(P17, "surrender_review_workbench.csv"), dtype=str)
    headers = pd.read_csv(os.path.join(P4, "claim_candidate_header.csv"), dtype=str)
    financials = pd.read_csv(os.path.join(P4, "claim_candidate_financials.csv"), dtype=str)
    crosswalk = pd.read_csv(P15, dtype=str)

    rem_ids = set(remaining["reconstructed_claim_id"])
    reb_sub = rebalance[rebalance["reconstructed_claim_id"].isin(rem_ids)].copy()
    for col, src in (
        ("net_payment_num", "net_payment"),
        ("payout_total_num", "payout_total"),
        ("adjusted_payout_num", "adjusted_payout"),
        ("balancing_difference_adjusted_num", "balancing_difference_adjusted"),
        ("div_on_dep_excluded_num", "div_on_dep_excluded"),
    ):
        reb_sub[col] = pd.to_numeric(reb_sub[src], errors="coerce")

    hdr_idx = {strip(r["reconstructed_claim_id"]): r for _, r in headers.iterrows()}
    fin_idx = {strip(r["reconstructed_claim_id"]): r for _, r in financials.iterrows()}
    xw = dict(zip(crosswalk["reconstructed_claim_id"], crosswalk["prototype_claimnum"]))

    unbal_rows = []
    for _, r in reb_sub.sort_values("balancing_difference_adjusted_num", key=abs, ascending=False).iterrows():
        cid = strip(r["reconstructed_claim_id"])
        h = hdr_idx.get(cid, {})
        f = fin_idx.get(cid, {})
        pattern = classify_unbalanced(r)
        unbal_rows.append({
            "audit_timestamp": TS,
            "rollback_snapshot_id": SNAP,
            "production_dbf_flag": PROD,
            "review_queue": "UNBALANCED_DEATH_CLAIM",
            "reconstructed_claim_id": cid,
            "prototype_claimnum": strip(xw.get(cid, remaining.loc[remaining["reconstructed_claim_id"] == cid, "prototype_claimnum"].iloc[0] if cid in rem_ids else "")),
            "policy_number": strip(r.get("policy_number", "")),
            "claim_family": strip(r.get("claim_family", "DEATH_CLAIM")),
            "first_activity_date": strip(h.get("first_activity_date", "")),
            "lifecycle_status": strip(h.get("reconstructed_lifecycle_status", "")),
            "transaction_codes": strip(h.get("claim_relevant_transaction_codes", "")),
            "net_payment": f"{float(r['net_payment_num']):.2f}",
            "payout_total": f"{float(r['payout_total_num']):.2f}",
            "div_on_dep_excluded": f"{float(r['div_on_dep_excluded_num']):.2f}",
            "adjusted_payout": f"{float(r['adjusted_payout_num']):.2f}",
            "balancing_difference_adjusted": f"{float(r['balancing_difference_adjusted_num']):.2f}",
            "phase4_balancing_status": strip(f.get("balancing_status", "")),
            "rebalance_status": strip(r.get("rebalance_status", "UNBALANCED")),
            "distortion_pattern": pattern,
            "business_explanation": (
                "Death claim remains unbalanced after client-authorized 2023/603703R "
                "dividend-on-deposit exclusion (Phase 24 rebalance)."
            ),
            "recommended_business_question": (
                "Approve for UAT as-is (client accepts accounting variance), convert header-only, "
                "or permanently exclude from claims conversion?"
            ),
            "recommended_next_action": "CLIENT_DECISION_REQUIRED",
            "rulebook_lineage": LINEAGE,
        })

    unbal_df = pd.DataFrame(unbal_rows)

    surr_sub = surrender[surrender["triage_disposition"] == "REMAINS_BUSINESS_REVIEW"].copy()
    wb_idx = {strip(r["reconstructed_claim_id"]): r for _, r in surrender_wb.iterrows()}
    surr_rows = []
    for _, r in surr_sub.iterrows():
        cid = strip(r["reconstructed_claim_id"])
        wb = wb_idx.get(cid, {})
        h = hdr_idx.get(cid, {})
        surr_rows.append({
            "audit_timestamp": TS,
            "rollback_snapshot_id": SNAP,
            "production_dbf_flag": PROD,
            "review_queue": "SURRENDER_INSUFFICIENT_EVIDENCE",
            "reconstructed_claim_id": cid,
            "prototype_claimnum": strip(xw.get(cid, "")),
            "policy_number": strip(h.get("policy_number", wb.get("policy_number", ""))),
            "claim_family": strip(r.get("claim_family", "SURRENDER_CLAIM")),
            "first_activity_date": strip(h.get("first_activity_date", "")),
            "lifecycle_status": strip(h.get("reconstructed_lifecycle_status", "")),
            "transaction_codes": strip(r.get("transaction_codes", "")),
            "blocker_category": strip(r.get("blocker_category", wb.get("blocker_category", ""))),
            "triage_disposition": "REMAINS_BUSINESS_REVIEW",
            "business_explanation": strip(wb.get("business_explanation", "No approved surrender payout evidence in transaction history.")),
            "recommended_business_question": surrender_question(r),
            "recommended_next_action": "CLIENT_DECISION_REQUIRED",
            "rulebook_lineage": LINEAGE,
        })
    surr_df = pd.DataFrame(surr_rows)

    combined = pd.concat([unbal_df, surr_df], ignore_index=True, sort=False)
    combined["review_queue_rank"] = range(1, len(combined) + 1)

    pattern_counts = unbal_df["distortion_pattern"].value_counts().to_dict() if not unbal_df.empty else {}

    policy_examples_unbal = pick_unbalanced_examples(unbal_df)
    policy_examples_surr = pick_surrender_policy_summary(surr_df)
    unbal_examples_md = format_unbalanced_examples_md(policy_examples_unbal)
    surr_examples_md = format_surrender_examples_md(policy_examples_surr, surr_df)

    # Representative examples (top variance + one per surrender pattern)
    unbal_examples = unbal_df.head(8)
    surr_examples = surr_df.head(5)
    examples = pd.concat([unbal_examples, surr_examples], ignore_index=True)

    outputs = {
        "unbalanced_claims_review_workbook.csv": unbal_df,
        "surrender_review_workbook.csv": surr_df,
        "combined_client_review_queue.csv": combined,
        "client_review_representative_examples.csv": examples,
        "client_review_policy_examples_unbalanced.csv": policy_examples_unbal,
        "client_review_policy_examples_surrender.csv": policy_examples_surr,
        "unbalanced_distortion_pattern_summary.csv": pd.DataFrame([
            {"distortion_pattern": k, "claim_count": v, "audit_timestamp": TS, "rulebook_lineage": LINEAGE}
            for k, v in pattern_counts.items()
        ]),
    }
    for name, df in outputs.items():
        df.to_csv(os.path.join(OUT, name), index=False)

    packet_md = os.path.join(OUT, "client_business_review_packet.md")
    with open(packet_md, "w", encoding="utf-8") as fh:
        fh.write(
            "# Client Business Review Packet — Remaining Deferred Claims\n\n"
            f"**Prepared:** {TS[:10]}  \n"
            f"**Rollback snapshot:** `{SNAP}`  \n"
            "**Context:** UAT DBF load and spot-checks passed (Phase 25). This packet covers populations "
            "still excluded from UAT pending client business decisions.\n\n"
            "---\n\n"
            "## Executive summary\n\n"
            "| Queue | Count | Disposition needed |\n"
            "|---|---:|---|\n"
            f"| Unbalanced death claims (post-rebalance) | {len(unbal_df)} | Approve UAT / header-only / exclude |\n"
            f"| Surrender insufficient evidence | {len(surr_df)} | Approve pattern / exclude / reclassify |\n"
            f"| **Total client review** | **{len(combined)}** | |\n\n"
            "### UAT already delivered (for reference)\n\n"
            "- **2,114** QUIKCLMS / **1,709** QUIKCLMP emitted and loaded to UAT DBFs\n"
            "- Client Items 14–19 applied (surrender triage, orphans, rebalance promotions, combined amounts, payee override)\n"
            "- **155** additional death claims cleared via Phase 24 dividend-on-deposit rebalance\n\n"
            "---\n\n"
            f"## Queue 1 — Unbalanced death claims ({len(unbal_df)})\n\n"
            "These claims received the client-authorized `2023` / `603703R` dividend-on-deposit exclusion "
            "(Phase 24) but **remain outside balancing tolerance** after adjustment.\n\n"
            "### Distortion patterns\n\n"
        )
        for pat, cnt in sorted(pattern_counts.items(), key=lambda x: -x[1]):
            fh.write(f"- **{pat}:** {cnt}\n")
        fh.write(
            "\n**Dominant pattern:** `PARTIAL_PAYOUT_MULTI_PAYEE_OR_INCOMPLETE` — payout total is less than "
            "reconstructed net benefit (typical multi-beneficiary split or incomplete payout chain).\n\n"
            "### Client decision options (per claim or batch)\n\n"
            "1. **APPROVE_UAT** — Accept variance; promote to UAT like Items 16.2/16.3 exemplars\n"
            "2. **HEADER_ONLY** — Convert settled header with no financial history\n"
            "3. **EXCLUDE** — Permanently exclude from claims conversion\n"
            "4. **DEFER** — Keep out of scope for September go-live\n\n"
            f"{unbal_examples_md}"
            "Detail: `unbalanced_claims_review_workbook.csv` | Policy examples: `client_review_policy_examples_unbalanced.csv`\n\n"
            "---\n\n"
            f"## Queue 2 — Surrender review ({len(surr_df)})\n\n"
            "Per client Item 14, 479 surrender items with approved payout evidence were cleared. "
            "These **21** items lack payout evidence codes (`1020`/`0560`/`0094`/`1900`/`0567`) in transaction history.\n\n"
            f"{surr_examples_md}"
            "### Client decision options\n\n"
            "1. **APPROVE_UAT** — Client confirms true surrender despite missing codes in extract\n"
            "2. **EXCLUDE_LOAN_ACCOUNTING** — Reclassify as loan activity (not QUIKCLMS)\n"
            "3. **DEFER** — Keep out of September scope\n\n"
            "Detail: `surrender_review_workbook.csv` | Policy summary: `client_review_policy_examples_surrender.csv`\n\n"
            "---\n\n"
            "## Artifacts in this folder\n\n"
            "| File | Purpose |\n"
            "|---|---|\n"
            "| `combined_client_review_queue.csv` | Full 147-item review queue |\n"
            "| `unbalanced_claims_review_workbook.csv` | 126 unbalanced death claims with financial detail |\n"
            "| `surrender_review_workbook.csv` | 21 surrender items |\n"
            "| `client_review_representative_examples.csv` | Top examples for client meeting |\n"
            "| `client_review_policy_examples_unbalanced.csv` | Curated unbalanced policy examples with amounts |\n"
            "| `client_review_policy_examples_surrender.csv` | Surrender policies with chain counts |\n"
            "| `unbalanced_distortion_pattern_summary.csv` | Pattern counts |\n"
            "| `client_review_decision_template.md` | Decision capture form |\n\n"
            "**Safety:** `production_dbf_flag=N`. No production DBF changes from this packet.\n"
        )

    template_path = os.path.join(OUT, "client_review_decision_template.md")
    with open(template_path, "w", encoding="utf-8") as fh:
        fh.write(
            "# Client Review Decision Template\n\n"
            f"**Date:** __________  \n"
            "**Reviewer:** __________  \n"
            f"**Packet snapshot:** `{SNAP}`\n\n"
            "## Batch decisions (check one per queue)\n\n"
            "### Unbalanced death claims (126)\n\n"
            "- [ ] Batch **APPROVE_UAT** all 126\n"
            "- [ ] Batch **EXCLUDE** all 126\n"
            "- [ ] Batch **DEFER** past go-live\n"
            "- [ ] Item-by-item review (attach annotated workbook)\n\n"
            "### Surrender insufficient evidence (21)\n\n"
            "- [ ] Batch **APPROVE_UAT** all 21\n"
            "- [ ] Batch **EXCLUDE_LOAN_ACCOUNTING** all 21\n"
            "- [ ] Batch **DEFER** past go-live\n"
            "- [ ] Item-by-item review (attach annotated workbook)\n\n"
            "## Item-specific notes (pre-filled examples)\n\n"
            "| reconstructed_claim_id | policy_number | queue | decision | notes |\n"
            "|---|---|---|---|---|\n"
        )
        for _, r in policy_examples_unbal.iterrows():
            fh.write(
                f"| {r['reconstructed_claim_id']} | **{r['policy_number']}** | Unbalanced | | "
                f"Gap ${r['balancing_difference_adjusted']}; {r['example_label']} |\n"
            )
        for _, r in policy_examples_surr.iterrows():
            fh.write(
                f"| {r['sample_claim_id']} | **{r['policy_number']}** | Surrender ({r['surrender_chain_count']} chains) | | "
                f"{r['client_review_note']} |\n"
            )
        fh.write(
            "| | | | | |\n\n"
            "## Sign-off\n\n"
            "- [ ] Decisions recorded; authorized to apply in Phase 27\n"
            "- [ ] No May re-validation required (per prior client guidance)\n"
        )

    # Copy reference into docs for client handoff
    docs_copy = os.path.join(DOCS, f"client_business_review_packet_{TS[:10]}.md")
    with open(packet_md, encoding="utf-8") as src, open(docs_copy, "w", encoding="utf-8") as dst:
        dst.write(src.read())

    summary = [
        "=== Phase 26 Client Business Review Packet ===",
        "",
        f"Rollback snapshot: {SNAP}",
        f"Unbalanced death claims: {len(unbal_df)}",
        f"Surrender review items: {len(surr_df)}",
        f"Combined review queue: {len(combined)}",
        f"Distortion patterns: {pattern_counts}",
        "",
        f"Packet: {packet_md}",
        f"Docs copy: {docs_copy}",
        "",
        "production_dbf_flag=N — review artifacts only.",
    ]
    summary_path = os.path.join(OUT, "phase26_execution_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(summary) + "\n")

    print("\n".join(summary))


if __name__ == "__main__":
    main()
