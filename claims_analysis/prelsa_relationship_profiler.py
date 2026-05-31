#!/usr/bin/env python3
"""
Phase 3 — PRELSA relationship intelligence profiler (read-only).

Profiles LifePRO RelationshipNameAddress extracts for claims payee resolution
onboarding. Does NOT modify source data, app.py, or emit QUIKCLMS/QUIKCLMP output.
"""

import argparse
import json
import logging
import os
import re
import sys

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SEMANTICS_PATH = os.path.join(SCRIPT_DIR, "config", "relationship_code_semantics.json")
DEFAULT_CLAIM_RULES_PATH = os.path.join(SCRIPT_DIR, "config", "claim_family_rules.json")

REQUIRED_COLUMNS = ("POLICY_NUMBER", "NAME_ID")
OPTIONAL_COLUMNS = (
    "RELATE_CODE", "BENEFIT_SEQ_NUMBER", "NAME_FORMAT_CODE",
    "INDIVIDUAL_LAST", "INDIVIDUAL_FIRST", "NAME_BUSINESS",
    "SOC_SEC_NUMBER", "BUSINESS_TAX_CODE", "DATE_OF_BIRTH",
    "ADDR_LINE_1", "ADDR_LINE_2", "ADDR_LINE_3", "CITY", "STATE", "ZIP",
    "COUNTRY", "TELE_NUM", "COMM_PCNT",
)

US_COUNTRY_VALUES = {"", "US", "USA", "UNITED STATES", "U.S.", "U.S.A."}

logger = logging.getLogger("prelsa_profiler")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_header(name):
    return str(name).strip().upper()


def dedupe_columns(df):
    seen = set()
    keep = []
    for i, col in enumerate(df.columns):
        if col not in seen:
            seen.add(col)
            keep.append(i)
    out = df.iloc[:, keep].copy()
    out.columns = [df.columns[i] for i in keep]
    return out


def normalize_columns(df):
    df = df.copy()
    df.columns = [normalize_header(c) for c in df.columns]
    return dedupe_columns(df)


