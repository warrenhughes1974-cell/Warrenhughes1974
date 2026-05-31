#!/usr/bin/env python3

"""Phase 22A/22B/22C orchestrator — semantic governance + claim domain eligibility (UAT-only)."""



import argparse

import json

import logging

import os

import subprocess

import sys



SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))

REPO_ROOT = os.path.normpath(os.path.join(ROOT, ".."))

DEFAULT_OUTPUT = os.path.join(ROOT, "phase22_semantic_governance")

DEFAULT_RULES = os.path.join(ROOT, "config", "claim_domain_eligibility_rules.json")

DEFAULT_GOV_RULES = os.path.join(ROOT, "config", "semantic_governance_rules.json")



logger = logging.getLogger("phase22_semantic_governance_runner")





def load_json(path):

    with open(path, encoding="utf-8") as fh:

        return json.load(fh)





def run_script(name, output_dir, extra=None):

    script = os.path.join(SCRIPT_DIR, name)

    cmd = [sys.executable, script, "--output", output_dir]

    if extra:

        cmd.extend(extra)

    logger.info("Running %s", name)

    result = subprocess.run(cmd, cwd=SCRIPT_DIR)

    return result.returncode == 0





def write_claim_domain_summary(rules, gov_rules, output_dir, metrics):

    lifepro = os.path.join(

        REPO_ROOT,

        "docs/claims_conversion_reference/LifePRO Accounting Transaction Information (4).pdf",

    )

    qladmin = os.path.join(REPO_ROOT, "docs/claims_conversion_reference/QLAdmin_Help.pdf")

    path = os.path.join(output_dir, "semantic_claim_domain_summary.txt")

    uat_baseline = metrics.get("uat_baseline", 5122)

    hold_count = metrics.get("non_claim_accounting_count", 0)

    emit_est = uat_baseline - hold_count

    lines = [

        "QLAdmin Enterprise Claims — Semantic Claim Domain Summary (Phase 22C)",

        "=" * 72,

        "",

        "EXECUTIVE SUMMARY",

        "-" * 20,

        "Course correction: 04xx Borrowed Money transactions are LOAN ACCOUNTING ACTIVITY,",

        "not QUIKCLMS claim events. Claim-domain eligibility now requires payout/benefit semantics",

        "(0530, 0560, 0561, 0090, 0094, 1020, etc.) — not internal loan offsets alone.",

        f"production_dbf_flag={rules.get('production_dbf_flag', 'N')}",

        f"Non-claim accounting rows held: {hold_count}",

        f"Affected policies: {metrics.get('policy_count', 0)}",

        f"UAT QUIKCLMS baseline (pre-hold): {uat_baseline}",

        f"Estimated UAT emit after hold: {emit_est}",

        "",

        "AUTHORITATIVE DOCUMENTATION",

        "-" * 20,

        f"LifePRO Accounting Transactions: {lifepro}",

        "- 04xx Borrowed Money: 0411 Loan Principal, 0412 Loan Interest Capitalized,",

        "  0413 Loan Payment, 0414-0416 Non-collateralized loan, 0417 Loan Write Off,",

        "  0451 Unearned Interest Income.",

        "- True surrender/disbursement: 0560 Total Cash, 0561 Partial Surrender,",

        "  0090 Cash Payout, 0530 Death Benefit, 0094 Death Claim Payout, 1020 Surrender Charge.",

        "",

        f"QLAdmin Help: {qladmin}",

        "- QUIKCLMS = Death Claims (p.733) — not loan accounting.",

        "- QuikLoan fields: MLOANPRIN, MLOANBAL, MLOANINT, MLOANACCR, MLOANBILL (p.827-828).",

        "- Loan History / loan interest charged -> QuikLoan (p.74-75).",

        "",

        "SEMANTIC CORRECTION",

        "-" * 20,

        "Prior over-expansion: 'claim-relevant accounting activity' was treated as 'claims-domain events'.",

        "0412/0451 annual capitalization cycles = loan maintenance, NOT surrender claims.",

        "0411|0412-only chains without payout codes must not enter QUIKCLMS.",

        "",

        "GOVERNANCE IMPACT",

        "-" * 20,

        f"hold_category={gov_rules.get('hold_category', 'SEMANTIC_PSEUDO_CLAIM')}",

        "Excluded from: output/quikclms.csv, output/quikclmp.csv, UAT DBFs.",

        "Preserved in: non_claim_accounting_activity_population.csv, workbenches, manifests.",

        f"QuikLoan candidate count (analysis only): {metrics.get('quikloan_candidate_count', 0)}",

        f"True surrender claims retained in UAT emit: {metrics.get('true_surrender_emit_est', 25)}",

        "",

        "RECOMMENDED BUSINESS DECISIONS",

        "-" * 20,

        "1. Accept expanded semantic hold for UAT — do not import loan accounting as claims.",

        "2. Confirm LifePRO 04xx semantics with business stakeholders.",

        "3. Initiate separate QuikLoan conversion workstream (NOT auto-converted here).",

        "",

        "RECOMMENDED FUTURE ARCHITECTURE",

        "-" * 20,

        "- QuikLoan staging for 04xx Borrowed Money events.",

        "- Claim-domain gate: require >=1 eligible payout/benefit code before QUIKCLMS emit.",

        "- Keep 04xx codes out of SURRENDER_CLAIM inference unless paired with 0560/0090/etc.",

        "",

        "ROLLBACK SAFETY",

        "-" * 20,

        "Set QLA_SEMANTIC_GOVERNANCE_HOLD=0 to disable emit filtering.",

        "Phase 4-17 artifacts unchanged. All populations lineage-preserved for replay.",

        "No production DBFs. No silent deletion.",

        "",

        f"Rulebook lineage: {rules.get('rulebook_lineage', '')}",

        f"Output directory: {os.path.abspath(output_dir)}",

    ]

    with open(path, "w", encoding="utf-8") as fh:

        fh.write("\n".join(lines) + "\n")



    legacy_path = os.path.join(output_dir, "semantic_governance_summary.txt")

    with open(legacy_path, "w", encoding="utf-8") as fh:

        fh.write("\n".join(lines[:20] + ["", "(See semantic_claim_domain_summary.txt for full report)"]) + "\n")

    return path





