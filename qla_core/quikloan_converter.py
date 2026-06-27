"""
PLOAN-primary QuikLoan staging converter (Phase L1).

Authoritative source: PLOAN.csv (LifePRO loan snapshot/history).
PACTG is not used to derive balances; reconciliation is separate.

Production emit is gated by config / QLA_ENABLE_QUIKLOAN_EMIT — default is staging + QA only.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from qla_core.schema_constants import QUIKLOAN_SCHEMA
from qla_core.normalize_utils import format_qladmin_mpolicy

_DEFAULT_RULES_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "plan_governance", "config", "quikloan_derivation_rules.json")
)

_PLACEHOLDER_POLICY_RE = re.compile(r"^[-_\s\.]+$")
_DATE_COLS = (
    "ACCRUAL_DATE",
    "LAST_CHG_DATE",
    "LAST_REPAY_DATE",
    "CAPITALIZED_DATE",
    "INT_START_DATE",
)


def default_derivation_rules_path() -> str:
    return _DEFAULT_RULES_PATH


def load_derivation_rules(path: str | None = None) -> dict:
    rules_path = path or _DEFAULT_RULES_PATH
    if not os.path.isfile(rules_path):
        return {}
    with open(rules_path, encoding="utf-8") as fh:
        return json.load(fh)


def _s(val: Any) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    return str(val).strip()


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().upper() for c in out.columns]
    return out


def parse_ploan_date(val: Any) -> pd.Timestamp | pd.NaT:
    """Parse LifePRO/PLOAN date values safely."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return pd.NaT
    s = _s(val)
    if not s or s in ("0", "00000000", "00/00/0000", "00/00/00"):
        return pd.NaT
    if _PLACEHOLDER_POLICY_RE.match(s.replace("/", "").replace("-", "")):
        return pd.NaT
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d", "%m/%d/%y"):
        try:
            return pd.Timestamp(datetime.strptime(s[:10], fmt))
        except ValueError:
            continue
    try:
        return pd.to_datetime(s, errors="coerce")
    except Exception:
        return pd.NaT


def format_quikloan_date(ts: pd.Timestamp | pd.NaT) -> str:
    if ts is None or pd.isna(ts):
        return ""
    return ts.strftime("%Y%m%d")


def is_valid_ploan_policy_number(policy: Any) -> bool:
    s = _s(policy)
    if not s:
        return False
    if _PLACEHOLDER_POLICY_RE.match(s):
        return False
    if set(s) <= {"-", "_", ".", " "}:
        return False
    return True


def _parse_balance(val: Any) -> float | None:
    s = _s(val)
    if not s or _PLACEHOLDER_POLICY_RE.match(s.replace(".", "").replace(",", "")):
        return None
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def normalize_loan_interest_rate(raw: Any, scale: str) -> tuple[str, str]:
    """
    Return (emit_value, scale_note). Does not silently scale unless config requests it.
    """
    s = _s(raw)
    if not s:
        return "", "missing"
    try:
        dec = float(s.replace(",", ""))
    except ValueError:
        return s, "unparsed_raw"

    if scale == "AS_PERCENT":
        return f"{dec * 100:.2f}", "AS_PERCENT"
    if scale == "AS_DECIMAL":
        return f"{dec:.4f}".rstrip("0").rstrip(".") if dec < 1 else f"{dec:.2f}", "AS_DECIMAL"
    # UNRESOLVED_REVIEW — preserve numeric string without *100
    if dec < 1:
        emit = f"{dec:.4f}".rstrip("0").rstrip(".")
    else:
        emit = f"{dec:.2f}"
    return emit, "UNRESOLVED_REVIEW"


def load_ploan_extract(path: str) -> pd.DataFrame:
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"PLOAN extract not found: {path}")
    df = pd.read_csv(path, dtype=str, low_memory=False)
    return _normalize_columns(df)