def strip_val(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def is_dash_only(value):
    s = strip_val(value)
    return bool(s) and set(s.replace(" ", "")) == {"-"}


def is_present(value):
    s = strip_val(value)
    if not s or s.lower() in {"nan", "none"}:
        return False
    compact = s.replace(" ", "")
    if set(compact) == {"0"}:
        return False
    if set(compact.replace("-", "")) == set() and "-" in compact:
        return False
    if compact in {"0000000000", "000000000", "00000000"}:
        return False
    return True


def is_separator_row(row):
    if is_dash_only(row.get("POLICY_NUMBER")) or is_dash_only(row.get("RELATE_CODE")):
        return True
    if is_dash_only(row.get("NAME_ID")):
        return True
    return False


def parse_numeric(value):
    s = strip_val(value).replace(",", "")
    if not s or s == ".":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def entity_type(row):
    fmt = strip_val(row.get("NAME_FORMAT_CODE", "")).upper()
    if fmt == "B":
        return "BUSINESS"
    if fmt == "I":
        return "INDIVIDUAL"
    if is_present(row.get("NAME_BUSINESS")):
        return "BUSINESS"
    if is_present(row.get("INDIVIDUAL_LAST")) or is_present(row.get("INDIVIDUAL_FIRST")):
        return "INDIVIDUAL"
    return "UNKNOWN"


def has_ssn(row):
    s = strip_val(row.get("SOC_SEC_NUMBER", ""))
    if not is_present(s):
        return False
    digits = re.sub(r"[^0-9]", "", s)
    return len(digits) >= 4


def has_tin(row):
    s = strip_val(row.get("BUSINESS_TAX_CODE", ""))
    if not is_present(s):
        return False
    digits = re.sub(r"[^0-9]", "", s)
    return len(digits) >= 4


def is_foreign_country(value):
    s = strip_val(value).upper()
    if not is_present(s):
        return False
    normalized = re.sub(r"[^A-Z ]", "", s).strip()
    return normalized not in {c.upper() for c in US_COUNTRY_VALUES if c}


def codes_pipe(values):
    return "|".join(sorted({strip_val(v) for v in values if strip_val(v)}))


def load_semantics(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def role_sets(semantics):
    cats = semantics["category_codes"]
    return {k: set(v) for k, v in cats.items()}


def classify_overlap(roles, semantics):
    role_set = set(roles)
    if len(role_set) < 2:
        return "", "NONE"
    matches = []
    risk_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}
    best_risk = "NONE"
    for pattern in semantics.get("overlap_patterns", []):
        needed = set(pattern["codes"])
        if needed.issubset(role_set):
            matches.append(pattern["overlap_type"])
            if risk_rank.get(pattern["risk"], 0) > risk_rank.get(best_risk, 0):
                best_risk = pattern["risk"]
    if len(role_set) >= 3 and not matches:
        return "MULTI_ROLE_COMPLEX", "MEDIUM"
    if matches:
        return "|".join(sorted(set(matches))), best_risk
    return "GENERAL_ROLE_OVERLAP", "LOW"


# ---------------------------------------------------------------------------
# Load PRELSA
# ---------------------------------------------------------------------------

def load_prelsa(path):
    logger.info("Reading PRELSA extract: %s", path)
    df = pd.read_csv(path, encoding="latin1", dtype=str, low_memory=False)
    df = normalize_columns(df)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            logger.warning("Optional column missing (will use blanks): %s", col)
            df[col] = ""

    df["source_row_number"] = range(2, len(df) + 2)
    sep_mask = df.apply(is_separator_row, axis=1)
    sep_count = int(sep_mask.sum())
    df = df[~sep_mask].copy()

    df["policy_norm"] = df["POLICY_NUMBER"].apply(strip_val)
    df["name_id_norm"] = df["NAME_ID"].apply(strip_val)
    df["relate_code_norm"] = df["RELATE_CODE"].apply(strip_val)
    df["benefit_seq_norm"] = df["BENEFIT_SEQ_NUMBER"].apply(strip_val)
    df["entity_type"] = df.apply(entity_type, axis=1)

    stats = {
        "total_rows_read": len(df) + sep_count,
        "separator_rows_skipped": sep_count,
        "usable_rows": len(df),
        "distinct_policies": int(df["policy_norm"].replace("", pd.NA).dropna().nunique()),
        "distinct_name_ids": int(df["name_id_norm"].replace("", pd.NA).dropna().nunique()),
        "distinct_relate_codes": int(df["relate_code_norm"].replace("", pd.NA).dropna().nunique()),
        "relate_codes_observed": codes_pipe(df["relate_code_norm"].tolist()),
    }
    logger.info(
        "Loaded %s usable PRELSA rows (%s separators skipped)",
        stats["usable_rows"],
        stats["separator_rows_skipped"],
    )
    return df, stats


def load_claim_active_policies(pactg_path, claim_rules_path):
    if not pactg_path or not os.path.isfile(pactg_path):
        return set()
    sys.path.insert(0, SCRIPT_DIR)
    from pactg_transaction_profiler import load_claim_family_rules, load_pactg

    rules = load_claim_family_rules(claim_rules_path)
    claim_codes = set(rules.keys())
    pactg, _ = load_pactg(pactg_path)
    mask = (
        pactg["credit_code_norm"].isin(claim_codes)
        | pactg["debit_code_norm"].isin(claim_codes)
    )
    policies = set(pactg.loc[mask, "policy_norm"].tolist())
    logger.info("Claim-active policies from PACTG: %s", len(policies))
    return policies


# ---------------------------------------------------------------------------
# Report builders
# ---------------------------------------------------------------------------

def build_relationship_code_frequency(df):
    rows = []
    grouped = df.groupby("relate_code_norm", dropna=False)
    for code, sub in grouped:
        if not code:
            continue
        rows.append({
            "relate_code": code,
            "row_count": len(sub),
            "distinct_policy_count": sub["policy_norm"].nunique(),
            "distinct_name_id_count": sub["name_id_norm"].nunique(),
            "individual_count": int((sub["entity_type"] == "INDIVIDUAL").sum()),
            "business_count": int((sub["entity_type"] == "BUSINESS").sum()),
            "address_present_count": int(sub["ADDR_LINE_1"].apply(is_present).sum()),
            "phone_present_count": int(sub["TELE_NUM"].apply(is_present).sum()),
            "ssn_present_count": int(sub.apply(has_ssn, axis=1).sum()),
            "dob_present_count": int(sub["DATE_OF_BIRTH"].apply(is_present).sum()),
        })
    out = pd.DataFrame(rows)
    return out.sort_values(["row_count", "relate_code"], ascending=[False, True]).reset_index(drop=True)


def build_relationship_hierarchy(df, semantics, claim_policies):
    cats = role_sets(semantics)

    def count_roles(sub, category):
        return int(sub["relate_code_norm"].isin(cats[category]).sum())

    rows = []
    for policy, sub in df.groupby("policy_norm", sort=True):
        if not policy:
            continue
        roles = sub["relate_code_norm"].tolist()
        role_set = {r for r in roles if r}
        overlap_type, risk = classify_overlap(role_set, semantics)

        priority = []
        for code in ("PE", "B1", "TR", "CU", "PO", "B2", "IN", "PA", "AS"):
            if code in role_set:
                priority.append(code)
        likely_primary = priority[0] if priority else (
            sub["relate_code_norm"].value_counts().idxmax() if len(sub) else ""
        )

        conflict = "N"
        if risk in {"HIGH", "MEDIUM"}:
            conflict = "Y"
        if policy in claim_policies:
            if not role_set.intersection(cats["payee"] | cats["beneficiary"] | cats["owner"]):
                conflict = "Y"
            if not role_set.intersection(cats["payee"] | cats["beneficiary"]) and "PE" not in role_set:
                conflict = "Y"

        rows.append({
            "policy_number": policy,
            "relationship_count": len(sub),
            "insured_count": count_roles(sub, "insured"),
            "beneficiary_count": count_roles(sub, "beneficiary"),
            "payee_count": count_roles(sub, "payee"),
            "owner_count": count_roles(sub, "owner"),
            "trustee_count": count_roles(sub, "trustee"),
            "assignee_count": count_roles(sub, "assignee"),
            "custodian_count": count_roles(sub, "custodian"),
            "distinct_relate_codes": codes_pipe(roles),
            "likely_primary_relationship": likely_primary,
            "possible_conflict_flag": conflict,
        })

    out = pd.DataFrame(rows)
    return out.sort_values(["possible_conflict_flag", "policy_number"], ascending=[False, True]).reset_index(drop=True)


def build_beneficiary_sequence_analysis(df):
    ben = df[df["relate_code_norm"].isin({"B1", "B2"})].copy()
    if ben.empty:
        return pd.DataFrame(columns=[
            "policy_number", "beneficiary_sequence", "beneficiary_count",
            "beneficiary_codes_present", "trust_present_flag", "business_present_flag",
            "percent_allocation_available_flag", "duplicate_sequence_flag",
        ])

    rows = []
    seq_groups = ben.groupby(["policy_norm", "benefit_seq_norm"], sort=True)
    seq_counts = ben.groupby(["policy_norm", "benefit_seq_norm"]).size()
    policy_trust = df.groupby("policy_norm")["relate_code_norm"].apply(
        lambda s: "Y" if set(s.tolist()) & {"TR", "CU"} else "N",
    )

    for (policy, seq), sub in seq_groups:
        codes = codes_pipe(sub["relate_code_norm"])
        dup_flag = "Y" if int(seq_counts.get((policy, seq), 0)) > 1 and len(sub) > 1 else "N"
        pct_flag = "N"
        pcts = sub["COMM_PCNT"].apply(parse_numeric).dropna()
        if not pcts.empty and ((pcts > 0).any()):
            unique_vals = set(round(v, 4) for v in pcts.tolist())
            if len(unique_vals) > 1 or (len(sub) > 1 and any(v not in (0.0, 100.0) for v in unique_vals)):
                pct_flag = "Y"
            elif len(sub) == 1 and 100.0 in unique_vals:
                pct_flag = "Y"

        rows.append({
            "policy_number": policy,
            "beneficiary_sequence": seq if seq else "0",
            "beneficiary_count": len(sub),
            "beneficiary_codes_present": codes,
            "trust_present_flag": policy_trust.get(policy, "N"),
            "business_present_flag": "Y" if (sub["entity_type"] == "BUSINESS").any() else "N",
            "percent_allocation_available_flag": pct_flag,
            "duplicate_sequence_flag": dup_flag,
        })

    out = pd.DataFrame(rows)
    return out.sort_values(
        ["policy_number", "beneficiary_sequence"],
        ascending=[True, True],
    ).reset_index(drop=True)


def build_relationship_overlap_analysis(df, semantics):
    rows = []
    grouped = df.groupby(["policy_norm", "name_id_norm"], sort=True)
    for (policy, name_id), sub in grouped:
        if not policy or not name_id:
            continue
        roles = sorted(set(sub["relate_code_norm"].tolist()) - {""})
        if len(roles) < 2:
            continue
        overlap_type, risk = classify_overlap(roles, semantics)
        entity = sub["entity_type"].mode().iloc[0] if not sub.empty else "UNKNOWN"
        rows.append({
            "policy_number": policy,
            "name_id": name_id,
            "relationship_roles": codes_pipe(roles),
            "role_count": len(roles),
            "individual_or_business": entity,
            "overlap_type": overlap_type,
            "potential_resolution_risk": risk,
        })

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    risk_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "NONE": 3}
    out["_risk_sort"] = out["potential_resolution_risk"].map(risk_order).fillna(9)
    out = out.sort_values(
        ["_risk_sort", "role_count", "policy_number"],
        ascending=[True, False, True],
    ).drop(columns=["_risk_sort"]).reset_index(drop=True)
    return out


