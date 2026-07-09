"""
Issue #21 open-item decision helpers (21E UL fund value, 21G premium/basis staging).

Official decisions (2026-07-09):
  21D — ISWL MDEPINT=4.50 / non-ISWL 4.00 (already implemented v57.36)
  21E — Traditional CV: compute via QuikCvs rates; UL: load FV_BALANCE2 -> quikridr.MCV0
  21F — Accept ~2017 premium-history floor (source-side; no engine change)
  21G — Source mapped; stage totals to Reports until QLAdmin target field named
  21I — Type/split correct; MRELATION=1000 is intentional (RNA has no kinship field)

Surgical helpers only — no schema redesign.
"""

from __future__ import annotations

import csv
import os
import re
from typing import Callable, Dict, Optional, Tuple


def _norm_money(raw) -> Optional[str]:
    """Return money string with 2 decimals, or None if blank/zero/unparseable."""
    s = str(raw or "").strip().replace(",", "")
    if s.endswith(".0") and s[:-2].replace("-", "").isdigit():
        s = s[:-2]
    if not s or s.lower() in ("nan", "none", "null", ""):
        return None
    try:
        amt = float(s)
    except ValueError:
        return None
    if abs(amt) < 0.005:
        return None
    return f"{amt:.2f}"


def _strip_cols(df):
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df


def build_ul_fund_balance_cache(
    ppben_path: str,
    normalize_fn: Callable[[str], str],
) -> Dict[str, str]:
    """
    Map normalized LifePRO POLICY_NUMBER -> FV_BALANCE2 for BENEFIT_TYPE=FV rows.

    Used by Issue #21E to populate quikridr.MCV0 on base (phase-1) coverage rows
    for Universal Life / fund-value policies. Traditional policies are left blank
    so QLAdmin computes CV from QuikCvs rate tables.
    """
    import pandas as pd

    if not ppben_path or not os.path.exists(ppben_path):
        return {}

    df = pd.read_csv(ppben_path, encoding="latin1", low_memory=False, dtype=str, on_bad_lines="skip").fillna("")
    df = _strip_cols(df)
    required = {"POLICY_NUMBER", "BENEFIT_TYPE", "FV_BALANCE2"}
    if not required.issubset(set(df.columns)):
        return {}

    bt = df["BENEFIT_TYPE"].astype(str).str.strip().str.upper()
    fv = df[bt == "FV"]
    cache: Dict[str, str] = {}
    for _, row in fv.iterrows():
        pol = normalize_fn(row.get("POLICY_NUMBER", ""))
        bal = _norm_money(row.get("FV_BALANCE2", ""))
        if pol and bal:
            # Prefer last non-zero FV row if multiples exist
            cache[pol] = bal
    return cache


def apply_ul_fund_balance_to_quikridr_row(
    row_data: dict,
    policy_key: str,
    phase: str,
    fund_cache: Dict[str, str],
) -> bool:
    """
    Set MCV0 from UL fund-balance cache on phase-1 rows only.
    Returns True if MCV0 was populated.
    """
    if not fund_cache or not policy_key:
        return False
    phase_n = str(phase or "").strip().lstrip("0") or "0"
    if phase_n != "1":
        return False
    bal = fund_cache.get(policy_key)
    if not bal:
        return False
    row_data["MCV0"] = bal
    # Leave MCV1/MCV2 untouched (blank) — single current fund value only
    return True