def sanitize_ploan_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Exclude invalid/separator rows. Returns (valid_df, excluded_df with reason).
    """
    work = _normalize_columns(df)
    reasons: list[str] = []
    keep: list[bool] = []

    for _, row in work.iterrows():
        pol = _s(row.get("POLICY_NUMBER", ""))
        bal = row.get("LOAN_BALANCE", "")
        if not is_valid_ploan_policy_number(pol):
            reasons.append("INVALID_POLICY")
            keep.append(False)
            continue
        parsed_bal = _parse_balance(bal)
        if parsed_bal is None:
            reasons.append("INVALID_LOAN_BALANCE")
            keep.append(False)
            continue
        reasons.append("")
        keep.append(True)

    work["_EXCLUDE_REASON"] = reasons
    work["_LOAN_BALANCE_NUM"] = work["LOAN_BALANCE"].map(_parse_balance)
    valid = work[work["_EXCLUDE_REASON"] == ""].copy()
    excluded = work[work["_EXCLUDE_REASON"] != ""].copy()
    return valid, excluded


def select_latest_ploan_row_per_policy(df: pd.DataFrame, rules: dict | None = None) -> pd.DataFrame:
    rules = rules or {}
    sort_cols = rules.get("latest_row_sort") or ["ACCRUAL_DATE", "LAST_CHG_DATE", "LAST_CHG_TIME"]
    work = df.copy()
    for col in _DATE_COLS:
        if col in work.columns:
            work[f"_{col}_TS"] = work[col].map(parse_ploan_date)
        else:
            work[f"_{col}_TS"] = pd.NaT
    for col in sort_cols:
        ts_col = f"_{col}_TS"
        if ts_col not in work.columns and col in work.columns:
            work[ts_col] = work[col].map(parse_ploan_date)
    policy_col = "POLICY_NUMBER"
    sort_keys = [policy_col] + [f"_{c}_TS" if f"_{c}_TS" in work.columns else c for c in sort_cols]
    existing = [k for k in sort_keys if k in work.columns]
    work = work.sort_values(existing, kind="mergesort")
    latest = work.groupby(policy_col, as_index=False).tail(1).copy()
    latest["_LATEST_BALANCE_CLASS"] = np.where(
        latest["_LOAN_BALANCE_NUM"].fillna(0) != 0,
        "ACTIVE_CANDIDATE",
        "ZERO_BALANCE_HOLD",
    )
    return latest


def _resolve_mloanidt(row: pd.Series, rules: dict) -> tuple[str, str]:
    precedence = rules.get("mloanidt_precedence") or ["LAST_REPAY_DATE", "CAPITALIZED_DATE"]
    for col in precedence:
        ts_col = f"_{col}_TS"
        if ts_col in row.index and pd.notna(row.get(ts_col)):
            return format_quikloan_date(row[ts_col]), col
        if col in row.index:
            ts = parse_ploan_date(row[col])
            if pd.notna(ts):
                return format_quikloan_date(ts), col
    return "", "missing"


def _map_policy_number(policy: str, cw_map: dict | None) -> tuple[str, str]:
    src = _s(policy)
    if not cw_map:
        return src, "NO_CROSSWALK"
    key = src.upper()
    mapped = cw_map.get(key) or cw_map.get(src)
    if mapped:
        return format_qladmin_mpolicy(mapped), "CROSSWALK_APPLIED"
    return src, "CROSSWALK_MISS"


def map_ploan_to_quikloan(
    latest_df: pd.DataFrame,
    cw_map: dict | None = None,
    rules: dict | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Map latest PLOAN rows to QuikLoan candidate schema.
    Returns (candidates_df, trace_df with mapping audit columns).
    """
    rules = rules or load_derivation_rules()
    scale = rules.get("mloanint_scale", "UNRESOLVED_REVIEW")
    mloanintx_default = rules.get("mloanintx_default", "")
    mloanbill_default = rules.get("mloanbill_default", "0.00")
    prin_src = rules.get("mloanprin_source", "LOAN_BALANCE")
    bal_src = rules.get("mloanbal_source", "LOAN_BALANCE")

    rows: list[dict] = []
    trace_rows: list[dict] = []

    for _, row in latest_df.iterrows():
        pol_src = _s(row.get("POLICY_NUMBER", ""))
        mpolicy, cw_status = _map_policy_number(pol_src, cw_map)

        bal_num = row.get("_LOAN_BALANCE_NUM")
        if bal_num is None:
            bal_num = _parse_balance(row.get(bal_src, ""))
        bal_str = f"{float(bal_num):.2f}" if bal_num is not None else ""

        prin_raw = row.get(prin_src, row.get("LOAN_BALANCE", ""))
        prin_num = _parse_balance(prin_raw)
        prin_str = f"{float(prin_num):.2f}" if prin_num is not None else bal_str

        mloanint, int_scale_note = normalize_loan_interest_rate(row.get("INTEREST_RATE", ""), scale)
        mloanintx = mloanintx_default if rules.get("mloanintx_source") == "UNRESOLVED" else _s(row.get("INTEREST_TYPE", ""))

        mloandate = ""
        acc_ts = row.get("_ACCRUAL_DATE_TS")
        if pd.notna(acc_ts):
            mloandate = format_quikloan_date(acc_ts)
        elif "ACCRUAL_DATE" in row.index:
            mloandate = format_quikloan_date(parse_ploan_date(row["ACCRUAL_DATE"]))

        mloanidt, idt_src = _resolve_mloanidt(row, rules)

        accr_raw = row.get(rules.get("mloanaccr_source", "ACCRUED_INT_AMT"), "0")
        accr_num = _parse_balance(accr_raw)
        mloanaccr = f"{float(accr_num):.2f}" if accr_num is not None else "0.00"

        candidate = {
            "MPOLICY": mpolicy,
            "MLOANPRIN": prin_str,
            "MLOANBAL": bal_str,
            "MLOANINT": mloanint,
            "MLOANINTX": mloanintx,
            "MLOANIDT": mloanidt,
            "MLOANDATE": mloandate,
            "MLOANACCR": mloanaccr,
            "MLOANBILL": mloanbill_default,
        }
        rows.append({k: candidate[k] for k in QUIKLOAN_SCHEMA})

        trace_rows.append({
            "SOURCE_POLICY": pol_src,
            "MPOLICY": mpolicy,
            "CROSSWALK_STATUS": cw_status,
            "LOAN_BALANCE": bal_str,
            "MLOANPRIN_SOURCE": prin_src,
            "MLOANINT_SCALE_NOTE": int_scale_note,
            "MLOANIDT_SOURCE": idt_src,
            "INTEREST_TYPE": _s(row.get("INTEREST_TYPE", "")),
            "INT_METHOD": _s(row.get("INT_METHOD", "")),
            "BALANCE_CLASS": row.get("_LATEST_BALANCE_CLASS", ""),
            **{k: candidate[k] for k in QUIKLOAN_SCHEMA},
        })

    return pd.DataFrame(rows, columns=QUIKLOAN_SCHEMA), pd.DataFrame(trace_rows)