def _candidate_string(sub, codes):
    if sub.empty:
        return ""
    cand = sub[sub["relate_code_norm"].isin(codes)]
    if cand.empty:
        return ""
    parts = []
    for _, row in cand.drop_duplicates(subset=["name_id_norm", "relate_code_norm"]).iterrows():
        parts.append(f"{row['relate_code_norm']}:{row['name_id_norm']}")
    return "|".join(sorted(parts))


def build_payee_candidate_analysis(df, semantics, claim_policies):
    cats = role_sets(semantics)
    role_meta = semantics["roles"]
    policies = sorted(set(df["policy_norm"].tolist()) - {""})

    rows = []
    for policy in policies:
        sub = df[df["policy_norm"] == policy]
        role_set = set(sub["relate_code_norm"].tolist()) - {""}
        claim_flag = "Y" if policy in claim_policies else "N"

        ben_c = _candidate_string(sub, cats["beneficiary"])
        pay_c = _candidate_string(sub, cats["payee"])
        own_c = _candidate_string(sub, cats["owner"])
        tr_c = _candidate_string(sub, cats["trustee"])
        cu_c = _candidate_string(sub, cats["custodian"])

        likely = []
        for code in ("PE", "B1", "TR", "CU", "PO", "B2", "AS", "IN"):
            if code in role_set:
                likely.append(f"{code}:{role_meta.get(code, {}).get('label', code)}")
        likely_payees = "|".join(likely)

        priority = []
        for code in ("PE", "B1", "TR", "CU", "PO", "B2", "AS", "IN"):
            if code in role_set:
                priority.append(code)
        fallback = []
        if claim_flag == "Y" and "PE" not in role_set:
            for code in ("B1", "PO", "TR", "B2", "IN"):
                if code in role_set:
                    fallback.append(code)
            strategy = "PRELSA_FALLBACK_NO_EXPLICIT_PAYEE" if fallback else "MANUAL_REVIEW_NO_PAYEE_SIGNAL"
        elif claim_flag == "Y":
            strategy = "EXPLICIT_PAYEE_AVAILABLE"
        else:
            strategy = "NO_CLAIM_ACTIVITY"

        trustee_parts = "|".join(p for p in (tr_c, cu_c) if p)
        rows.append({
            "policy_number": policy,
            "claim_activity_present_flag": claim_flag,
            "likely_payee_candidates": likely_payees,
            "beneficiary_candidates": ben_c,
            "payee_candidates": pay_c,
            "owner_candidates": own_c,
            "trustee_candidates": trustee_parts,
            "relationship_resolution_priority": "|".join(priority),
            "fallback_strategy_candidate": strategy if claim_flag == "Y" else "",
        })

    out = pd.DataFrame(rows)
    return out.sort_values(
        ["claim_activity_present_flag", "policy_number"],
        ascending=[False, True],
    ).reset_index(drop=True)


