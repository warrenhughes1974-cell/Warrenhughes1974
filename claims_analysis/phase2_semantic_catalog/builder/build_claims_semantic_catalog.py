#!/usr/bin/env python3
"""
Phase 2 — Build claims semantic catalog and data quality findings (read-only).

Merges seeded transaction-code semantics with Phase 1 profiler observations.
Does NOT modify app.py or generate QUIKCLMS/QUIKCLMP output.
"""

import argparse
import json
import logging
import os
import sys

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SEMANTICS_PATH = os.path.join(SCRIPT_DIR, "config", "transaction_code_semantics.json")
DEFAULT_PROFILER_OUTPUT = os.path.join(SCRIPT_DIR, "output")
DEFAULT_CATALOG_PATH = os.path.join(SCRIPT_DIR, "Claims_Transaction_Code_Catalog.csv")
DEFAULT_DQ_PATH = os.path.join(SCRIPT_DIR, "data_quality_findings.csv")

# Reasonable conversion window for future-date detection (inclusive).
FUTURE_DATE_CUTOFF = "20301231"
LARGE_AMOUNT_THRESHOLD = 50000.0

CATALOG_COLUMNS = [
    "transaction_code",
    "known_description",
    "claim_relevant_flag",
    "claim_family",
    "financial_component",
    "lifecycle_role",
    "payment_indicator",
    "tax_indicator",
    "interest_indicator",
    "loan_offset_indicator",
    "surrender_indicator",
    "reversal_sensitive_flag",
    "observed_credit_count",
    "observed_debit_count",
    "observed_total_amount",
    "observed_pairings",
    "confidence_level",
    "notes",
]

logger = logging.getLogger("claims_catalog_builder")


def format_transaction_code(code):
    return str(int(code)).zfill(4)


def load_semantics(path):
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    return {str(int(k)): v for k, v in raw.items()}


