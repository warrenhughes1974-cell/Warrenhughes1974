"""Issue #21J — plan-level modal premium factors and PAC policy overrides."""

from __future__ import annotations

import os
from typing import Any

import pandas as pd

from qla_core.normalize_utils import format_qladmin_mpolicy

MODAL_FACTOR_FIELDS = ("ANNL", "SEMI", "QTRL", "MTHD", "MTHB")
MODAL_FEE_FACTOR_MAP = (
    ("MSEMI", "MSEMIFEE"),
    ("MQTRL", "MQTRLFEE"),
    ("MMTHD", "MMTHDFEE"),
    ("MMTHB", "MMTHBFEE"),
)
PAC_GL85_PLANS = frozenset({"170858", "17085M"})
PAC_QTR_FACTOR = "25.0000"
PAC_SEMI_FACTOR = "50.0000"
CONVERSION_MEMO_TAG = "[CONVERSION]"
MEMO_SEGMENT_SEPARATOR = "\n---\n"


def default_mapping_path(repo_root: str | None = None) -> str:
    repo_root = repo_root or os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.normpath(
        os.path.join(repo_root, "QLA_Migration", "Mapping", "Modal_Premium_Factors_By_Plan.csv")
    )


def load_modal_factor_mapping(path: str | None = None, repo_root: str | None = None) -> dict[str, dict[str, str]]:
    """Return QL_PLAN -> {ANNL, SEMI, QTRL, MTHD, MTHB}."""
    path = path or default_mapping_path(repo_root)
    if not os.path.isfile(path):
        return {}
    df = pd.read_csv(path, dtype=str).fillna("")
    df.columns = [str(c).strip().upper() for c in df.columns]
    out: dict[str, dict[str, str]] = {}
    for _, row in df.iterrows():
        plan = str(row.get("QL_PLAN", "")).strip()
        if not plan:
            continue
        out[plan] = {f: str(row.get(f, "")).strip() for f in MODAL_FACTOR_FIELDS}
    return out