def build_address_quality_analysis(df):
    addr1 = df["ADDR_LINE_1"].apply(is_present)
    city = df["CITY"].apply(is_present)
    state = df["STATE"].apply(is_present)
    zip_code = df["ZIP"].apply(is_present)
    foreign = df["COUNTRY"].apply(is_foreign_country)
    incomplete = ~(addr1 & city & state & zip_code)

    out = pd.DataFrame({
        "policy_number": df["policy_norm"],
        "name_id": df["name_id_norm"],
        "relate_code": df["relate_code_norm"],
        "address_present_flag": addr1.map(lambda x: "Y" if x else "N"),
        "city_present_flag": city.map(lambda x: "Y" if x else "N"),
        "state_present_flag": state.map(lambda x: "Y" if x else "N"),
        "zip_present_flag": zip_code.map(lambda x: "Y" if x else "N"),
        "foreign_address_flag": foreign.map(lambda x: "Y" if x else "N"),
        "incomplete_address_flag": incomplete.map(lambda x: "Y" if x else "N"),
    })
    out = out[(out["policy_number"] != "") & (out["name_id"] != "")]
    return out.sort_values(
        ["incomplete_address_flag", "policy_number", "relate_code", "name_id"],
        ascending=[False, True, True, True],
    ).reset_index(drop=True)


