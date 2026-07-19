"""Issue #78 — recover missing quikclmp rows from PACTG + relationship payee tiers."""

from __future__ import annotations

import os
from typing import Any

import pandas as pd

from qla_core.normalize_utils import normalize

PAYOUT_CODES = frozenset({"90", "92", "94", "567", "1900", "0090", "0092", "0094", "0567"})
REVERSAL_CODES = frozenset({"Y", "R", "V"})
QUIKCLMP_SCHEMA = [
    "MPOLICY", "MPHASE", "MCHECKNO", "MAMOUNT", "MPAYNAME", "MPAYADDR1", "MPAYADDR2",
    "MPAYCITY", "MPAYST", "MPAYZIP", "MPAYZIP2", "MTIN", "MBANKNO", "MHDPMT", "MHDCODE",
    "MCHKDATE", "MPMTDATE", "MSEQ", "MHOLDINT", "MFEDTAX", "MSTTAX", "MGROSS", "MDOB",
    "MGENDER", "MCOUNTRY",
]


def _strip(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text or text.lower() in ("nan", "none"):
        return ""
    return text


def _money(value: Any) -> str:
    try:
        return f"{float(str(value).replace(',', '').strip() or 0):.2f}"
    except (TypeError, ValueError):
        return "0.00"


def _qla_to_lifepro(mpolicy: str) -> str:
    mp = normalize(mpolicy)
    if mp.endswith("C") and len(mp) >= 2:
        return "9" + mp[:-1]
    return mp


def _build_display_name(row: pd.Series) -> str:
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
    if key:
        return " ".join(key.split())[:50]
    return ""


def _payee_from_row(row: pd.Series) -> dict[str, str]:
    return {
        "MPAYNAME": _build_display_name(row),
        "MPAYADDR1": _strip(row.get("ADDR_LINE_1", ""))[:25],
        "MPAYADDR2": _strip(row.get("ADDR_LINE_2", ""))[:25],
        "MPAYCITY": _strip(row.get("CITY", ""))[:50],
        "MPAYST": _strip(row.get("STATE", ""))[:2],
        "MPAYZIP": _strip(row.get("ZIP", ""))[:5],
        "MPAYZIP2": _strip(row.get("ZIP_EXTENSION", ""))[:4],
    }


def _load_crosswalk(path: str) -> dict[str, str]:
    if not os.path.isfile(path):
        return {}
    df = pd.read_csv(path, dtype=str)
    return {normalize(k): normalize(v) for k, v in zip(df.iloc[:, 0], df.iloc[:, 1])}


def _load_relationship_index(rel_path: str, lifepro_pols: set[str]) -> dict[str, pd.DataFrame]:
    rel = pd.read_csv(
        rel_path,
        encoding="latin1",
        dtype=str,
        engine="python",
        on_bad_lines="skip",
    )
    rel.columns = [_strip(c) for c in rel.columns]
    rel["POL"] = rel["POLICY_NUMBER"].astype(str).str.strip()
    rel = rel[rel["POL"].isin(lifepro_pols)].copy()
    rel["RC"] = rel["RELATE_CODE"].astype(str).str.strip()
    rel["NAME_ID"] = rel["NAME_ID"].astype(str).str.strip()
    return {pol: grp for pol, grp in rel.groupby("POL", sort=False)}


def _load_pactg_payouts(pactg_path: str, lifepro_pols: set[str]) -> pd.DataFrame:
    hdr = pd.read_csv(pactg_path, encoding="latin1", dtype=str, nrows=0)
    colmap = {_strip(c): c for c in hdr.columns}
    want = [
        "POLICY_NUMBER",
        "CREDIT_CODE",
        "DEBIT_CODE",
        "TRANS_AMOUNT",
        "EFFECTIVE_DATE",
        "REVERSAL_CODE",
        "CONTROL_NUMBER",
    ]
    usecols = [colmap[w] for w in want if w in colmap]
    rows: list[pd.DataFrame] = []
    for chunk in pd.read_csv(pactg_path, encoding="latin1", dtype=str, usecols=usecols, chunksize=300000):
        chunk.columns = [_strip(c) for c in chunk.columns]
        chunk["POL"] = chunk["POLICY_NUMBER"].astype(str).str.strip()
        m = chunk[chunk["POL"].isin(lifepro_pols)]
        m = m[
            (m["CREDIT_CODE"].astype(str).str.strip().isin(PAYOUT_CODES))
            | (m["DEBIT_CODE"].astype(str).str.strip().isin(PAYOUT_CODES))
        ]
        m = m[~m["REVERSAL_CODE"].astype(str).str.strip().isin(REVERSAL_CODES)]
        rows.append(m)
    if not rows:
        return pd.DataFrame(columns=["POL", "TRANS_AMOUNT", "EFFECTIVE_DATE", "CONTROL_NUMBER"])
    out = pd.concat(rows, ignore_index=True)
    out["AMT"] = pd.to_numeric(out["TRANS_AMOUNT"].astype(str).str.strip(), errors="coerce").fillna(0)
    out["EFF"] = out["EFFECTIVE_DATE"].astype(str).str.strip()
    out["CHECK"] = out["CONTROL_NUMBER"].astype(str).str.strip()
    return out


def _resolve_tier_and_payees(rel_grp: pd.DataFrame | None) -> tuple[int, list[dict[str, str]], str]:
    if rel_grp is None or rel_grp.empty:
        return 3, [], "ESTATE_UNKNOWN"
    pe = rel_grp[rel_grp["RC"] == "PE"].copy()
    if not pe.empty:
        pe = pe.sort_values("NAME_ID").drop_duplicates("NAME_ID", keep="first")
        pe_rows = [_payee_from_row(r) for _, r in pe.iterrows()]
        if len(pe_rows) == 1:
            return 1, pe_rows[:1], "PE_SINGLE"
        return 2, pe_rows, "PE_MULTI"
    for code, src in (("B1", "B1"), ("B2", "B2")):
        sub = rel_grp[rel_grp["RC"] == code]
        if not sub.empty:
            return 3, [_payee_from_row(sub.iloc[0])], src
    ins = rel_grp[rel_grp["RC"].isin(["IN", "INSD"])]
    if not ins.empty:
        payee = _payee_from_row(ins.iloc[0])
        name = payee.get("MPAYNAME", "")
        if name:
            payee["MPAYNAME"] = f"ESTATE OF {name}"[:50]
        return 3, [payee], "ESTATE_IN"
    return 3, [], "ESTATE_UNKNOWN"


def _pick_payee_for_payout(
    tier: int,
    payees: list[dict[str, str]],
    payout_idx: int,
    pair_note: str,
) -> dict[str, str]:
    blank = {k: "" for k in ("MPAYNAME", "MPAYADDR1", "MPAYADDR2", "MPAYCITY", "MPAYST", "MPAYZIP", "MPAYZIP2")}
    if not payees:
        return blank
    if tier == 1:
        return payees[0]
    if tier == 2 and pair_note == "PAIR_OK" and payout_idx < len(payees):
        return payees[payout_idx]
    return payees[0]


def _blank_payment_row(mpolicy: str, mphase: str = "1") -> dict[str, str]:
    row = {h: "" for h in QUIKCLMP_SCHEMA}
    row["MPOLICY"] = mpolicy
    row["MPHASE"] = mphase
    row["MCHECKNO"] = "0"
    row["MHDPMT"] = "C"
    row["MSEQ"] = "0"
    row["MHOLDINT"] = "0.00"
    row["MFEDTAX"] = "0.00"
    row["MSTTAX"] = "0.00"
    return row


def recover_missing_quikclmp_payments(
    clms_df: pd.DataFrame,
    clmp_df: pd.DataFrame,
    pactg_path: str,
    rel_path: str,
    crosswalk_path: str,
    format_mpolicy=None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Append recovered payment rows for policies with zero quikclmp today."""
    clms = clms_df.copy().fillna("")
    clmp = clmp_df.copy().fillna("")

    clms_pols = set(clms["MPOLICY"].astype(str).str.strip())
    clmp_pols = set(clmp["MPOLICY"].astype(str).str.strip())
    missing_pols = sorted(clms_pols - clmp_pols)
    if not missing_pols:
        return clmp, pd.DataFrame()

    hdr = clms.copy()
    hdr["POL_KEY"] = hdr["MPOLICY"].astype(str).str.strip()
    hdr = hdr.drop_duplicates("POL_KEY").set_index("POL_KEY")

    lp_map = {_qla_to_lifepro(p): p for p in missing_pols}
    lifepro_pols = set(lp_map)
    rel_index = _load_relationship_index(rel_path, lifepro_pols)
    payouts = _load_pactg_payouts(pactg_path, lifepro_pols)

    new_rows: list[dict[str, str]] = []
    audit: list[dict[str, Any]] = []

    for lp in sorted(lifepro_pols):
        qla = lp_map[lp]
        if format_mpolicy:
            qla = format_mpolicy(qla)
        pol_payouts = payouts[payouts["POL"] == lp].sort_values(["EFF", "AMT"]).reset_index(drop=True)
        if pol_payouts.empty:
            continue

        header = hdr.loc[qla] if qla in hdr.index else None
        mphase = _strip(header["MPHASE"]) if header is not None else "1"
        claimstat = _strip(header["CLAIMSTAT"]) if header is not None else ""
        header_mpaid = _money(header["MPAID"]) if header is not None else "0.00"

        tier, payees, payee_src = _resolve_tier_and_payees(rel_index.get(lp))
        payout_count = len(pol_payouts)
        pe_count = len(payees)
        pair_note = ""
        if tier == 2:
            if payout_count == pe_count and pe_count > 0:
                pair_note = "PAIR_OK"
                payee_src = "PE_MULTI_PAIR_OK"
            else:
                pair_note = "PRIMARY_PE_ALL"
                payee_src = "PE_MULTI_PRIMARY_PE_ALL"

        payout_total = round(float(pol_payouts["AMT"].sum()), 2)
        for idx, prow in pol_payouts.iterrows():
            payee = _pick_payee_for_payout(tier, payees, idx, pair_note)
            row = _blank_payment_row(qla, mphase)
            amt = _money(prow["AMT"])
            eff = _strip(prow["EFF"])
            check = _strip(prow["CHECK"])
            row["MAMOUNT"] = amt
            row["MGROSS"] = amt
            row["MCHKDATE"] = eff
            row["MPMTDATE"] = eff
            row["MCHECKNO"] = check if check.isdigit() else "0"
            row.update(payee)
            new_rows.append(row)

        audit.append(
            {
                "mpolicy": qla,
                "lifepro": lp,
                "tier": tier,
                "payout_rows": payout_count,
                "pe_count": pe_count,
                "payout_amount": payout_total,
                "claimstat": claimstat,
                "header_mpaid": header_mpaid,
                "payee_source": payee_src,
                "pair_note": pair_note,
                "header_mpaid_delta": round(payout_total - float(header_mpaid.replace(",", "") or 0), 2),
            }
        )

    if not new_rows:
        return clmp, pd.DataFrame(audit)

    new_df = pd.DataFrame(new_rows, columns=QUIKCLMP_SCHEMA)
    combined = pd.concat([clmp.reindex(columns=QUIKCLMP_SCHEMA, fill_value=""), new_df], ignore_index=True)
    return combined, pd.DataFrame(audit)


def write_recovery_audit(audit_df: pd.DataFrame, reports_dir: str) -> str:
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.join(reports_dir, "issue78_quikclmp_recovery_audit.csv")
    audit_df.to_csv(path, index=False, encoding="utf-8")
    return path
