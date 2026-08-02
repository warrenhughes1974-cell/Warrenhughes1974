"""Issue #135 — controlled CSO claim expansion / Option-3 consume (post-emit).

Business lock (2026-08-02):
  - 142 DERIVED_HIGH: emit death headers + payees from PACTG economic legs + PRELSA.
  - 308 NO_PACTG_HISTORY: emit CSO-controlled header-only rows (no quikclmp).
  - 9 HOLD_INCOMPLETE_SOURCE: audit only — do not emit.
  - Preserve Option-3 overlay corrections (43) and integrate consistently.
  - MINTAMT always 0.00; do not fabricate payees/check numbers/accounting history.
  - #134 MEMOTEXT: marker also in CAUSE; issue134 preserves marker when replacing notes.

Does not rewrite Phase 10a/10b architecture — append/update Output tables only.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from qla_core.issue78_quikclmp_recovery import (
    QUIKCLMP_SCHEMA,
    _resolve_tier_and_payees,
)
from qla_core.issue135_match_cso_zero_payee_backfill import (
    apply_match_cso_zero_payee_backfill,
    write_zero_payee_backfill_audit,
)
from qla_core.issue135_surrender_zero_payee_backfill import (
    apply_surrender_zero_payee_backfill,
    write_surrender_zero_payee_audit,
)
from qla_core.normalize_utils import normalize

ROOT = Path(__file__).resolve().parents[1]
TOOLS_135 = ROOT / "Issue_Log_Items" / "Issue_135" / "tools"
EVIDENCE_135 = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"

if str(TOOLS_135) not in sys.path:
    sys.path.insert(0, str(TOOLS_135))

from issue135_cso_pactg_recon import (  # noqa: E402
    TOLERANCE,
    _money,
    _strip,
    load_cso,
    resolve_pactg,
    stream_pactg_for_policies,
)
from issue135_option3_economic_reconstruction import (  # noqa: E402
    best_subset,
    build_header_overlay_row,
    economic_payout_events,
    loop_reissue_dates,
)

CSO_NO_PACTG_MARKER = "CSO_CONTROLLED_NO_PACTG_HISTORY"
QUIKCLMS_SCHEMA = [
    "MPOLICY", "MPHASE", "CLAIMNUM", "CLAIMSTAT", "DTOFDEATH", "RPTDATE", "PDDATE",
    "MPAID", "MFACE", "DIVIDENDS", "LOAN", "NETDB", "PREMIUM", "SUSPENSE", "ADJUST",
    "CAUSE", "MEMOTEXT", "ORIGSTTUS", "ACCPTDATE", "MCONTEST", "MINTST", "MINTDAYS",
    "MINTRATE", "MINTAMT", "MSURRCHG", "MSEQ", "MHOLDINT", "MFEDTAX", "MSTTAX",
    "MCLMPNDLTR", "MFACPMT", "MPHPAIDTO",
]

DEFAULT_ANALYSIS = EVIDENCE_135 / "issue135_459_analysis_per_policy.csv"
DEFAULT_OPTION3_CLMS = EVIDENCE_135 / "issue135_option3_quikclms_overlay.csv"
DEFAULT_OPTION3_CLMP = EVIDENCE_135 / "issue135_option3_quikclmp_overlay.csv"
DEFAULT_OPTION3_SUMMARY = EVIDENCE_135 / "issue135_option3_candidate_summary.csv"
DEFAULT_CSO = ROOT / "docs" / "Claims" / "CSO Life claims summary - 2017 - 2025.xlsx"
DEFAULT_PRELSA = ROOT / "QLA_Migration" / "Source" / "RelationshipNameAddress_Extract_20260630.csv"


def _qla_date(value: Any) -> str:
    """Normalize CSO / Excel dates to YYYYMMDD (Output convention)."""
    text = _strip(value)
    if not text:
        return ""
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 8:
        # Prefer leading YYYYMMDD when ISO-like
        if text[0:4].isdigit() and ("-" in text or "/" in text or " " in text):
            return digits[:8]
        if len(digits) == 8:
            return digits
    try:
        dt = pd.to_datetime(text, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y%m%d")
    except Exception:
        pass
    return digits[:8] if len(digits) >= 8 else ""


def _policy_digits(mpolicy: str) -> str:
    mp = normalize(mpolicy)
    if mp.endswith("C") and len(mp) >= 2:
        return mp[:-1]
    return "".join(ch for ch in mp if ch.isdigit())


def _claimnum_for_policy(mpolicy: str) -> str:
    return f"RC-{_policy_digits(mpolicy)}"


def _blank_clms_row(mpolicy: str) -> dict[str, str]:
    row = {h: "" for h in QUIKCLMS_SCHEMA}
    row.update(
        {
            "MPOLICY": mpolicy,
            "MPHASE": "1",
            "CLAIMNUM": _claimnum_for_policy(mpolicy),
            "CLAIMSTAT": "2",
            "MPAID": "0.00",
            "MFACE": "0.00",
            "DIVIDENDS": "0.00",
            "LOAN": "0.00",
            "NETDB": "0.00",
            "PREMIUM": "0.00",
            "SUSPENSE": "0.00",
            "ADJUST": "0.00",
            "ORIGSTTUS": "3",
            "MCONTEST": "F",
            "MINTDAYS": "0",
            "MINTRATE": "0",
            "MINTAMT": "0.00",
            "MSURRCHG": "F",
            "MSEQ": "0",
            "MHOLDINT": "0.00",
            "MFEDTAX": "0.00",
            "MSTTAX": "0.00",
            "MCLMPNDLTR": "0",
            "MFACPMT": "F",
        }
    )
    return row


def _blank_clmp_row(mpolicy: str, mphase: str = "1") -> dict[str, str]:
    row = {h: "" for h in QUIKCLMP_SCHEMA}
    row.update(
        {
            "MPOLICY": mpolicy,
            "MPHASE": mphase or "1",
            "MCHECKNO": "0",
            "MAMOUNT": "0.00",
            "MHDPMT": "C",
            "MSEQ": "1",
            "MHOLDINT": "0.00",
            "MFEDTAX": "0.00",
            "MSTTAX": "0.00",
            "MGROSS": "0.00",
        }
    )
    return row


def _load_prelsa_index(prelsa_path: Path, policy_digits: set[str]) -> dict[str, pd.DataFrame]:
    if not prelsa_path.is_file() or not policy_digits:
        return {}
    rel = pd.read_csv(
        prelsa_path,
        encoding="latin1",
        dtype=str,
        engine="python",
        on_bad_lines="skip",
    )
    rel.columns = [_strip(c) for c in rel.columns]
    if "POLICY_NUMBER" not in rel.columns:
        return {}
    rel["POL"] = rel["POLICY_NUMBER"].astype(str).str.strip()
    rel = rel[rel["POL"].isin(policy_digits)].copy()
    if rel.empty:
        return {}
    rel["RC"] = rel["RELATE_CODE"].astype(str).str.strip() if "RELATE_CODE" in rel.columns else ""
    rel["NAME_ID"] = rel["NAME_ID"].astype(str).str.strip() if "NAME_ID" in rel.columns else ""
    return {pol: grp for pol, grp in rel.groupby("POL", sort=False)}


def _safe_payees_from_prelsa(rel_grp: pd.DataFrame | None) -> tuple[list[dict[str, str]], str]:
    """Return named payees only — never fabricate identity stubs."""
    tier, payees, src = _resolve_tier_and_payees(rel_grp)
    named = [p for p in payees if _strip(p.get("MPAYNAME", ""))]
    if not named:
        return [], "NO_SAFE_PAYEE_NAME"
    return named, src


def _is_death_header_row(row: pd.Series | dict) -> bool:
    memo = _strip(row.get("MEMOTEXT", "")).upper()
    claimstat = _strip(row.get("CLAIMSTAT", ""))
    claimnum = _strip(row.get("CLAIMNUM", ""))
    cause = _strip(row.get("CAUSE", ""))
    if "PARTIAL_SURRENDER" in memo or claimnum.upper().startswith("PS-"):
        return False
    if "DISBURSEMENT_CLAIM" in memo and "DEATH_CLAIM" not in memo:
        return False
    if "DEATH_CLAIM" in memo or CSO_NO_PACTG_MARKER in cause or CSO_NO_PACTG_MARKER in memo:
        return True
    if claimstat in ("1", "2") and claimnum.upper().startswith("RC-"):
        return True
    return False


def _existing_keys(clms: pd.DataFrame) -> set[tuple[str, str, str]]:
    keys = set()
    for _, r in clms.iterrows():
        keys.add(
            (
                _strip(r.get("MPOLICY", "")),
                _strip(r.get("CLAIMNUM", "")),
                _strip(r.get("MSEQ", "")),
            )
        )
    return keys


def _header_memo_death(mpolicy: str, paid_date: str, marker: str = "") -> str:
    dig = _policy_digits(mpolicy)
    date = paid_date or "00000000"
    base = (
        f"RC-{dig}-1-DEATH_CLAIM-C0-{date}|"
        f"ESG-{dig}-RC-{dig}-1-DEATH_CLAIM-C0-{date}-SOLO|"
        f"DEATH_CLAIM|SETTLED"
    )
    if marker:
        return f"{base}|{marker}"
    return base


def _build_cso_header(
    mpolicy: str,
    amount: float,
    cso_row: dict,
    marker: str = "",
    lineage_note: str = "",
) -> dict[str, str]:
    incurred = _qla_date(cso_row.get("cso_date_incurred", ""))
    notice = _qla_date(cso_row.get("cso_notice_date", ""))
    last_pd = _qla_date(cso_row.get("cso_last_pd_date", ""))
    paid = last_pd or notice or incurred
    row = _blank_clms_row(mpolicy)
    amt = f"{amount:.2f}"
    row["MPAID"] = amt
    row["NETDB"] = amt
    row["DTOFDEATH"] = incurred
    row["RPTDATE"] = notice or paid
    row["PDDATE"] = paid
    row["ACCPTDATE"] = paid
    row["MINTAMT"] = "0.00"
    row["CLAIMSTAT"] = "2"
    row["ORIGSTTUS"] = "3"
    # CAUSE is C(3) in Output (e.g. SRR) — too short for the lineage marker.
    # Put CSO_CONTROLLED_NO_PACTG_HISTORY in MEMOTEXT; #134 preserves it on PNOTE replace.
    # Full mapping also written to Issue_135 evidence audit CSV.
    row["CAUSE"] = ""
    row["MEMOTEXT"] = _header_memo_death(mpolicy, paid, marker=marker)
    if lineage_note:
        row["MEMOTEXT"] = f"{row['MEMOTEXT']}|{lineage_note}"
    return row


def _select_eco_legs(pactg_rows: list[dict], cso_total: float) -> list[dict]:
    loop_dates = loop_reissue_dates(pactg_rows)
    eco = [e for e in economic_payout_events(pactg_rows) if e["effective_date"] not in loop_dates]
    if not eco:
        return []
    items = [
        ((i, e["effective_date"], round(float(e["amount"]), 2)), round(float(e["amount"]), 2))
        for i, e in enumerate(eco)
    ]
    subset = best_subset(items, cso_total)
    if subset is None:
        return []
    chosen_idx = {s[0][0] for s in subset}
    return [eco[i] for i in sorted(chosen_idx)]


def _payee_rows_for_legs(
    mpolicy: str,
    legs: list[dict],
    named_payees: list[dict[str, str]],
    payee_src: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not legs or not named_payees:
        return rows
    pair_ok = payee_src.startswith("PE") and len(named_payees) == len(legs)
    for i, leg in enumerate(legs):
        payee = named_payees[i] if pair_ok and i < len(named_payees) else named_payees[0]
        amt = f"{_money(leg.get('amount', 0)):.2f}"
        date = _strip(leg.get("effective_date", ""))
        row = _blank_clmp_row(mpolicy, "1")
        row.update(payee)
        row["MAMOUNT"] = amt
        row["MGROSS"] = amt
        row["MCHKDATE"] = date
        row["MPMTDATE"] = date
        row["MCHECKNO"] = "0"  # do not invent check numbers
        # Must match claim-header MSEQ for QLAdmin relation index
        # MPOLICY+STR(MPHASE,2,0)+STR(MSEQ,3,0). Duplicate keys OK for multi-payee.
        row["MSEQ"] = "0"
        row["MHDPMT"] = "C"
        rows.append(row)
    return rows


def _apply_option3_corrections(
    clms: pd.DataFrame,
    clmp: pd.DataFrame,
    option3_clms: pd.DataFrame,
    option3_clmp: pd.DataFrame,
    prelsa_index: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict], list[dict]]:
    """Update existing Output rows for Option-3 CORRECTED policies."""
    audit: list[dict] = []
    hold_payee: list[dict] = []
    if option3_clms is None or option3_clms.empty:
        return clms, clmp, audit, hold_payee

    clms = clms.copy().fillna("")
    clmp = clmp.copy().fillna("")
    drop_clmp_pols: set[str] = set()
    new_clmp_rows: list[dict] = []

    for _, ov in option3_clms.iterrows():
        pol = _strip(ov.get("MPOLICY", ""))
        if not pol:
            continue
        mask = clms["MPOLICY"].map(_strip) == pol
        death_mask = mask & clms.apply(_is_death_header_row, axis=1)
        if not death_mask.any():
            # fallback any RC- header
            death_mask = mask & clms["CLAIMNUM"].map(lambda x: _strip(x).upper().startswith("RC-"))
        if not death_mask.any():
            audit.append({"mpolicy": pol, "action": "OPTION3_SKIP_NO_HEADER", "detail": "no death header"})
            continue
        idx = clms.index[death_mask][0]
        hdr = clms.loc[idx].to_dict()
        corr = _money(ov.get("MPAID", ov.get("_cso_total_paid", 0)))
        payees_ov = option3_clmp[option3_clmp["MPOLICY"].map(_strip) == pol].copy() if len(option3_clmp) else pd.DataFrame()
        # Strip helper columns
        for c in list(payees_ov.columns):
            if str(c).startswith("_"):
                payees_ov = payees_ov.drop(columns=[c])
        needs = False
        if len(option3_clmp) and "_needs_payee_identity" in option3_clmp.columns:
            needs = bool(
                (
                    option3_clmp[option3_clmp["MPOLICY"].map(_strip) == pol]["_needs_payee_identity"]
                    .map(_strip)
                    == "Y"
                ).any()
            )
        safe_payees = pd.DataFrame()
        if len(payees_ov):
            names = payees_ov["MPAYNAME"].map(_strip) if "MPAYNAME" in payees_ov.columns else pd.Series(dtype=str)
            fake = names.str.contains("NEEDS_PAYEE_IDENTITY", na=False) | (names == "")
            if (~fake).any():
                safe_payees = payees_ov.loc[~fake].copy()
            elif needs or fake.all():
                named, src = _safe_payees_from_prelsa(prelsa_index.get(_policy_digits(pol)))
                if named:
                    # one economic amount from overlay / corrected MPAID
                    amt = corr
                    date = _strip(ov.get("PDDATE", "")) or _strip(payees_ov.iloc[0].get("MPMTDATE", ""))
                    prow = _blank_clmp_row(pol, _strip(ov.get("MPHASE", "1")) or "1")
                    prow.update(named[0])
                    prow["MAMOUNT"] = f"{amt:.2f}"
                    prow["MGROSS"] = f"{amt:.2f}"
                    prow["MCHKDATE"] = date
                    prow["MPMTDATE"] = date
                    prow["MSEQ"] = "0"
                    safe_payees = pd.DataFrame([prow])
                    audit.append({"mpolicy": pol, "action": "OPTION3_PAYEE_FROM_PRELSA", "detail": src})
                else:
                    hold_payee.append(
                        {
                            "mpolicy": pol,
                            "category": "OPTION3_HOLD_NO_SAFE_PAYEE",
                            "cso_total_paid": f"{corr:.2f}",
                            "note": "Header MPAID corrected; payee not fabricated",
                        }
                    )
        updated = build_header_overlay_row(hdr, corr, safe_payees if len(safe_payees) else pd.DataFrame())
        for col in QUIKCLMS_SCHEMA:
            if col in updated:
                clms.at[idx, col] = updated[col]
        clms.at[idx, "MINTAMT"] = "0.00"
        audit.append(
            {
                "mpolicy": pol,
                "action": "OPTION3_HEADER_UPDATED",
                "detail": f"mpaid={corr:.2f};payees={len(safe_payees)}",
            }
        )
        if len(safe_payees):
            drop_clmp_pols.add(pol)
            for i, (_, pr) in enumerate(safe_payees.iterrows(), start=1):
                prow = _blank_clmp_row(pol, _strip(pr.get("MPHASE", "1")) or "1")
                for k in QUIKCLMP_SCHEMA:
                    if k in pr.index:
                        prow[k] = pr.get(k, prow.get(k, ""))
                prow["MPOLICY"] = pol
                prow["MSEQ"] = "0"
                prow["MAMOUNT"] = f"{_money(prow.get('MAMOUNT', 0)):.2f}"
                prow["MGROSS"] = prow["MAMOUNT"] if not _strip(prow.get("MGROSS", "")) else f"{_money(prow.get('MGROSS')):.2f}"
                if not _strip(prow.get("MCHECKNO", "")):
                    prow["MCHECKNO"] = "0"
                if "***" in _strip(prow.get("MPAYNAME", "")):
                    continue
                new_clmp_rows.append(prow)

    if drop_clmp_pols:
        keep = ~clmp["MPOLICY"].map(_strip).isin(drop_clmp_pols)
        clmp = clmp.loc[keep].copy()
    if new_clmp_rows:
        clmp = pd.concat(
            [clmp.reindex(columns=QUIKCLMP_SCHEMA, fill_value=""), pd.DataFrame(new_clmp_rows)],
            ignore_index=True,
        )
    return clms, clmp, audit, hold_payee


def apply_issue135_cso_claims_expansion(
    clms_df: pd.DataFrame,
    clmp_df: pd.DataFrame,
    *,
    analysis_path: Path | str = DEFAULT_ANALYSIS,
    option3_clms_path: Path | str = DEFAULT_OPTION3_CLMS,
    option3_clmp_path: Path | str = DEFAULT_OPTION3_CLMP,
    cso_path: Path | str = DEFAULT_CSO,
    prelsa_path: Path | str = DEFAULT_PRELSA,
    pactg_path: Path | str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """
    Apply Option-3 corrections + 459 expansion to in-memory claim tables.

    Returns (clms, clmp, stats_with_audit_frames).
    """
    stats: dict[str, Any] = {
        "applied": False,
        "option3_headers_updated": 0,
        "derived_headers_emitted": 0,
        "derived_payees_emitted": 0,
        "derived_payee_holds": 0,
        "header_only_308_emitted": 0,
        "holds_9": 0,
        "skipped_duplicates": 0,
        "reason": "",
    }
    audit_rows: list[dict] = []
    hold_rows: list[dict] = []

    clms = clms_df.copy().fillna("") if clms_df is not None else pd.DataFrame(columns=QUIKCLMS_SCHEMA)
    clmp = clmp_df.copy().fillna("") if clmp_df is not None else pd.DataFrame(columns=QUIKCLMP_SCHEMA)
    for col in QUIKCLMS_SCHEMA:
        if col not in clms.columns:
            clms[col] = ""
    for col in QUIKCLMP_SCHEMA:
        if col not in clmp.columns:
            clmp[col] = ""

    analysis = pd.read_csv(analysis_path, dtype=str, keep_default_na=False)
    option3_clms = (
        pd.read_csv(option3_clms_path, dtype=str, keep_default_na=False)
        if Path(option3_clms_path).is_file()
        else pd.DataFrame()
    )
    option3_clmp = (
        pd.read_csv(option3_clmp_path, dtype=str, keep_default_na=False)
        if Path(option3_clmp_path).is_file()
        else pd.DataFrame()
    )
    cso = load_cso(Path(cso_path))
    cso_by = { _strip(r["mpolicy"]): r for _, r in cso.iterrows() }

    digits_needed: set[str] = set()
    for _, r in analysis.iterrows():
        if _strip(r.get("category", "")) in ("DERIVED_HIGH", "HOLD_INCOMPLETE_SOURCE"):
            digits_needed.add(_strip(r.get("policy_digits", "")) or _policy_digits(r.get("mpolicy", "")))
    for _, r in option3_clms.iterrows():
        digits_needed.add(_policy_digits(r.get("MPOLICY", "")))

    prelsa_index = _load_prelsa_index(Path(prelsa_path), digits_needed)
    pactg = resolve_pactg(str(pactg_path) if pactg_path else None)
    derived = analysis[analysis["category"].map(_strip) == "DERIVED_HIGH"].copy()
    no_pactg = analysis[analysis["category"].map(_strip) == "NO_PACTG_HISTORY"].copy()
    holds = analysis[analysis["category"].map(_strip) == "HOLD_INCOMPLETE_SOURCE"].copy()

    # --- Option 3 consume ---
    clms, clmp, o3_audit, o3_hold = _apply_option3_corrections(
        clms, clmp, option3_clms, option3_clmp, prelsa_index
    )
    audit_rows.extend(o3_audit)
    hold_rows.extend(o3_hold)
    stats["option3_headers_updated"] = sum(1 for a in o3_audit if a["action"] == "OPTION3_HEADER_UPDATED")

    existing_pols = set(clms["MPOLICY"].map(_strip))
    existing_keys = _existing_keys(clms)
    new_clms: list[dict] = []
    new_clmp: list[dict] = []

    # --- 9 HOLDS ---
    for _, r in holds.iterrows():
        pol = _strip(r.get("mpolicy", ""))
        hold_rows.append(
            {
                "mpolicy": pol,
                "category": "HOLD_INCOMPLETE_SOURCE",
                "cso_total_paid": _strip(r.get("cso_total_paid", "")),
                "note": _strip(r.get("analysis_note", "")) or "Incomplete/ambiguous PACTG chain — not emitted",
            }
        )
    stats["holds_9"] = int(len(holds))

    # --- 142 DERIVED_HIGH ---
    derived_digits = {
        _strip(r.get("policy_digits", "")) or _policy_digits(r.get("mpolicy", ""))
        for _, r in derived.iterrows()
    }
    buckets = stream_pactg_for_policies(pactg, derived_digits) if derived_digits else {}

    for _, r in derived.iterrows():
        pol = _strip(r.get("mpolicy", ""))
        dig = _strip(r.get("policy_digits", "")) or _policy_digits(pol)
        cso_amt = _money(r.get("cso_total_paid", r.get("derived_amount", 0)))
        if pol in existing_pols:
            # Already represented (should not happen for 459) — do not duplicate
            stats["skipped_duplicates"] += 1
            audit_rows.append({"mpolicy": pol, "action": "SKIP_ALREADY_IN_OUTPUT", "detail": "derived"})
            continue
        claimnum = _claimnum_for_policy(pol)
        key = (pol, claimnum, "0")
        if key in existing_keys:
            stats["skipped_duplicates"] += 1
            continue
        cso_row = cso_by.get(pol, {
            "cso_date_incurred": "",
            "cso_notice_date": "",
            "cso_last_pd_date": _strip(r.get("cso_last_pd_date", "")),
            "cso_total_paid": cso_amt,
        })
        legs = _select_eco_legs(buckets.get(dig, []), cso_amt)
        if not legs or abs(sum(_money(x.get("amount", 0)) for x in legs) - cso_amt) > TOLERANCE:
            hold_rows.append(
                {
                    "mpolicy": pol,
                    "category": "DERIVED_HOLD_ECO_RESELECT_FAIL",
                    "cso_total_paid": f"{cso_amt:.2f}",
                    "note": "Could not reselect eco legs safely at emit time",
                }
            )
            continue
        named, src = _safe_payees_from_prelsa(prelsa_index.get(dig))
        header = _build_cso_header(
            pol,
            cso_amt,
            cso_row,
            marker="",
            lineage_note="ISSUE135_DERIVED_HIGH_PACTG",
        )
        # Prefer eco leg dates for PDDATE when available
        leg_dates = sorted({_strip(x.get("effective_date", "")) for x in legs if _strip(x.get("effective_date", ""))})
        if leg_dates:
            header["PDDATE"] = leg_dates[-1]
            if not header["RPTDATE"]:
                header["RPTDATE"] = leg_dates[-1]
        new_clms.append(header)
        existing_pols.add(pol)
        existing_keys.add(key)
        stats["derived_headers_emitted"] += 1
        if named:
            pay_rows = _payee_rows_for_legs(pol, legs, named, src)
            new_clmp.extend(pay_rows)
            stats["derived_payees_emitted"] += len(pay_rows)
            audit_rows.append(
                {
                    "mpolicy": pol,
                    "action": "DERIVED_EMIT_HEADER_PAYEES",
                    "detail": f"mpaid={cso_amt:.2f};legs={len(legs)};payees={len(pay_rows)};src={src}",
                }
            )
        else:
            stats["derived_payee_holds"] += 1
            hold_rows.append(
                {
                    "mpolicy": pol,
                    "category": "DERIVED_HOLD_NO_SAFE_PAYEE",
                    "cso_total_paid": f"{cso_amt:.2f}",
                    "note": "Header emitted from accounting; payee held — no safe PRELSA name",
                }
            )
            audit_rows.append(
                {
                    "mpolicy": pol,
                    "action": "DERIVED_EMIT_HEADER_ONLY_PAYEE_HOLD",
                    "detail": f"mpaid={cso_amt:.2f};legs={len(legs)}",
                }
            )

    # --- 308 NO_PACTG_HISTORY header-only ---
    for _, r in no_pactg.iterrows():
        pol = _strip(r.get("mpolicy", ""))
        cso_amt = _money(r.get("cso_total_paid", 0))
        if pol in existing_pols:
            stats["skipped_duplicates"] += 1
            audit_rows.append({"mpolicy": pol, "action": "SKIP_ALREADY_IN_OUTPUT", "detail": "no_pactg"})
            continue
        claimnum = _claimnum_for_policy(pol)
        key = (pol, claimnum, "0")
        if key in existing_keys:
            stats["skipped_duplicates"] += 1
            continue
        cso_row = cso_by.get(pol, {
            "cso_date_incurred": "",
            "cso_notice_date": "",
            "cso_last_pd_date": _strip(r.get("cso_last_pd_date", "")),
            "cso_total_paid": cso_amt,
        })
        header = _build_cso_header(
            pol,
            cso_amt,
            cso_row,
            marker=CSO_NO_PACTG_MARKER,
            lineage_note="HEADER_ONLY_NO_PACTG",
        )
        new_clms.append(header)
        existing_pols.add(pol)
        existing_keys.add(key)
        stats["header_only_308_emitted"] += 1
        audit_rows.append(
            {
                "mpolicy": pol,
                "action": "HEADER_ONLY_NO_PACTG_EMIT",
                "detail": f"mpaid={cso_amt:.2f};marker={CSO_NO_PACTG_MARKER}",
            }
        )

    if new_clms:
        clms = pd.concat(
            [clms.reindex(columns=QUIKCLMS_SCHEMA, fill_value=""), pd.DataFrame(new_clms)],
            ignore_index=True,
        )
    if new_clmp:
        clmp = pd.concat(
            [clmp.reindex(columns=QUIKCLMP_SCHEMA, fill_value=""), pd.DataFrame(new_clmp)],
            ignore_index=True,
        )

    # MATCH_CSO_EXISTING_HEADER_ZERO_PAYEE cohort: evidence-gated SAFE_BACKFILL only.
    # Discovers open 2032->1058 + PRELSA PE/B1; does not fabricate HOLD cases.
    recon_path = Path(analysis_path).resolve().parent / "issue135_cso_output_recon.csv"
    if not recon_path.is_file():
        recon_path = DEFAULT_ANALYSIS.parent / "issue135_cso_output_recon.csv"
    clms, clmp, zp_stats = apply_match_cso_zero_payee_backfill(
        clms,
        clmp,
        prelsa_path=prelsa_path,
        pactg_path=pactg,
        auto_discover=True,
        recon_path=recon_path if recon_path.is_file() else None,
    )
    stats["zero_payee_backfill_policies"] = int(zp_stats.get("policies_backfilled", 0) or 0)
    stats["zero_payee_backfill_rows"] = int(zp_stats.get("rows_added", 0) or 0)
    stats["zero_payee_backfill_stats"] = zp_stats
    for a in zp_stats.get("audit_rows") or []:
        if _strip(a.get("mseq", "")) == "SUMMARY":
            audit_rows.append(
                {
                    "mpolicy": _strip(a.get("mpolicy", "")),
                    "action": "MATCH_CSO_ZERO_PAYEE_BACKFILL",
                    "detail": _strip(a.get("detail", "")) or _strip(a.get("reason", "")),
                }
            )

    # Surrender CLAIMSTAT=99 zero-payee backfill (PE sum match, else OWNR/INSD/PAYR).
    out_dir = Path(__file__).resolve().parents[1] / "QLA_Migration" / "Output"
    clid_path = out_dir / "quikclid.csv"
    clnt_path = out_dir / "quikclnt.csv"
    clms, clmp, surr_stats = apply_surrender_zero_payee_backfill(
        clms,
        clmp,
        pactg_path=pactg,
        prelsa_path=prelsa_path,
        clid_path=clid_path,
        clnt_path=clnt_path,
    )
    stats["surrender_zero_payee_backfill_policies"] = int(
        (surr_stats.get("rule1_policies", 0) or 0) + (surr_stats.get("rule2_policies", 0) or 0)
    )
    stats["surrender_zero_payee_backfill_rows"] = int(surr_stats.get("rows_added", 0) or 0)
    stats["surrender_zero_payee_backfill_stats"] = surr_stats

    # Force MINTAMT=0 on all rows touched / all headers
    if "MINTAMT" in clms.columns and len(clms):
        clms["MINTAMT"] = "0.00"

    stats["applied"] = True
    stats["clms_rows_after"] = int(len(clms))
    stats["clmp_rows_after"] = int(len(clmp))
    stats["audit_df"] = pd.DataFrame(audit_rows)
    stats["hold_df"] = pd.DataFrame(hold_rows)
    stats["marker_field"] = "MEMOTEXT(+evidence_audit)"
    stats["marker_value"] = CSO_NO_PACTG_MARKER
    stats["marker_note"] = (
        "CAUSE is C(3) and cannot hold the marker; MEMOTEXT carries "
        "CSO_CONTROLLED_NO_PACTG_HISTORY and issue134 preserves it on PNOTE-B replace"
    )
    stats["claimstat_convention"] = "2_DEATH_PAID_IN_FULL_post_issue79"
    return clms, clmp, stats


def write_issue135_expansion_audits(
    stats: dict[str, Any],
    evidence_dir: Path | str,
    reports_dir: Path | str | None = None,
) -> dict[str, str]:
    """Write audit / hold artifacts under Issue_135/evidence (and optional Reports)."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    audit_df = stats.get("audit_df")
    hold_df = stats.get("hold_df")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    zp = stats.get("zero_payee_backfill_stats")
    if isinstance(zp, dict) and zp.get("audit_rows"):
        paths.update(write_zero_payee_backfill_audit(zp, evidence_dir))
    surr = stats.get("surrender_zero_payee_backfill_stats")
    if isinstance(surr, dict) and (surr.get("audit_rows") or surr.get("applied")):
        paths.update(write_surrender_zero_payee_audit(surr, evidence_dir))
    if isinstance(audit_df, pd.DataFrame):
        p = evidence_dir / "issue135_production_apply_audit.csv"
        audit_df.to_csv(p, index=False, encoding="utf-8")
        paths["audit"] = str(p)
    if isinstance(hold_df, pd.DataFrame):
        p = evidence_dir / "issue135_production_hold_audit.csv"
        hold_df.to_csv(p, index=False, encoding="utf-8")
        paths["hold"] = str(p)
    summary = {
        k: v
        for k, v in stats.items()
        if k not in ("audit_df", "hold_df") and not isinstance(v, (pd.DataFrame,))
    }
    summary["generated_at"] = ts
    sp = evidence_dir / "issue135_production_apply_summary.json"
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    paths["summary"] = str(sp)
    if reports_dir:
        import shutil

        reports_dir = Path(reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)
        for key, src in list(paths.items()):
            dest = reports_dir / Path(src).name
            shutil.copy2(src, dest)
            paths[f"reports_{key}"] = str(dest)
    return paths


def preserve_cso_no_pactg_marker(old_memo: str, new_memo: str) -> str:
    """Keep CSO_CONTROLLED_NO_PACTG_HISTORY when #134 replaces MEMOTEXT with PNOTE-B."""
    old = _strip(old_memo)
    new = _strip(new_memo)
    if CSO_NO_PACTG_MARKER in old and CSO_NO_PACTG_MARKER not in new:
        if new:
            return f"{new}\n---\n{CSO_NO_PACTG_MARKER}"
        return CSO_NO_PACTG_MARKER
    return new_memo
