"""
Issue #21F — Conversion premium adjustment for truncated quikprmh history.

Business rules:
  - One additive Conversion Adjustment row per eligible policy (all plans)
  - Traditional: LifePRO total = BA/BF PREMIUMS_PAID + PU + SU + SL (PPBENTYP)
  - ISWL/UL (BF book): LifePRO total = PPBEN FV_GUAR_DEPOSITS (PPBENTYP premiums are .00)
  - DATEPAID = 2017-12-31; classify via MSOURCE/USER_ID/MBATCH markers
  - Positive adjustments only; negatives → exception report
  - Idempotent: strip prior CONV_ADJ rows and rebuild each run (same output on re-run)

v58.79: ISWL included — FV_GUAR_DEPOSITS authority (was phase-1 exclude).
"""

from __future__ import annotations

import csv
import os
import re
from typing import Callable, Dict, List, Optional, Tuple

import pandas as pd

# Conversion Adjustment marker literals (documented in Issue_21F_Implementation_Notes)
CONV_ADJ_DATEPAID = "20171231"
CONV_ADJ_MSOURCE = "CONV_ADJ"
CONV_ADJ_USER_ID = "QLA21F"
CONV_ADJ_MBATCH = "21F-ADJ"
MONEY_TOLERANCE = 0.005

PRMH_SCHEMA = [
    "MPOLICY", "DATEPAID", "RENEWAL", "PREMIUM", "MLIFE", "MTERM", "MSUPP",
    "MANN", "MHEALTH", "XS", "MPAIDTO", "POSTDATE", "MPOSTDATE", "MSOURCE",
    "MBATCH", "USER_ID", "MBILLFRM", "MMODEPD",
]

VALIDATION_FIELDS = [
    "SOURCE_POLICY",
    "MPOLICY",
    "ISWL",
    "BASE_PREMIUMS_PAID",
    "PUA_PREMIUMS_PAID",
    "SU_PREMIUMS_PAID",
    "SL_PREMIUMS_PAID",
    "LIFEPRO_TOTAL",
    "HIST_TOTAL",
    "ADJUSTMENT",
    "FINAL_TOTAL",
    "REMAINING_VARIANCE",
    "HAS_HIST",
    "STATUS",
]

EXCEPTION_FIELDS = [
    "SOURCE_POLICY",
    "MPOLICY",
    "ISWL",
    "LIFEPRO_TOTAL",
    "HIST_TOTAL",
    "ADJUSTMENT",
    "STATUS",
    "NOTE",
]


def _norm_policy_key(raw) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(raw or "").strip())


