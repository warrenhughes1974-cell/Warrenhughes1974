#!/usr/bin/env python3
"""
Phase 11 — Prototype QUIKCLMS/QUIKCLMP DBF generation & QA/UAT reconciliation.

Generates prototype DBFs from Phase 10A/10B RULEBOOK_READY candidates only.
Does NOT deploy production DBFs or modify app.py / prior phase outputs.
"""

import argparse
import json
import logging
import os
import shutil
from collections import Counter, defaultdict

import dbf
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "prototype_dbf_generation_rules.json")
PHASE10A = os.path.join(ROOT, "phase10a_quikclmp_derivation_design")
PHASE10B = os.path.join(ROOT, "phase10b_quikclms_derivation_design")
PHASE9 = os.path.join(ROOT, "phase9_quikclmp_canonical_staging")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase11_prototype_dbf_generation")

logger = logging.getLogger("prototype_dbf")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def confidence_rank(level):
    order = {
        "HIGH_CONFIDENCE": 4, "MODERATE_CONFIDENCE": 3,
        "INFERRED": 2, "LOW_CONFIDENCE": 1,
    }
    return order.get(strip_val(level).upper(), 0)


def parse_date(value):
    s = strip_val(value)
    if not s or s.lower() in {"nan", "none", "null"}:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d", "%m-%d-%Y"):
        try:
            dt = pd.to_datetime(s, format=fmt)
            return dbf.Date(dt.year, dt.month, dt.day)
        except (ValueError, TypeError):
            continue
    try:
        dt = pd.to_datetime(s)
        return dbf.Date(dt.year, dt.month, dt.day)
    except (ValueError, TypeError):
        return None


def layout_to_dbf_spec(layout):
    parts = []
    for fld in layout:
        name = fld["field"]
        ftype = fld["type"].upper()
        length = int(fld.get("length", 10))
        decimals = int(fld.get("decimals", 0))
        if ftype == "CHARACTER":
            parts.append(f"{name} C({length})")
        elif ftype == "NUMERIC":
            parts.append(f"{name} N({length},{decimals})")
        elif ftype == "DATE":
            parts.append(f"{name} D")
        elif ftype == "LOGICAL":
            parts.append(f"{name} L")
        elif ftype == "MEMO":
            parts.append(f"{name} M")
        else:
            parts.append(f"{name} C({length})")
    return "; ".join(parts)


def truncate_char(value, length):
    s = strip_val(value)
    if not s:
        return None
    return s[:length]


def coerce_numeric(value, default=0.0):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    s = strip_val(value)
    if not s:
        return default
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return default


def coerce_logical(value, default=False):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default if default is not None else None
    if isinstance(value, bool):
        return value
    s = strip_val(value).upper()
    if not s:
        return default if default is not None else None
    return s in {"Y", "YES", "TRUE", "T", "1"}


def row_get(row, key, default=""):
    if key == "constant":
        return default
    val = row.get(key, default)
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    return val


def passes_gating(row, rules):
    gating = rules["gating_rules"]
    status = strip_val(row.get("derivation_status_cand", row.get("derivation_status", "")))
    validation = strip_val(row.get("validation_result", ""))
    confidence = strip_val(row.get("derivation_confidence_cand", row.get("derivation_confidence", "")))
    if status != gating["require_derivation_status"]:
        return False, f"derivation_status={status}"
    if validation != gating["require_validation_result"]:
        return False, f"validation_result={validation}"
    min_rank = confidence_rank(gating["minimum_confidence"])
    if confidence_rank(confidence) < min_rank:
        return False, f"confidence={confidence}"
    return True, ""


