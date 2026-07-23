"""
PACTG → QuikBenh loan history converter (Issue #54).

Emits multi-line Loan History grid rows (MBENTYP 10/11/12) from PACTG 0411/0412/0413.
When history starts mid-stream, emits one synthetic opening seed row (MBENTYP 10) from
the last PLOAN LOAN_BALANCE before the first history date (OBQ-1 Option 1).
Appends to existing quikbenh.csv — preserves MBENTYP=8 (#34 ISRR) and other non-loan types.
Does not modify quikloan (#32/#44 footer companion).

Production emit is gated by QLA_ENABLE_QUIKBENH_LOAN_EMIT / QLA_QUIKBENH_LOAN_WRITE_OUTPUT.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import pandas as pd

from qla_core.normalize_utils import format_qladmin_mpolicy, normalize, normalize_columns
from qla_core.schema_constants import QUIKBENH_SCHEMA

_DEFAULT_RULES_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "plan_governance",
        "config",
        "quikbenh_loan_history_rules.json",
    )
)

_LOAN_REPLACE_TYPES = frozenset({"10", "11", "12"})


def default_derivation_rules_path() -> str:
    return _DEFAULT_RULES_PATH


def load_derivation_rules(path: str | None = None) -> dict:
    rules_path = path or _DEFAULT_RULES_PATH
    if not os.path.isfile(rules_path):
        return {}
    with open(rules_path, encoding="utf-8") as fh:
        return json.load(fh)


def _norm_pactg_code(val: Any) -> str:
    s = "".join(ch for ch in str(val).strip() if ch.isdigit())
    if not s:
        return ""
    return s.zfill(4)[-4:]


def _fmt_amount(val: Any) -> str:
    try:
        return f"{abs(float(str(val).replace(',', '').strip() or 0)):.2f}"
    except Exception:
        return ""


def _fmt_date_yyyymmdd(val: Any) -> str:
    s = normalize(val)
    if not s:
        return ""
    digits = "".join(ch for ch in s if ch.isdigit())
    if len(digits) >= 8:
        return digits[:8]
    return ""


def _load_existing_benh(path: str | None) -> pd.DataFrame:
    if not path or not os.path.isfile(path):
        return pd.DataFrame(columns=QUIKBENH_SCHEMA)
    df = pd.read_csv(path, encoding="utf-8", dtype=str, on_bad_lines="skip").fillna("")
    df = normalize_columns(df)
    for col in QUIKBENH_SCHEMA:
        if col not in df.columns:
            df[col] = ""
    return df[QUIKBENH_SCHEMA].copy()


def _rules_emit_map(rules: dict) -> dict[str, str]:
    raw = rules.get("pactg_emit_codes") or {"0411": "10", "0412": "11", "0413": "12"}
    return {str(k): str(v) for k, v in raw.items()}


def _rules_scan_codes(rules: dict) -> set[str]:
    raw = rules.get("pactg_scan_codes") or ["0411", "0412", "0413", "0414", "0415", "0416", "0417", "0451"]
    return {_norm_pactg_code(c) for c in raw if _norm_pactg_code(c)}


def _rules_exclude_codes(rules: dict) -> set[str]:
    raw = rules.get("pactg_exclude_codes") or ["0451"]
    return {_norm_pactg_code(c) for c in raw if _norm_pactg_code(c)}


def _loan_code_side(emit_code: str, credit_code: str, debit_code: str) -> str:
    """Return DEBIT / CREDIT / BOTH / NONE for where the emit loan code sits."""
    on_db = debit_code == emit_code
    on_cr = credit_code == emit_code
    if on_db and on_cr:
        return "BOTH"
    if on_db:
        return "DEBIT"
    if on_cr:
        return "CREDIT"
    return "NONE"


def _resolve_mbentyp_for_side(
    emit_code: str,
    side: str,
    emit_map: dict[str, str],
    *,
    credit_decrease_mbentyp: str = "12",
) -> str:
    """
    Map PACTG loan code + debit/credit side → QuikBenh MBENTYP.

    Debit-side 0411/0412 increase principal (10/11).
    Credit-side 0412 (interest offset) and 0413 (payment) decrease → type 12.
    """
    base = emit_map.get(emit_code, "")
    if side == "CREDIT" and base in {"10", "11"}:
        return str(credit_decrease_mbentyp or "12").strip() or "12"
    if side == "DEBIT":
        return base
    # BOTH / NONE: keep base map (legacy abs behavior)
    return base


def _to_float_balance(val: Any) -> float | None:
    try:
        return float(str(val).replace(",", "").strip())
    except Exception:
        return None


def _reverse_crosswalk(cw_map: dict[str, str]) -> dict[str, str]:
    return {v: k for k, v in cw_map.items() if v}


def _load_ploan_by_lifepro(ploan_path: str | None) -> dict[str, list[tuple[str, float]]]:
    if not ploan_path or not os.path.isfile(ploan_path):
        return {}
    df = pd.read_csv(
        ploan_path, encoding="latin1", low_memory=False, dtype=str, on_bad_lines="skip"
    ).fillna("")
    df = normalize_columns(df)
    by_lp: dict[str, list[tuple[str, float]]] = {}
    for _, row in df.iterrows():
        lp = str(row.get("POLICY_NUMBER", "")).strip()
        dt = _fmt_date_yyyymmdd(row.get("ACCRUAL_DATE", ""))
        bal = _to_float_balance(row.get("LOAN_BALANCE", ""))
        if not lp or not dt or bal is None:
            continue
        by_lp.setdefault(lp, []).append((dt, bal))
    for lp in by_lp:
        by_lp[lp].sort(key=lambda x: x[0])
    return by_lp


def _apply_opening_balance_seeds(
    loan_rows: list[dict[str, str]],
    *,
    ploan_by_lp: dict[str, list[tuple[str, float]]],
    lp_of_mpolicy: dict[str, str],
    rules: dict,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    seed_stats: dict[str, Any] = {
        "seed_emit": 0,
        "seed_skip_no_ploan": 0,
        "seed_skip_no_prior": 0,
        "seed_skip_zero_prior": 0,
        "seed_skip_dedupe": 0,
    }
    if not bool(rules.get("opening_balance_seed_enabled", True)):
        return loan_rows, seed_stats

    seed_mbentyp = str(rules.get("opening_balance_seed_mbentyp") or "10").strip()
    skip_same_day = bool(rules.get("opening_balance_seed_skip_if_same_day_type10", True))

    first_by_mp: dict[str, str] = {}
    type10_dates: set[tuple[str, str]] = set()
    for row in loan_rows:
        mp = row["MPOLICY"]
        dt = row["MDATE"]
        if mp not in first_by_mp or dt < first_by_mp[mp]:
            first_by_mp[mp] = dt
        if row["MBENTYP"] == "10":
            type10_dates.add((mp, dt))

    seed_rows: list[dict[str, str]] = []
    for mp, first_dt in first_by_mp.items():
        lp = lp_of_mpolicy.get(mp, "")
        if not lp or lp not in ploan_by_lp:
            seed_stats["seed_skip_no_ploan"] += 1
            continue
        prior = [(d, b) for d, b in ploan_by_lp[lp] if d < first_dt]
        if not prior:
            seed_stats["seed_skip_no_prior"] += 1
            continue
        seed_dt, seed_bal = prior[-1]
        if seed_bal <= 0:
            seed_stats["seed_skip_zero_prior"] += 1
            continue
        if skip_same_day and (mp, seed_dt) in type10_dates:
            seed_stats["seed_skip_dedupe"] += 1
            continue
        seed_rows.append(
            {
                "MPOLICY": mp,
                "MBENTYP": seed_mbentyp,
                "MDATE": seed_dt,
                "MBEN": f"{abs(seed_bal):.2f}",
            }
        )
        seed_stats["seed_emit"] += 1

    return loan_rows + seed_rows, seed_stats


def convert_quikbenh_loan_history_from_pactg(
    pactg_path: str,
    *,
    cw_map: dict[str, str] | None = None,
    rules: dict | None = None,
    ploan_path: str | None = None,
    output_dir: str | None = None,
    existing_benh_path: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """
    Build loan-history QuikBenh rows from PACTG and merge with existing Benh output.

    Returns:
        merged_df, loan_only_df, trace_df, exceptions_df, stats
    """
    rules = rules or load_derivation_rules()
    cw_map = cw_map or {}
    emit_map = _rules_emit_map(rules)
    scan_codes = _rules_scan_codes(rules)
    exclude_codes = _rules_exclude_codes(rules)
    exclude_reversal = bool(rules.get("exclude_reversal_code_y", True))
    side_aware = bool(rules.get("pactg_side_aware_mbentyp", True))
    credit_decrease_mbentyp = str(rules.get("credit_side_decrease_mbentyp") or "12").strip() or "12"
    replace_types = frozenset(
        str(t) for t in (rules.get("loan_mbentyp_replace_on_rerun") or sorted(_LOAN_REPLACE_TYPES))
    )

    source = pd.read_csv(pactg_path, encoding="latin1", low_memory=False, dtype=str, on_bad_lines="skip").fillna("")
    source = normalize_columns(source)

    loan_rows: list[dict[str, str]] = []
    trace_rows: list[dict[str, str]] = []
    exc_rows: list[dict[str, str]] = []
    stats: dict[str, Any] = {
        "pactg_rows_read": len(source),
        "bm_rows": 0,
        "emit_passed": 0,
        "emit_exceptions": 0,
        "reversed_excluded": 0,
        "excluded_0451_only": 0,
        "other_bm_skipped": 0,
        "orphan_no_crosswalk": 0,
        "bad_amount": 0,
        "bad_date": 0,
        "by_pactg_code": {},
        "by_mbentyp": {},
        "credit_side_as_12": 0,
        "debit_side_increase": 0,
        "policies": set(),
    }

    for _, src_row in source.iterrows():
        cr = _norm_pactg_code(src_row.get("CREDIT_CODE", ""))
        db = _norm_pactg_code(src_row.get("DEBIT_CODE", ""))
        codes = {c for c in (cr, db) if c in scan_codes}
        if not codes:
            continue
        stats["bm_rows"] += 1

        if exclude_reversal and normalize(src_row.get("REVERSAL_CODE", "")) == "Y":
            stats["reversed_excluded"] += 1
            continue

        emit_code = None
        for c in ("0411", "0412", "0413"):
            if c in codes:
                emit_code = c
                break
        if emit_code is None:
            if codes & exclude_codes or codes <= exclude_codes:
                stats["excluded_0451_only"] += 1
            else:
                stats["other_bm_skipped"] += 1
            continue

        pol = str(src_row.get("POLICY_NUMBER", "")).strip()
        amt_raw = src_row.get("TRANS_AMOUNT", "")
        if not str(amt_raw).strip() and "TRANS_AMOUNT     " in src_row.index:
            amt_raw = src_row.get("TRANS_AMOUNT     ", "")
        eff = _fmt_date_yyyymmdd(src_row.get("EFFECTIVE_DATE", ""))

        # Issue #2: membership via cw keys; identity is source + C
        pol_key = pol.strip().upper()
        if cw_map is not None and pol_key not in cw_map and pol.strip() not in cw_map:
            stats["orphan_no_crosswalk"] += 1
            exc_rows.append(
                {
                    "POLICY_NUMBER": pol,
                    "PACTG_CODE": emit_code,
                    "REASON": "ORPHAN_NO_CROSSWALK",
                    "EFFECTIVE_DATE": eff,
                    "TRANS_AMOUNT": str(amt_raw),
                }
            )
            continue
        mpolicy = format_qladmin_mpolicy(pol)
        if not mpolicy:
            stats["orphan_no_crosswalk"] += 1
            exc_rows.append(
                {
                    "POLICY_NUMBER": pol,
                    "PACTG_CODE": emit_code,
                    "REASON": "INVALID_POLICY_KEY",
                    "EFFECTIVE_DATE": eff,
                    "TRANS_AMOUNT": str(amt_raw),
                }
            )
            continue

        mben = _fmt_amount(amt_raw)
        if not mben:
            stats["bad_amount"] += 1
            exc_rows.append(
                {
                    "POLICY_NUMBER": pol,
                    "MPOLICY": mpolicy,
                    "PACTG_CODE": emit_code,
                    "REASON": "BAD_AMOUNT",
                    "EFFECTIVE_DATE": eff,
                    "TRANS_AMOUNT": str(amt_raw),
                }
            )
            continue
        if not eff:
            stats["bad_date"] += 1
            exc_rows.append(
                {
                    "POLICY_NUMBER": pol,
                    "MPOLICY": mpolicy,
                    "PACTG_CODE": emit_code,
                    "REASON": "BAD_DATE",
                    "EFFECTIVE_DATE": str(src_row.get("EFFECTIVE_DATE", "")),
                    "TRANS_AMOUNT": mben,
                }
            )
            continue

        side = _loan_code_side(emit_code, cr, db)
        if side_aware:
            mbentyp = _resolve_mbentyp_for_side(
                emit_code,
                side,
                emit_map,
                credit_decrease_mbentyp=credit_decrease_mbentyp,
            )
            if side == "CREDIT" and mbentyp == credit_decrease_mbentyp and emit_map.get(emit_code) in {
                "10",
                "11",
            }:
                stats["credit_side_as_12"] += 1
            elif side == "DEBIT":
                stats["debit_side_increase"] += 1
        else:
            mbentyp = emit_map[emit_code]
        row = {
            "MPOLICY": mpolicy,
            "MBENTYP": mbentyp,
            "MDATE": eff,
            "MBEN": mben,
        }
        loan_rows.append(row)
        stats["emit_passed"] += 1
        stats["by_pactg_code"][emit_code] = stats["by_pactg_code"].get(emit_code, 0) + 1
        stats["by_mbentyp"][mbentyp] = stats["by_mbentyp"].get(mbentyp, 0) + 1
        stats["policies"].add(mpolicy)

        if len(trace_rows) < 500:
            trace_rows.append(
                {
                    "POLICY_NUMBER": pol,
                    "MPOLICY": mpolicy,
                    "MBENTYP": mbentyp,
                    "MDATE": eff,
                    "MBEN": mben,
                    "PACTG_CODE": emit_code,
                    "CREDIT_CODE": cr,
                    "DEBIT_CODE": db,
                    "LOAN_CODE_SIDE": side,
                }
            )

    ploan_by_lp = _load_ploan_by_lifepro(ploan_path)
    lp_of_mpolicy = _reverse_crosswalk(cw_map)
    loan_rows, seed_stats = _apply_opening_balance_seeds(
        loan_rows,
        ploan_by_lp=ploan_by_lp,
        lp_of_mpolicy=lp_of_mpolicy,
        rules=rules,
    )
    stats.update(seed_stats)
    if seed_stats.get("seed_emit"):
        stats["by_mbentyp"]["10"] = stats["by_mbentyp"].get("10", 0) + seed_stats["seed_emit"]

    loan_df = pd.DataFrame(loan_rows, columns=QUIKBENH_SCHEMA)
    existing_df = _load_existing_benh(existing_benh_path)
    preserved_df = existing_df[
        ~existing_df["MBENTYP"].astype(str).str.strip().isin(replace_types)
    ].copy()

    stats["existing_rows"] = len(existing_df)
    stats["existing_preserved_rows"] = len(preserved_df)
    stats["existing_type8_rows"] = int(
        (existing_df["MBENTYP"].astype(str).str.strip() == "8").sum()
    )
    stats["existing_loan_type_rows_removed"] = len(existing_df) - len(preserved_df)

    if loan_df.empty:
        merged_df = preserved_df.reindex(columns=QUIKBENH_SCHEMA)
    else:
        merged_df = pd.concat([preserved_df, loan_df], ignore_index=True)
        sort_cols = ["MPOLICY", "MDATE", "MBENTYP"]
        merged_df = merged_df.sort_values(sort_cols, kind="mergesort").reset_index(drop=True)

    merged_df = merged_df.reindex(columns=QUIKBENH_SCHEMA).fillna("")
    loan_df = loan_df.reindex(columns=QUIKBENH_SCHEMA).fillna("")
    trace_df = pd.DataFrame(trace_rows)
    exceptions_df = pd.DataFrame(exc_rows)
    stats["emit_exceptions"] = len(exc_rows)
    stats["merged_rows"] = len(merged_df)
    stats["policy_count"] = len(stats["policies"])
    stats["policies"] = sorted(stats["policies"])

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sub = rules.get("staging_subdir") or "staged"
        stage_dir = os.path.join(output_dir, sub)
        os.makedirs(stage_dir, exist_ok=True)
        trace_df.to_csv(os.path.join(stage_dir, f"quikbenh_loan_trace_{stamp}.csv"), index=False)
        exceptions_df.to_csv(
            os.path.join(stage_dir, f"quikbenh_loan_exceptions_{stamp}.csv"), index=False
        )
        loan_df.to_csv(os.path.join(stage_dir, f"quikbenh_loan_emit_{stamp}.csv"), index=False)
        summary_path = os.path.join(output_dir, "quikbenh_loan_emit_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as fh:
            fh.write(f"Issue #54 QuikBenh loan history emit @ {stamp}\n")
            for key in (
                "pactg_rows_read",
                "bm_rows",
                "emit_passed",
                "emit_exceptions",
                "reversed_excluded",
                "excluded_0451_only",
                "seed_emit",
                "seed_skip_no_prior",
                "seed_skip_zero_prior",
                "seed_skip_dedupe",
                "credit_side_as_12",
                "debit_side_increase",
                "existing_rows",
                "existing_preserved_rows",
                "existing_type8_rows",
                "merged_rows",
                "policy_count",
            ):
                fh.write(f"{key}: {stats.get(key)}\n")
            fh.write(f"by_pactg_code: {stats.get('by_pactg_code')}\n")
            fh.write(f"by_mbentyp: {stats.get('by_mbentyp')}\n")

    return merged_df, loan_df, trace_df, exceptions_df, stats


def write_quikbenh_csv(df: pd.DataFrame, out_path: str) -> None:
    out = df.reindex(columns=QUIKBENH_SCHEMA).fillna("")
    out.to_csv(out_path, index=False)
