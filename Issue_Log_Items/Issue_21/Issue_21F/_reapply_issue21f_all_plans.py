#!/usr/bin/env python3
"""Re-apply Issue #21F CONV_ADJ on Output quikprmh (includes ISWL via FV deposits)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import pandas as pd

from qla_core.issue21_open_item_decisions import resolve_ppben_path, resolve_ppbentyp_extract_path
from qla_core.issue21f_premium_adjustment import apply_issue21f_conversion_adjustments
from qla_core.normalize_utils import format_qladmin_mpolicy


def normalize(v: str) -> str:
    return str(v or "").strip()


def main() -> int:
    out = ROOT / "QLA_Migration" / "Output" / "quikprmh.csv"
    mstr = ROOT / "QLA_Migration" / "Output" / "quikmstr.csv"
    reports = ROOT / "QLA_Migration" / "Reports"
    src_root = ROOT / "QLA_Migration" / "Source"
    dated = src_root / "LifePRO_Extracts_20260731"

    ppbentyp = resolve_ppbentyp_extract_path(str(dated)) or resolve_ppbentyp_extract_path(str(src_root))
    ppben = resolve_ppben_path(str(dated)) or resolve_ppben_path(str(src_root))
    if not ppbentyp:
        print("FAIL: no PPBENTYP")
        return 2
    if not ppben:
        print("FAIL: no PPBEN (required for ISWL)")
        return 2

    qdf = pd.read_csv(out, dtype=str, encoding="utf-8-sig").fillna("")
    mstr_keys = set()
    if mstr.is_file():
        mdf = pd.read_csv(mstr, dtype=str, encoding="latin1").fillna("")
        if "MPOLICY" in mdf.columns:
            mstr_keys = {str(v).strip() for v in mdf["MPOLICY"] if str(v).strip()}

    print("ppbentyp", ppbentyp)
    print("ppben", ppben)
    print("prmh before", len(qdf))

    new_df, stats = apply_issue21f_conversion_adjustments(
        qdf,
        str(ppbentyp),
        normalize_fn=normalize,
        format_mpolicy_fn=format_qladmin_mpolicy,
        reports_dir=str(reports),
        mstr_mpolicy_keys=mstr_keys or None,
        reject_orphan_vs_mstr=bool(mstr_keys),
        ppben_path=str(ppben),
    )
    new_df.to_csv(out, index=False, encoding="utf-8-sig")
    print("stats", {k: v for k, v in stats.items() if k != "ppben_path"})
    print("prmh after", len(new_df))

    # spot-check gold
    gold = "9010718309C"
    sub = new_df[new_df["MPOLICY"].astype(str).str.strip() == gold]
    adj = sub[sub["MSOURCE"].astype(str).str.upper() == "CONV_ADJ"]
    print("gold", gold, "rows", len(sub), "CONV_ADJ", adj[["DATEPAID", "PREMIUM", "MSOURCE"]].to_dict("records"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
