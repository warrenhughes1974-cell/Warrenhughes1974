"""Issue #135 — surrender (CLAIMSTAT=99) zero-payee quikclmp backfill.

Cohort: CLAIMSTAT=99 headers with MPAID>0 and zero quikclmp rows.

Rule 1: PACTG PE payout legs (credit/debit 90/92/94) sum to MPAID (±$0.01)
        → emit those PE amounts with PE/OWNR/INSD identity; MSEQ=header MSEQ.
Rule 2: else emit one payee = OWNR → INSD → PAYR for full MPAID (from quikclid/clnt).
Hold: no usable identity → no fabricate.
"""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path
from typing import Any

import pandas as pd

from qla_core.issue78_quikclmp_recovery import QUIKCLMP_SCHEMA, _blank_payment_row
from qla_core.normalize_utils import normalize

TOLERANCE = 0.01
PAYOUT_CODES = frozenset({"90", "92", "94", "0090", "0092", "0094"})
REVERSAL_CODES = frozenset({"Y", "R", "V"})
ROLE_FALLBACK = ("OWNR", "INSD", "PAYR")


def _strip(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text or text.lower() in ("nan", "none"):
        return ""
    return text


def _money(value: Any) -> float:
    try:
        return float(str(value).replace(",", "").strip() or 0)
    except (TypeError, ValueError):
        return 0.0


def _money_s(value: Any) -> str:
    return f"{_money(value):.2f}"


def _policy_digits(mpolicy: str) -> str:
    mp = normalize(mpolicy)
    if mp.endswith("C") and len(mp) >= 2:
        return mp[:-1]
    return "".join(ch for ch in mp if ch.isdigit())


def _norm_code(v: Any) -> str:
    digits = re.sub(r"[^0-9]", "", _strip(v))
    if not digits:
        return ""
    return str(int(digits))


def _display_name_clnt(row: pd.Series) -> str:
    parts = [_strip(row.get("MFNAME", "")), _strip(row.get("MMNAME", "")), _strip(row.get("MLNAME", ""))]
    name = " ".join(p for p in parts if p).strip()
    if name:
        return name[:50]
    return _strip(row.get("MCOMPANY", "") or row.get("MNAME", ""))[:50]


def _payee_from_clnt(row: pd.Series) -> dict[str, str]:
    return {
        "MPAYNAME": _display_name_clnt(row),
        "MPAYADDR1": _strip(row.get("MADDR1", "") or row.get("MADDRESS1", ""))[:25],
        "MPAYADDR2": _strip(row.get("MADDR2", "") or row.get("MADDRESS2", ""))[:25],
        "MPAYCITY": _strip(row.get("MCITY", ""))[:50],
        "MPAYST": _strip(row.get("MST", "") or row.get("MSTATE", ""))[:2],
        "MPAYZIP": _strip(row.get("MZIP", ""))[:5],
        "MPAYZIP2": _strip(row.get("MZIP2", "") or row.get("MZIP4", ""))[:4],
    }


def _build_display_name_rna(row: pd.Series) -> str:
    business = _strip(row.get("NAME_BUSINESS", ""))
    if business:
        return business[:50]
    parts = [
        _strip(row.get("INDIVIDUAL_FIRST", "")),
        _strip(row.get("INDIVIDUAL_MIDDLE", "")),
        _strip(row.get("INDIVIDUAL_LAST", "")),
    ]
    name = " ".join(p for p in parts if p).strip()
    if name:
        return name[:50]
    key = _strip(row.get("KEY_NAME", ""))
    return " ".join(key.split())[:50] if key else ""


def _payee_from_rna(row: pd.Series) -> dict[str, str]:
    return {
        "MPAYNAME": _build_display_name_rna(row),
        "MPAYADDR1": _strip(row.get("ADDR_LINE_1", ""))[:25],
        "MPAYADDR2": _strip(row.get("ADDR_LINE_2", ""))[:25],
        "MPAYCITY": _strip(row.get("CITY", ""))[:50],
        "MPAYST": _strip(row.get("STATE", ""))[:2],
        "MPAYZIP": _strip(row.get("ZIP", ""))[:5],
        "MPAYZIP2": _strip(row.get("ZIP_EXTENSION", ""))[:4],
    }


def _load_role_payees(
    clid_path: str | Path,
    clnt_path: str | Path,
    policies: set[str],
) -> dict[str, dict[str, dict[str, str]]]:
    """mpolicy -> role -> payee fields."""
    out: dict[str, dict[str, dict[str, str]]] = {}
    if not os.path.isfile(clid_path) or not os.path.isfile(clnt_path):
        return out
    clid = pd.read_csv(clid_path, dtype=str).fillna("")
    clnt = pd.read_csv(clnt_path, dtype=str).fillna("")
    clid["MPOLICY"] = clid["MPOLICY"].map(_strip)
    clid = clid[clid["MPOLICY"].isin(policies)].copy()
    if clid.empty:
        return out
    id_col = "MCLIENTID" if "MCLIENTID" in clid.columns else "MCLIENT"
    clnt["MCLIENTID"] = clnt["MCLIENTID"].map(_strip)
    clnt = clnt.drop_duplicates("MCLIENTID", keep="first").set_index("MCLIENTID")
    for _, r in clid.iterrows():
        pol = _strip(r.get("MPOLICY", ""))
        role = _strip(r.get("MRELATION", "")).upper()
        if role not in ROLE_FALLBACK:
            continue
        cid = _strip(r.get(id_col, ""))
        if not cid or cid not in clnt.index:
            continue
        payee = _payee_from_clnt(clnt.loc[cid])
        if not payee.get("MPAYNAME"):
            continue
        out.setdefault(pol, {})
        # Prefer first occurrence per role (stable file order).
        if role not in out[pol]:
            out[pol][role] = payee
    return out


def _pick_role_payee(role_map: dict[str, dict[str, str]] | None) -> tuple[dict[str, str] | None, str]:
    if not role_map:
        return None, ""
    for role in ROLE_FALLBACK:
        if role in role_map and role_map[role].get("MPAYNAME"):
            return role_map[role], role
    return None, ""


def _load_prelsa_pe(
    prelsa_path: str | Path,
    lifepro_pols: set[str],
) -> dict[str, list[pd.Series]]:
    """lifepro digits -> ordered PE RNA rows."""
    out: dict[str, list[pd.Series]] = {}
    if not os.path.isfile(prelsa_path):
        return out
    try:
        # Full read (not chunked): LifePRO extract has irregular quotes that break
        # chunked python-engine iteration mid-file.
        rel = pd.read_csv(
            prelsa_path,
            encoding="latin1",
            dtype=str,
            engine="python",
            on_bad_lines="skip",
        )
    except Exception:
        return out
    rel.columns = [_strip(c) for c in rel.columns]
    if "POLICY_NUMBER" not in rel.columns or "RELATE_CODE" not in rel.columns:
        return out
    pol = rel[rel["POLICY_NUMBER"].map(_strip).isin(lifepro_pols)].copy()
    pol["RC"] = pol["RELATE_CODE"].map(_strip).str.upper()
    pe = pol[pol["RC"] == "PE"]
    for dig, grp in pe.groupby(pe["POLICY_NUMBER"].map(_strip), sort=False):
        seen: set[str] = set()
        rows: list[pd.Series] = []
        for _, r in grp.iterrows():
            nid = _strip(r.get("NAME_ID", ""))
            key = nid or _build_display_name_rna(r)
            if not key or key in seen:
                continue
            if not _build_display_name_rna(r):
                continue
            seen.add(key)
            rows.append(r)
        if rows:
            out[dig] = rows
    return out


def _load_pe_payouts(
    pactg_path: str | Path,
    lifepro_pols: set[str],
) -> dict[str, pd.DataFrame]:
    """lifepro -> PE payout rows (codes 90/92/94, PAYEE_RELA=PE, not reversed)."""
    if not os.path.isfile(pactg_path):
        return {}
    hdr = pd.read_csv(pactg_path, encoding="latin1", dtype=str, nrows=0)
    colmap = {_strip(c): c for c in hdr.columns}
    want = [
        "POLICY_NUMBER",
        "CREDIT_CODE",
        "DEBIT_CODE",
        "TRANS_AMOUNT",
        "EFFECTIVE_DATE",
        "REVERSAL_CODE",
        "PAYEE_RELA_CODE",
        "PAYEE_SEQUENCE",
        "CONTROL_NUMBER",
        "DATE_REVERSED",
    ]
    usecols = [colmap[w] for w in want if w in colmap]
    buckets: dict[str, list[pd.DataFrame]] = {}
    for chunk in pd.read_csv(
        pactg_path, encoding="latin1", dtype=str, usecols=usecols, chunksize=300000
    ):
        chunk.columns = [_strip(c) for c in chunk.columns]
        chunk["POL"] = chunk["POLICY_NUMBER"].map(_strip)
        m = chunk[chunk["POL"].isin(lifepro_pols)].copy()
        if m.empty:
            continue
        m["RELA"] = m.get("PAYEE_RELA_CODE", pd.Series("", index=m.index)).map(_strip).str.upper()
        m = m[m["RELA"] == "PE"]
        if m.empty:
            continue
        cr = m["CREDIT_CODE"].map(_norm_code)
        dr = m["DEBIT_CODE"].map(_norm_code)
        m = m[cr.isin(PAYOUT_CODES) | dr.isin(PAYOUT_CODES)]
        if "REVERSAL_CODE" in m.columns:
            m = m[~m["REVERSAL_CODE"].map(_strip).str.upper().isin(REVERSAL_CODES)]
        if "DATE_REVERSED" in m.columns:
            rev = m["DATE_REVERSED"].map(_strip)
            m = m[~rev.isin({"Y", "R", "V"})]
            # numeric non-zero reversed dates drop
            def _rev_date(s: str) -> bool:
                if not s or s in {"0", "0.0", "00000000"}:
                    return False
                try:
                    return float(s.replace(",", "")) != 0.0
                except ValueError:
                    return bool(s)

            m = m[~rev.map(_rev_date)]
        if m.empty:
            continue
        m["AMT"] = pd.to_numeric(m["TRANS_AMOUNT"].map(_strip), errors="coerce").fillna(0.0)
        m = m[m["AMT"].abs() > 0.009]
        m["EFF"] = m["EFFECTIVE_DATE"].map(_strip)
        m["SEQ"] = m.get("PAYEE_SEQUENCE", pd.Series("", index=m.index)).map(_strip)
        for pol, grp in m.groupby("POL", sort=False):
            buckets.setdefault(pol, []).append(grp)
    return {
        pol: pd.concat(parts, ignore_index=True).sort_values(["EFF", "SEQ", "AMT"])
        for pol, parts in buckets.items()
    }


def _surrender_eff_date(header: pd.Series, pe_df: pd.DataFrame | None) -> str:
    for col in ("PDDATE", "RPTDATE", "ACCPTDATE"):
        v = _strip(header.get(col, ""))
        if v:
            return v
    if pe_df is not None and len(pe_df):
        return _strip(pe_df.iloc[-1].get("EFF", ""))
    return ""


def apply_surrender_zero_payee_backfill(
    clms_df: pd.DataFrame,
    clmp_df: pd.DataFrame,
    *,
    pactg_path: str | Path,
    prelsa_path: str | Path,
    clid_path: str | Path,
    clnt_path: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    stats: dict[str, Any] = {
        "applied": False,
        "cohort_n": 0,
        "rule1_policies": 0,
        "rule1_rows": 0,
        "rule2_policies": 0,
        "rule2_rows": 0,
        "hold_n": 0,
        "rows_added": 0,
        "audit_rows": [],
        "holds": [],
    }
    clms = clms_df.copy().fillna("")
    clmp = clmp_df.copy().fillna("")
    for col in QUIKCLMP_SCHEMA:
        if col not in clmp.columns:
            clmp[col] = ""

    have_payee = set(clmp["MPOLICY"].map(_strip))
    surr = clms[
        (clms["CLAIMSTAT"].map(_strip) == "99")
        & (clms["MPAID"].map(_money) > 0)
        & (~clms["MPOLICY"].map(_strip).isin(have_payee))
    ].copy()
    # One header per policy (prefer MSEQ=0).
    surr["_pol"] = surr["MPOLICY"].map(_strip)
    surr["_mseq"] = pd.to_numeric(surr["MSEQ"], errors="coerce").fillna(0)
    surr = surr.sort_values(["_pol", "_mseq"]).drop_duplicates("_pol", keep="first")
    stats["cohort_n"] = int(len(surr))
    if surr.empty:
        return clms, clmp, stats

    policies = set(surr["_pol"])
    digits = {_policy_digits(p) for p in policies}
    digit_to_qla = {_policy_digits(p): p for p in policies}

    role_maps = _load_role_payees(clid_path, clnt_path, policies)
    pe_payouts = _load_pe_payouts(pactg_path, digits)
    pe_rna = _load_prelsa_pe(prelsa_path, digits)

    new_rows: list[dict[str, str]] = []

    for _, hdr in surr.iterrows():
        pol = _strip(hdr.get("MPOLICY", ""))
        dig = _policy_digits(pol)
        mpaid = _money(hdr.get("MPAID", 0))
        header_mseq = _strip(hdr.get("MSEQ", "0")) or "0"
        mphase = _strip(hdr.get("MPHASE", "1")) or "1"
        pe_df = pe_payouts.get(dig)
        pe_sum = round(float(pe_df["AMT"].sum()), 2) if pe_df is not None and len(pe_df) else 0.0
        role_payee, role_src = _pick_role_payee(role_maps.get(pol))
        rna_list = pe_rna.get(dig, [])

        applied_rule = ""
        built: list[dict[str, str]] = []

        if pe_df is not None and len(pe_df) and abs(pe_sum - mpaid) <= TOLERANCE:
            # Rule 1
            payouts = pe_df.reset_index(drop=True)
            identities: list[dict[str, str]] = []
            if rna_list and len(rna_list) == len(payouts):
                identities = [_payee_from_rna(r) for r in rna_list]
            elif rna_list and len(payouts) == 1:
                identities = [_payee_from_rna(rna_list[0])]
            elif role_payee and len(payouts) == 1:
                identities = [role_payee]
            elif role_payee and rna_list:
                # Multi payout, use primary PE RNA if counts differ — only if single unique name
                names = {_build_display_name_rna(r) for r in rna_list}
                if len(names) == 1:
                    identities = [_payee_from_rna(rna_list[0])] * len(payouts)
                else:
                    identities = []
            elif role_payee:
                identities = [role_payee] * len(payouts)

            if identities and all(x.get("MPAYNAME") for x in identities):
                if len(identities) == 1 and len(payouts) > 1:
                    identities = identities * len(payouts)
                eff_default = _surrender_eff_date(hdr, payouts)
                for i, prow in payouts.iterrows():
                    payee = identities[min(i, len(identities) - 1)]
                    row = _blank_payment_row(pol, mphase)
                    row.update(payee)
                    amt = _money_s(prow.get("AMT", 0))
                    row["MAMOUNT"] = amt
                    row["MGROSS"] = amt
                    row["MCHKDATE"] = _strip(prow.get("EFF", "")) or eff_default
                    row["MPMTDATE"] = row["MCHKDATE"]
                    row["MCHECKNO"] = "0"
                    row["MSEQ"] = header_mseq
                    row["MHDPMT"] = "C"
                    built.append(row)
                applied_rule = "RULE1_PE_SUM_MATCH"
            else:
                stats["holds"].append(
                    {
                        "mpolicy": pol,
                        "reason": "RULE1_MATCH_NO_IDENTITY",
                        "mpaid": mpaid,
                        "pe_sum": pe_sum,
                        "pe_n": int(len(payouts)),
                    }
                )
                stats["hold_n"] += 1
                continue

        if not built:
            # Rule 2
            if not role_payee:
                stats["holds"].append(
                    {
                        "mpolicy": pol,
                        "reason": "RULE2_NO_OWNR_INSD_PAYR",
                        "mpaid": mpaid,
                        "pe_sum": pe_sum,
                    }
                )
                stats["hold_n"] += 1
                continue
            row = _blank_payment_row(pol, mphase)
            row.update(role_payee)
            row["MAMOUNT"] = _money_s(mpaid)
            row["MGROSS"] = row["MAMOUNT"]
            row["MCHKDATE"] = _surrender_eff_date(hdr, pe_df)
            row["MPMTDATE"] = row["MCHKDATE"]
            row["MCHECKNO"] = "0"
            row["MSEQ"] = header_mseq
            row["MHDPMT"] = "C"
            built.append(row)
            applied_rule = f"RULE2_ROLE_{role_src}"

        new_rows.extend(built)
        pay_sum = round(sum(_money(r["MAMOUNT"]) for r in built), 2)
        stats["audit_rows"].append(
            {
                "mpolicy": pol,
                "rule": applied_rule,
                "mpaid": mpaid,
                "pe_sum": pe_sum,
                "rows": len(built),
                "payee_sum": pay_sum,
                "header_mseq": header_mseq,
                "payee_name_0": built[0].get("MPAYNAME", ""),
            }
        )
        if applied_rule.startswith("RULE1"):
            stats["rule1_policies"] += 1
            stats["rule1_rows"] += len(built)
        else:
            stats["rule2_policies"] += 1
            stats["rule2_rows"] += len(built)

    if new_rows:
        add = pd.DataFrame(new_rows, columns=QUIKCLMP_SCHEMA)
        clmp = pd.concat(
            [clmp.reindex(columns=QUIKCLMP_SCHEMA, fill_value=""), add],
            ignore_index=True,
        )
        stats["applied"] = True
        stats["rows_added"] = len(new_rows)

    stats["digit_to_qla_n"] = len(digit_to_qla)
    return clms, clmp, stats


def write_surrender_zero_payee_audit(
    stats: dict[str, Any],
    evidence_dir: str | Path,
) -> dict[str, str]:
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    audit = pd.DataFrame(stats.get("audit_rows") or [])
    holds = pd.DataFrame(stats.get("holds") or [])
    audit_path = evidence_dir / "issue135_surrender_zero_payee_backfill_audit.csv"
    hold_path = evidence_dir / "issue135_surrender_zero_payee_holds.csv"
    summary_path = evidence_dir / "issue135_surrender_zero_payee_backfill_summary.json"
    audit.to_csv(audit_path, index=False, encoding="utf-8")
    holds.to_csv(hold_path, index=False, encoding="utf-8")
    summary = {
        k: v
        for k, v in stats.items()
        if k not in {"audit_rows", "holds"}
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    paths["audit"] = str(audit_path)
    paths["holds"] = str(hold_path)
    paths["summary"] = str(summary_path)
    return paths
