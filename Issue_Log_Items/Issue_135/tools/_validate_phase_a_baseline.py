#!/usr/bin/env python3
"""Read-only: validate whether Phase-A-only baseline is reconstructable from HEAD."""
from __future__ import annotations

import json
import subprocess
from io import BytesIO
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "QLA_Migration" / "Output"
TV = OUT / "Test_Validation"


def load_git(rel: str) -> pd.DataFrame:
    data = subprocess.check_output(["git", "show", f"HEAD:{rel}"], cwd=ROOT)
    return pd.read_csv(BytesIO(data), dtype=str, keep_default_na=False)


def main() -> int:
    artifacts = sorted(
        [
            p.name
            for p in OUT.iterdir()
            if p.is_file()
            and not (p.name.lower().startswith("quik") and p.suffix.lower() == ".csv")
        ]
    )
    clms = pd.read_csv(OUT / "quikclms.csv", dtype=str, keep_default_na=False)
    clmp = pd.read_csv(OUT / "quikclmp.csv", dtype=str, keep_default_na=False)
    h_clms = load_git("QLA_Migration/Output/quikclms.csv")
    h_clmp = load_git("QLA_Migration/Output/quikclmp.csv")

    key_cols = [c for c in ["MPOLICY", "CLAIMNUM", "CLAIMSTAT"] if c in clms.columns]
    cur = clms.copy()
    head = h_clms.copy()
    for df in (cur, head):
        for c in key_cols:
            df[c] = df[c].astype(str).str.strip()

    cur_keys = set(map(tuple, cur[key_cols].values.tolist()))
    head_keys = set(map(tuple, head[key_cols].values.tolist()))
    common = cur.merge(head, on=key_cols, how="inner", suffixes=("_cur", "_head"))

    money_fields = [
        c
        for c in ["MPAID", "MFACE", "NETDB", "MLOAN", "MINTAMT", "MPREM", "MDIV", "MSUSPENSE"]
        if c in clms.columns
    ]
    date_fields = [c for c in ["PDDATE", "DTOFDEATH", "CLAIMDATE"] if c in clms.columns]
    # Skip key_cols — merge keeps them unsuffixed
    compare_fields = [
        f
        for f in money_fields + date_fields + ["MEMOTEXT", "MPAYEE"]
        if f in clms.columns and f not in key_cols
    ]
    diffs = {}
    for f in compare_fields:
        a = common[f + "_cur"].astype(str).str.strip()
        b = common[f + "_head"].astype(str).str.strip()
        n = int((a != b).sum())
        if n:
            diffs[f] = n

    sim = head.copy()
    sim["MINTAMT"] = "0.00"
    sim_m = sim.merge(cur, on=key_cols, how="inner", suffixes=("_sim", "_cur"))
    non_mint_diff = {}
    for f in [c for c in clms.columns if c not in key_cols]:
        a = sim_m[f + "_sim"].astype(str).str.strip()
        b = sim_m[f + "_cur"].astype(str).str.strip()
        n = int((a != b).sum())
        if n:
            non_mint_diff[f] = n

    # Among common rows where only MINTAMT differs in HEAD vs CUR for money/date?
    mint_only_rows = 0
    mixed_drift_rows = 0
    for _, r in common.iterrows():
        field_changed = []
        for f in money_fields + date_fields:
            if str(r[f + "_cur"]).strip() != str(r[f + "_head"]).strip():
                field_changed.append(f)
        if not field_changed:
            continue
        if field_changed == ["MINTAMT"]:
            mint_only_rows += 1
        else:
            mixed_drift_rows += 1

    tv_clmp = TV / "quikclmp.csv"
    tv_clms = TV / "quikclms.csv"
    tv_info = {
        "tv_clmp_exists": tv_clmp.exists(),
        "tv_clms_exists": tv_clms.exists(),
    }
    if tv_clmp.exists():
        t = pd.read_csv(tv_clmp, dtype=str, keep_default_na=False)
        tv_info["tv_clmp_rows"] = len(t)
        tv_info["out_clmp_rows"] = len(clmp)
        tv_info["tv_clmp_cols_match"] = list(t.columns) == list(clmp.columns)
        if list(t.columns) == list(clmp.columns) and len(t) == len(clmp):
            tv_info["tv_clmp_equal"] = bool((t.fillna("") == clmp.fillna("")).all().all())
        else:
            tv_info["tv_clmp_equal"] = False
    if tv_clms.exists():
        t = pd.read_csv(tv_clms, dtype=str, keep_default_na=False)
        tv_info["tv_clms_rows"] = len(t)
        tv_info["out_clms_rows"] = len(clms)
        if "MINTAMT" in t.columns:
            tv_info["tv_mintamt_nonzero"] = int(
                (t["MINTAMT"].astype(str).str.strip() != "0.00").sum()
            )
        # Compare TV vs OUT on MINTAMT only for common keys
        if list(t.columns) == list(clms.columns):
            t2 = t.copy()
            c2 = clms.copy()
            for df in (t2, c2):
                for c in key_cols:
                    df[c] = df[c].astype(str).str.strip()
            m = t2.merge(c2, on=key_cols, how="inner", suffixes=("_tv", "_out"))
            tv_info["tv_clms_common"] = len(m)
            if "MINTAMT" in clms.columns:
                tv_info["tv_vs_out_mintamt_diff"] = int(
                    (
                        m["MINTAMT_tv"].astype(str).str.strip()
                        != m["MINTAMT_out"].astype(str).str.strip()
                    ).sum()
                )

    summary = {
        "output_root_non_quik_count": len(artifacts),
        "output_root_non_quik_sample": artifacts[:40],
        "clms_rows": len(clms),
        "clmp_rows": len(clmp),
        "head_clms_rows": len(h_clms),
        "head_clmp_rows": len(h_clmp),
        "clmp_row_delta": len(clmp) - len(h_clmp),
        "mintamt_nonzero_current": int(
            (clms["MINTAMT"].astype(str).str.strip() != "0.00").sum()
        )
        if "MINTAMT" in clms.columns
        else None,
        "mintamt_nonzero_head": int(
            (h_clms["MINTAMT"].astype(str).str.strip() != "0.00").sum()
        )
        if "MINTAMT" in h_clms.columns
        else None,
        "clms_keys_only_cur": len(cur_keys - head_keys),
        "clms_keys_only_head": len(head_keys - cur_keys),
        "clms_keys_common": len(cur_keys & head_keys),
        "field_diffs_common_rows": diffs,
        "mint_only_changed_rows": mint_only_rows,
        "mixed_drift_rows": mixed_drift_rows,
        "phase_a_only_reconstructable": non_mint_diff == {}
        or set(non_mint_diff.keys()) <= {"MINTAMT"},
        "sim_head_mint0_vs_cur_diffs_top": dict(
            sorted(non_mint_diff.items(), key=lambda x: -x[1])[:30]
        ),
        "test_validation": tv_info,
        "verdict": (
            "PHASE_A_ONLY_BASELINE_RECONSTRUCTABLE"
            if (non_mint_diff == {} or set(non_mint_diff.keys()) <= {"MINTAMT"})
            and len(cur_keys) == len(head_keys)
            and len(clmp) == len(h_clmp)
            else "DRIFT_IS_DOCUMENTED_BASELINE_LIMITATION"
        ),
    }
    out_path = (
        ROOT
        / "Issue_Log_Items"
        / "Issue_135"
        / "evidence"
        / "issue135_phase_a_baseline_validation.json"
    )
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
