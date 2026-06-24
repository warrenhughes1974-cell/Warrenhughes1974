"""
PACTG vs PLOAN reconciliation (read-only).

Does not modify PACTG processing or feed PACTG into QuikLoan values.
Produces pactg_ploan_reconciliation.csv when enabled from runner config.
"""

from __future__ import annotations

import os
import re

import pandas as pd

_LOAN_TX_RE = re.compile(r"^0?4(11|12|13|14|15|16|17|51)\b", re.I)


def _norm_policy(val) -> str:
    return str(val).strip().upper()


def _loan_codes_from_pactg(pactg_path: str) -> set[str]:
    if not os.path.isfile(pactg_path):
        return set()
    df = pd.read_csv(pactg_path, dtype=str, low_memory=False)
    df.columns = [str(c).strip().upper() for c in df.columns]
    pol_col = "POLICY_NUMBER" if "POLICY_NUMBER" in df.columns else "MPOLICY"
    code_col = next((c for c in ("TRANSACTION_CODE", "TX_CODE", "CODE") if c in df.columns), None)
    if not code_col or pol_col not in df.columns:
        return set()
    mask = df[code_col].astype(str).str.strip().str.match(_LOAN_TX_RE, na=False)
    return {_norm_policy(p) for p in df.loc[mask, pol_col].dropna().unique()}


def run_reconciliation(
    *,
    ploan_latest_path: str,
    output_dir: str,
    pactg_path: str | None = None,
    repo_root: str | None = None,
) -> str:
    repo_root = repo_root or os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if not pactg_path:
        for name in (
            "PACTG_Accounting_Extract20260427.csv",
            "PACTG.csv",
        ):
            p = os.path.join(repo_root, "QLA_Migration", "Source", name)
            if os.path.isfile(p):
                pactg_path = p
                break

    if not os.path.isfile(ploan_latest_path):
        raise FileNotFoundError(ploan_latest_path)

    latest = pd.read_csv(ploan_latest_path, dtype=str)
    ploan_policies = {_norm_policy(p) for p in latest.get("POLICY_NUMBER", pd.Series()).dropna()}

    pactg_loan_policies = _loan_codes_from_pactg(pactg_path or "")

    rows = []
    for pol in sorted(ploan_policies):
        rows.append({
            "POLICY_NUMBER": pol,
            "IN_PLOAN_LATEST": "Y",
            "IN_PACTG_LOAN_TX": "Y" if pol in pactg_loan_policies else "N",
            "RECON_NOTE": (
                "PLOAN-only (no PACTG loan tx)"
                if pol not in pactg_loan_policies
                else "Both sources present"
            ),
        })
    for pol in sorted(pactg_loan_policies - ploan_policies):
        rows.append({
            "POLICY_NUMBER": pol,
            "IN_PLOAN_LATEST": "N",
            "IN_PACTG_LOAN_TX": "Y",
            "RECON_NOTE": "PACTG loan tx without PLOAN latest row",
        })

    out_path = os.path.join(output_dir, "pactg_ploan_reconciliation.csv")
    pd.DataFrame(rows).to_csv(out_path, index=False)
    return out_path