def _money_float(raw) -> float:
    s = str(raw or "").strip().replace(",", "")
    if not s or s.lower() in ("nan", "none", "null"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _money_str(amount: float) -> str:
    return f"{amount:.2f}"


def is_conversion_adjustment_row(row: dict) -> bool:
    """True when row is an Issue 21F conversion adjustment (idempotency check)."""
    msource = str(row.get("MSOURCE", "")).strip().upper()
    user_id = str(row.get("USER_ID", "")).strip().upper()
    if msource == CONV_ADJ_MSOURCE:
        return True
    if user_id == CONV_ADJ_USER_ID:
        return True
    return False


def _aggregate_policy_components(g: pd.DataFrame) -> Tuple[float, float, float, float]:
    """
    LifePRO four-component totals per Eric / workbook rules.

    - Base: PREMIUMS_PAID on BA/BF rows only (exclude OR and other TYPE_CODEs)
    - PUA: PU_PREMIUMS_PAID summed on PU rows
    - Supplemental: SU_PREMIUMS_PAID summed on SU rows (negatives included)
    - Substandard: SL_PREMIUMS_PAID summed on SL rows
    """
    base = float(g.loc[g["TC"].isin(["BA", "BF"]), "PREMIUMS_PAID"].sum())
    pu_rows = g[g["TC"] == "PU"]
    pua = float(pu_rows["PU_PREMIUMS_PAID"].sum()) if len(pu_rows) else 0.0
    su_rows = g[g["TC"] == "SU"]
    su = float(su_rows["SU_PREMIUMS_PAID"].sum()) if len(su_rows) else 0.0
    sl_rows = g[g["TC"] == "SL"]
    sl = float(sl_rows["SL_PREMIUMS_PAID"].sum()) if len(sl_rows) else 0.0
    return base, pua, su, sl


def resolve_issue21f_output_mpolicy(
    source_pol: str,
    format_mpolicy_fn: Callable[[str], str],
    *,
    hist_keys: Optional[set] = None,
    mstr_keys: Optional[set] = None,
) -> str:
    """
    Issue #21F-local MPOLICY join — match existing quikprmh/quikmstr grain.

    Uses the same path as non-adj quikprmh history: format(source POLICY_NUMBER).
    Does **not** re-format crosswalk New_Value (that already ends in C and orphans as *CC).
    Prefers an exact key already present on history/mstr when available.
    """
    pol = str(source_pol or "").strip()
    if not pol:
        return ""
    candidate = str(format_mpolicy_fn(pol) or "").strip()
    if not candidate:
        return ""

    allowed: set = set()
    if hist_keys:
        allowed |= {str(k).strip() for k in hist_keys if str(k).strip()}
    if mstr_keys:
        allowed |= {str(k).strip() for k in mstr_keys if str(k).strip()}

    if allowed:
        if candidate in allowed:
            return candidate
        # Rare: history retained a different pad/grain for the same core — join by digits+C
        core = pol.upper().rstrip("C")
        for key in allowed:
            k = str(key).strip()
            if k.upper().rstrip("C").lstrip("0") == core.lstrip("0"):
                return k
        return candidate
    return candidate


def _load_iswl_fv_deposits(ppben_path: Optional[str], normalize_fn: Callable[[str], str]) -> Dict[str, float]:
    """PPBEN BENEFIT_TYPE=FV → FV_GUAR_DEPOSITS keyed by normalized source POLICY_NUMBER."""
    if not ppben_path or not os.path.isfile(ppben_path):
        return {}
    ben = pd.read_csv(
        ppben_path,
        encoding="latin1",
        low_memory=False,
        dtype=str,
        on_bad_lines="skip",
    ).fillna("")
    ben.columns = [str(c).strip().upper() for c in ben.columns]
    if "POLICY_NUMBER" not in ben.columns or "FV_GUAR_DEPOSITS" not in ben.columns:
        return {}
    type_col = "BENEFIT_TYPE" if "BENEFIT_TYPE" in ben.columns else None
    if type_col is None:
        return {}
    out: Dict[str, float] = {}
    fv = ben[ben[type_col].astype(str).str.strip().str.upper() == "FV"]
    for _, row in fv.iterrows():
        pol = normalize_fn(str(row.get("POLICY_NUMBER", "")))
        if not pol:
            continue
        amt = _money_float(row.get("FV_GUAR_DEPOSITS", ""))
        # Prefer largest deposit if multiple FV rows (rare)
        if amt > out.get(pol, 0.0):
            out[pol] = amt
    return out


def build_lifepro_premium_totals(
    ppbentyp_path: Optional[str],
    normalize_fn: Callable[[str], str],
    format_mpolicy_fn: Callable[[str], str],
    crosswalk: Optional[Dict[str, str]] = None,
    *,
    hist_keys: Optional[set] = None,
    mstr_keys: Optional[set] = None,
    ppben_path: Optional[str] = None,
) -> Dict[str, dict]:
    """
    Per-policy LifePRO totals for #21F gap calculation.

    Traditional: PPBENTYP four-component sum.
    ISWL (TYPE_CODE=BF): overlay BASE/LIFEPRO_TOTAL from PPBEN FV_GUAR_DEPOSITS.

    Returns dict keyed by MPOLICY (Output/loadable grain) with component breakdown + ISWL flag.

    ``crosswalk`` is accepted for call-site compatibility but is **not** used to build
    CONV_ADJ MPOLICY keys (Wave 0 / Cut Completeness — join to history/mstr grain).
    """
    if not ppbentyp_path or not os.path.isfile(ppbentyp_path):
        return {}

    _ = crosswalk  # retained for API compatibility; not used for key emit
    fv_deposits = _load_iswl_fv_deposits(ppben_path, normalize_fn)
    df = pd.read_csv(
        ppbentyp_path,
        encoding="latin1",
        low_memory=False,
        dtype=str,
        on_bad_lines="skip",
    ).fillna("")
    df.columns = [str(c).strip().upper() for c in df.columns]
    required = {
        "POLICY_NUMBER",
        "TYPE_CODE",
        "PREMIUMS_PAID",
        "PU_PREMIUMS_PAID",
        "SU_PREMIUMS_PAID",
        "SL_PREMIUMS_PAID",
    }
    if not required.issubset(set(df.columns)):
        return {}

    df["POL"] = df["POLICY_NUMBER"].map(lambda x: normalize_fn(str(x)))
    df["TC"] = df["TYPE_CODE"].astype(str).str.strip().str.upper()
    for col in ("PREMIUMS_PAID", "PU_PREMIUMS_PAID", "SU_PREMIUMS_PAID", "SL_PREMIUMS_PAID"):
        df[col] = df[col].map(_money_float)

    iswl_pols = set(df.loc[df["TC"] == "BF", "POL"])

    totals: Dict[str, dict] = {}
    for pol, grp in df.groupby("POL"):
        pol = str(pol).strip()
        if not pol:
            continue
        # Same grain as quikprmh history emit: format(source), never format(cw New_Value)
        mpolicy = resolve_issue21f_output_mpolicy(
            pol,
            format_mpolicy_fn,
            hist_keys=hist_keys,
            mstr_keys=mstr_keys,
        )
        if not mpolicy:
            continue
        base, pua, su, sl = _aggregate_policy_components(grp)
        is_iswl = pol in iswl_pols
        # ISWL/UL: PPBENTYP PREMIUMS_PAID on BF is .00; lifetime paid is FV deposits
        if is_iswl and pol in fv_deposits:
            base = float(fv_deposits[pol])
            pua = su = sl = 0.0
        lp_total = base + pua + su + sl
        totals[mpolicy] = {
            "SOURCE_POLICY": pol,
            "MPOLICY": mpolicy,
            "ISWL": is_iswl,
            "BASE_PREMIUMS_PAID": base,
            "PUA_PREMIUMS_PAID": pua,
            "SU_PREMIUMS_PAID": su,
            "SL_PREMIUMS_PAID": sl,
            "LIFEPRO_TOTAL": lp_total,
        }
    return totals


def _format_mpolicy_key(mpolicy: str, format_mpolicy_fn: Optional[Callable[[str], str]] = None) -> str:
    """Canonical MPOLICY key for joins (strip; do not re-append C on already-final keys)."""
    raw = str(mpolicy or "").strip()
    if not raw:
        return ""
    if format_mpolicy_fn:
        # Idempotent for Issue #2 width-11 trailing-C keys already on history rows
        return str(format_mpolicy_fn(raw) or "").strip() or raw
    return raw


def _hist_totals_from_prmh(
    qdf: pd.DataFrame,
    format_mpolicy_fn: Optional[Callable[[str], str]] = None,
) -> Dict[str, float]:
    """Sum PREMIUM per MPOLICY excluding existing conversion adjustment rows."""
    if qdf.empty:
        return {}
    work = qdf.copy()
    work["_MPOL"] = work["MPOLICY"].map(lambda m: _format_mpolicy_key(m, format_mpolicy_fn))
    work["PREMIUM_F"] = work["PREMIUM"].map(_money_float)
    mask_adj = work.apply(
        lambda r: is_conversion_adjustment_row(r.to_dict()), axis=1
    )
    hist = work.loc[~mask_adj].groupby("_MPOL")["PREMIUM_F"].sum()
    return {k: float(v) for k, v in hist.items() if k}


def _existing_adj_amounts(
    qdf: pd.DataFrame,
    format_mpolicy_fn: Optional[Callable[[str], str]] = None,
) -> Dict[str, float]:
    """Map MPOLICY -> existing CONV_ADJ PREMIUM (for report / replace detection)."""
    if qdf.empty:
        return {}
    work = qdf.copy()
    work["_MPOL"] = work["MPOLICY"].map(lambda m: _format_mpolicy_key(m, format_mpolicy_fn))
    mask = work.apply(lambda r: is_conversion_adjustment_row(r.to_dict()), axis=1)
    adj = work.loc[mask]
    out: Dict[str, float] = {}
    for _, row in adj.iterrows():
        key = str(row["_MPOL"]).strip()
        if key:
            out[key] = _money_float(row.get("PREMIUM", ""))
    return out


def _strip_conversion_adjustment_rows(qdf: pd.DataFrame) -> pd.DataFrame:
    """Remove Issue 21F synthetic rows; preserve payment history."""
    if qdf.empty:
        return qdf
    mask = qdf.apply(lambda r: is_conversion_adjustment_row(r.to_dict()), axis=1)
    return qdf.loc[~mask].copy()


def _classify_status(
    rec: dict,
    hist_total: float,
    adj: float,
) -> str:
    if not rec.get("MPOLICY"):
        return "NO_CROSSWALK"
    if rec["LIFEPRO_TOTAL"] <= 0 and hist_total <= 0:
        return "NO_PREMIUM_DATA"
    if abs(adj) < MONEY_TOLERANCE:
        return "NO_GAP"
    if adj < 0:
        return "NEGATIVE_EXCEPTION"
    if hist_total <= 0:
        return "OPENING_BALANCE"
    return "LOADED"


def _emit_issue2_mpolicy(mpolicy: str) -> str:
    """Width-11 Issue #2 emit form (leading spaces). Join maps may be strip-keyed."""
    s = str(mpolicy or "").strip()
    if not s:
        return ""
    if len(s) < 11:
        return s.rjust(11)
    return s


def build_conversion_adjustment_row(
    mpolicy: str,
    adjustment: float,
    format_mpolicy_fn: Optional[Callable[[str], str]] = None,
) -> dict:
    """Synthetic quikprmh row for conversion opening-balance premium."""
    amt = _money_str(adjustment)
    # Emit path passes format_mpolicy_fn=None with an already-resolved Output key.
    # Pad short *C keys to Issue #2 width 11 (48 CONV_ADJ shorts were unpadded).
    if format_mpolicy_fn is None:
        mp = _emit_issue2_mpolicy(mpolicy)
    else:
        mp = _emit_issue2_mpolicy(_format_mpolicy_key(mpolicy, format_mpolicy_fn))
    return {
        "MPOLICY": mp,
        "DATEPAID": CONV_ADJ_DATEPAID,
        "RENEWAL": "0",
        "PREMIUM": amt,
        "MLIFE": amt,
        "MTERM": "0.00",
        "MSUPP": "0.00",
        "MANN": "0.00",
        "MHEALTH": "0.00",
        "XS": "0.00",
        "MPAIDTO": "",
        "POSTDATE": "",
        "MPOSTDATE": CONV_ADJ_DATEPAID,
        "MSOURCE": CONV_ADJ_MSOURCE,
        "MBATCH": CONV_ADJ_MBATCH,
        "USER_ID": CONV_ADJ_USER_ID,
        "MBILLFRM": "",
        "MMODEPD": "0",
    }


def apply_issue21f_conversion_adjustments(
    qdf: pd.DataFrame,
    ppbentyp_path: Optional[str],
    normalize_fn: Callable[[str], str],
    format_mpolicy_fn: Callable[[str], str],
    crosswalk: Optional[Dict[str, str]] = None,
    reports_dir: Optional[str] = None,
    mstr_mpolicy_keys: Optional[set] = None,
    reject_orphan_vs_mstr: bool = True,
    ppben_path: Optional[str] = None,
) -> Tuple[pd.DataFrame, dict]:
    """
    Append Conversion Adjustment rows to quikprmh DataFrame; write validation reports.

    Returns (modified_qdf, stats_dict). Existing payment rows are never modified.

    When ``reject_orphan_vs_mstr`` is True and ``mstr_mpolicy_keys`` is provided, any
    CONV_ADJ MPOLICY not in quikmstr raises ValueError (hard fail — no orphan *CC keys).

    ``ppben_path`` supplies FV_GUAR_DEPOSITS for ISWL/UL (required for positive ISWL adj).
    """
    stats = {
        "loaded": 0,
        "opening_balance": 0,
        "iswl_loaded": 0,
        "iswl_excluded": 0,  # retained for log compatibility; always 0 after v58.79
        "negative_exceptions": 0,
        "no_gap": 0,
        "no_premium_data": 0,
        "no_crosswalk": 0,
        "stripped_adj": 0,
        "orphan_adj_rejected": 0,
        "join_mstr": 0,
        "ppben_path": ppben_path or "",
    }

    if qdf is None or not isinstance(qdf, pd.DataFrame):
        return qdf, stats

    schema = list(qdf.columns) if len(qdf.columns) else PRMH_SCHEMA
    work = qdf.copy()
    for col in schema:
        if col not in work.columns:
            work[col] = ""

    # Strip prior CONV_ADJ rows so each run recalculates with current formula (idempotent output)
    stripped_mask = work.apply(lambda r: is_conversion_adjustment_row(r.to_dict()), axis=1)
    stats["stripped_adj"] = int(stripped_mask.sum())
    work = work.loc[~stripped_mask].reset_index(drop=True)

    hist_map = _hist_totals_from_prmh(work, format_mpolicy_fn)
    hist_keys = set(hist_map.keys())
    mstr_keys = {str(k).strip() for k in (mstr_mpolicy_keys or set()) if str(k).strip()}

    lp_totals = build_lifepro_premium_totals(
        ppbentyp_path,
        normalize_fn,
        format_mpolicy_fn,
        crosswalk,
        hist_keys=hist_keys,
        mstr_keys=mstr_keys or None,
        ppben_path=ppben_path,
    )
    if not lp_totals:
        return work[schema], stats

    validation_rows: List[dict] = []
    exception_rows: List[dict] = []
    new_rows: List[dict] = []
    orphan_keys: List[str] = []

    for mpolicy in sorted(lp_totals.keys()):
        rec = lp_totals[mpolicy]
        # Emit the already-resolved Output key; do not re-run format on a finished key
        mp_key = str(rec["MPOLICY"] or "").strip()
        hist_total = float(hist_map.get(mp_key, 0.0))
        adj = round(rec["LIFEPRO_TOTAL"] - hist_total, 2)
        status = _classify_status(rec, hist_total, adj)

        if status in ("LOADED", "OPENING_BALANCE"):
            final_total = rec["LIFEPRO_TOTAL"]
            variance = 0.0
            adj_str = _money_str(adj)
        elif status == "NEGATIVE_EXCEPTION":
            final_total = hist_total
            variance = round(rec["LIFEPRO_TOTAL"] - hist_total, 2)
            adj_str = _money_str(adj)
        else:
            final_total = hist_total
            variance = round(rec["LIFEPRO_TOTAL"] - hist_total, 2)
            adj_str = ""

        vrow = {
            "SOURCE_POLICY": rec["SOURCE_POLICY"],
            "MPOLICY": mp_key,
            "ISWL": "Y" if rec["ISWL"] else "N",
            "BASE_PREMIUMS_PAID": _money_str(rec["BASE_PREMIUMS_PAID"]),
            "PUA_PREMIUMS_PAID": _money_str(rec["PUA_PREMIUMS_PAID"]),
            "SU_PREMIUMS_PAID": _money_str(rec["SU_PREMIUMS_PAID"]),
            "SL_PREMIUMS_PAID": _money_str(rec["SL_PREMIUMS_PAID"]),
            "LIFEPRO_TOTAL": _money_str(rec["LIFEPRO_TOTAL"]),
            "HIST_TOTAL": _money_str(hist_total),
            "ADJUSTMENT": adj_str,
            "FINAL_TOTAL": _money_str(final_total),
            "REMAINING_VARIANCE": _money_str(variance),
            "HAS_HIST": "Y" if hist_total > 0 else "N",
            "STATUS": status,
        }
        validation_rows.append(vrow)

        if status == "NEGATIVE_EXCEPTION":
            stats["negative_exceptions"] += 1
            exception_rows.append({
                "SOURCE_POLICY": rec["SOURCE_POLICY"],
                "MPOLICY": mp_key,
                "ISWL": "Y" if rec["ISWL"] else "N",
                "LIFEPRO_TOTAL": _money_str(rec["LIFEPRO_TOTAL"]),
                "HIST_TOTAL": _money_str(hist_total),
                "ADJUSTMENT": _money_str(adj),
                "STATUS": status,
                "NOTE": "QLAdmin history exceeds LifePRO total — review before load",
            })
        elif status in ("LOADED", "OPENING_BALANCE"):
            if mstr_keys and mp_key not in mstr_keys:
                stats["orphan_adj_rejected"] += 1
                orphan_keys.append(mp_key)
                exception_rows.append({
                    "SOURCE_POLICY": rec["SOURCE_POLICY"],
                    "MPOLICY": mp_key,
                    "ISWL": "Y" if rec["ISWL"] else "N",
                    "LIFEPRO_TOTAL": _money_str(rec["LIFEPRO_TOTAL"]),
                    "HIST_TOTAL": _money_str(hist_total),
                    "ADJUSTMENT": _money_str(adj),
                    "STATUS": "ORPHAN_NO_MSTR",
                    "NOTE": "CONV_ADJ MPOLICY not in quikmstr — not emitted",
                })
                continue
            stats["loaded"] += 1
            if rec.get("ISWL"):
                stats["iswl_loaded"] += 1
            if status == "OPENING_BALANCE":
                stats["opening_balance"] += 1
            if mstr_keys and mp_key in mstr_keys:
                stats["join_mstr"] += 1
            # Pass key as-is (already Output grain); avoid format re-append
            new_rows.append(build_conversion_adjustment_row(mp_key, adj, None))
        elif status == "NO_GAP":
            stats["no_gap"] += 1
        elif status == "NO_PREMIUM_DATA":
            stats["no_premium_data"] += 1
        elif status == "NO_CROSSWALK":
            stats["no_crosswalk"] += 1

    if orphan_keys and reject_orphan_vs_mstr and mstr_keys:
        if reports_dir:
            write_issue21f_reports(validation_rows, exception_rows, reports_dir)
        raise ValueError(
            f"Issue #21F: {len(orphan_keys)} CONV_ADJ MPOLICY key(s) not in quikmstr "
            f"(sample={orphan_keys[:5]})"
        )

    if new_rows:
        add_df = pd.DataFrame(new_rows, columns=schema)
        work = pd.concat([work[schema], add_df], ignore_index=True)

    if reports_dir:
        write_issue21f_reports(validation_rows, exception_rows, reports_dir)

    stats["rows_before"] = len(qdf)
    stats["rows_after"] = len(work)
    stats["conv_adj_rows"] = len(new_rows)
    return work[schema], stats


def write_issue21f_reports(
    validation_rows: List[dict],
    exception_rows: List[dict],
    reports_dir: str,
) -> Tuple[str, str]:
    """Write validation + exception CSVs under QLA_Migration/Reports/."""
    os.makedirs(reports_dir, exist_ok=True)
    val_path = os.path.join(reports_dir, "issue21f_premium_adjustment_validation.csv")
    exc_path = os.path.join(reports_dir, "issue21f_premium_adjustment_exceptions.csv")

    with open(val_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=VALIDATION_FIELDS)
        w.writeheader()
        for row in validation_rows:
            w.writerow({k: row.get(k, "") for k in VALIDATION_FIELDS})

    with open(exc_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=EXCEPTION_FIELDS)
        w.writeheader()
        for row in exception_rows:
            w.writerow({k: row.get(k, "") for k in EXCEPTION_FIELDS})

    return val_path, exc_path