def build_claimnum_crosswalk(accepted_claims, rules):
    strategy = rules["claimnum_strategy"]
    prefix = strategy.get("prefix", "CLM")
    width = int(strategy.get("width", 7))
    sort_key = strategy.get("sort_key", "reconstructed_claim_id")
    sorted_claims = accepted_claims.sort_values(sort_key).reset_index(drop=True)
    crosswalk = []
    for idx, row in sorted_claims.iterrows():
        seq = idx + 1
        prototype_claimnum = f"{prefix}{seq:0{width}d}"
        crosswalk.append({
            "prototype_claimnum": prototype_claimnum,
            "sequence_number": seq,
            "reconstructed_claim_id": strip_val(row.get("reconstructed_claim_id", "")),
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
            "enhanced_settlement_group_id": strip_val(row.get("enhanced_settlement_group_id", "")),
            "policy_number": strip_val(row.get("policy_number", row.get("mpolicy", ""))),
            "claim_family": strip_val(row.get("claim_family", "")),
            "derivation_confidence": strip_val(row.get("derivation_confidence_cand", row.get("derivation_confidence", ""))),
            "lineage_source": "phase10b_quikclms_derivation",
        })
    return pd.DataFrame(crosswalk), {r["reconstructed_claim_id"]: r["prototype_claimnum"] for r in crosswalk}


def map_row_to_dbf_values(row, layout, field_mapping, rules, claimnum_lookup=None):
    values = []
    mhdpmt_map = rules.get("payment_type_mhdpmt_mapping", {})
    for fld in layout:
        name = fld["field"]
        ftype = fld["type"].upper()
        cfg = field_mapping.get(name, {"source": "constant", "default": ""})
        source = cfg.get("source", "constant")
        default = cfg.get("default", "")

        if source == "prototype_claimnum":
            cid = strip_val(row.get("reconstructed_claim_id", ""))
            raw = claimnum_lookup.get(cid, default) if claimnum_lookup else default
        elif source == "derived_mhdpmt":
            paytype = strip_val(row.get("mpaytype", "")).upper()
            raw = mhdpmt_map.get(paytype, mhdpmt_map.get("default", "C"))
        elif source == "constant":
            raw = default
        else:
            raw = row_get(row, source, default)
            if (not strip_val(raw)) and cfg.get("fallback"):
                raw = row_get(row, cfg["fallback"], default)

        if ftype == "CHARACTER":
            val = truncate_char(raw, int(fld.get("length", 10)))
        elif ftype == "NUMERIC":
            val = coerce_numeric(raw, coerce_numeric(default, 0.0))
        elif ftype == "DATE":
            val = parse_date(raw) if strip_val(raw) else None
        elif ftype == "LOGICAL":
            val = coerce_logical(raw, coerce_logical(default, False))
        elif ftype == "MEMO":
            val = strip_val(raw) or None
        else:
            val = truncate_char(raw, int(fld.get("length", 10)))
        values.append(val)
    return tuple(values)


def validate_required_fields(values, layout, required_fields):
    issues = []
    field_index = {fld["field"]: i for i, fld in enumerate(layout)}
    for req in required_fields:
        if req not in field_index:
            continue
        val = values[field_index[req]]
        if val is None or (isinstance(val, str) and not strip_val(val)):
            issues.append(f"missing_{req.lower()}")
    return issues


def write_dbf(path, layout, rows):
    spec = layout_to_dbf_spec(layout)
    if os.path.exists(path):
        os.remove(path)
    table = dbf.Table(path, spec)
    table.open(mode=dbf.READ_WRITE)
    for row_vals in rows:
        table.append(row_vals)
    table.close()
    return len(rows)


def normalize_merged_columns(df):
    """Resolve _cand/_val suffix collisions after validation merge."""
    if df.empty:
        return df
    out = df.copy()
    for col in list(out.columns):
        if col.endswith("_cand"):
            base = col[:-5]
            if base not in out.columns:
                out[base] = out[col]
    for preferred in (
        "reconstructed_claim_id", "derivation_status", "derivation_confidence",
        "derivation_candidate_id", "canonical_payment_stage_id", "policy_number",
        "enhanced_settlement_group_id", "claim_family",
    ):
        cand = f"{preferred}_cand"
        if preferred not in out.columns and cand in out.columns:
            out[preferred] = out[cand]
    return out