def validate_quikloan_emit(
    quikloan_df: pd.DataFrame,
    latest_df: pd.DataFrame,
    rules: dict | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Split emit candidates vs exceptions using derivation rules.
    """
    rules = rules or load_derivation_rules()
    emit_zero = bool(rules.get("emit_zero_balance_loans", False))
    hold_missing_rate = bool(rules.get("hold_missing_interest_rate", True))
    hold_missing_date = bool(rules.get("hold_missing_mloandate", True))

    passed: list[dict] = []
    exceptions: list[dict] = []

    for i in range(len(quikloan_df)):
        row = quikloan_df.iloc[i]
        src_row = latest_df.iloc[i] if i < len(latest_df) else None
        src_pol = _s(src_row.get("POLICY_NUMBER", row.get("MPOLICY", ""))) if src_row is not None else _s(row.get("MPOLICY", ""))

        reasons: list[str] = []
        if src_row is not None:
            bal_class = _s(src_row.get("_LATEST_BALANCE_CLASS", ""))
        else:
            try:
                bal_num = float(_s(row.get("MLOANBAL", "0")) or 0)
            except ValueError:
                bal_num = 0
            bal_class = "ACTIVE_CANDIDATE" if bal_num != 0 else "ZERO_BALANCE_HOLD"

        if bal_class == "ZERO_BALANCE_HOLD" and not emit_zero:
            reasons.append("ZERO_BALANCE_HELD")
        if hold_missing_date and not _s(row.get("MLOANDATE", "")):
            reasons.append("MISSING_MLOANDATE")
        if hold_missing_rate and not _s(row.get("MLOANINT", "")):
            reasons.append("MISSING_INTEREST_RATE")
        if not is_valid_ploan_policy_number(src_pol):
            reasons.append("INVALID_POLICY")
        if not _s(row.get("MLOANBAL", "")):
            reasons.append("INVALID_LOAN_BALANCE")

        blocking = [r for r in reasons if r]
        if blocking:
            exceptions.append({**row.to_dict(), "EXCEPTION_REASON": ";".join(blocking), "SOURCE_POLICY": src_pol})
        else:
            passed.append(row.to_dict())

    passed_df = pd.DataFrame(passed, columns=QUIKLOAN_SCHEMA) if passed else pd.DataFrame(columns=QUIKLOAN_SCHEMA)

    exc_cols = list(QUIKLOAN_SCHEMA) + ["EXCEPTION_REASON", "SOURCE_POLICY"]
    exceptions_df = pd.DataFrame(exceptions, columns=exc_cols) if exceptions else pd.DataFrame(columns=exc_cols)

    stats = {
        "candidate_rows": len(quikloan_df),
        "emit_passed": len(passed_df),
        "emit_exceptions": len(exceptions_df),
        "zero_balance_held": sum(1 for e in exceptions if "ZERO_BALANCE_HELD" in _s(e.get("EXCEPTION_REASON", ""))),
    }
    return passed_df, exceptions_df, stats


def _build_ploan_profile_summary(
    raw_count: int,
    valid_df: pd.DataFrame,
    excluded_df: pd.DataFrame,
    latest_df: pd.DataFrame,
    rules: dict,
) -> str:
    lines = [
        "PLOAN Profile Summary (Phase L1 QuikLoan staging)",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"total_raw_rows: {raw_count}",
        f"valid_data_rows: {len(valid_df)}",
        f"excluded_placeholder_separator_rows: {len(excluded_df)}",
        f"unique_policy_count: {valid_df['POLICY_NUMBER'].nunique() if 'POLICY_NUMBER' in valid_df.columns else 0}",
    ]
    if "_LATEST_BALANCE_CLASS" in latest_df.columns:
        active = int((latest_df["_LATEST_BALANCE_CLASS"] == "ACTIVE_CANDIDATE").sum())
        zero = int((latest_df["_LATEST_BALANCE_CLASS"] == "ZERO_BALANCE_HOLD").sum())
        lines.append(f"latest_non_zero_balance_count: {active}")
        lines.append(f"latest_zero_balance_count: {zero}")
        if active:
            active_bal = latest_df[latest_df["_LATEST_BALANCE_CLASS"] == "ACTIVE_CANDIDATE"]["_LOAN_BALANCE_NUM"].sum()
            lines.append(f"total_latest_LOAN_BALANCE_active_candidates: {active_bal:.2f}")

    if "POLICY_NUMBER" in valid_df.columns:
        per_pol = valid_df.groupby("POLICY_NUMBER").size()
        lines.extend([
            f"rows_per_policy_min: {int(per_pol.min())}",
            f"rows_per_policy_median: {float(per_pol.median()):.1f}",
            f"rows_per_policy_max: {int(per_pol.max())}",
        ])

    if "_ACCRUAL_DATE_TS" in valid_df.columns:
        acc = valid_df["_ACCRUAL_DATE_TS"].dropna()
        if len(acc):
            lines.append(f"ACCRUAL_DATE_range: {acc.min().date()} to {acc.max().date()}")

    for col, label in (
        ("INTEREST_RATE", "INTEREST_RATE"),
        ("INTEREST_TYPE", "INTEREST_TYPE"),
        ("INT_METHOD", "INT_METHOD"),
        ("STATUS_CODE", "STATUS_CODE"),
        ("TYPE_CODE", "TYPE_CODE"),
    ):
        if col in latest_df.columns:
            lines.append(f"\n{label} distribution (latest row per policy):")
            for k, v in latest_df[col].fillna("(blank)").astype(str).value_counts().head(15).items():
                lines.append(f"  {k}: {v}")

    for col in ("ACCRUAL_DATE", "LAST_REPAY_DATE", "CAPITALIZED_DATE", "INTEREST_RATE"):
        if col in latest_df.columns:
            if col == "INTEREST_RATE":
                miss = latest_df[col].map(lambda x: not _s(x) or _parse_balance(x) is None and not _s(x)).sum()
            else:
                ts_col = f"_{col}_TS"
                if ts_col in latest_df.columns:
                    miss = latest_df[ts_col].isna().sum()
                else:
                    miss = latest_df[col].map(lambda x: pd.isna(parse_ploan_date(x))).sum()
            lines.append(f"missing_{col}_latest: {int(miss)}")

    lines.append("\nDerivation rules: " + (rules.get("description") or "quikloan_derivation_rules.json"))
    lines.append("PACTG: reconciliation-only; not used for QuikLoan balances in Phase L1.")
    return "\n".join(lines) + "\n"


def write_quikloan_phase_reports(
    *,
    output_dir: str,
    raw_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    excluded_df: pd.DataFrame,
    latest_df: pd.DataFrame,
    quikloan_df: pd.DataFrame,
    trace_df: pd.DataFrame,
    passed_df: pd.DataFrame,
    exceptions_df: pd.DataFrame,
    rules: dict,
    stats: dict,
) -> dict[str, str]:
    """Write all Phase L1 QA artifacts. Returns path map."""
    os.makedirs(output_dir, exist_ok=True)
    paths: dict[str, str] = {}

    profile_path = os.path.join(output_dir, "ploan_profile_summary.txt")
    with open(profile_path, "w", encoding="utf-8") as fh:
        fh.write(
            _build_ploan_profile_summary(len(raw_df), valid_df, excluded_df, latest_df, rules)
        )
    paths["ploan_profile_summary"] = profile_path

    sel_cols = [
        "POLICY_NUMBER", "ACCRUAL_DATE", "LAST_CHG_DATE", "LAST_CHG_TIME",
        "LOAN_BALANCE", "ORIG_LOAN_AMOUNT", "LOAN_AMT_ADDED", "ACCRUED_INT_AMT",
        "INTEREST_RATE", "INTEREST_TYPE", "INT_METHOD", "STATUS_CODE", "TYPE_CODE",
        "LAST_REPAY_DATE", "CAPITALIZED_DATE", "INT_START_DATE", "_LATEST_BALANCE_CLASS",
    ]
    sel = latest_df[[c for c in sel_cols if c in latest_df.columns]].copy()
    p = os.path.join(output_dir, "ploan_latest_row_selection.csv")
    sel.to_csv(p, index=False)
    paths["ploan_latest_row_selection"] = p

    emit_cols = [c for c in QUIKLOAN_SCHEMA if c in passed_df.columns]
    p = os.path.join(output_dir, "quikloan_emit_candidates.csv")
    (passed_df[emit_cols] if emit_cols else passed_df).to_csv(p, index=False)
    paths["quikloan_emit_candidates"] = p

    zero = latest_df[latest_df.get("_LATEST_BALANCE_CLASS", pd.Series()) == "ZERO_BALANCE_HOLD"]
    p = os.path.join(output_dir, "zero_balance_loan_policies.csv")
    zero.to_csv(p, index=False)
    paths["zero_balance_loan_policies"] = p

    date_issues = []
    for _, row in latest_df.iterrows():
        pol = _s(row.get("POLICY_NUMBER", ""))
        mloandate_ok = pd.notna(row.get("_ACCRUAL_DATE_TS", pd.NaT))
        idt_ok = any(
            pd.notna(row.get(f"_{c}_TS", pd.NaT))
            for c in (rules.get("mloanidt_precedence") or [])
        )
        if not mloandate_ok or not idt_ok:
            date_issues.append({
                "POLICY_NUMBER": pol,
                "MLOANDATE_MISSING": not mloandate_ok,
                "MLOANIDT_MISSING": not idt_ok,
                "SEVERITY": "HIGH" if not mloandate_ok else "MEDIUM",
                "ACCRUAL_DATE": _s(row.get("ACCRUAL_DATE", "")),
                "LAST_REPAY_DATE": _s(row.get("LAST_REPAY_DATE", "")),
                "CAPITALIZED_DATE": _s(row.get("CAPITALIZED_DATE", "")),
            })
    p = os.path.join(output_dir, "missing_invalid_dates.csv")
    pd.DataFrame(date_issues).to_csv(p, index=False)
    paths["missing_invalid_dates"] = p

    def _missing_rate(val):
        s = _s(val)
        if not s or _PLACEHOLDER_POLICY_RE.match(s.replace(".", "")):
            return True
        try:
            float(s.replace(",", ""))
            return False
        except ValueError:
            return True

    miss_rate = latest_df[latest_df["INTEREST_RATE"].map(_missing_rate)] if "INTEREST_RATE" in latest_df.columns else latest_df.iloc[0:0]
    p = os.path.join(output_dir, "missing_interest_rate.csv")
    miss_rate.to_csv(p, index=False)
    paths["missing_interest_rate"] = p

    intx = latest_df[["POLICY_NUMBER", "INTEREST_TYPE", "INT_METHOD"]].copy()
    intx["NOTE"] = "INTEREST_TYPE=F is fixed-rate in LifePRO; do not map to QLAdmin MLOANINTX A/R without BA confirmation."
    p = os.path.join(output_dir, "unresolved_mloanintx.csv")
    intx.to_csv(p, index=False)
    paths["unresolved_mloanintx"] = p

    bill = trace_df[["SOURCE_POLICY", "MPOLICY", "MLOANBILL"]].copy() if len(trace_df) else pd.DataFrame()
    if len(bill):
        bill["NOTE"] = "MLOANBILL has no PLOAN source; value is config default only."
    p = os.path.join(output_dir, "unresolved_mloanbill.csv")
    bill.to_csv(p, index=False)
    paths["unresolved_mloanbill"] = p

    rate_review = []
    if "INTEREST_RATE" in latest_df.columns:
        for rate, grp in latest_df.groupby(latest_df["INTEREST_RATE"].astype(str).str.strip()):
            try:
                dec = float(rate.replace(",", ""))
            except ValueError:
                dec = np.nan
            rate_review.append({
                "raw_source_value": rate,
                "as_decimal_candidate": f"{dec:.4f}" if pd.notna(dec) and dec < 1 else str(dec),
                "as_percent_candidate": f"{dec * 100:.2f}" if pd.notna(dec) and dec < 1 else str(dec),
                "policy_count": len(grp),
                "recommendation": "pending BA — mloanint_scale=UNRESOLVED_REVIEW",
            })
    p = os.path.join(output_dir, "interest_rate_format_review.csv")
    pd.DataFrame(rate_review).to_csv(p, index=False)
    paths["interest_rate_format_review"] = p

    prin_exc = []
    for _, row in latest_df.iterrows():
        orig = _parse_balance(row.get("ORIG_LOAN_AMOUNT", ""))
        added = _parse_balance(row.get("LOAN_AMT_ADDED", ""))
        bal = row.get("_LOAN_BALANCE_NUM")
        sum_check = (orig or 0) + (added or 0) if orig is not None and added is not None else None
        flag = ""
        if sum_check is not None and bal is not None and abs(sum_check - bal) > 0.01:
            flag = "ORIG_PLUS_ADDED_NE_BALANCE"
        prin_exc.append({
            "POLICY_NUMBER": _s(row.get("POLICY_NUMBER", "")),
            "ORIG_LOAN_AMOUNT": orig,
            "LOAN_AMT_ADDED": added,
            "LOAN_BALANCE": bal,
            "MLOANPRIN_STAGING": f"{bal:.2f}" if bal is not None else "",
            "MLOANBAL_STAGING": f"{bal:.2f}" if bal is not None else "",
            "BA_REVIEW_FLAG": flag or "MLOANPRIN=LOAN_BALANCE per staging config; confirm principal definition",
        })
    p = os.path.join(output_dir, "mloanprin_vs_balance_exceptions.csv")
    pd.DataFrame(prin_exc).to_csv(p, index=False)
    paths["mloanprin_vs_balance_exceptions"] = p

    p = os.path.join(output_dir, "quikloan_emit_exceptions.csv")
    exceptions_df.to_csv(p, index=False)
    paths["quikloan_emit_exceptions"] = p

    trace_path = os.path.join(output_dir, "quikloan_mapping_trace.csv")
    trace_df.to_csv(trace_path, index=False)
    paths["quikloan_mapping_trace"] = trace_path

    return paths


def convert_quikloan_from_ploan(
    ploan_path: str,
    *,
    cw_map: dict | None = None,
    rules: dict | None = None,
    output_dir: str | None = None,
    crosswalk_path: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """
    Full PLOAN → QuikLoan staging pipeline.

    Returns (passed_candidates_df, trace_df, exceptions_df, stats).
    When output_dir is set, writes Phase L1 QA reports.
    """
    rules = rules or load_derivation_rules()
    if cw_map is None and crosswalk_path and os.path.isfile(crosswalk_path):
        from qla_core.quikplan_converter import load_crosswalk_map

        cw_map = load_crosswalk_map(crosswalk_path)

    raw_df = load_ploan_extract(ploan_path)
    valid_df, excluded_df = sanitize_ploan_rows(raw_df)

    for col in _DATE_COLS:
        if col in valid_df.columns:
            valid_df[f"_{col}_TS"] = valid_df[col].map(parse_ploan_date)

    latest_df = select_latest_ploan_row_per_policy(valid_df, rules)
    quikloan_df, trace_df = map_ploan_to_quikloan(latest_df, cw_map, rules)
    passed_df, exceptions_df, stats = validate_quikloan_emit(quikloan_df, latest_df, rules)

    stats.update({
        "raw_rows": len(raw_df),
        "valid_rows": len(valid_df),
        "excluded_rows": len(excluded_df),
        "latest_policies": len(latest_df),
        "mapped_rows": len(quikloan_df),
    })

    if output_dir:
        report_paths = write_quikloan_phase_reports(
            output_dir=output_dir,
            raw_df=raw_df,
            valid_df=valid_df,
            excluded_df=excluded_df,
            latest_df=latest_df,
            quikloan_df=quikloan_df,
            trace_df=trace_df,
            passed_df=passed_df,
            exceptions_df=exceptions_df,
            rules=rules,
            stats=stats,
        )
        stats["report_paths"] = report_paths

    return passed_df, trace_df, exceptions_df, stats