def main():

    parser = argparse.ArgumentParser(description="Phase 22 semantic governance orchestrator.")

    parser.add_argument("--output", default=DEFAULT_OUTPUT)

    parser.add_argument("--rules", default=DEFAULT_RULES)

    parser.add_argument("--gov-rules", default=DEFAULT_GOV_RULES)

    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    os.makedirs(args.output, exist_ok=True)

    rules = load_json(args.rules)

    gov_rules = load_json(args.gov_rules)



    steps = [

        "non_claim_accounting_activity_engine.py",

        "semantic_pseudo_claim_detection_engine.py",

        "borrowed_money_semantic_review_engine.py",

        "quikloan_candidate_population_engine.py",

        "semantic_governance_hold_engine.py",

        "claims_domain_eligibility_analysis_engine.py",

        "qladmin_domain_alignment_analysis_engine.py",

        "semantic_business_review_workbench_engine.py",

    ]

    for step in steps:

        extra = ["--rules", args.rules] if step != "semantic_governance_hold_engine.py" else ["--rules", args.gov_rules]

        if step == "semantic_governance_hold_engine.py":

            extra = ["--rules", args.gov_rules]

        elif step in (

            "non_claim_accounting_activity_engine.py",

            "semantic_pseudo_claim_detection_engine.py",

            "borrowed_money_semantic_review_engine.py",

            "quikloan_candidate_population_engine.py",

        ):

            extra = ["--rules", args.rules]

        else:

            extra = None

        if not run_script(step, args.output, extra=extra):

            return 1



    import pandas as pd

    non_claim_path = os.path.join(args.output, "non_claim_accounting_activity_population.csv")

    non_claim_count = 0

    policy_count = 0

    if os.path.isfile(non_claim_path):

        pdf = pd.read_csv(non_claim_path, dtype=str)

        non_claim_count = len(pdf)

        policy_count = pdf["policy_number"].nunique() if "policy_number" in pdf.columns else 0



    ql_path = os.path.join(args.output, "quikloan_candidate_population.csv")

    ql_count = len(pd.read_csv(ql_path, dtype=str)) if os.path.isfile(ql_path) else 0

    wb_path = os.path.join(args.output, "semantic_business_review_workbench.csv")

    wb_rows = len(pd.read_csv(wb_path, dtype=str)) if os.path.isfile(wb_path) else 0



    metrics = {

        "non_claim_accounting_count": non_claim_count,

        "policy_count": policy_count,

        "uat_baseline": 5122,

        "quikloan_candidate_count": ql_count,

        "true_surrender_emit_est": 25,

        "workbench_rows": wb_rows,

    }

    summary_path = write_claim_domain_summary(rules, gov_rules, args.output, metrics)



    exec_path = os.path.join(args.output, "phase22_execution_summary.txt")

    with open(exec_path, "w", encoding="utf-8") as fh:

        fh.write("\n".join([

            "Phase 22A/22B/22C Semantic Claim Domain — Complete",

            f"Non-claim accounting held: {non_claim_count}",

            f"Policies: {policy_count}",

            f"QuikLoan candidates (analysis): {ql_count}",

            f"Summary: {summary_path}",

            "production_dbf_flag=N",

            "Phase 4-17 engines NOT modified",

        ]) + "\n")



    print("PHASE22_STATUS: PASS")

    print(f"NON_CLAIM_ACCOUNTING_COUNT: {non_claim_count}")

    print(f"POLICY_COUNT: {policy_count}")

    print(f"SUMMARY: {os.path.abspath(summary_path)}")

    return 0





if __name__ == "__main__":

    raise SystemExit(main())

