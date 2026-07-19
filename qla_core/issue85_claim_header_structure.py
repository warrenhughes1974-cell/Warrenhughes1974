"""Issue #85 — unique quikclms claim identity (merge same CLAIMNUM / re-phase distinct)."""

from __future__ import annotations

import os
from typing import Any

import pandas as pd

PHASE_SEQ = ["0", "2", "3", "4", "5", "6", "7", "8", "9", "1", "10", "11", "12"]


def _strip(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text or text.lower() in ("nan", "none"):
        return ""
    return text


def _num(value: Any) -> float:
    try:
        return float(pd.to_numeric(value, errors="coerce") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _money(value: float) -> str:
    return f"{value:.2f}"


def _date_key(value: Any) -> str:
    text = _strip(value)
    return text if text else "00000000"


def _earliest(values: list[str]) -> str:
    vals = [v for v in values if v]
    return min(vals) if vals else ""


def _latest(values: list[str]) -> str:
    vals = [v for v in values if v]
    return max(vals) if vals else ""


def apply_issue85_header_structure(
    clms_df: pd.DataFrame,
    clmp_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Return (clms_after, clmp_after, merge_audit, rephase_payee_audit).

    D1 hybrid: merge same CLAIMNUM on same pol+phase; re-phase distinct CLAIMNUMs.
    D2/D3/D4 per Issue_85_Scope_Decisions. Does not invent/delete payee rows.
    """
    if clms_df is None or clms_df.empty:
        empty = pd.DataFrame()
        return clms_df.copy() if clms_df is not None else empty, (
            clmp_df.copy() if clmp_df is not None else empty
        ), empty, empty

    work = clms_df.copy().fillna("")
    for col in ("MPOLICY", "MPHASE", "CLAIMNUM"):
        if col not in work.columns:
            raise ValueError(f"quikclms missing required column {col}")

    work["_pol"] = work["MPOLICY"].map(_strip)
    work["_ph"] = work["MPHASE"].map(_strip)
    work["_cn"] = work["CLAIMNUM"].map(_strip)
    work["_mpaid_n"] = work.get("MPAID", pd.Series([""] * len(work))).map(_num)
    work["_mface_n"] = work.get("MFACE", pd.Series([""] * len(work))).map(_num)

    merge_audit_rows: list[dict[str, Any]] = []
    keep_frames: list[pd.Series] = []

    for (pol, ph, cn), grp in work.groupby(["_pol", "_ph", "_cn"], sort=False):
        if len(grp) == 1:
            keep_frames.append(grp.iloc[0])
            continue

        survivor = grp.iloc[0].copy()
        total_paid = float(grp["_mpaid_n"].sum())
        survivor["MPAID"] = _money(total_paid)
        survivor["_mpaid_n"] = total_paid

        if "DTOFDEATH" in grp.columns:
            survivor["DTOFDEATH"] = _earliest([_strip(v) for v in grp["DTOFDEATH"].tolist()])
        if "RPTDATE" in grp.columns:
            survivor["RPTDATE"] = _earliest([_strip(v) for v in grp["RPTDATE"].tolist()])
        if "PDDATE" in grp.columns:
            survivor["PDDATE"] = _latest([_strip(v) for v in grp["PDDATE"].tolist()])

        face_rows = grp.loc[grp["_mface_n"] > 0]
        if len(face_rows):
            survivor["MFACE"] = face_rows.iloc[0]["MFACE"]
            survivor["_mface_n"] = _num(survivor["MFACE"])

        keep_frames.append(survivor)
        for _, dropped in grp.iloc[1:].iterrows():
            merge_audit_rows.append(
                {
                    "action": "MERGE_DROP",
                    "mpolicy": pol,
                    "mphase_before": ph,
                    "claimnum": cn,
                    "dropped_mpaid": _money(dropped["_mpaid_n"]),
                    "survivor_mpaid_after": _money(total_paid),
                    "survivor_mface": _strip(survivor.get("MFACE", "")),
                    "claimstat": _strip(survivor.get("CLAIMSTAT", "")),
                }
            )

    merged = pd.DataFrame(keep_frames).reset_index(drop=True)

    # Re-phase distinct claims within each policy to unique MPHASE
    rephase_audit_rows: list[dict[str, Any]] = []
    out_rows: list[pd.Series] = []

    for pol, grp in merged.groupby("_pol", sort=False):
        claims: list[tuple[tuple[str, str, str], pd.Series]] = []
        for _, row in grp.iterrows():
            sort_key = (
                _date_key(row.get("PDDATE", "")),
                _date_key(row.get("RPTDATE", "")),
                _strip(row.get("_cn", "")),
            )
            claims.append((sort_key, row))
        claims.sort(key=lambda x: x[0])

        phase_claim_counts = grp.groupby("_ph")["_cn"].nunique()
        already_unique = bool((phase_claim_counts <= 1).all()) and not bool(grp["_ph"].duplicated().any())

        used: set[str] = set()
        for i, (_, row) in enumerate(claims):
            row = row.copy()
            ph_before = _strip(row["_ph"])
            if already_unique:
                ph_after = ph_before
            elif i == 0 and ph_before and ph_before not in used:
                ph_after = ph_before
            else:
                ph_after = next(p for p in PHASE_SEQ if p not in used)
            used.add(ph_after)
            if ph_after != ph_before:
                rephase_audit_rows.append(
                    {
                        "action": "REPHASE",
                        "mpolicy": pol,
                        "claimnum": _strip(row["_cn"]),
                        "mphase_before": ph_before,
                        "mphase_after": ph_after,
                        "mpaid": _money(row["_mpaid_n"]),
                        "claimstat": _strip(row.get("CLAIMSTAT", "")),
                    }
                )
            row["MPHASE"] = ph_after
            row["_ph"] = ph_after
            out_rows.append(row)

    clms_after = pd.DataFrame(out_rows).reset_index(drop=True)
    # Drop helper columns
    helper_cols = [c for c in clms_after.columns if c.startswith("_")]
    clms_after = clms_after.drop(columns=helper_cols, errors="ignore")

    # Preserve original column order when possible
    orig_cols = [c for c in clms_df.columns if c in clms_after.columns]
    extra = [c for c in clms_after.columns if c not in orig_cols]
    clms_after = clms_after[orig_cols + extra]

    clmp_after = clmp_df.copy().fillna("") if clmp_df is not None else pd.DataFrame()
    payee_audit_rows: list[dict[str, Any]] = []
    if not clmp_after.empty and "MPOLICY" in clmp_after.columns:
        clmp_after = _reattach_payees(clms_after, clmp_after, payee_audit_rows)

    merge_audit = pd.DataFrame(merge_audit_rows)
    rephase_payee_audit = pd.DataFrame(rephase_audit_rows + payee_audit_rows)
    return clms_after, clmp_after, merge_audit, rephase_payee_audit


def _reattach_payees(
    clms_after: pd.DataFrame,
    clmp_df: pd.DataFrame,
    audit_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    """D4: payees follow claim by date/amount; unmatched attach to best survivor + flag."""
    claims = clms_after.copy()
    claims["_pol"] = claims["MPOLICY"].map(_strip)
    claims["_ph"] = claims["MPHASE"].map(_strip)
    claims["_cn"] = claims["CLAIMNUM"].map(_strip)
    claims["_mpaid_n"] = claims.get("MPAID", pd.Series([""] * len(claims))).map(_num)
    claims["_pddate"] = claims.get("PDDATE", pd.Series([""] * len(claims))).map(_strip)

    by_pol: dict[str, pd.DataFrame] = {
        pol: g.reset_index(drop=True) for pol, g in claims.groupby("_pol", sort=False)
    }

    out = clmp_df.copy()
    new_phases: list[str] = []
    for _, pay in out.iterrows():
        pol = _strip(pay.get("MPOLICY", ""))
        old_ph = _strip(pay.get("MPHASE", ""))
        amt = _num(pay.get("MAMOUNT", 0))
        pmt = _strip(pay.get("MPMTDATE", "")) or _strip(pay.get("MCHKDATE", ""))
        cands = by_pol.get(pol)
        if cands is None or cands.empty:
            new_phases.append(old_ph)
            audit_rows.append(
                {
                    "action": "PAYEE_NO_HEADER",
                    "mpolicy": pol,
                    "mphase_before": old_ph,
                    "mphase_after": old_ph,
                    "mamount": _money(amt),
                    "match_rule": "NONE",
                    "exception": "Y",
                }
            )
            continue

        if len(cands) == 1:
            ph_after = _strip(cands.iloc[0]["_ph"])
            new_phases.append(ph_after)
            if ph_after != old_ph:
                audit_rows.append(
                    {
                        "action": "PAYEE_REPHASE",
                        "mpolicy": pol,
                        "mphase_before": old_ph,
                        "mphase_after": ph_after,
                        "mamount": _money(amt),
                        "match_rule": "SOLE_CLAIM",
                        "exception": "N",
                        "claimnum": _strip(cands.iloc[0]["_cn"]),
                    }
                )
            continue

        matched = None
        rule = ""
        # Date match
        if pmt:
            date_hits = cands[cands["_pddate"] == pmt]
            if len(date_hits) == 1:
                matched = date_hits.iloc[0]
                rule = "PDDATE"
            elif len(date_hits) > 1 and amt > 0:
                amt_hits = date_hits[date_hits["_mpaid_n"].round(2) == round(amt, 2)]
                if len(amt_hits) == 1:
                    matched = amt_hits.iloc[0]
                    rule = "PDDATE+AMOUNT"
                else:
                    # amount is a share of claim total
                    for _, hit in date_hits.iterrows():
                        if hit["_mpaid_n"] > 0 and abs(hit["_mpaid_n"] % amt) < 0.02:
                            matched = hit
                            rule = "PDDATE+SHARE"
                            break

        # Amount equals full claim MPAID
        if matched is None and amt > 0:
            amt_hits = cands[cands["_mpaid_n"].round(2) == round(amt, 2)]
            if len(amt_hits) == 1:
                matched = amt_hits.iloc[0]
                rule = "AMOUNT"

        # Prefer claim still on old phase if unique
        if matched is None:
            same_ph = cands[cands["_ph"] == old_ph]
            if len(same_ph) == 1:
                matched = same_ph.iloc[0]
                rule = "OLD_PHASE"

        exception = "N"
        if matched is None:
            # Fallback: latest PDDATE among candidates (D4-A fallback)
            tmp = cands.copy()
            tmp["_dk"] = tmp["_pddate"].map(_date_key)
            matched = tmp.sort_values("_dk", ascending=False).iloc[0]
            rule = "FALLBACK_LATEST"
            exception = "Y"

        ph_after = _strip(matched["_ph"])
        new_phases.append(ph_after)
        if ph_after != old_ph or exception == "Y":
            audit_rows.append(
                {
                    "action": "PAYEE_REPHASE" if exception == "N" else "PAYEE_EXCEPTION",
                    "mpolicy": pol,
                    "mphase_before": old_ph,
                    "mphase_after": ph_after,
                    "mamount": _money(amt),
                    "match_rule": rule,
                    "exception": exception,
                    "claimnum": _strip(matched["_cn"]),
                }
            )

    out["MPHASE"] = new_phases
    return out


def write_structure_audits(
    merge_audit: pd.DataFrame,
    rephase_payee_audit: pd.DataFrame,
    reports_dir: str,
) -> dict[str, str]:
    os.makedirs(reports_dir, exist_ok=True)
    paths = {}
    merge_path = os.path.join(reports_dir, "issue85_merge_audit.csv")
    rephase_path = os.path.join(reports_dir, "issue85_rephase_payee_audit.csv")
    merge_audit.to_csv(merge_path, index=False, encoding="utf-8")
    rephase_payee_audit.to_csv(rephase_path, index=False, encoding="utf-8")
    paths["merge_audit"] = merge_path
    paths["rephase_payee_audit"] = rephase_path
    return paths
