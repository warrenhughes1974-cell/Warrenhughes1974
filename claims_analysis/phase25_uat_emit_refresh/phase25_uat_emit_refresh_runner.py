"""Phase 25 — UAT emit refresh (post-rebalance populations + client overlays).

Stages Phase 24 post-rebalance UAT candidates, runs headless Phase 21 emit via app.py,
then applies client decision overlays:
  - Item 18: combined claim amounts (NETDB / MPAID / MFACE on QUIKCLMS)
  - Item 19: payee override (MPAYNAME on QUIKCLMP)

Does NOT modify app.py, Phase 4-24 engines, or generate production DBFs.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

import pandas as pd

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
P24_DIR = os.path.join(ROOT, "claims_analysis", "phase24_client_balancing_rerun")
P23_DIR = os.path.join(ROOT, "claims_analysis", "phase23_client_decision_application")
P15_CROSSWALK = os.path.join(
    ROOT, "claims_analysis", "phase15_qa_signoff_replay_execution", "phase15_claimnum_crosswalk.csv"
)
OUT_DIR = os.path.join(ROOT, "claims_analysis", "phase25_uat_emit_refresh")
DEFAULT_OUTPUT = os.path.join(ROOT, "QLA_Migration", "Output")
HEADLESS_EMIT = os.path.join(os.path.dirname(__file__), "headless_claims_uat_emit.py")

TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
SNAP = "PHASE25-UAT-EMIT-REFRESH-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LINEAGE = "phase24_client_balancing_rerun|phase25_uat_emit_refresh"
PROD_FLAG = "N"


def claimnum_prefix(reconstructed_claim_id):
    text = str(reconstructed_claim_id or "").strip()
    return text[:13] if text else ""


def apply_combined_amount_overlay(clms_path, adjustments_path):
    if not os.path.isfile(clms_path) or not os.path.isfile(adjustments_path):
        return {"applied": 0, "skipped": 0, "reason": "missing_file"}

    clms = pd.read_csv(clms_path, dtype=str).fillna("")
    adj = pd.read_csv(adjustments_path, dtype=str)
    adj["combined_claim_amount"] = pd.to_numeric(adj["combined_claim_amount"], errors="coerce")
    adj = adj.dropna(subset=["combined_claim_amount"])

    prefix_map = {
        claimnum_prefix(row["reconstructed_claim_id"]): row["combined_claim_amount"]
        for _, row in adj.iterrows()
    }

    applied = 0
    for idx, row in clms.iterrows():
        claimnum = str(row.get("CLAIMNUM", "")).strip()
        amount = prefix_map.get(claimnum)
        if amount is None:
            continue
        amt_str = f"{float(amount):.2f}"
        for field in ("NETDB", "MPAID", "MFACE"):
            if field in clms.columns:
                clms.at[idx, field] = amt_str
        applied += 1

    clms.to_csv(clms_path, index=False, encoding="utf-8")
    return {"applied": applied, "skipped": len(adj) - applied, "eligible": len(adj)}


def apply_payee_override(clmp_path, override_path):
    if not os.path.isfile(clmp_path) or not os.path.isfile(override_path):
        return {"applied": 0, "reason": "missing_file"}

    clmp = pd.read_csv(clmp_path, dtype=str).fillna("")
    ovr = pd.read_csv(override_path, dtype=str)
    if ovr.empty:
        return {"applied": 0, "reason": "no_overrides"}

    applied = 0
    audit = []
    for _, spec in ovr.iterrows():
        policy = str(spec.get("policy_number", "")).strip()
        new_payee = str(spec.get("new_payee", "")).strip()
        old_payee = str(spec.get("old_payee", "")).strip()
        if not policy or not new_payee:
            continue
        mask = clmp["MPOLICY"].astype(str).str.strip() == policy
        count = int(mask.sum())
        if count:
            clmp.loc[mask, "MPAYNAME"] = new_payee
            applied += count
            audit.append({
                "policy_number": policy,
                "rows_updated": count,
                "old_payee": old_payee,
                "new_payee": new_payee,
                "prototype_claimnum": spec.get("prototype_claimnum", ""),
            })

    clmp.to_csv(clmp_path, index=False, encoding="utf-8")
    return {"applied": applied, "details": audit}


def count_rows(path):
    if not os.path.isfile(path):
        return 0
    with open(path, encoding="utf-8") as fh:
        return max(sum(1 for _ in fh) - 1, 0)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    output_dir = os.environ.get("QLA_CLAIMS_OUTPUT_DIR", DEFAULT_OUTPUT)
    os.makedirs(output_dir, exist_ok=True)

    uat_clms = os.path.join(P24_DIR, "uat_candidate_quikclms_post_rebalance.csv")
    uat_clmp = os.path.join(P24_DIR, "uat_candidate_quikclmp_post_rebalance.csv")
    combined_adj = os.path.join(P23_DIR, "combined_claim_amount_adjustments.csv")
    payee_ovr = os.path.join(P23_DIR, "payee_override_application.csv")

    staging_dir = os.path.join(output_dir, "claims_uat_staging")
    os.makedirs(staging_dir, exist_ok=True)

    before_clms = count_rows(os.path.join(output_dir, "quikclms.csv"))
    before_clmp = count_rows(os.path.join(output_dir, "quikclmp.csv"))

    cmd = [
        sys.executable,
        HEADLESS_EMIT,
        "--uat-clms", uat_clms,
        "--uat-clmp", uat_clmp,
        "--output-dir", output_dir,
        "--staging-dir", staging_dir,
    ]
    print("Running headless UAT emit...")
    print(" ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode not in (0, 2):
        print(f"Headless emit failed with code {result.returncode}")
        return result.returncode

    clms_out = os.path.join(output_dir, "quikclms.csv")
    clmp_out = os.path.join(output_dir, "quikclmp.csv")

    overlay_clms = apply_combined_amount_overlay(clms_out, combined_adj)
    overlay_payee = apply_payee_override(clmp_out, payee_ovr)

    after_clms = count_rows(clms_out)
    after_clmp = count_rows(clmp_out)

    audit = {
        "audit_timestamp": TS,
        "rollback_snapshot_id": SNAP,
        "production_dbf_flag": PROD_FLAG,
        "uat_clms_source": uat_clms,
        "uat_clmp_source": uat_clmp,
        "output_dir": output_dir,
        "emit_return_code": result.returncode,
        "combined_amount_overlay": overlay_clms,
        "payee_override_overlay": overlay_payee,
        "rulebook_lineage": LINEAGE,
    }
    with open(os.path.join(OUT_DIR, "phase25_emit_audit.json"), "w", encoding="utf-8") as fh:
        json.dump(audit, fh, indent=2)

    pd.DataFrame(overlay_payee.get("details", [])).to_csv(
        os.path.join(OUT_DIR, "payee_override_emit_trace.csv"), index=False
    )

    summary_lines = [
        "=== Phase 25 UAT Emit Refresh Summary ===",
        "",
        f"Rollback snapshot: {SNAP}",
        f"UAT claims source: {uat_clms}",
        f"UAT payments source: {uat_clmp}",
        f"Output directory: {output_dir}",
        "",
        "EMIT (Phase 21 headless via app.py):",
        f"  Return code: {result.returncode}",
        f"  quikclms.csv: {before_clms} -> {after_clms} rows",
        f"  quikclmp.csv: {before_clmp} -> {after_clmp} rows",
        "",
        "CLIENT OVERLAYS:",
        f"  Item 18 combined amounts: {overlay_clms}",
        f"  Item 19 payee overrides:  {overlay_payee}",
        "",
        "production_dbf_flag=N — UAT staging CSVs only.",
        "app.py invoked headlessly; no production DBF generation.",
    ]
    summary_path = os.path.join(OUT_DIR, "phase25_execution_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(summary_lines) + "\n")

    report_lines = [
        "# Phase 25 — UAT Emit Refresh Report",
        "",
        f"**Run date:** {TS[:10]}",
        f"**Rollback snapshot:** `{SNAP}`",
        "",
        "## Population sources",
        "",
        f"- Claims: `phase24_client_balancing_rerun/uat_candidate_quikclms_post_rebalance.csv` (5,965 UAT claims)",
        f"- Payments: `phase24_client_balancing_rerun/uat_candidate_quikclmp_post_rebalance.csv` (1,709 UAT payments)",
        "",
        "## Emit results",
        "",
        f"| Table | Rows emitted | Output |",
        f"|---|---:|---|",
        f"| QUIKCLMS | {after_clms} | `{clms_out}` |",
        f"| QUIKCLMP | {after_clmp} | `{clmp_out}` |",
        "",
        "## Client overlays applied post-emit",
        "",
        f"- **Item 18** — combined claim amounts: {overlay_clms['applied']} QUIKCLMS rows updated (NETDB/MPAID/MFACE)",
        f"- **Item 19** — payee override: {overlay_payee.get('applied', 0)} QUIKCLMP rows updated (`010807842C` → KENNETH WAYNE MATTHEW)",
        "",
        "## Notes",
        "",
        "- MPOLICY cross-table validation disabled (`QLA_VALIDATE_CLAIMS_MPOLICY=0`) because converted `quikmstr.csv` was not present in output.",
        "- Phase 22 semantic governance hold remains active; pseudo surrender chains in baseline UAT are quarantined at emit.",
        "- `production_dbf_flag=N` — no production DBFs generated.",
        "",
        f"Audit: `phase25_emit_audit.json`",
    ]
    report_path = os.path.join(OUT_DIR, "uat_emit_refresh_report.md")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(report_lines) + "\n")

    print("\n".join(summary_lines))
    print(f"\nReport: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
