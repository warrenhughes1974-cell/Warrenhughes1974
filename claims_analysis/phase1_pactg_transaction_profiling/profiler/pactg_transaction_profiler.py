#!/usr/bin/env python3
"""
Phase 1 — PACTG transaction semantic profiler (read-only).

Profiles LifePRO accounting extract CSVs for claims conversion onboarding.
Does NOT modify source data, app.py, or emit QUIKCLMS/QUIKCLMP output.
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime

import pandas as pd


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RULES_PATH = os.path.join(SCRIPT_DIR, "config", "claim_family_rules.json")

REQUIRED_COLUMNS = ("TRANS_AMOUNT", "POLICY_NUMBER")
OPTIONAL_COLUMNS = (
    "CREDIT_CODE", "DEBIT_CODE", "CREDIT_ACCOUNT", "DEBIT_ACCOUNT",
    "DESCRIPTION", "DISTRIBUTION_CODE", "PAYEE_RELA_CODE", "PAYEE_SEQUENCE",
    "BENEFIT_SEQ", "EFFECTIVE_DATE",
)

REVERSAL_DESCRIPTION_PATTERNS = re.compile(
    r"REVERS|OFFSET|CORRECT|VOID|CANCEL|REVERSE|CHARGEBACK|ADJUSTMENT",
    re.IGNORECASE,
)

logger = logging.getLogger("pactg_profiler")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_claim_family_rules(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return {str(k): v for k, v in raw.items()}


def normalize_header(name):
    return str(name).strip().upper()


def normalize_columns(df):
    mapping = {c: normalize_header(c) for c in df.columns}
    return df.rename(columns=mapping)


def norm_code(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    s = str(value).strip()
    if not s or set(s) == {"-"}:
        return ""
    digits = re.sub(r"[^0-9]", "", s)
    if digits:
        try:
            return str(int(digits))
        except ValueError:
            return ""
    return s.upper()


def is_separator_row(row):
    amount = str(row.get("TRANS_AMOUNT", "")).strip()
    if amount and set(amount.replace(" ", "")) == {"-"}:
        return True
    for col in ("CREDIT_CODE", "DEBIT_CODE", "POLICY_NUMBER"):
        val = str(row.get(col, "")).strip()
        if val and set(val.replace(" ", "")) == {"-"}:
            return True
    return False


def parse_amount(value):
    """
    Parse TRANS_AMOUNT; supports decimal-leading values (.12).
    Returns (float_or_none, is_malformed).
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None, False
    raw = str(value).strip()
    if not raw or set(raw.replace(" ", "")) == {"-"}:
        return None, False
    cleaned = raw.replace(",", "").replace("$", "").strip()
    if cleaned.startswith("."):
        cleaned = "0" + cleaned
    if cleaned.startswith("-."):
        cleaned = "-0" + cleaned[1:]
    try:
        return float(cleaned), False
    except ValueError:
        return None, True