def build_tax_identifier_analysis(df, semantics):
    cats = role_sets(semantics)
    payee_relevant = (
        cats["payee"] | cats["beneficiary"] | cats["owner"]
        | cats["trustee"] | cats["custodian"] | cats["assignee"]
    )

    rows = []
    for code, sub in df.groupby("relate_code_norm", sort=True):
        if not code:
            continue
        ind = sub[sub["entity_type"] == "INDIVIDUAL"]
        biz = sub[sub["entity_type"] == "BUSINESS"]
        ssn_n = int(sub.apply(has_ssn, axis=1).sum())
        tin_n = int(sub.apply(has_tin, axis=1).sum())
        missing = int((~sub.apply(has_ssn, axis=1) & ~sub.apply(has_tin, axis=1)).sum())
        relevance = "HIGH" if code in payee_relevant else "LOW"
        if code in cats["agent"]:
            relevance = "NONE"
        rows.append({
            "relate_code": code,
            "individual_count": len(ind),
            "business_count": len(biz),
            "ssn_present_count": ssn_n,
            "tin_like_identifier_count": tin_n,
            "missing_tax_id_count": missing,
            "likely_payee_relevance": relevance,
        })

    out = pd.DataFrame(rows)
    freq = df["relate_code_norm"].value_counts()
    out["row_count"] = out["relate_code"].map(freq)
    return out.sort_values(
        ["likely_payee_relevance", "row_count", "relate_code"],
        ascending=[True, False, True],
    ).drop(columns=["row_count"]).reset_index(drop=True)


def build_resolution_recommendations(semantics):
    rows = semantics.get("resolution_scenarios", [])
    out = pd.DataFrame(rows, columns=[
        "claim_scenario",
        "recommended_priority_order",
        "fallback_order",
        "confidence_level",
        "notes",
    ])
    return out.sort_values("claim_scenario").reset_index(drop=True)


def compute_summary_extras(df, overlap_df, payee_df, claim_policies):
    total = len(df)
    individual_n = int((df["entity_type"] == "INDIVIDUAL").sum())
    business_n = int((df["entity_type"] == "BUSINESS").sum())
    addr_pct = round(100.0 * df["ADDR_LINE_1"].apply(is_present).sum() / total, 2) if total else 0.0
    tax_present = int((df.apply(has_ssn, axis=1) | df.apply(has_tin, axis=1)).sum())
    tax_pct = round(100.0 * tax_present / total, 2) if total else 0.0

    top_overlaps = []
    if not overlap_df.empty:
        vc = overlap_df["overlap_type"].value_counts().head(5)
        top_overlaps = [f"{k}({v})" for k, v in vc.items()]

    claim_linked = 0
    if not payee_df.empty:
        claim_linked = int((payee_df["claim_activity_present_flag"] == "Y").sum())

    return {
        "individual_count": individual_n,
        "business_count": business_n,
        "address_completeness_pct": addr_pct,
        "tax_id_completeness_pct": tax_pct,
        "top_relationship_overlaps": "; ".join(top_overlaps),
        "claim_linked_policies": claim_linked,
        "claim_active_policy_count": len(claim_policies),
    }