def gate_candidates(candidates, validation, merge_key, rules):
    merged = candidates.merge(validation, on=merge_key, suffixes=("_cand", "_val"))
    merged = normalize_merged_columns(merged)
    accepted = []
    rejected = []
    for _, row in merged.iterrows():
        ok, reason = passes_gating(row, rules)
        record = row.to_dict()
        if ok:
            accepted.append(record)
        else:
            record["rejection_reason"] = reason
            rejected.append(record)
    return pd.DataFrame(accepted), pd.DataFrame(rejected)


def run_reconciliation(claim_rows, payment_rows, crosswalk_df, rules):
    tol = float(rules["reconciliation_rules"].get("payment_amount_tolerance", 0.01))
    claim_lookup = {strip_val(r["reconstructed_claim_id"]): r for _, r in claim_rows.iterrows()}
    claimnums = set(crosswalk_df["prototype_claimnum"])
    recon_rows = []
    payment_by_claim = defaultdict(list)
    for _, prow in payment_rows.iterrows():
        payment_by_claim[strip_val(prow["reconstructed_claim_id"])].append(prow)

    for _, crow in claim_rows.iterrows():
        cid = strip_val(crow["reconstructed_claim_id"])
        prototype_claimnum = strip_val(crow.get("prototype_claimnum", ""))
        mpaid = parse_amount(crow.get("mpaid_dbf", crow.get("mpaid", 0)))
        mnet = parse_amount(crow.get("mnetamt", 0))
        mpaycount = int(parse_amount(crow.get("mpaycount", 0)))
        mresidual = parse_amount(crow.get("mresidual", 0))
        payments = payment_by_claim.get(cid, [])
        pay_sum = round(sum(parse_amount(p.get("mamount_dbf", p.get("mamount", 0))) for p in payments), 2)
        pay_count = len(payments)
        variance = round(mpaid - pay_sum, 2)
        net_variance = round(mnet - pay_sum, 2) if pay_count > 0 else None
        count_match = pay_count == mpaycount if mpaycount > 0 else (pay_count == 0 or pay_count == mpaycount)
        amount_match = abs(variance) <= tol if pay_count > 0 else True
        recon_rows.append({
            "prototype_claimnum": prototype_claimnum,
            "reconstructed_claim_id": cid,
            "policy_number": strip_val(crow.get("mpolicy", "")),
            "claim_family": strip_val(crow.get("claim_family", "")),
            "quikclms_mpaid": mpaid,
            "quikclmp_sum_mamount": pay_sum,
            "mpaid_variance": variance,
            "mnetamt": mnet,
            "net_payment_variance": net_variance,
            "quikclms_mpaycount": mpaycount,
            "quikclmp_payment_count": pay_count,
            "payment_count_match": "Y" if count_match else "N",
            "amount_reconciliation": "PASS" if amount_match else "VARIANCE",
            "mresidual": mresidual,
            "residual_preserved": "Y" if mresidual != 0 else "N",
            "reconciliation_status": "PASS" if amount_match and count_match else "REVIEW",
        })

    recon_df = pd.DataFrame(recon_rows)
    return recon_df


def analyze_orphans(claim_rows, payment_rows, crosswalk_df):
    claim_ids = set(strip_val(x) for x in claim_rows["reconstructed_claim_id"])
    orphan_rows = []
    for _, prow in payment_rows.iterrows():
        cid = strip_val(prow["reconstructed_claim_id"])
        issues = []
        if cid not in claim_ids:
            issues.append("MISSING_CLAIM_HEADER")
        policy = strip_val(prow.get("mpolicy", ""))
        claim_policy = ""
        if cid in claim_ids:
            match = claim_rows[claim_rows["reconstructed_claim_id"] == cid]
            if not match.empty:
                claim_policy = strip_val(match.iloc[0].get("mpolicy", ""))
                if policy and claim_policy and policy != claim_policy:
                    issues.append("MPOLICY_MISMATCH")
        orphan_rows.append({
            "derivation_candidate_id": strip_val(prow.get("derivation_candidate_id", "")),
            "canonical_payment_stage_id": strip_val(prow.get("canonical_payment_stage_id", "")),
            "reconstructed_claim_id": cid,
            "prototype_claimnum": strip_val(prow.get("prototype_claimnum", "")),
            "mpolicy": policy,
            "mseq": strip_val(prow.get("mseq", "")),
            "mamount": parse_amount(prow.get("mamount", 0)),
            "orphan_issues": "|".join(issues) if issues else "NONE",
            "is_orphan": "Y" if issues else "N",
        })
    return pd.DataFrame(orphan_rows)