def load_amount_stats(profiler_dir):
    path = os.path.join(profiler_dir, "transaction_amount_statistics.csv")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Profiler output not found: {path}")
    df = pd.read_csv(path, dtype=str)
    df["transaction_code"] = df["transaction_code"].astype(str).str.strip()
    for col in ("credit_row_count", "debit_row_count", "combined_total_amount"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df.set_index("transaction_code")


def build_pairings(profiler_dir, code, limit=8):
    path = os.path.join(profiler_dir, "transaction_pair_analysis.csv")
    if not os.path.isfile(path):
        return ""
    pairs = pd.read_csv(path, dtype=str)
    for col in ("credit_code", "debit_code", "row_count"):
        pairs[col] = pairs[col].astype(str).str.strip()
    pairs["row_count"] = pd.to_numeric(pairs["row_count"], errors="coerce").fillna(0)

    as_credit = pairs[pairs["credit_code"] == code].copy()
    as_credit["pair_label"] = as_credit["credit_code"] + "|" + as_credit["debit_code"]
    as_debit = pairs[pairs["debit_code"] == code].copy()
    as_debit["pair_label"] = as_debit["credit_code"] + "|" + as_debit["debit_code"]

    combined = pd.concat([as_credit, as_debit], ignore_index=True)
    if combined.empty:
        return ""

    combined = combined.sort_values(["row_count", "pair_label"], ascending=[False, True])
    labels = []
    for _, row in combined.head(limit).iterrows():
        labels.append(f"{row['pair_label']}({int(row['row_count'])})")
    return ";".join(labels)


def build_catalog(semantics, profiler_dir):
    stats = load_amount_stats(profiler_dir)
    rows = []
    for code in sorted(semantics.keys(), key=lambda c: int(c)):
        meta = semantics[code]
        tx_code = format_transaction_code(code)
        if code in stats.index:
            observed_credit = int(stats.at[code, "credit_row_count"])
            observed_debit = int(stats.at[code, "debit_row_count"])
            observed_total = round(float(stats.at[code, "combined_total_amount"]), 2)
            pairings = build_pairings(profiler_dir, code)
            confidence = meta["confidence_level"]
            notes = meta["notes"]
        else:
            observed_credit = 0
            observed_debit = 0
            observed_total = 0.0
            pairings = ""
            confidence = meta["confidence_level"]
            notes = meta["notes"]
            if "not observed" not in notes.lower():
                notes = f"{notes} Not observed in current profiler output."

        rows.append({
            "transaction_code": tx_code,
            "known_description": meta["known_description"],
            "claim_relevant_flag": meta["claim_relevant_flag"],
            "claim_family": meta["claim_family"],
            "financial_component": meta["financial_component"],
            "lifecycle_role": meta["lifecycle_role"],
            "payment_indicator": meta["payment_indicator"],
            "tax_indicator": meta["tax_indicator"],
            "interest_indicator": meta["interest_indicator"],
            "loan_offset_indicator": meta["loan_offset_indicator"],
            "surrender_indicator": meta["surrender_indicator"],
            "reversal_sensitive_flag": meta["reversal_sensitive_flag"],
            "observed_credit_count": observed_credit,
            "observed_debit_count": observed_debit,
            "observed_total_amount": observed_total,
            "observed_pairings": pairings,
            "confidence_level": confidence,
            "notes": notes,
        })

    return pd.DataFrame(rows, columns=CATALOG_COLUMNS)


def _sample_rows(df, n=5):
    if df.empty:
        return ""
    return "|".join(str(v) for v in df["source_row_number"].head(n).tolist())


def _blank(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return True
    s = str(value).strip()
    return s == "" or s.lower() in {"nan", "none"}


def build_data_quality_findings(pactg_path, claim_codes):
    from pactg_transaction_profiler import load_pactg

    df, stats = load_pactg(pactg_path)
    findings = []

    def add_finding(category, description, subset, severity, notes="", extra=None):
        row = {
            "finding_category": category,
            "finding_description": description,
            "row_count": len(subset),
            "distinct_policy_count": int(subset["policy_norm"].nunique()) if len(subset) else 0,
            "min_trans_amount": "",
            "max_trans_amount": "",
            "sample_policy_number": "",
            "sample_effective_date": "",
            "sample_source_row_numbers": _sample_rows(subset),
            "severity": severity,
            "notes": notes,
        }
        if len(subset) and subset["amount_parsed"].notna().any():
            valid = subset["amount_parsed"].dropna()
            row["min_trans_amount"] = round(float(valid.min()), 2)
            row["max_trans_amount"] = round(float(valid.max()), 2)
        if len(subset):
            sample = subset.iloc[0]
            row["sample_policy_number"] = str(sample["POLICY_NUMBER"]).strip()
            row["sample_effective_date"] = str(sample["EFFECTIVE_DATE"]).strip()
        if extra:
            row.update(extra)
        findings.append(row)

    invalid_dates = df[df["EFFECTIVE_DATE"].astype(str).str.strip() != ""]
    invalid_dates = invalid_dates[invalid_dates["effective_date_parsed"].isna()]
    add_finding(
        "INVALID_EFFECTIVE_DATE",
        "EFFECTIVE_DATE present but not parseable as YYYYMMDD",
        invalid_dates,
        "HIGH",
        f"Profiler earliest/latest: {stats.get('earliest_effective_date', '')} / {stats.get('latest_effective_date', '')}",
    )

    parsed_dates = df[df["effective_date_parsed"].notna()].copy()
    future_cutoff = pd.to_datetime(FUTURE_DATE_CUTOFF, format="%Y%m%d")
    future_dates = parsed_dates[parsed_dates["effective_date_parsed"] > future_cutoff]
    add_finding(
        "FUTURE_EFFECTIVE_DATE",
        f"EFFECTIVE_DATE after conversion cutoff {FUTURE_DATE_CUTOFF}",
        future_dates,
        "HIGH",
        "Includes sentinel/garbage dates such as 50500904 observed in extract.",
    )

    claim_mask = df["credit_code_norm"].isin(claim_codes) | df["debit_code_norm"].isin(claim_codes)
    claim_rows = df[claim_mask].copy()

    blank_rela = claim_rows[claim_rows["PAYEE_RELA_CODE"].apply(_blank)]
    add_finding(
        "BLANK_RELATIONSHIP_CODE",
        "Claim-relevant row with blank PAYEE_RELA_CODE",
        blank_rela,
        "MEDIUM",
        "Payee relationship may be required for QUIKCLMP distribution reconstruction.",
    )

    payout_like = claim_rows[
        claim_rows["credit_code_norm"].isin({"94", "90", "1900"})
        | claim_rows["debit_code_norm"].isin({"94", "90", "1900", "567"})
    ]
    missing_dist = payout_like[payout_like["DISTRIBUTION_CODE"].apply(_blank)]
    add_finding(
        "MISSING_DISTRIBUTION_CODE",
        "Claim payment/disbursement row with blank DISTRIBUTION_CODE",
        missing_dist,
        "MEDIUM",
        "Distribution code often present on payout rows (e.g. code 94 with PE relationship).",
    )

    benefit_zero = claim_rows[claim_rows["BENEFIT_SEQ"].astype(str).str.strip().isin({"0", "0.0"})]
    add_finding(
        "BENEFIT_SEQ_ZERO",
        "Claim-relevant row with BENEFIT_SEQ = 0",
        benefit_zero,
        "LOW",
        "May be valid for base benefit; flag for lifecycle review.",
    )

    large_amounts = df[df["amount_parsed"].notna() & (df["amount_parsed"].abs() >= LARGE_AMOUNT_THRESHOLD)]
    add_finding(
        "UNUSUALLY_LARGE_AMOUNT",
        f"TRANS_AMOUNT absolute value >= {LARGE_AMOUNT_THRESHOLD:,.0f}",
        large_amounts,
        "MEDIUM",
        "Large-value transactions warrant manual review during claim reconstruction.",
    )

    negative_amounts = df[df["amount_parsed"].notna() & (df["amount_parsed"] < 0)]
    add_finding(
        "NEGATIVE_TRANS_AMOUNT",
        "Row with negative TRANS_AMOUNT",
        negative_amounts,
        "HIGH",
        "Potential reversal/correction activity; cross-reference reversal_candidate_analysis.csv.",
    )

    out = pd.DataFrame(findings)
    return out.sort_values(
        ["severity", "finding_category"],
        ascending=[True, True],
    ).reset_index(drop=True)


def run_builder(pactg_path, profiler_dir, semantics_path, catalog_path, dq_path):
    semantics = load_semantics(semantics_path)
    catalog = build_catalog(semantics, profiler_dir)
    catalog.to_csv(catalog_path, index=False, encoding="utf-8")
    logger.info("Wrote %s (%s codes)", catalog_path, len(catalog))

    dq = build_data_quality_findings(pactg_path, set(semantics.keys()))
    dq.to_csv(dq_path, index=False, encoding="utf-8")
    logger.info("Wrote %s (%s findings)", dq_path, len(dq))

    return catalog, dq


def main():
    parser = argparse.ArgumentParser(
        description="Build Phase 2 claims semantic catalog and data quality findings.",
    )
    parser.add_argument(
        "--pactg",
        default=os.path.join("docs", "claims_conversion_reference", "PACTG_Accounting_Extract20260427.csv"),
        help="Path to PACTG accounting extract CSV",
    )
    parser.add_argument(
        "--profiler-output",
        default=DEFAULT_PROFILER_OUTPUT,
        help="Directory containing Phase 1 profiler CSV reports",
    )
    parser.add_argument(
        "--semantics",
        default=DEFAULT_SEMANTICS_PATH,
        help="Seeded transaction code semantics JSON",
    )
    parser.add_argument(
        "--catalog-output",
        default=DEFAULT_CATALOG_PATH,
        help="Output path for Claims_Transaction_Code_Catalog.csv",
    )
    parser.add_argument(
        "--dq-output",
        default=DEFAULT_DQ_PATH,
        help="Output path for data_quality_findings.csv",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if not os.path.isfile(args.pactg):
        logger.error("PACTG input not found: %s", args.pactg)
        return 1
    if not os.path.isdir(args.profiler_output):
        logger.error("Profiler output directory not found: %s", args.profiler_output)
        return 1

    sys.path.insert(0, SCRIPT_DIR)
    try:
        catalog, dq = run_builder(
            args.pactg,
            args.profiler_output,
            args.semantics,
            args.catalog_output,
            args.dq_output,
        )
        print(f"Catalog codes: {len(catalog)}")
        print(f"Data quality findings: {len(dq)}")
        print(f"Catalog: {os.path.abspath(args.catalog_output)}")
        print(f"Data quality: {os.path.abspath(args.dq_output)}")
        return 0
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