def write_summary(path, prelsa_path, pactg_path, stats, extras, output_files):
    lines = [
        "=== PRELSA Relationship Profile Summary ===",
        f"PRELSA input: {os.path.abspath(prelsa_path)}",
        f"PACTG cross-reference: {os.path.abspath(pactg_path) if pactg_path else 'not supplied'}",
        f"Total rows read: {stats['total_rows_read']}",
        f"Separator rows skipped: {stats['separator_rows_skipped']}",
        f"Usable rows: {stats['usable_rows']}",
        f"Distinct policies: {stats['distinct_policies']}",
        f"Distinct NAME_ID count: {stats['distinct_name_ids']}",
        f"Distinct relationship codes: {stats['distinct_relate_codes']}",
        f"Relationship codes observed: {stats['relate_codes_observed']}",
        f"Individual rows: {extras['individual_count']}",
        f"Business rows: {extras['business_count']}",
        f"Address completeness (ADDR_LINE_1): {extras['address_completeness_pct']}%",
        f"Tax ID completeness (SSN or TIN): {extras['tax_id_completeness_pct']}%",
        f"Top relationship overlaps: {extras['top_relationship_overlaps'] or 'none'}",
        f"Claim-active policies (PACTG): {extras['claim_active_policy_count']}",
        f"Claim-linked policies in PRELSA: {extras['claim_linked_policies']}",
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

def run_profiler(prelsa_path, output_dir, semantics_path, pactg_path=None, claim_rules_path=None):
    os.makedirs(output_dir, exist_ok=True)
    semantics = load_semantics(semantics_path)
    df, stats = load_prelsa(prelsa_path)

    claim_policies = set()
    if pactg_path and os.path.isfile(pactg_path):
        claim_policies = load_claim_active_policies(
            pactg_path,
            claim_rules_path or DEFAULT_CLAIM_RULES_PATH,
        )

    reports = {}

    logger.info("Building relationship_code_frequency.csv")
    reports["relationship_code_frequency.csv"] = build_relationship_code_frequency(df)

    logger.info("Building relationship_hierarchy_analysis.csv")
    reports["relationship_hierarchy_analysis.csv"] = build_relationship_hierarchy(
        df, semantics, claim_policies,
    )

    logger.info("Building beneficiary_sequence_analysis.csv")
    reports["beneficiary_sequence_analysis.csv"] = build_beneficiary_sequence_analysis(df)

    logger.info("Building relationship_overlap_analysis.csv")
    reports["relationship_overlap_analysis.csv"] = build_relationship_overlap_analysis(df, semantics)

    logger.info("Building payee_candidate_analysis.csv")
    reports["payee_candidate_analysis.csv"] = build_payee_candidate_analysis(
        df, semantics, claim_policies,
    )

    logger.info("Building address_quality_analysis.csv")
    reports["address_quality_analysis.csv"] = build_address_quality_analysis(df)

    logger.info("Building tax_identifier_analysis.csv")
    reports["tax_identifier_analysis.csv"] = build_tax_identifier_analysis(df, semantics)

    logger.info("Building relationship_resolution_recommendations.csv")
    reports["relationship_resolution_recommendations.csv"] = build_resolution_recommendations(semantics)

    output_files = []
    for filename, frame in reports.items():
        out_path = os.path.join(output_dir, filename)
        frame.to_csv(out_path, index=False, encoding="utf-8")
        output_files.append(out_path)
        logger.info("Wrote %s (%s rows)", filename, len(frame))

    extras = compute_summary_extras(
        df,
        reports["relationship_overlap_analysis.csv"],
        reports["payee_candidate_analysis.csv"],
        claim_policies,
    )
    summary_path = os.path.join(output_dir, "prelsa_profile_summary.txt")
    write_summary(summary_path, prelsa_path, pactg_path, stats, extras, output_files)
    output_files.append(summary_path)
    logger.info("Wrote prelsa_profile_summary.txt")

    return stats, extras, output_files


def main():
    parser = argparse.ArgumentParser(
        description="Read-only PRELSA relationship intelligence profiler (Phase 3).",
    )
    parser.add_argument("--prelsa", required=True, help="Path to RelationshipNameAddress extract CSV")
    parser.add_argument("--output", required=True, help="Output directory for profiling reports")
    parser.add_argument("--pactg", default="", help="Optional PACTG CSV for claim-policy cross-reference")
    parser.add_argument(
        "--semantics",
        default=DEFAULT_SEMANTICS_PATH,
        help="Relationship code semantics JSON",
    )
    parser.add_argument(
        "--claim-rules",
        default=DEFAULT_CLAIM_RULES_PATH,
        help="Claim family rules JSON for PACTG cross-reference",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if not os.path.isfile(args.prelsa):
        logger.error("PRELSA input not found: %s", args.prelsa)
        return 1

    try:
        stats, extras, outputs = run_profiler(
            args.prelsa,
            args.output,
            args.semantics,
            pactg_path=args.pactg or None,
            claim_rules_path=args.claim_rules,
        )
        print(f"Profiling complete. Usable PRELSA rows: {stats['usable_rows']}")
        print(f"Distinct policies: {stats['distinct_policies']}")
        print(f"Claim-linked policies: {extras['claim_linked_policies']}")
        print(f"Output directory: {os.path.abspath(args.output)}")
        for p in outputs:
            print(f"  {p}")
        return 0
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
