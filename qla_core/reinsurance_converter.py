"""
Phase 1 QuikRein / QuikRmst converter — stored LifePRO values only.

Authoritative sources:
  PROD_PTRTY -> QuikRein
  PREINTRT + PREIN -> QuikRmst

Production emit gated by QLA_ENABLE_REINSURANCE_EMIT / QLA_REINSURANCE_WRITE_OUTPUT.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from qla_core.reinsurance_lookups import (
    build_ptrty_treaty_index,
    load_quikmstr_index,
    load_quikmstr_policy_set,
    load_quikridr_index,
    load_reinsurance_type_crosswalk,
    load_reinsurer_crosswalk,
    resolve_mpolicy,
    resolve_quikridr_phase,
)
from qla_core.reinsurance_source_loader import (
    build_prein_index,
    default_config_path,
    load_prein,
    load_preintrt,
    load_prod_ptrty,
    prein_join_key,
    select_canonical_preintrt_rows,
    _s,
)
from qla_core.schema_constants import QUIKREIN_SCHEMA, QUIKRMST_SCHEMA

_DEFAULT_RULES_PATH = default_config_path("quikrein_derivation_rules.json")


def default_derivation_rules_path() -> str:
    return _DEFAULT_RULES_PATH


def load_derivation_rules(path: str | None = None) -> dict:
    rules_path = path or _DEFAULT_RULES_PATH
    if not os.path.isfile(rules_path):
        return {}
    with open(rules_path, encoding="utf-8") as fh:
        return json.load(fh)


def parse_lifepro_date(val: Any) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    s = _s(val)
    if not s or s in ("0", "00000000", "00/00/0000"):
        return ""
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(s[:10], fmt).strftime("%Y%m%d")
        except ValueError:
            continue
    digits = "".join(ch for ch in s if ch.isdigit())
    if len(digits) == 8:
        return digits
    return ""


def parse_amount(val: Any) -> float | None:
    s = _s(val).replace(",", "")
    if not s or s in (".", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def format_amount(val: float | None, *, decimals: int = 2) -> str:
    if val is None:
        return ""
    return f"{val:.{decimals}f}"


def format_percent(val: float | None, *, decimals: int = 2) -> str:
    if val is None:
        return ""
    return f"{val:.{decimals}f}"


def format_percent4(val: float | None) -> str:
    if val is None:
        return ""
    return f"{val:.4f}"


def _blank_row(schema: list[str]) -> dict[str, str]:
    return {h: "" for h in schema}


def _resolve_mtype(reinsurance_code: str, type_map: dict[str, str]) -> tuple[str, str]:
    code = _s(reinsurance_code).upper()
    if not code:
        return "", "MISSING_REINSURANCE_CODE"
    mapped = type_map.get(code, "")
    if not mapped:
        return "", f"UNKNOWN_REINSURANCE_CODE:{code}"
    return mapped, "TYPE_CROSSWALK"


def convert_quikrein_from_ptrty(
    ptrty_df: pd.DataFrame,
    *,
    reinsurer_crosswalk: dict[str, dict[str, str]],
    type_map: dict[str, str],
    rules: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[dict]]:
    default_mcomp = _s(rules.get("default_mcomp", "C")) or "C"
    treaty_index = build_ptrty_treaty_index(ptrty_df)
    rows: list[dict[str, str]] = []
    trace_rows: list[dict] = []
    exceptions: list[dict] = []
    seen_treaties: set[str] = set()

    for treaty_code, src_row in sorted(treaty_index.items()):
        cw = reinsurer_crosswalk.get(treaty_code.upper())
        if not cw:
            exceptions.append({
                "TREATY_CODE": treaty_code,
                "EXCEPTION_REASON": "MISSING_REINSURER_CROSSWALK",
            })
            continue
        if treaty_code.upper() in seen_treaties:
            exceptions.append({
                "TREATY_CODE": treaty_code,
                "EXCEPTION_REASON": "DUPLICATE_TREATY_KEY",
            })
            continue
        seen_treaties.add(treaty_code.upper())

        mtype, type_source = _resolve_mtype(src_row.get("REINSURANCE_CODE", ""), type_map)
        if not mtype:
            exceptions.append({
                "TREATY_CODE": treaty_code,
                "EXCEPTION_REASON": type_source,
                "REINSURANCE_CODE": _s(src_row.get("REINSURANCE_CODE", "")),
            })
            continue

        pct = None
        if _s(src_row.get("CONST_REIN_PCT_IND", "")).upper() == "Y":
            pct = parse_amount(src_row.get("CONSTANT_REIN_PCT", ""))

        start_dt = parse_lifepro_date(src_row.get("START_DATE", ""))
        stop_dt = parse_lifepro_date(src_row.get("STOP_DATE", ""))
        if _s(src_row.get("START_DATE", "")) and not start_dt:
            exceptions.append({
                "TREATY_CODE": treaty_code,
                "EXCEPTION_REASON": "INVALID_START_DATE",
                "START_DATE": _s(src_row.get("START_DATE", "")),
            })
        if _s(src_row.get("STOP_DATE", "")) and not stop_dt:
            exceptions.append({
                "TREATY_CODE": treaty_code,
                "EXCEPTION_REASON": "INVALID_STOP_DATE",
                "STOP_DATE": _s(src_row.get("STOP_DATE", "")),
            })

        row = _blank_row(QUIKREIN_SCHEMA)
        row.update({
            "MREINCO": cw.get("MREINCO", ""),
            "MTREATY": treaty_code[:20],
            "MTYPE": mtype,
            "MCOMP": default_mcomp,
            "MEFFDATE": start_dt,
            "MENDDATE": stop_dt,
            "MREINNAME": cw.get("MREINNAME", "")[:40],
            "MREINADDR1": cw.get("MREINADDR1", "")[:30],
            "MREINADDR2": cw.get("MREINADDR2", "")[:30],
            "MREINCITY": cw.get("MREINCITY", "")[:30],
            "MREINST": cw.get("MREINST", "")[:2],
            "MREINZIP": cw.get("MREINZIP", "")[:5],
            "MREINZIP2": cw.get("MREINZIP2", "")[:4],
            "MCEDED": format_percent(pct, decimals=2),
            "MNARCALC": "",
            "MBILLPFEE": "F",
        })
        rows.append(row)
        trace_rows.append({
            "TABLE": "QUIKREIN",
            "TREATY_CODE": treaty_code,
            "MREINCO": row["MREINCO"],
            "MREINNAME": row["MREINNAME"],
            "MTYPE": row["MTYPE"],
            "MTYPE_SOURCE": type_source,
            "REINSURANCE_CODE": _s(src_row.get("REINSURANCE_CODE", "")),
            "MCEDED_SOURCE": "PROD_PTRTY.CONSTANT_REIN_PCT" if pct is not None else "BLANK",
            "MCEDED_VALUE": row["MCEDED"],
            "CROSSWALK_CONFIDENCE": cw.get("CONFIDENCE", ""),
            "CROSSWALK_SOURCE": cw.get("SOURCE", ""),
            "CROSSWALK_NOTES": cw.get("NOTES", ""),
        })

    output_df = pd.DataFrame(rows, columns=QUIKREIN_SCHEMA) if rows else pd.DataFrame(columns=QUIKREIN_SCHEMA)
    trace_df = pd.DataFrame(trace_rows)
    exc_df = pd.DataFrame(exceptions) if exceptions else pd.DataFrame(columns=["TREATY_CODE", "EXCEPTION_REASON"])
    return output_df, trace_df, exc_df, exceptions


def convert_quikrmst_from_preintrt(
    preintrt_df: pd.DataFrame,
    prein_index: dict[tuple[str, str, str, str], pd.Series],
    *,
    reinsurer_crosswalk: dict[str, dict[str, str]],
    ptrty_index: dict[str, pd.Series],
    type_map: dict[str, str],
    quikridr_index: dict[tuple[str, str], dict[str, str]],
    quikmstr_index: dict[str, dict[str, str]],
    quikmstr_policies: set[str],
    quikrein_treaties: set[str],
    cw_map: dict[str, str] | None,
    rules: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[dict], list[dict]]:
    rows: list[dict[str, str]] = []
    trace_rows: list[dict] = []
    exceptions: list[dict] = []
    defaulted: list[dict] = []

    for src_idx, src_row in preintrt_df.iterrows():
        join_key = prein_join_key(src_row)
        parent = prein_index.get(join_key)
        if parent is None:
            exceptions.append({
                **{k: join_key[i] for i, k in enumerate(["POLICY_NUMBER", "BENEFIT_SEQ", "EFFECTIVE_DATE", "RECORD_SEQUENCE"])},
                "TREATY_CODE": _s(src_row.get("TREATY_CODE", "")),
                "EXCEPTION_REASON": "MISSING_PARENT_PREIN",
            })
            continue

        treaty_code = _s(src_row.get("TREATY_CODE", ""))
        treaty_key = treaty_code.upper()
        if not treaty_code:
            exceptions.append({**dict(zip(["POLICY_NUMBER", "BENEFIT_SEQ"], join_key[:2])), "EXCEPTION_REASON": "BLANK_TREATY_CODE"})
            continue

        cw = reinsurer_crosswalk.get(treaty_key)
        if not cw:
            exceptions.append({
                "POLICY_NUMBER": join_key[0],
                "BENEFIT_SEQ": join_key[1],
                "TREATY_CODE": treaty_code,
                "EXCEPTION_REASON": "MISSING_REINSURER_CROSSWALK",
            })
            continue

        if treaty_key not in quikrein_treaties:
            exceptions.append({
                "POLICY_NUMBER": join_key[0],
                "TREATY_CODE": treaty_code,
                "EXCEPTION_REASON": "MISSING_TREATY_SETUP",
            })
            continue

        mpolicy, pol_source = resolve_mpolicy(join_key[0], cw_map)
        if not mpolicy:
            exceptions.append({"POLICY_NUMBER": join_key[0], "EXCEPTION_REASON": "INVALID_POLICY_NUMBER"})
            continue
        if quikmstr_policies and mpolicy not in quikmstr_policies:
            exceptions.append({
                "MPOLICY": mpolicy,
                "SOURCE_POLICY": join_key[0],
                "EXCEPTION_REASON": "MISSING_CONVERTED_POLICY",
            })
            continue

        phase, rider, phase_source = resolve_quikridr_phase(
            mpolicy,
            src_row.get("BENEFIT_SEQ", ""),
            quikridr_index,
        )
        if rider is None:
            exceptions.append({
                "MPOLICY": mpolicy,
                "SOURCE_POLICY": join_key[0],
                "BENEFIT_SEQ": join_key[1],
                "CANDIDATE_MPHASE": phase,
                "TREATY_CODE": treaty_code,
                "EXCEPTION_REASON": "MISSING_CONVERTED_PHASE",
                "PHASE_SOURCE": phase_source,
            })
            continue

        ptrty_row = ptrty_index.get(treaty_key)
        reins_code = _s(ptrty_row.get("REINSURANCE_CODE", "")) if ptrty_row is not None else ""
        mtype, type_source = _resolve_mtype(reins_code, type_map)
        if not mtype:
            exceptions.append({
                "MPOLICY": mpolicy,
                "MTREATY": treaty_code,
                "EXCEPTION_REASON": type_source,
            })
            continue

        retained = parse_amount(parent.get("RETENTION_AMOUNT", ""))
        ceded = parse_amount(src_row.get("AMOUNT_REINSURED", ""))
        if _s(parent.get("RETENTION_AMOUNT", "")) and retained is None:
            exceptions.append({
                "MPOLICY": mpolicy,
                "FIELD": "RETENTION_AMOUNT",
                "RAW_VALUE": _s(parent.get("RETENTION_AMOUNT", "")),
                "EXCEPTION_REASON": "INVALID_NUMERIC",
            })
            continue
        if _s(src_row.get("AMOUNT_REINSURED", "")) and ceded is None:
            exceptions.append({
                "MPOLICY": mpolicy,
                "FIELD": "AMOUNT_REINSURED",
                "RAW_VALUE": _s(src_row.get("AMOUNT_REINSURED", "")),
                "EXCEPTION_REASON": "INVALID_NUMERIC",
            })
            continue

        init_amt = parse_amount(parent.get("SPECIFIED_AMT", ""))
        if init_amt is None:
            init_amt = parse_amount(parent.get("DEATH_BENEFIT_AMT", ""))

        qm = quikmstr_index.get(mpolicy, {})
        mmode = _s(qm.get("MMODE", ""))
        mmodeprem = _s(qm.get("MMODEPREM", ""))
        if not mmodeprem:
            defaulted.append({
                "MPOLICY": mpolicy,
                "FIELD": "MMODEPREM",
                "DEFAULT": "BLANK",
                "REASON": "NO_QUIKMSTR_MMODEPREM",
            })

        row = _blank_row(QUIKRMST_SCHEMA)
        row.update({
            "MPOLICY": mpolicy,
            "MPHASE": phase,
            "MSTATUS": rider.get("MSTATUS", "")[:2],
            "MPLAN": rider.get("MPLAN", "")[:6],
            "MREINCO": cw.get("MREINCO", "")[:1],
            "MTREATY": treaty_code[:20],
            "MTYPE": mtype[:3],
            "MUWCLASS": (rider.get("MUWCLASS", "") or _s(parent.get("UNDERWRITING_CLASS", "")))[:2],
            "MINITAMT": format_amount(init_amt),
            "MRETAINED": format_amount(retained),
            "MCEDED": format_amount(ceded),
            "MPCTCEDED": "",
            "MBILLTO": "",
            "MMODE": mmode,
            "MMODEPREM": format_amount(parse_amount(mmodeprem)) if mmodeprem else "",
            "MCLAIMAMT": "0.00",
            "MCLAIMDATE": "",
            "MRECOVERBL": "0.00",
            "MRECVDDATE": "",
        })
        rows.append(row)
        trace_rows.append({
            "TABLE": "QUIKRMST",
            "SOURCE_ROW": int(src_idx) + 2,
            "SOURCE_POLICY": join_key[0],
            "MPOLICY": mpolicy,
            "MPOLICY_SOURCE": pol_source,
            "BENEFIT_SEQ": join_key[1],
            "MPHASE": phase,
            "MPHASE_SOURCE": phase_source,
            "MTREATY": treaty_code,
            "MREINCO": row["MREINCO"],
            "MREINNAME": cw.get("MREINNAME", ""),
            "MRETAINED_SOURCE": "PREIN.RETENTION_AMOUNT",
            "MRETAINED_VALUE": row["MRETAINED"],
            "MCEDED_SOURCE": "PREINTRT.AMOUNT_REINSURED",
            "MCEDED_VALUE": row["MCEDED"],
            "MSTATUS_SOURCE": "QUIKRIDR.MPHSTAT",
            "MPLAN_SOURCE": "QUIKRIDR.MPLAN",
            "MTYPE_SOURCE": type_source,
            "CROSSWALK_CONFIDENCE": cw.get("CONFIDENCE", ""),
            "CROSSWALK_SOURCE": cw.get("SOURCE", ""),
        })

    output_df = pd.DataFrame(rows, columns=QUIKRMST_SCHEMA) if rows else pd.DataFrame(columns=QUIKRMST_SCHEMA)
    trace_df = pd.DataFrame(trace_rows)
    exc_df = pd.DataFrame(exceptions) if exceptions else pd.DataFrame(columns=["EXCEPTION_REASON"])
    return output_df, trace_df, exc_df, exceptions, defaulted


def write_reinsurance_phase_reports(
    *,
    output_dir: str,
    rein_df: pd.DataFrame,
    rmst_df: pd.DataFrame,
    trace_df: pd.DataFrame,
    rein_exc_df: pd.DataFrame,
    rmst_exc_df: pd.DataFrame,
    defaulted_df: pd.DataFrame,
    ptrty_df: pd.DataFrame,
    prein_df: pd.DataFrame,
    preintrt_df: pd.DataFrame,
    superseded_df: pd.DataFrame,
    stats: dict,
) -> dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    paths: dict[str, str] = {}

    summary_lines = [
        "Phase 1 Reinsurance Conversion Summary",
        f"PROD_PTRTY rows: {stats.get('ptrty_rows', 0)}",
        f"PREIN rows: {stats.get('prein_rows', 0)}",
        f"PREINTRT rows (raw): {stats.get('preintrt_rows_raw', stats.get('preintrt_rows', 0))}",
        f"PREINTRT rows (canonical): {stats.get('preintrt_rows_canonical', len(preintrt_df))}",
        f"PREINTRT superseded: {stats.get('preintrt_superseded', len(superseded_df))}",
        f"QuikRein emitted: {len(rein_df)}",
        f"QuikRmst emitted: {len(rmst_df)}",
        f"QuikRein exceptions: {stats.get('quikrein_exceptions', 0)}",
        f"QuikRmst exceptions: {stats.get('quikrmst_exceptions', 0)}",
        f"Defaulted fields: {stats.get('defaulted_fields', 0)}",
        "",
        "Reinsurer crosswalk: Manual Placeholder / User Provided",
        "Stored-value rule: no recalculation of retained/ceded/allocation/premium.",
    ]
    summary_path = os.path.join(output_dir, "reinsurance_emit_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(summary_lines) + "\n")
    paths["reinsurance_emit_summary"] = summary_path

    p = os.path.join(output_dir, "quikrein_emit_candidates.csv")
    rein_df.to_csv(p, index=False)
    paths["quikrein_emit_candidates"] = p

    p = os.path.join(output_dir, "quikrmst_emit_candidates.csv")
    rmst_df.to_csv(p, index=False)
    paths["quikrmst_emit_candidates"] = p

    p = os.path.join(output_dir, "reinsurance_mapping_trace.csv")
    trace_df.to_csv(p, index=False)
    paths["reinsurance_mapping_trace"] = p

    p = os.path.join(output_dir, "quikrein_emit_exceptions.csv")
    rein_exc_df.to_csv(p, index=False)
    paths["quikrein_emit_exceptions"] = p

    p = os.path.join(output_dir, "quikrmst_emit_exceptions.csv")
    rmst_exc_df.to_csv(p, index=False)
    paths["quikrmst_emit_exceptions"] = p

    p = os.path.join(output_dir, "defaulted_fields_audit.csv")
    defaulted_df.to_csv(p, index=False)
    paths["defaulted_fields_audit"] = p

    rein_recon = pd.DataFrame([
        {
            "SOURCE_TREATY_CODE": _s(r.get("TREATY_CODE", "")),
            "EMITTED": 1,
            "STATUS": "PASS" if _s(r.get("TREATY_CODE", "")).upper() in set(rein_df["MTREATY"].astype(str).str.strip().str.upper()) else "MISSING",
        }
        for _, r in ptrty_df.iterrows()
    ])
    p = os.path.join(output_dir, "quikrein_source_reconciliation.csv")
    rein_recon.to_csv(p, index=False)
    paths["quikrein_source_reconciliation"] = p

    rmst_recon = pd.DataFrame([{
        "PREINTRT_ROWS_RAW": stats.get("preintrt_rows_raw", len(preintrt_df)),
        "PREINTRT_ROWS_CANONICAL": len(preintrt_df),
        "EMITTED_RMST_ROWS": len(rmst_df),
        "EXCEPTION_ROWS": stats.get("quikrmst_exceptions", 0),
        "STATUS": "PASS" if len(rmst_df) + stats.get("quikrmst_exceptions", 0) == len(preintrt_df) else "REVIEW",
    }])
    p = os.path.join(output_dir, "quikrmst_source_reconciliation.csv")
    rmst_recon.to_csv(p, index=False)
    paths["quikrmst_source_reconciliation"] = p

    tol = float(stats.get("amount_tolerance", 0.01))
    retained_total_src = sum(parse_amount(v) or 0.0 for v in prein_df.get("RETENTION_AMOUNT", []))
    ceded_total_src = sum(parse_amount(v) or 0.0 for v in preintrt_df.get("AMOUNT_REINSURED", []))
    retained_total_emit = sum(parse_amount(v) or 0.0 for v in rmst_df.get("MRETAINED", [])) if len(rmst_df) else 0.0
    ceded_total_emit = sum(parse_amount(v) or 0.0 for v in rmst_df.get("MCEDED", [])) if len(rmst_df) else 0.0

    p = os.path.join(output_dir, "quikrmst_retained_reconciliation.csv")
    pd.DataFrame([{
        "PREIN_RETENTION_AMOUNT_SUM": retained_total_src,
        "QUIKRMST_MRETAINED_SUM": retained_total_emit,
        "VARIANCE": retained_total_emit - retained_total_src,
        "TOLERANCE": tol,
        "STATUS": "INFO",
        "NOTE": "MRETAINED repeated on each treaty row; sum is informational not 1:1",
    }]).to_csv(p, index=False)
    paths["quikrmst_retained_reconciliation"] = p

    p = os.path.join(output_dir, "quikrmst_ceded_reconciliation.csv")
    pd.DataFrame([{
        "PREINTRT_AMOUNT_REINSURED_SUM": ceded_total_src,
        "QUIKRMST_MCEDED_SUM": ceded_total_emit,
        "VARIANCE": abs(ceded_total_emit - ceded_total_src),
        "TOLERANCE": tol,
        "STATUS": "PASS" if abs(ceded_total_emit - ceded_total_src) <= tol else "FAIL",
        "NOTE": "Canonical PREINTRT row per policy/benefit/treaty (latest EFFECTIVE_DATE)",
    }]).to_csv(p, index=False)
    paths["quikrmst_ceded_reconciliation"] = p

    p = os.path.join(output_dir, "superseded_preintrt_rows.csv")
    superseded_df.to_csv(p, index=False)
    paths["superseded_preintrt_rows"] = p

    for name, key in (
        ("missing_parent_prein.csv", "MISSING_PARENT_PREIN"),
        ("missing_treaty_setup.csv", "MISSING_TREATY_SETUP"),
        ("missing_converted_policy.csv", "MISSING_CONVERTED_POLICY"),
        ("missing_converted_phase.csv", "MISSING_CONVERTED_PHASE"),
        ("missing_reinsurer_crosswalk.csv", "MISSING_REINSURER_CROSSWALK"),
        ("duplicate_policy_phase_treaty.csv", "DUPLICATE_POLICY_PHASE_TREATY"),
        ("blank_treaty_rows.csv", "BLANK_TREATY_CODE"),
    ):
        subset = rmst_exc_df[rmst_exc_df["EXCEPTION_REASON"] == key] if len(rmst_exc_df) and "EXCEPTION_REASON" in rmst_exc_df.columns else pd.DataFrame()
        if key == "MISSING_REINSURER_CROSSWALK":
            rein_subset = rein_exc_df[rein_exc_df["EXCEPTION_REASON"] == key] if len(rein_exc_df) and "EXCEPTION_REASON" in rein_exc_df.columns else pd.DataFrame()
            subset = pd.concat([subset, rein_subset], ignore_index=True) if len(rein_subset) else subset
        p = os.path.join(output_dir, name)
        subset.to_csv(p, index=False)
        paths[name.replace(".csv", "")] = p

    invalid = []
    if len(rmst_exc_df) and "EXCEPTION_REASON" in rmst_exc_df.columns:
        invalid.extend(rmst_exc_df[rmst_exc_df["EXCEPTION_REASON"] == "INVALID_NUMERIC"].to_dict("records"))
    if len(rein_exc_df) and "EXCEPTION_REASON" in rein_exc_df.columns:
        invalid.extend(rein_exc_df[rein_exc_df["EXCEPTION_REASON"].isin(["INVALID_START_DATE", "INVALID_STOP_DATE"])].to_dict("records"))
    p = os.path.join(output_dir, "invalid_numerics.csv")
    pd.DataFrame(invalid).to_csv(p, index=False)
    paths["invalid_numerics"] = p

    p = os.path.join(output_dir, "invalid_dates.csv")
    date_invalid = rein_exc_df[rein_exc_df["EXCEPTION_REASON"].isin(["INVALID_START_DATE", "INVALID_STOP_DATE"])] if len(rein_exc_df) and "EXCEPTION_REASON" in rein_exc_df.columns else pd.DataFrame()
    date_invalid.to_csv(p, index=False)
    paths["invalid_dates"] = p

    unknown = rmst_exc_df[rmst_exc_df["EXCEPTION_REASON"].astype(str).str.startswith("UNKNOWN_", na=False)] if len(rmst_exc_df) and "EXCEPTION_REASON" in rmst_exc_df.columns else pd.DataFrame()
    p = os.path.join(output_dir, "unknown_type_status_uw_mappings.csv")
    unknown.to_csv(p, index=False)
    paths["unknown_type_status_uw_mappings"] = p

    return paths


def convert_reinsurance_phase1(
    ptrty_path: str,
    prein_path: str,
    preintrt_path: str,
    *,
    cw_map: dict[str, str] | None = None,
    rules: dict | None = None,
    output_dir: str | None = None,
    reinsurer_crosswalk_path: str | None = None,
    type_crosswalk_path: str | None = None,
    quikmstr_path: str | None = None,
    quikridr_path: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """
    Full Phase 1 reinsurance pipeline.

    Returns (quikrein_df, quikrmst_df, trace_df, quikrein_exc_df, quikrmst_exc_df, stats).
    """
    rules = rules or load_derivation_rules()
    reinsurer_crosswalk = load_reinsurer_crosswalk(reinsurer_crosswalk_path)
    type_map = load_reinsurance_type_crosswalk(type_crosswalk_path)
    quikridr_index = load_quikridr_index(quikridr_path)
    quikmstr_index = load_quikmstr_index(quikmstr_path)
    quikmstr_policies = load_quikmstr_policy_set(quikmstr_path)

    ptrty_df = load_prod_ptrty(ptrty_path)
    prein_df = load_prein(prein_path)
    preintrt_all_df = load_preintrt(preintrt_path)
    preintrt_df, superseded_df = select_canonical_preintrt_rows(preintrt_all_df)
    prein_index = build_prein_index(prein_df)
    ptrty_index = build_ptrty_treaty_index(ptrty_df)

    rein_df, rein_trace, rein_exc_df, rein_exceptions = convert_quikrein_from_ptrty(
        ptrty_df,
        reinsurer_crosswalk=reinsurer_crosswalk,
        type_map=type_map,
        rules=rules,
    )
    quikrein_treaties = set(rein_df["MTREATY"].astype(str).str.strip().str.upper()) if len(rein_df) else set()

    rmst_df, rmst_trace, rmst_exc_df, rmst_exceptions, defaulted = convert_quikrmst_from_preintrt(
        preintrt_df,
        prein_index,
        reinsurer_crosswalk=reinsurer_crosswalk,
        ptrty_index=ptrty_index,
        type_map=type_map,
        quikridr_index=quikridr_index,
        quikmstr_index=quikmstr_index,
        quikmstr_policies=quikmstr_policies,
        quikrein_treaties=quikrein_treaties,
        cw_map=cw_map,
        rules=rules,
    )

    trace_df = pd.concat([rein_trace, rmst_trace], ignore_index=True) if len(rein_trace) or len(rmst_trace) else pd.DataFrame()
    defaulted_df = pd.DataFrame(defaulted) if defaulted else pd.DataFrame(columns=["MPOLICY", "FIELD", "DEFAULT", "REASON"])

    tol = float(rules.get("amount_tolerance", 0.01))
    ceded_src = sum(parse_amount(v) or 0.0 for v in preintrt_df.get("AMOUNT_REINSURED", []))
    ceded_emit = sum(parse_amount(v) or 0.0 for v in rmst_df.get("MCEDED", [])) if len(rmst_df) else 0.0

    stats = {
        "ptrty_rows": len(ptrty_df),
        "prein_rows": len(prein_df),
        "preintrt_rows_raw": len(preintrt_all_df),
        "preintrt_rows": len(preintrt_all_df),
        "preintrt_rows_canonical": len(preintrt_df),
        "preintrt_superseded": len(superseded_df),
        "quikrein_emitted": len(rein_df),
        "quikrmst_emitted": len(rmst_df),
        "quikrein_exceptions": len(rein_exceptions),
        "quikrmst_exceptions": len(rmst_exceptions),
        "defaulted_fields": len(defaulted),
        "ceded_reconciliation_ok": abs(ceded_emit - ceded_src) <= tol,
        "ceded_source_total": ceded_src,
        "ceded_emit_total": ceded_emit,
        "amount_tolerance": tol,
        "reinsurer_crosswalk_rows": len(reinsurer_crosswalk),
    }

    if output_dir:
        stats["report_paths"] = write_reinsurance_phase_reports(
            output_dir=output_dir,
            rein_df=rein_df,
            rmst_df=rmst_df,
            trace_df=trace_df,
            rein_exc_df=rein_exc_df,
            rmst_exc_df=rmst_exc_df,
            defaulted_df=defaulted_df,
            ptrty_df=ptrty_df,
            prein_df=prein_df,
            preintrt_df=preintrt_df,
            superseded_df=superseded_df,
            stats=stats,
        )

    return rein_df, rmst_df, trace_df, rein_exc_df, rmst_exc_df, stats