def parse_effective_date(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = re.sub(r"[^0-9]", "", str(value).strip())
    if len(s) == 8:
        try:
            return datetime.strptime(s, "%Y%m%d")
        except ValueError:
            return None
    return None


def resolve_column(df, name):
    return name if name in df.columns else None


def codes_observed_series(codes):
    unique = sorted({c for c in codes if c})
    return "|".join(unique)


# ---------------------------------------------------------------------------
# Load & prepare
# ---------------------------------------------------------------------------

def load_pactg(path):
    logger.info("Reading PACTG extract: %s", path)
    df = pd.read_csv(path, encoding="latin1", dtype=str, low_memory=False)
    df = normalize_columns(df)

    missing_critical = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_critical:
        raise ValueError(f"Missing required columns: {', '.join(missing_critical)}")

    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            logger.warning("Optional column missing (will use blanks): %s", col)
            df[col] = ""

    df["source_row_number"] = range(2, len(df) + 2)

    separator_mask = df.apply(is_separator_row, axis=1)
    separator_count = int(separator_mask.sum())
    df = df[~separator_mask].copy()

    amounts = df["TRANS_AMOUNT"].apply(parse_amount)
    df["amount_parsed"] = amounts.apply(lambda x: x[0])
    df["amount_malformed"] = amounts.apply(lambda x: x[1])
    df["effective_date_parsed"] = df["EFFECTIVE_DATE"].apply(parse_effective_date)

    df["credit_code_norm"] = df["CREDIT_CODE"].apply(norm_code)
    df["debit_code_norm"] = df["DEBIT_CODE"].apply(norm_code)
    df["policy_norm"] = df["POLICY_NUMBER"].astype(str).str.strip()

    stats = {
        "total_rows_read": len(df) + separator_count,
        "separator_rows_skipped": separator_count,
        "usable_rows": len(df),
        "trans_amount_populated": int(df["amount_parsed"].notna().sum()),
        "malformed_amount_count": int(df["amount_malformed"].sum()),
        "distinct_policies": int(df["policy_norm"].nunique()),
        "distinct_credit_codes": int(df["credit_code_norm"].replace("", pd.NA).dropna().nunique()),
        "distinct_debit_codes": int(df["debit_code_norm"].replace("", pd.NA).dropna().nunique()),
    }

    valid_dates = df["effective_date_parsed"].dropna()
    stats["earliest_effective_date"] = (
        valid_dates.min().strftime("%Y%m%d") if not valid_dates.empty else ""
    )
    stats["latest_effective_date"] = (
        valid_dates.max().strftime("%Y%m%d") if not valid_dates.empty else ""
    )

    logger.info(
        "Loaded %s usable rows (%s separators skipped)",
        stats["usable_rows"],
        stats["separator_rows_skipped"],
    )
    return df, stats


# ---------------------------------------------------------------------------
# Report builders
# ---------------------------------------------------------------------------

def amount_stats(series):
    valid = series.dropna()
    if valid.empty:
        return {
            "total_amount": 0.0,
            "positive_amount_count": 0,
            "negative_amount_count": 0,
            "zero_amount_count": 0,
            "min_amount": "",
            "max_amount": "",
            "avg_amount": "",
            "median_amount": "",
        }
    return {
        "total_amount": round(float(valid.sum()), 2),
        "positive_amount_count": int((valid > 0).sum()),
        "negative_amount_count": int((valid < 0).sum()),
        "zero_amount_count": int((valid == 0).sum()),
        "min_amount": round(float(valid.min()), 2),
        "max_amount": round(float(valid.max()), 2),
        "avg_amount": round(float(valid.mean()), 4),
        "median_amount": round(float(valid.median()), 4),
    }


def date_range(sub):
    dates = sub["effective_date_parsed"].dropna()
    if dates.empty:
        return "", ""
    return dates.min().strftime("%Y%m%d"), dates.max().strftime("%Y%m%d")


def build_transaction_code_frequency(df):
    rows = []
    for position, col in (("CREDIT_CODE", "credit_code_norm"), ("DEBIT_CODE", "debit_code_norm")):
        grouped = df[df[col] != ""].groupby(col, dropna=False)
        for code, sub in grouped:
            stats = amount_stats(sub["amount_parsed"])
            earliest, latest = date_range(sub)
            rows.append({
                "transaction_code": code,
                "code_position": position,
                "row_count": len(sub),
                "distinct_policy_count": sub["policy_norm"].nunique(),
                "total_amount": stats["total_amount"],
                "positive_amount_count": stats["positive_amount_count"],
                "negative_amount_count": stats["negative_amount_count"],
                "zero_amount_count": stats["zero_amount_count"],
                "min_amount": stats["min_amount"],
                "max_amount": stats["max_amount"],
                "avg_amount": stats["avg_amount"],
                "earliest_effective_date": earliest,
                "latest_effective_date": latest,
            })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(
        ["row_count", "code_position", "transaction_code"],
        ascending=[False, True, True],
    ).reset_index(drop=True)


def build_transaction_amount_statistics(df):
    credit = df.loc[df["credit_code_norm"] != "", ["credit_code_norm", "amount_parsed", "amount_malformed"]].rename(
        columns={"credit_code_norm": "transaction_code"},
    )
    debit = df.loc[df["debit_code_norm"] != "", ["debit_code_norm", "amount_parsed", "amount_malformed"]].rename(
        columns={"debit_code_norm": "transaction_code"},
    )

    credit_counts = credit.groupby("transaction_code", sort=False).size()
    debit_counts = debit.groupby("transaction_code", sort=False).size()
    malformed_counts = (
        pd.concat([
            credit.loc[credit["amount_malformed"], "transaction_code"],
            debit.loc[debit["amount_malformed"], "transaction_code"],
        ])
        .value_counts()
    )

    all_codes = sorted(set(credit_counts.index) | set(debit_counts.index))
    rows = []
    for code in all_codes:
        credit_amts = credit.loc[credit["transaction_code"] == code, "amount_parsed"]
        debit_amts = debit.loc[debit["transaction_code"] == code, "amount_parsed"]
        amounts = pd.concat([credit_amts, debit_amts], ignore_index=True)
        stats = amount_stats(amounts)
        credit_n = int(credit_counts.get(code, 0))
        debit_n = int(debit_counts.get(code, 0))
        abs_total = round(float(amounts.abs().sum()), 2) if not amounts.empty else 0.0
        rows.append({
            "transaction_code": code,
            "credit_row_count": credit_n,
            "debit_row_count": debit_n,
            "combined_row_count": credit_n + debit_n,
            "combined_total_amount": stats["total_amount"],
            "absolute_total_amount": abs_total,
            "min_amount": stats["min_amount"],
            "max_amount": stats["max_amount"],
            "avg_amount": stats["avg_amount"],
            "median_amount": stats["median_amount"],
            "malformed_amount_count": int(malformed_counts.get(code, 0)),
        })

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(
        ["combined_row_count", "transaction_code"],
        ascending=[False, True],
    ).reset_index(drop=True)


def build_pair_analysis(df, credit_col, debit_col, out_credit_name, out_debit_name):
    sub = df[(df[credit_col] != "") | (df[debit_col] != "")].copy()
    if sub.empty:
        return pd.DataFrame()

    grouped = sub.groupby([credit_col, debit_col], dropna=False)
    rows = []
    for (credit, debit), g in grouped:
        stats = amount_stats(g["amount_parsed"])
        earliest, latest = date_range(g)
        rows.append({
            out_credit_name: credit,
            out_debit_name: debit,
            "row_count": len(g),
            "distinct_policy_count": g["policy_norm"].nunique(),
            **{k: stats[k] for k in ("total_amount", "min_amount", "max_amount", "avg_amount")},
            "earliest_effective_date": earliest,
            "latest_effective_date": latest,
        })
    out = pd.DataFrame(rows)
    return out.sort_values(["row_count", out_credit_name, out_debit_name], ascending=[False, True, True]).reset_index(drop=True)


def build_relationship_distribution(df):
    sub = df.copy()
    sub["payee_rela_code"] = sub["PAYEE_RELA_CODE"].astype(str).str.strip()
    sub["payee_sequence"] = sub["PAYEE_SEQUENCE"].astype(str).str.strip()

    rows = []
    grouped = sub.groupby(["payee_rela_code", "payee_sequence"], dropna=False)
    for (rela, seq), g in grouped:
        cc = codes_observed_series(g["credit_code_norm"].tolist() + g["debit_code_norm"].tolist())
        earliest, latest = date_range(g)
        stats = amount_stats(g["amount_parsed"])
        rows.append({
            "payee_rela_code": rela,
            "payee_sequence": seq,
            "row_count": len(g),
            "distinct_policy_count": g["policy_norm"].nunique(),
            "total_amount": stats["total_amount"],
            "transaction_codes_observed": cc,
            "earliest_effective_date": earliest,
            "latest_effective_date": latest,
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["row_count", "payee_rela_code"], ascending=[False, True]).reset_index(drop=True)


def build_code_distribution(df, code_col, rela_col=None):
    sub = df.copy()
    sub["code_value"] = sub[code_col].astype(str).str.strip()
    rows = []
    grouped = sub.groupby("code_value", dropna=False)
    for code, g in grouped:
        tx_codes = codes_observed_series(g["credit_code_norm"].tolist() + g["debit_code_norm"].tolist())
        rel_codes = ""
        if rela_col and rela_col in g.columns:
            rel_codes = codes_observed_series(g[rela_col].astype(str).str.strip().tolist())
        stats = amount_stats(g["amount_parsed"])
        rows.append({
            code_col.lower(): code,
            "row_count": len(g),
            "distinct_policy_count": g["policy_norm"].nunique(),
            "total_amount": stats["total_amount"],
            "transaction_codes_observed": tx_codes,
            "relationship_codes_observed": rel_codes,
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    col = code_col.lower()
    return out.sort_values(["row_count", col], ascending=[False, True]).reset_index(drop=True)


def _vectorized_claim_metadata(sub, rules):
    """Assign claim family metadata; credit code takes precedence over debit."""
    credit_families = sub["credit_code_norm"].map(
        lambda c: rules[c]["family"] if c in rules else "",
    )
    debit_families = sub["debit_code_norm"].map(
        lambda c: rules[c]["family"] if c in rules else "",
    )
    credit_labels = sub["credit_code_norm"].map(
        lambda c: rules[c]["label"] if c in rules else "",
    )
    debit_labels = sub["debit_code_norm"].map(
        lambda c: rules[c]["label"] if c in rules else "",
    )
    credit_hit = sub["credit_code_norm"].isin(rules)
    families = credit_families.where(credit_hit, debit_families)
    labels = credit_labels.where(credit_hit, debit_labels)
    components = pd.Series(
        ["CREDIT_CODE" if hit else ("DEBIT_CODE" if fam else "")
         for hit, fam in zip(credit_hit, debit_families)],
        index=sub.index,
    )
    components = components.where(components != "", labels)
    return families, labels, components


def build_potential_claim_activity(df, rules):
    claim_codes = set(rules.keys())
    mask = df["credit_code_norm"].isin(claim_codes) | df["debit_code_norm"].isin(claim_codes)
    sub = df.loc[mask].copy()
    if sub.empty:
        return sub

    families, labels, components = _vectorized_claim_metadata(sub, rules)
    out = pd.DataFrame({
        "policy_number": sub["POLICY_NUMBER"],
        "effective_date": sub["EFFECTIVE_DATE"],
        "credit_code": sub["CREDIT_CODE"],
        "debit_code": sub["DEBIT_CODE"],
        "credit_account": sub["CREDIT_ACCOUNT"],
        "debit_account": sub["DEBIT_ACCOUNT"],
        "trans_amount": sub["TRANS_AMOUNT"],
        "distribution_code": sub["DISTRIBUTION_CODE"],
        "payee_rela_code": sub["PAYEE_RELA_CODE"],
        "payee_sequence": sub["PAYEE_SEQUENCE"],
        "benefit_seq": sub["BENEFIT_SEQ"],
        "description": sub["DESCRIPTION"],
        "claim_family_candidate": families,
        "financial_component_candidate": components,
        "source_row_number": sub["source_row_number"],
    })
    return out.sort_values(
        ["policy_number", "effective_date", "source_row_number"],
        ascending=[True, True, True],
    ).reset_index(drop=True)


def _reversal_output_columns(sub, reason):
    return pd.DataFrame({
        "policy_number": sub["POLICY_NUMBER"],
        "effective_date": sub["EFFECTIVE_DATE"],
        "credit_code": sub["CREDIT_CODE"],
        "debit_code": sub["DEBIT_CODE"],
        "trans_amount": sub["TRANS_AMOUNT"],
        "description": sub["DESCRIPTION"],
        "reversal_reason_candidate": reason,
        "source_row_number": sub["source_row_number"],
    })


def build_reversal_candidates(df):
    parts = []

    negative = df.loc[df["amount_parsed"].notna() & (df["amount_parsed"] < 0)]
    if not negative.empty:
        parts.append(_reversal_output_columns(negative, "NEGATIVE_TRANS_AMOUNT"))

    desc_match = df["DESCRIPTION"].astype(str).str.contains(
        REVERSAL_DESCRIPTION_PATTERNS, na=False,
    )
    if desc_match.any():
        parts.append(_reversal_output_columns(df.loc[desc_match], "REVERSAL_DESCRIPTION_TEXT"))

    work = df.loc[df["amount_parsed"].notna()].copy()
    work["eff_str"] = work["effective_date_parsed"].apply(
        lambda d: d.strftime("%Y%m%d") if pd.notna(d) else "",
    )

    pair_cols = ["policy_norm", "eff_str", "credit_code_norm", "debit_code_norm"]
    pair_agg = work.groupby(pair_cols, sort=False)["amount_parsed"].agg(
        row_count="count",
        has_pos=lambda s: (s > 0).any(),
        has_neg=lambda s: (s < 0).any(),
    )
    pair_keys = pair_agg[
        (pair_agg["row_count"] >= 2) & pair_agg["has_pos"] & pair_agg["has_neg"]
    ].reset_index()[pair_cols]
    if not pair_keys.empty:
        flagged = work.merge(pair_keys, on=pair_cols, how="inner")
        parts.append(_reversal_output_columns(flagged, "SAME_DAY_OPPOSITE_SIGNS"))

    for code_col, label in (("credit_code_norm", "CREDIT_CODE"), ("debit_code_norm", "DEBIT_CODE")):
        keyed = work.loc[work[code_col] != ""]
        if keyed.empty:
            continue
        offset_agg = keyed.groupby(["policy_norm", code_col], sort=False)["amount_parsed"].agg(
            row_count="count",
            total="sum",
            has_pos=lambda s: (s > 0).any(),
            has_neg=lambda s: (s < 0).any(),
        )
        offset_keys = offset_agg[
            (offset_agg["row_count"] >= 2)
            & (offset_agg["total"].abs() < 0.01)
            & offset_agg["has_pos"]
            & offset_agg["has_neg"]
        ].reset_index()[["policy_norm", code_col]]
        if offset_keys.empty:
            continue
        flagged = keyed.merge(offset_keys, on=["policy_norm", code_col], how="inner")
        parts.append(_reversal_output_columns(flagged, f"OFFSETTING_{label}_AMOUNTS"))

    if not parts:
        return pd.DataFrame()

    out = pd.concat(parts, ignore_index=True)
    out = out.drop_duplicates(subset=["source_row_number", "reversal_reason_candidate"])
    return out.sort_values(
        ["policy_number", "effective_date", "source_row_number", "reversal_reason_candidate"],
        ascending=[True, True, True, True],
    ).reset_index(drop=True)


def write_summary(path, input_path, stats, output_files):
    lines = [
        "=== PACTG Transaction Profile Summary ===",
        f"Input file: {os.path.abspath(input_path)}",
        f"Total rows read: {stats['total_rows_read']}",
        f"Separator rows skipped: {stats['separator_rows_skipped']}",
        f"Usable rows: {stats['usable_rows']}",
        f"TRANS_AMOUNT populated count: {stats['trans_amount_populated']}",
        f"Malformed amount count: {stats['malformed_amount_count']}",
        f"Distinct policies: {stats['distinct_policies']}",
        f"Distinct CREDIT_CODE count: {stats['distinct_credit_codes']}",
        f"Distinct DEBIT_CODE count: {stats['distinct_debit_codes']}",
        f"Earliest EFFECTIVE_DATE: {stats['earliest_effective_date']}",
        f"Latest EFFECTIVE_DATE: {stats['latest_effective_date']}",
        "",
        "Output files generated:",
    ]
    for f in output_files:
        lines.append(f"  - {f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_profiler(input_path, output_dir, rules_path):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_claim_family_rules(rules_path)
    df, stats = load_pactg(input_path)

    reports = {}

    logger.info("Building transaction_code_frequency.csv")
    reports["transaction_code_frequency.csv"] = build_transaction_code_frequency(df)

    logger.info("Building transaction_amount_statistics.csv")
    reports["transaction_amount_statistics.csv"] = build_transaction_amount_statistics(df)

    logger.info("Building transaction_pair_analysis.csv")
    reports["transaction_pair_analysis.csv"] = build_pair_analysis(
        df, "credit_code_norm", "debit_code_norm", "credit_code", "debit_code",
    )

    logger.info("Building account_pair_analysis.csv")
    df_acct = df.copy()
    df_acct["credit_account_norm"] = df_acct["CREDIT_ACCOUNT"].astype(str).str.strip()
    df_acct["debit_account_norm"] = df_acct["DEBIT_ACCOUNT"].astype(str).str.strip()
    reports["account_pair_analysis.csv"] = build_pair_analysis(
        df_acct, "credit_account_norm", "debit_account_norm", "credit_account", "debit_account",
    )

    logger.info("Building relationship_distribution_analysis.csv")
    reports["relationship_distribution_analysis.csv"] = build_relationship_distribution(df)

    logger.info("Building distribution_code_analysis.csv")
    dist = build_code_distribution(df, "DISTRIBUTION_CODE", "PAYEE_RELA_CODE")
    if not dist.empty:
        dist = dist.rename(columns={"distribution_code": "distribution_code"})
    reports["distribution_code_analysis.csv"] = dist

    logger.info("Building benefit_sequence_analysis.csv")
    ben = build_code_distribution(df, "BENEFIT_SEQ", "PAYEE_RELA_CODE")
    if not ben.empty:
        ben = ben.rename(columns={"benefit_seq": "benefit_seq"})
    reports["benefit_sequence_analysis.csv"] = ben

    logger.info("Building potential_claim_activity.csv")
    reports["potential_claim_activity.csv"] = build_potential_claim_activity(df, rules)

    logger.info("Building reversal_candidate_analysis.csv")
    reports["reversal_candidate_analysis.csv"] = build_reversal_candidates(df)

    output_files = []
    for filename, frame in reports.items():
        out_path = os.path.join(output_dir, filename)
        frame.to_csv(out_path, index=False, encoding="utf-8")
        output_files.append(out_path)
        logger.info("Wrote %s (%s rows)", filename, len(frame))

    summary_path = os.path.join(output_dir, "pactg_profile_summary.txt")
    write_summary(summary_path, input_path, stats, output_files)
    output_files.append(summary_path)
    logger.info("Wrote pactg_profile_summary.txt")

    return stats, output_files


def main():
    parser = argparse.ArgumentParser(
        description="Read-only PACTG transaction semantic profiler (Phase 1 claims intelligence).",
    )
    parser.add_argument("--input", required=True, help="Path to PACTG accounting extract CSV")
    parser.add_argument("--output", required=True, help="Output directory for profiling reports")
    parser.add_argument(
        "--rules",
        default=DEFAULT_RULES_PATH,
        help="Claim family rules JSON (profiling metadata only)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if not os.path.isfile(args.input):
        logger.error("Input file not found: %s", args.input)
        return 1

    try:
        stats, outputs = run_profiler(args.input, args.output, args.rules)
        print(f"Profiling complete. Usable rows: {stats['usable_rows']}")
        print(f"TRANS_AMOUNT populated: {stats['trans_amount_populated']}")
        print(f"Output directory: {os.path.abspath(args.output)}")
        for p in outputs:
            print(f"  {p}")
        return 0
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