def _money_or_zero(raw) -> float:
    s = str(raw or "").strip().replace(",", "")
    if not s or s.lower() in ("nan", "none", "null"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def build_premium_basis_totals(
    ppbentyp_path: Optional[str],
    ppben_path: Optional[str],
    normalize_fn: Callable[[str], str],
    crosswalk: Optional[Dict[str, str]] = None,
) -> list:
    """
    Stage Issue #21G totals per policy (informational until QLAdmin target field named).

    Non-ISWL (traditional):
      premiums_paid = BA PREMIUMS_PAID + PU PU_PREMIUMS_PAID
      tax_basis     = BA TAX_BASIS + PU PU_TAX_BASIS

    ISWL / UL (FV benefit):
      premiums_paid = FV_GUAR_DEPOSITS
      tax_basis     = FV_BASIS2
    """
    import pandas as pd

    cw = crosswalk or {}
    totals: Dict[str, dict] = {}

    def _ensure(pol_raw: str) -> Optional[dict]:
        pol = normalize_fn(pol_raw)
        if not pol:
            return None
        if pol not in totals:
            mpolicy = cw.get(pol, pol)
            totals[pol] = {
                "SOURCE_POLICY": pol,
                "MPOLICY": mpolicy,
                "BOOK": "",
                "PREMIUMS_PAID": 0.0,
                "TAX_BASIS": 0.0,
                "SOURCE_NOTE": "",
            }
        return totals[pol]

    if ppbentyp_path and os.path.exists(ppbentyp_path):
        typ = pd.read_csv(ppbentyp_path, encoding="latin1", low_memory=False, dtype=str, on_bad_lines="skip").fillna("")
        typ = _strip_cols(typ)
        # Prefer TYPE_CODE when present; else BENEFIT_TYPE
        type_col = "TYPE_CODE" if "TYPE_CODE" in typ.columns else (
            "BENEFIT_TYPE" if "BENEFIT_TYPE" in typ.columns else None
        )
        if type_col and "POLICY_NUMBER" in typ.columns:
            for _, row in typ.iterrows():
                tc = str(row.get(type_col, "")).strip().upper()
                rec = _ensure(row.get("POLICY_NUMBER", ""))
                if not rec:
                    continue
                if tc in ("BA", "BF"):
                    prem = _money_or_zero(row.get("PREMIUMS_PAID", ""))
                    basis = _money_or_zero(row.get("TAX_BASIS", ""))
                    if prem or basis:
                        rec["BOOK"] = rec["BOOK"] or "TRADITIONAL"
                        rec["PREMIUMS_PAID"] += prem
                        rec["TAX_BASIS"] += basis
                        rec["SOURCE_NOTE"] = "PPBENTYP BA/BF + PU"
                elif tc == "PU":
                    prem = _money_or_zero(row.get("PU_PREMIUMS_PAID", row.get("PREMIUMS_PAID", "")))
                    basis = _money_or_zero(row.get("PU_TAX_BASIS", row.get("TAX_BASIS", "")))
                    if prem or basis:
                        rec["BOOK"] = rec["BOOK"] or "TRADITIONAL"
                        rec["PREMIUMS_PAID"] += prem
                        rec["TAX_BASIS"] += basis
                        rec["SOURCE_NOTE"] = "PPBENTYP BA/BF + PU"

    if ppben_path and os.path.exists(ppben_path):
        ben = pd.read_csv(ppben_path, encoding="latin1", low_memory=False, dtype=str, on_bad_lines="skip").fillna("")
        ben = _strip_cols(ben)
        if "POLICY_NUMBER" in ben.columns and "BENEFIT_TYPE" in ben.columns:
            bt = ben["BENEFIT_TYPE"].astype(str).str.strip().str.upper()
            fv = ben[bt == "FV"]
            for _, row in fv.iterrows():
                rec = _ensure(row.get("POLICY_NUMBER", ""))
                if not rec:
                    continue
                deposits = _money_or_zero(row.get("FV_GUAR_DEPOSITS", ""))
                basis = _money_or_zero(row.get("FV_BASIS2", ""))
                if deposits or basis:
                    # UL/ISWL fund values take precedence for book label when FV present
                    rec["BOOK"] = "ISWL_UL"
                    rec["PREMIUMS_PAID"] = deposits
                    rec["TAX_BASIS"] = basis
                    rec["SOURCE_NOTE"] = "PPBEN FV_GUAR_DEPOSITS / FV_BASIS2"

    rows = []
    for pol in sorted(totals.keys()):
        rec = totals[pol]
        if rec["PREMIUMS_PAID"] == 0.0 and rec["TAX_BASIS"] == 0.0:
            continue
        rows.append({
            "SOURCE_POLICY": rec["SOURCE_POLICY"],
            "MPOLICY": rec["MPOLICY"],
            "BOOK": rec["BOOK"] or "UNKNOWN",
            "PREMIUMS_PAID": f"{rec['PREMIUMS_PAID']:.2f}",
            "TAX_BASIS": f"{rec['TAX_BASIS']:.2f}",
            "SOURCE_NOTE": rec["SOURCE_NOTE"],
            "QLADMIN_TARGET": "PENDING_CLIENT_FIELD",
            "STATUS": "STAGED_INFORMATIONAL",
        })
    return rows


def write_premium_basis_report(rows: list, reports_dir: str) -> Tuple[str, int]:
    """Write staged 21G report under QLA_Migration/Reports/. Returns (path, row_count)."""
    os.makedirs(reports_dir, exist_ok=True)
    out_path = os.path.join(reports_dir, "issue21g_premium_basis_totals.csv")
    fields = [
        "SOURCE_POLICY",
        "MPOLICY",
        "BOOK",
        "PREMIUMS_PAID",
        "TAX_BASIS",
        "SOURCE_NOTE",
        "QLADMIN_TARGET",
        "STATUS",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})
    return out_path, len(rows)


def resolve_ppben_path(source_dir: str) -> Optional[str]:
    """Locate PPBEN_PolicyBenefit extract in a Source folder."""
    if not source_dir or not os.path.isdir(source_dir):
        return None
    preferred = []
    for name in os.listdir(source_dir):
        low = name.lower()
        if low.startswith("ppben_policybenefit") and low.endswith(".csv"):
            preferred.append(os.path.join(source_dir, name))
        elif low == "ppben.csv":
            preferred.append(os.path.join(source_dir, name))
    if not preferred:
        return None
    preferred.sort(reverse=True)  # dated extracts sort last-first
    return preferred[0]


def resolve_ppbentyp_extract_path(source_dir: str) -> Optional[str]:
    """Locate PPBENTYP_BenefitType extract in a Source folder."""
    if not source_dir or not os.path.isdir(source_dir):
        return None
    preferred = []
    for name in os.listdir(source_dir):
        low = name.lower()
        if low.startswith("ppbentyp_benefittype") and low.endswith(".csv"):
            preferred.append(os.path.join(source_dir, name))
        elif low == "ppbentyp.csv":
            preferred.append(os.path.join(source_dir, name))
    if not preferred:
        return None
    preferred.sort(reverse=True)
    return preferred[0]