def analyze_duplicates(payment_rows):
    dup_rows = []
    key_counts = Counter(
        (strip_val(r["mpolicy"]), strip_val(r["mseq"])) for _, r in payment_rows.iterrows()
    )
    for (policy, mseq), count in key_counts.items():
        if count > 1 and policy:
            dup_rows.append({
                "mpolicy": policy,
                "mseq": mseq,
                "duplicate_count": count,
                "issue": "DUPLICATE_MSEQ",
            })
    return pd.DataFrame(dup_rows)


def run_engine(
    clmp_candidates, clmp_validation,
    clms_candidates, clms_validation,
    rules_path, output_dir,
):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    clms_layout = rules["quikclms_layout"]
    clmp_layout = rules["quikclmp_layout"]
    clms_mapping = rules["quikclms_field_mapping"]
    clmp_mapping = rules["quikclmp_field_mapping"]

    accepted_claims, rejected_claims = gate_candidates(
        clms_candidates, clms_validation, "reconstructed_claim_id", rules,
    )
    accepted_payments, rejected_payments = gate_candidates(
        clmp_candidates, clmp_validation, "canonical_payment_stage_id", rules,
    )

    crosswalk_df, claimnum_lookup = build_claimnum_crosswalk(accepted_claims, rules)
    crosswalk_path = os.path.join(output_dir, "claimnum_crosswalk.csv")
    crosswalk_df.to_csv(crosswalk_path, index=False, encoding="utf-8")

    claim_audit_rows = []
    clms_dbf_rows = []
    for _, row in accepted_claims.iterrows():
        row_dict = row.to_dict()
        row_dict["prototype_claimnum"] = claimnum_lookup.get(
            strip_val(row_dict.get("reconstructed_claim_id", "")), "",
        )
        dbf_vals = map_row_to_dbf_values(
            row_dict, clms_layout, clms_mapping, rules, claimnum_lookup,
        )
        issues = validate_required_fields(dbf_vals, clms_layout, rules.get("required_quikclms_fields", []))
        mpaid_idx = next(i for i, f in enumerate(clms_layout) if f["field"] == "MPAID")
        row_dict["mpaid_dbf"] = dbf_vals[mpaid_idx]
        if issues:
            rejected_claims = pd.concat([
                rejected_claims,
                pd.DataFrame([{**row_dict, "rejection_reason": "|".join(issues)}]),
            ], ignore_index=True)
            claim_audit_rows.append({
                **row_dict,
                "generation_status": "REJECTED",
                "rejection_reason": "|".join(issues),
            })
            continue
        clms_dbf_rows.append(dbf_vals)
        claim_audit_rows.append({
            "generation_status": "ACCEPTED",
            "prototype_claimnum": row_dict["prototype_claimnum"],
            "reconstructed_claim_id": strip_val(row_dict.get("reconstructed_claim_id", "")),
            "derivation_candidate_id": strip_val(row_dict.get("derivation_candidate_id", "")),
            "enhanced_settlement_group_id": strip_val(row_dict.get("enhanced_settlement_group_id", "")),
            "claim_family": strip_val(row_dict.get("claim_family", "")),
            "derivation_confidence": strip_val(row_dict.get("derivation_confidence_cand", "")),
            "target_table": "QUIKCLMS_PROTOTYPE.DBF",
            "production_dbf_flag": "N",
        })

    payment_audit_rows = []
    clmp_dbf_rows = []
    for _, row in accepted_payments.iterrows():
        row_dict = row.to_dict()
        cid = strip_val(row_dict.get("reconstructed_claim_id", ""))
        row_dict["prototype_claimnum"] = claimnum_lookup.get(cid, "")
        dbf_vals = map_row_to_dbf_values(row_dict, clmp_layout, clmp_mapping, rules)
        issues = validate_required_fields(dbf_vals, clmp_layout, rules.get("required_quikclmp_fields", []))
        mamount_idx = next(i for i, f in enumerate(clmp_layout) if f["field"] == "MAMOUNT")
        row_dict["mamount_dbf"] = dbf_vals[mamount_idx]
        if issues:
            rejected_payments = pd.concat([
                rejected_payments,
                pd.DataFrame([{**row_dict, "rejection_reason": "|".join(issues)}]),
            ], ignore_index=True)
            payment_audit_rows.append({**row_dict, "generation_status": "REJECTED", "rejection_reason": "|".join(issues)})
            continue
        clmp_dbf_rows.append(dbf_vals)
        payment_audit_rows.append({
            "generation_status": "ACCEPTED",
            "prototype_claimnum": row_dict["prototype_claimnum"],
            "reconstructed_claim_id": cid,
            "derivation_candidate_id": strip_val(row_dict.get("derivation_candidate_id", "")),
            "canonical_payment_stage_id": strip_val(row_dict.get("canonical_payment_stage_id", "")),
            "enhanced_settlement_group_id": strip_val(row_dict.get("enhanced_settlement_group_id", "")),
            "derivation_confidence": strip_val(row_dict.get("derivation_confidence_cand", "")),
            "target_table": "QUIKCLMP_PROTOTYPE.DBF",
            "production_dbf_flag": "N",
        })

    clms_path = os.path.join(output_dir, "QUIKCLMS_PROTOTYPE.DBF")
    clmp_path = os.path.join(output_dir, "QUIKCLMP_PROTOTYPE.DBF")
    clms_count = write_dbf(clms_path, clms_layout, clms_dbf_rows)
    clmp_count = write_dbf(clmp_path, clmp_layout, clmp_dbf_rows)
    logger.info("Wrote QUIKCLMS_PROTOTYPE.DBF (%s rows)", clms_count)
    logger.info("Wrote QUIKCLMP_PROTOTYPE.DBF (%s rows)", clmp_count)

    # Build claim rows for reconciliation from accepted claims with dbf values
    recon_claim_rows = []
    for audit, dbf_vals in zip(
        [r for r in claim_audit_rows if r.get("generation_status") == "ACCEPTED"],
        clms_dbf_rows,
    ):
        cid = audit["reconstructed_claim_id"]
        src = accepted_claims[accepted_claims["reconstructed_claim_id"] == cid]
        if src.empty:
            continue
        r = src.iloc[0].to_dict()
        r["prototype_claimnum"] = audit["prototype_claimnum"]
        mpaid_idx = next(i for i, f in enumerate(clms_layout) if f["field"] == "MPAID")
        r["mpaid_dbf"] = dbf_vals[mpaid_idx]
        recon_claim_rows.append(r)
    recon_claim_df = pd.DataFrame(recon_claim_rows)

    recon_pay_rows = []
    for audit, dbf_vals in zip(
        [r for r in payment_audit_rows if r.get("generation_status") == "ACCEPTED"],
        clmp_dbf_rows,
    ):
        stage_id = strip_val(audit.get("canonical_payment_stage_id", ""))
        match = accepted_payments[accepted_payments["canonical_payment_stage_id"] == stage_id]
        if match.empty:
            continue
        r = match.iloc[0].to_dict()
        r["prototype_claimnum"] = audit["prototype_claimnum"]
        mamount_idx = next(i for i, f in enumerate(clmp_layout) if f["field"] == "MAMOUNT")
        r["mamount_dbf"] = dbf_vals[mamount_idx]
        recon_pay_rows.append(r)
    recon_pay_df = pd.DataFrame(recon_pay_rows)

    recon_df = run_reconciliation(recon_claim_df, recon_pay_df, crosswalk_df, rules)
    recon_path = os.path.join(output_dir, "prototype_claim_payment_reconciliation.csv")
    recon_df.to_csv(recon_path, index=False, encoding="utf-8")

    orphan_df = analyze_orphans(recon_claim_df, recon_pay_df, crosswalk_df)
    orphan_path = os.path.join(output_dir, "prototype_orphan_analysis.csv")
    orphan_df.to_csv(orphan_path, index=False, encoding="utf-8")

    dup_df = analyze_duplicates(recon_pay_df)

    validation_rows = []
    for _, row in recon_df.iterrows():
        validation_rows.append({
            "prototype_claimnum": row["prototype_claimnum"],
            "reconstructed_claim_id": row["reconstructed_claim_id"],
            "validation_type": "CLAIM_PAYMENT_RECONCILIATION",
            "validation_result": row["reconciliation_status"],
            "validation_detail": f"mpaid_variance={row['mpaid_variance']}; pay_count_match={row['payment_count_match']}",
        })
    for _, row in orphan_df.iterrows():
        if row["is_orphan"] == "Y":
            validation_rows.append({
                "prototype_claimnum": row["prototype_claimnum"],
                "reconstructed_claim_id": row["reconstructed_claim_id"],
                "validation_type": "ORPHAN_PAYMENT",
                "validation_result": "REVIEW",
                "validation_detail": row["orphan_issues"],
            })
    for _, row in dup_df.iterrows():
        validation_rows.append({
            "prototype_claimnum": "",
            "reconstructed_claim_id": "",
            "validation_type": "DUPLICATE_MSEQ",
            "validation_result": "REVIEW",
            "validation_detail": f"mpolicy={row['mpolicy']}; mseq={row['mseq']}; count={row['duplicate_count']}",
        })
    val_df = pd.DataFrame(validation_rows)

    audit_records = []
    for r in claim_audit_rows:
        audit_records.append({**r, "record_type": "CLAIM"})
    for r in payment_audit_rows:
        audit_records.append({**r, "record_type": "PAYMENT"})
    for _, row in rejected_claims.iterrows():
        audit_records.append({
            "record_type": "CLAIM",
            "generation_status": "REJECTED",
            "reconstructed_claim_id": strip_val(row.get("reconstructed_claim_id", "")),
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
            "rejection_reason": strip_val(row.get("rejection_reason", "")),
            "target_table": "QUIKCLMS_PROTOTYPE.DBF",
            "production_dbf_flag": "N",
        })
    for _, row in rejected_payments.iterrows():
        audit_records.append({
            "record_type": "PAYMENT",
            "generation_status": "REJECTED",
            "reconstructed_claim_id": strip_val(row.get("reconstructed_claim_id", "")),
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
            "canonical_payment_stage_id": strip_val(row.get("canonical_payment_stage_id", "")),
            "rejection_reason": strip_val(row.get("rejection_reason", "")),
            "target_table": "QUIKCLMP_PROTOTYPE.DBF",
            "production_dbf_flag": "N",
        })
    audit_df = pd.DataFrame(audit_records)

    recon_pass = (recon_df["reconciliation_status"] == "PASS").sum() if not recon_df.empty else 0
    recon_total = len(recon_df)
    recon_pct = round(100.0 * recon_pass / recon_total, 2) if recon_total else 0.0
    orphan_count = (orphan_df["is_orphan"] == "Y").sum() if not orphan_df.empty else 0
    residual_count = (recon_df["residual_preserved"] == "Y").sum() if not recon_df.empty else 0

    summary_rows = [{
        "metric": "prototype_quikclms_rows",
        "value": clms_count,
    }, {
        "metric": "prototype_quikclmp_rows",
        "value": clmp_count,
    }, {
        "metric": "rejected_claim_rows",
        "value": len(rejected_claims),
    }, {
        "metric": "rejected_payment_rows",
        "value": len(rejected_payments),
    }, {
        "metric": "orphan_payment_count",
        "value": orphan_count,
    }, {
        "metric": "reconciliation_pass_pct",
        "value": recon_pct,
    }, {
        "metric": "duplicate_mseq_count",
        "value": len(dup_df),
    }, {
        "metric": "residual_preserved_count",
        "value": residual_count,
    }]
    if not recon_df.empty:
        summary_rows.append({
            "metric": "payment_aggregation_variance_count",
            "value": (recon_df["amount_reconciliation"] == "VARIANCE").sum(),
        })
        summary_rows.append({
            "metric": "balancing_variance_count",
            "value": recon_df["net_payment_variance"].apply(
                lambda x: abs(parse_amount(x)) > float(rules["reconciliation_rules"].get("net_amount_tolerance", 0.01))
                if x is not None and strip_val(x) else False
            ).sum(),
        })
    summary_df = pd.DataFrame(summary_rows)

    conf_claim = Counter(strip_val(r.get("derivation_confidence_cand", "")) for _, r in accepted_claims.iterrows())
    conf_pay = Counter(strip_val(r.get("derivation_confidence_cand", "")) for _, r in accepted_payments.iterrows())

    recommendations = [{
        "observed_pattern": f"{clms_count} prototype QUIKCLMS rows generated from {len(accepted_claims)} gated candidates",
        "root_cause": "Rulebook-ready claim subset passed validation gates",
        "recommended_action": "Use claimnum_crosswalk.csv for all downstream QA/UAT joins",
        "expected_impact": "HIGH",
        "confidence_level": "HIGH_CONFIDENCE",
    }]
    if orphan_count > 0:
        recommendations.append({
            "observed_pattern": f"{orphan_count} orphan payment rows detected",
            "root_cause": "Payments accepted without matching prototype claim header",
            "recommended_action": "Review prototype_orphan_analysis.csv before production cutover",
            "expected_impact": "MEDIUM",
            "confidence_level": "MODERATE_CONFIDENCE",
        })
    if recon_pct < 100:
        recommendations.append({
            "observed_pattern": f"Reconciliation pass rate {recon_pct}%",
            "root_cause": "MPAID vs sum(MAMOUNT) variance on multi-payee or non-death families",
            "recommended_action": "Review prototype_claim_payment_reconciliation.csv variances",
            "expected_impact": "MEDIUM",
            "confidence_level": "MODERATE_CONFIDENCE",
        })
    rec_df = pd.DataFrame(recommendations)

    stats = {
        "clms_rows": clms_count,
        "clmp_rows": clmp_count,
        "rejected_claims": len(rejected_claims),
        "rejected_payments": len(rejected_payments),
        "orphan_count": orphan_count,
        "recon_pass_pct": recon_pct,
        "recon_pass": recon_pass,
        "recon_total": recon_total,
        "dup_mseq": len(dup_df),
        "residual_preserved": residual_count,
        "confidence_claim": dict(conf_claim),
        "confidence_pay": dict(conf_pay),
    }

    rules_out = os.path.join(output_dir, "prototype_dbf_generation_rules.json")
    shutil.copy2(rules_path, rules_out)
    output_files = [rules_out, clms_path, clmp_path, crosswalk_path, recon_path, orphan_path]

    val_path = os.path.join(output_dir, "prototype_dbf_validation.csv")
    val_df.to_csv(val_path, index=False, encoding="utf-8")
    output_files.append(val_path)

    audit_path = os.path.join(output_dir, "prototype_dbf_generation_audit.csv")
    audit_df.to_csv(audit_path, index=False, encoding="utf-8")
    output_files.append(audit_path)

    summary_csv_path = os.path.join(output_dir, "prototype_reconciliation_summary.csv")
    summary_df.to_csv(summary_csv_path, index=False, encoding="utf-8")
    output_files.append(summary_csv_path)

    rec_path = os.path.join(output_dir, "prototype_generation_recommendations.csv")
    rec_df.to_csv(rec_path, index=False, encoding="utf-8")
    output_files.append(rec_path)

    summary_txt = os.path.join(output_dir, "prototype_generation_summary.txt")
    write_summary_txt(summary_txt, stats, output_files, recon_df, orphan_df)
    output_files.append(summary_txt)

    for name, path in [
        ("prototype_dbf_validation.csv", val_path),
        ("prototype_dbf_generation_audit.csv", audit_path),
        ("prototype_reconciliation_summary.csv", summary_csv_path),
        ("prototype_generation_recommendations.csv", rec_path),
    ]:
        logger.info("Wrote %s", name)

    return stats, output_files