def apply_modal_factors_to_quikplan(
    df: pd.DataFrame,
    mapping_path: str | None = None,
    repo_root: str | None = None,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Overlay client-approved modal factors onto quikplan rows by PLAN code."""
    mapping = load_modal_factor_mapping(mapping_path, repo_root)
    stats = {"plans_in_mapping": len(mapping), "plans_updated": 0, "plans_missing_mapping": 0}
    if not mapping or df is None or df.empty or "PLAN" not in df.columns:
        return df, stats

    out = df.copy()
    for idx, row in out.iterrows():
        plan = str(row.get("PLAN", "")).strip()
        factors = mapping.get(plan)
        if not factors:
            stats["plans_missing_mapping"] += 1
            continue
        for field in MODAL_FACTOR_FIELDS:
            val = factors.get(field, "")
            if val:
                out.at[idx, field] = val
        stats["plans_updated"] += 1
    return out, stats


def _strip(val: Any) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val).strip()


def _normalize_bill_form(val: str) -> str:
    v = _strip(val).upper()
    if v in ("2", "PAC", "BF_PAC"):
        return "PAC"
    return v


def _normalize_mode(val: str) -> str:
    v = _strip(val)
    if v.endswith(".0") and v[:-2].isdigit():
        v = v[:-2]
    return v.lstrip("0") or "0"


def _parse_positive_amount(val: Any) -> float:
    try:
        return max(0.0, float(_strip(val).replace(",", "") or 0))
    except ValueError:
        return 0.0


def _format_modal_fee(amount: float) -> str:
    return f"{amount:.4f}"


def crude_billing_mode_ann_factor(bill_mode: int | None) -> float:
    """Issue #88 calendar payments-per-year factor (fallback when modal % missing)."""
    return {12: 1.0, 6: 2.0, 3: 4.0, 1: 12.0}.get(
        bill_mode if bill_mode is not None else 12, 1.0
    )


def parse_modal_factor_percent(val: Any) -> float | None:
    """Parse QLAdmin-style modal factor percent (e.g. 9.1999); None if blank/invalid/≤0."""
    s = _strip(val).replace(",", "")
    if not s or s.lower() in ("nan", "none", "null"):
        return None
    try:
        pct = float(s)
    except ValueError:
        return None
    if pct <= 0.0:
        return None
    return pct


def modal_factor_percent_for_billing(
    bill_mode: int | None,
    bill_form: Any,
    plan_factors: dict[str, str] | None,
) -> float | None:
    """Return modal factor percent for current billing mode/form, or None.

    Issue #137 — LifePRO BILLING_MODE on this book: 1=monthly, 3=quarterly,
    6=semiannual, 12=annual. Monthly PAC uses MTHB; Direct uses MTHD.
    """
    if not plan_factors:
        return None
    mode = bill_mode if bill_mode is not None else 12
    if mode == 12:
        pct = parse_modal_factor_percent(plan_factors.get("ANNL", ""))
        return pct if pct is not None else 100.0
    if mode == 6:
        return parse_modal_factor_percent(plan_factors.get("SEMI", ""))
    if mode == 3:
        return parse_modal_factor_percent(plan_factors.get("QTRL", ""))
    if mode == 1:
        key = "MTHB" if _normalize_bill_form(str(bill_form or "")) == "PAC" else "MTHD"
        return parse_modal_factor_percent(plan_factors.get(key, ""))
    return None


def blank_ann_annual_ppu(
    mode_prem: float,
    units: float,
    bill_mode: int | None,
    bill_form: Any,
    plan_factors: dict[str, str] | None,
) -> tuple[float, str]:
    """Annual premium per unit for blank ANN_PREM_PER_UNIT (#88/#137).

    Prefer modalized annual: MODE ÷ (factor%/100) ÷ units.
    Fall back to crude MODE × payments_per_year ÷ units when factor missing.
    Returns (annual_ppu, method) with method in {'modal', 'crude'}.
    """
    if units <= 0.0 or mode_prem < 0.0:
        return 0.0, "crude"
    pct = modal_factor_percent_for_billing(bill_mode, bill_form, plan_factors)
    if pct is not None and pct > 0.0:
        return (mode_prem / (pct / 100.0)) / units, "modal"
    ann_factor = crude_billing_mode_ann_factor(bill_mode)
    return (mode_prem * ann_factor) / units, "crude"


def format_mprem_ppu(annual_ppu: float) -> str:
    """Match app.py MPREM emit formatting."""
    val = f"{annual_ppu:.6f}".rstrip("0").rstrip(".")
    if val in ("", "-0"):
        return "0"
    return val


def _load_phase1_mplan(quikridr_path: str) -> dict[str, str]:
    if not quikridr_path or not os.path.isfile(quikridr_path):
        return {}
    df = pd.read_csv(quikridr_path, dtype=str, encoding="latin1", low_memory=False).fillna("")
    df.columns = [str(c).strip().upper() for c in df.columns]
    out: dict[str, str] = {}
    for _, row in df.iterrows():
        phase = _strip(row.get("MPHASE", ""))
        if phase not in ("1", "01"):
            continue
        mpolicy = format_qladmin_mpolicy(_strip(row.get("MPOLICY", "")))
        if not mpolicy:
            continue
        out[mpolicy] = _strip(row.get("MPLAN", ""))
    return out


def _phase1_mplan_lookup(
    quikridr_df: pd.DataFrame | None = None,
    quikridr_path: str | None = None,
) -> dict[str, str]:
    if quikridr_df is not None:
        phase1: dict[str, str] = {}
        cols = {str(c).strip().upper() for c in quikridr_df.columns}
        for _, row in quikridr_df.iterrows():
            if _strip(row.get("MPHASE", "") if "MPHASE" in cols else "") not in ("1", "01"):
                continue
            mp = format_qladmin_mpolicy(_strip(row.get("MPOLICY", "")))
            if mp:
                phase1[mp] = _strip(row.get("MPLAN", ""))
        return phase1
    return _load_phase1_mplan(quikridr_path or "")


def apply_plan_modal_factors_to_quikmstr(
    mstr_df: pd.DataFrame,
    quikridr_df: pd.DataFrame | None = None,
    quikridr_path: str | None = None,
    quikplan_df: pd.DataFrame | None = None,
    quikplan_path: str | None = None,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Copy quikplan SEMI/QTRL/MTHD/MTHB onto quikmstr MSEMI/MQTRL/MMTHD/MMTHB by phase-1 plan.

    Issue #36 — Names-tab Modal Premiums require policy-level factors. MMTHD and MMTHB are
    copied independently (often differ). Call *before* apply_pac_gl85_modal_overrides so the
    two PAC special modes (Q→MQTRL=25, S→MSEMI=50) win on GL85 PAC policies.
    """
    stats = {
        "policies_checked": 0,
        "policies_updated": 0,
        "policies_missing_plan": 0,
        "policies_missing_factors": 0,
        "used_mapping_fallback": 0,
    }
    if mstr_df is None or mstr_df.empty:
        return mstr_df, stats

    phase1 = _phase1_mplan_lookup(quikridr_df=quikridr_df, quikridr_path=quikridr_path)

    if quikplan_df is not None and not quikplan_df.empty:
        plan_factors: dict[str, dict[str, str]] = {}
        qp = quikplan_df.copy()
        qp.columns = [str(c).strip().upper() for c in qp.columns]
        for _, row in qp.iterrows():
            plan = _strip(row.get("PLAN", ""))
            if plan:
                plan_factors[plan] = {f: _strip(row.get(f, "")) for f in MODAL_FACTOR_FIELDS}
    else:
        plan_factors = load_quikplan_factor_lookup(quikplan_path or "")

    # Fallback when quikplan.csv not yet emitted (e.g. product-setup isolated batch).
    if not plan_factors:
        plan_factors = load_modal_factor_mapping()
        stats["used_mapping_fallback"] = 1 if plan_factors else 0
    else:
        stats["used_mapping_fallback"] = 0

    out = mstr_df.copy()
    for col in ("MSEMI", "MQTRL", "MMTHD", "MMTHB", "MPOLICY"):
        if col not in out.columns:
            out[col] = ""

    field_map = (("SEMI", "MSEMI"), ("QTRL", "MQTRL"), ("MTHD", "MMTHD"), ("MTHB", "MMTHB"))
    for idx, row in out.iterrows():
        stats["policies_checked"] += 1
        mpolicy = format_qladmin_mpolicy(_strip(row.get("MPOLICY", "")))
        mplan = phase1.get(mpolicy, "")
        if not mplan:
            stats["policies_missing_plan"] += 1
            continue
        factors = plan_factors.get(mplan)
        if not factors or not any(factors.get(src) for src, _ in field_map):
            stats["policies_missing_factors"] += 1
            continue
        for src, dest in field_map:
            val = factors.get(src, "")
            if val:
                out.at[idx, dest] = val
        stats["policies_updated"] += 1
    return out, stats


def apply_pac_gl85_modal_overrides(
    mstr_df: pd.DataFrame,
    quikridr_df: pd.DataFrame | None = None,
    quikridr_path: str | None = None,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Set quikmstr.MSEMI/MQTRL for PAC quarterly/semiannual on plans 170858/17085M."""
    stats = {
        "policies_checked": 0,
        "qtr_overrides": 0,
        "semi_overrides": 0,
        "skipped_not_target_plan": 0,
    }
    if mstr_df is None or mstr_df.empty:
        return mstr_df, stats

    phase1 = _phase1_mplan_lookup(quikridr_df=quikridr_df, quikridr_path=quikridr_path)

    out = mstr_df.copy()
    for col in ("MSEMI", "MQTRL", "MMTHD", "MMTHB", "MBILLFRM", "MMODE", "MPOLICY"):
        if col not in out.columns:
            out[col] = ""

    for idx, row in out.iterrows():
        stats["policies_checked"] += 1
        mpolicy = format_qladmin_mpolicy(_strip(row.get("MPOLICY", "")))
        mplan = phase1.get(mpolicy, "")
        if mplan not in PAC_GL85_PLANS:
            stats["skipped_not_target_plan"] += 1
            continue
        if _normalize_bill_form(row.get("MBILLFRM", "")) != "PAC":
            continue
        mode = _normalize_mode(row.get("MMODE", ""))
        if mode == "3":
            out.at[idx, "MQTRL"] = PAC_QTR_FACTOR
            stats["qtr_overrides"] += 1
        elif mode == "6":
            out.at[idx, "MSEMI"] = PAC_SEMI_FACTOR
            stats["semi_overrides"] += 1
    return out, stats


def apply_modal_policy_fees_to_quikridr(
    ridr_df: pd.DataFrame,
    mstr_df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Derive quikridr modal policy fees from MANNLFEE and post-PAC quikmstr factors.

    Issue #58 — Names-tab Modal Premium amounts need MSEMIFEE/MQTRLFEE/MMTHDFEE/MMTHBFEE
    on base-coverage rows when MANNLFEE > 0. Call after apply_pac_gl85_modal_overrides.
    """
    stats = {
        "rows_checked": 0,
        "rows_updated": 0,
        "skipped_not_phase1": 0,
        "skipped_zero_fee": 0,
        "skipped_missing_mstr": 0,
        "skipped_missing_factors": 0,
    }
    if ridr_df is None or ridr_df.empty:
        return ridr_df, stats

    factors_by_policy: dict[str, dict[str, str]] = {}
    if mstr_df is not None and not mstr_df.empty:
        for _, row in mstr_df.iterrows():
            pol = format_qladmin_mpolicy(_strip(row.get("MPOLICY", "")))
            if not pol:
                continue
            factors_by_policy[pol] = {
                src: _strip(row.get(src, "")) for src, _ in MODAL_FEE_FACTOR_MAP
            }

    out = ridr_df.copy()
    for col in ("MSEMIFEE", "MQTRLFEE", "MMTHDFEE", "MMTHBFEE", "MANNLFEE", "MPHASE", "MPOLICY"):
        if col not in out.columns:
            out[col] = ""

    for idx, row in out.iterrows():
        stats["rows_checked"] += 1
        if _strip(row.get("MPHASE", "")) not in ("1", "01"):
            stats["skipped_not_phase1"] += 1
            continue
        annual_fee = _parse_positive_amount(row.get("MANNLFEE"))
        if annual_fee <= 0:
            stats["skipped_zero_fee"] += 1
            continue
        pol = format_qladmin_mpolicy(_strip(row.get("MPOLICY", "")))
        fac = factors_by_policy.get(pol)
        if not fac:
            stats["skipped_missing_mstr"] += 1
            continue
        written = 0
        for src, dest in MODAL_FEE_FACTOR_MAP:
            pct = _parse_positive_amount(fac.get(src, ""))
            if pct <= 0:
                continue
            out.at[idx, dest] = _format_modal_fee(annual_fee * pct / 100.0)
            written += 1
        if written:
            stats["rows_updated"] += 1
        else:
            stats["skipped_missing_factors"] += 1
    return out, stats


def load_quikplan_factor_lookup(quikplan_path: str) -> dict[str, dict[str, str]]:
    if not quikplan_path or not os.path.isfile(quikplan_path):
        return {}
    df = pd.read_csv(quikplan_path, dtype=str, encoding="latin1", low_memory=False).fillna("")
    df.columns = [str(c).strip().upper() for c in df.columns]
    out: dict[str, dict[str, str]] = {}
    for _, row in df.iterrows():
        plan = _strip(row.get("PLAN", ""))
        if not plan:
            continue
        out[plan] = {f: _strip(row.get(f, "")) for f in MODAL_FACTOR_FIELDS}
    return out


def format_conversion_modal_factor_memo(
    conversion_version: str,
    plan_code: str,
    factors: dict[str, str],
    mmodesprem: str = "",
    pac_override_note: str = "",
) -> str:
    lines = [
        CONVERSION_MEMO_TAG,
        f"Conversion Version: {conversion_version}",
        f"Product Plan: {plan_code or 'Unknown'}",
        "Plan-level modal premium factors (quikplan setup):",
        f"  Annual = {factors.get('ANNL', '100.0000')}",
        f"  Semi-Annual = {factors.get('SEMI', '')}",
        f"  Quarterly = {factors.get('QTRL', '')}",
        f"  Monthly Draft = {factors.get('MTHD', '')}",
        f"  Monthly Billing = {factors.get('MTHB', '')}",
    ]
    if mmodesprem:
        lines.append(f"Policy modal premium (MMODEPREM) loaded from LifePRO MODE_PREMIUM: {mmodesprem}")
    if pac_override_note:
        lines.append(pac_override_note)
    lines.append(
        "WARNING: If plan-level or policy-level modal factors are changed in QLAdmin after conversion, "
        "Customer Service must recalculate premiums before relying on Coverage Detail quotes."
    )
    return "\n".join(lines)


def _pac_override_note(mplan: str, mbillfrm: str, mmode: str, msemi: str, mqtrl: str) -> str:
    if mplan not in PAC_GL85_PLANS or _normalize_bill_form(mbillfrm) != "PAC":
        return ""
    mode = _normalize_mode(mmode)
    if mode == "3" and _strip(mqtrl) == PAC_QTR_FACTOR:
        return (
            "Policy override: PAC Quarterly billing uses modal factor 25% on quikmstr.MQTRL "
            "(plan default overridden for 670 GL85 PAC quarterly)."
        )
    if mode == "6" and _strip(msemi) == PAC_SEMI_FACTOR:
        return (
            "Policy override: PAC Semiannual billing uses modal factor 50% on quikmstr.MSEMI "
            "(plan default overridden for 670 GL85 PAC semiannual)."
        )
    return ""


def _merge_conversion_segment(existing: str, new_segment: str) -> str:
    text = _strip(existing)
    if not text:
        return new_segment
    if text.startswith(CONVERSION_MEMO_TAG):
        remainder = text
        if MEMO_SEGMENT_SEPARATOR in text:
            _, _, remainder = text.partition(MEMO_SEGMENT_SEPARATOR)
            remainder = remainder.lstrip("\n")
        else:
            remainder = ""
        if remainder:
            return f"{new_segment}{MEMO_SEGMENT_SEPARATOR}{remainder}"
        return new_segment
    return f"{new_segment}{MEMO_SEGMENT_SEPARATOR}{text}"


def append_issue21j_conversion_memos(
    memo_df: pd.DataFrame,
    conversion_version: str,
    quikmstr_path: str,
    quikridr_path: str,
    quikplan_path: str,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Prepend [CONVERSION] modal-factor memo for every converted policy (fleet-wide)."""
    stats = {
        "conversion_memos_added": 0,
        "conversion_memos_merged": 0,
        "conversion_memos_new_row": 0,
        "policies_without_plan": 0,
        "converted_policies": 0,
    }
    if not os.path.isfile(quikmstr_path):
        return memo_df, stats

    mstr = pd.read_csv(quikmstr_path, dtype=str, encoding="latin1", low_memory=False).fillna("")
    mstr.columns = [str(c).strip().upper() for c in mstr.columns]
    phase1 = _load_phase1_mplan(quikridr_path)
    plan_factors = load_quikplan_factor_lookup(quikplan_path)

    mstr_by_key = {}
    for _, row in mstr.iterrows():
        key = format_qladmin_mpolicy(_strip(row.get("MPOLICY", "")))
        if key:
            mstr_by_key[key] = row

    memo_records = []
    if memo_df is not None and not memo_df.empty:
        memo_df = memo_df.copy()
        memo_df.columns = [str(c).strip().upper() for c in memo_df.columns]
        for _, row in memo_df.iterrows():
            memo_records.append({
                "MEMOKEY": format_qladmin_mpolicy(_strip(row.get("MEMOKEY", ""))),
                "MEMOTEXT": _strip(row.get("MEMOTEXT", "")),
            })

    memo_by_key = {r["MEMOKEY"]: r for r in memo_records if r["MEMOKEY"]}

    for key, mrow in mstr_by_key.items():
        stats["converted_policies"] += 1
        mplan = phase1.get(key, "")
        if not mplan:
            stats["policies_without_plan"] += 1
            mplan = "Unknown"
        factors = plan_factors.get(mplan, {f: "" for f in MODAL_FACTOR_FIELDS})
        if not any(factors.values()) and mplan != "Unknown":
            fallback = load_modal_factor_mapping()
            factors = fallback.get(mplan, factors)
        mmodesprem = _strip(mrow.get("MMODEPREM", ""))
        pac_note = _pac_override_note(
            mplan,
            mrow.get("MBILLFRM", ""),
            mrow.get("MMODE", ""),
            mrow.get("MSEMI", ""),
            mrow.get("MQTRL", ""),
        )
        segment = format_conversion_modal_factor_memo(
            conversion_version, mplan, factors, mmodesprem, pac_note,
        )
        if key in memo_by_key:
            old = memo_by_key[key]["MEMOTEXT"]
            memo_by_key[key]["MEMOTEXT"] = _merge_conversion_segment(old, segment)
            stats["conversion_memos_merged"] += 1
        else:
            memo_by_key[key] = {"MEMOKEY": key, "MEMOTEXT": segment}
            stats["conversion_memos_new_row"] += 1
        stats["conversion_memos_added"] += 1

    out = pd.DataFrame(list(memo_by_key.values()), columns=["MEMOKEY", "MEMOTEXT"])
    out = out.sort_values("MEMOKEY").reset_index(drop=True)
    return out, stats