def write_summary_txt(path, stats, output_files, recon_df, orphan_df):
    lines = [
        "=== Prototype DBF Generation & QA/UAT Reconciliation Summary (Phase 11) ===",
        "",
        f"Prototype QUIKCLMS rows: {stats['clms_rows']}",
        f"Prototype QUIKCLMP rows: {stats['clmp_rows']}",
        f"Rejected claim rows: {stats['rejected_claims']}",
        f"Rejected payment rows: {stats['rejected_payments']}",
        f"Orphan payment count: {stats['orphan_count']}",
        f"Reconciliation pass: {stats['recon_pass']}/{stats['recon_total']} ({stats['recon_pass_pct']}%)",
        f"Duplicate MSEQ groups: {stats['dup_mseq']}",
        f"Residual preserved count: {stats['residual_preserved']}",
        "",
        "Confidence distribution (claims):",
    ]
    for level, count in sorted(stats.get("confidence_claim", {}).items()):
        lines.append(f"  {level}: {count}")
    lines.extend(["", "Confidence distribution (payments):"])
    for level, count in sorted(stats.get("confidence_pay", {}).items()):
        lines.append(f"  {level}: {count}")
    lines.extend([
        "",
        "Architectural notes:",
        "  - Prototype DBFs only; production_dbf_flag=N",
        "  - CLAIMNUM crosswalk in claimnum_crosswalk.csv",
        "  - Official layout field order preserved per quikclms_quikclmp reference",
        "",
        "Recommended next phase:",
        "  - Phase 12: QA/UAT hardening & production readiness",
        "",
        "Output files generated:",
    ])
    for f in output_files:
        lines.append(f"  - {f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Phase 11 prototype QUIKCLMS/QUIKCLMP DBF generator.")
    parser.add_argument("--clmp-candidates", default=os.path.join(PHASE10A, "quikclmp_derivation_candidates.csv"))
    parser.add_argument("--clmp-validation", default=os.path.join(PHASE10A, "quikclmp_derivation_validation.csv"))
    parser.add_argument("--clms-candidates", default=os.path.join(PHASE10B, "quikclms_derivation_candidates.csv"))
    parser.add_argument("--clms-validation", default=os.path.join(PHASE10B, "quikclms_derivation_validation.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    for label, path in (
        ("QUIKCLMP candidates", args.clmp_candidates),
        ("QUIKCLMP validation", args.clmp_validation),
        ("QUIKCLMS candidates", args.clms_candidates),
        ("QUIKCLMS validation", args.clms_validation),
        ("Rules", args.rules),
    ):
        if not os.path.isfile(path):
            logger.error("%s not found: %s", label, path)
            return 1

    clmp_candidates = load_csv(args.clmp_candidates)
    clmp_validation = load_csv(args.clmp_validation)
    clms_candidates = load_csv(args.clms_candidates)
    clms_validation = load_csv(args.clms_validation)

    try:
        stats, outputs = run_engine(
            clmp_candidates, clmp_validation,
            clms_candidates, clms_validation,
            args.rules, args.output,
        )
        print(f"Prototype DBF generation complete.")
        print(f"QUIKCLMS rows: {stats['clms_rows']}")
        print(f"QUIKCLMP rows: {stats['clmp_rows']}")
        print(f"Reconciliation pass: {stats['recon_pass_pct']}%")
        print(f"Output: {os.path.abspath(args.output)}")
        for p in outputs:
            print(f"  {p}")
        return 0
    except (ValueError, FileNotFoundError, json.JSONDecodeError, KeyError, OSError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
