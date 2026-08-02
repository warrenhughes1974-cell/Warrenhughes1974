"""Surgical Issue #134 apply to current Output: overlay quikclms + re-emit quikmemo (B excluded)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qla_core.issue134_claim_memo_overlay import (  # noqa: E402
    apply_issue134_claim_memos,
    write_issue134_orphan_audit,
)
from qla_core.lifepro_source_resolver import resolve_quikmemo_sources  # noqa: E402
from qla_core.modal_premium_factors import append_issue21j_conversion_memos  # noqa: E402
from qla_core.quikmemo_converter import convert_quikmemo_from_pnote_pense  # noqa: E402

OUT = ROOT / "QLA_Migration" / "Output"
SRC = ROOT / "QLA_Migration" / "Source"
REPORTS = ROOT / "QLA_Migration" / "Reports"
CW = ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"


def _load_cw_map(path: Path) -> dict[str, str]:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    cols = {c.upper(): c for c in df.columns}
    old_c = cols.get("OLD_VALUE") or cols.get("OLD") or list(df.columns)[0]
    new_c = cols.get("NEW_VALUE") or cols.get("NEW") or list(df.columns)[1]
    out: dict[str, str] = {}
    for _, row in df.iterrows():
        old = str(row.get(old_c, "")).strip()
        new = str(row.get(new_c, "")).strip()
        if old:
            out[old.upper()] = new
            out[old] = new
    return out


def main() -> int:
    pnote_path, pnote_label, pense_path, pense_label = resolve_quikmemo_sources(str(SRC))
    print(f"PNOTE: {pnote_path} ({pnote_label})")
    print(f"PENSE: {pense_path} ({pense_label})")

    clms_path = OUT / "quikclms.csv"
    clms = pd.read_csv(clms_path, dtype=str, keep_default_na=False)
    before_lineage = int(clms["MEMOTEXT"].astype(str).str.contains("DEATH_CLAIM", regex=False).sum())
    clms_after, orphan_df, stats = apply_issue134_claim_memos(clms, pnote_path)
    tmp = clms_path.with_suffix(".csv.tmp")
    clms_after.to_csv(tmp, index=False, encoding="utf-8")
    tmp.replace(clms_path)
    audit = write_issue134_orphan_audit(orphan_df, str(REPORTS))
    after_b = int(clms_after["MEMOTEXT"].astype(str).str.contains("[PNOTE-B]", regex=False).sum())
    print("quikclms overlay:", stats)
    print(f"  death_lineage_before={before_lineage} pnote_b_after={after_b}")
    print(f"  orphan audit: {audit}")

    cw_map = _load_cw_map(CW)
    memo_df, memo_orphan, memo_stats = convert_quikmemo_from_pnote_pense(
        pnote_path or None,
        pense_path or None,
        cw_map=cw_map,
    )
    # Match batch path: keep fleet [CONVERSION] memos (do not drop vs prior Output).
    memo_df, conv_stats = append_issue21j_conversion_memos(
        memo_df,
        conversion_version="v57.46",
        quikmstr_path=str(OUT / "quikmstr.csv"),
        quikridr_path=str(OUT / "quikridr.csv"),
        quikplan_path=str(OUT / "quikplan.csv"),
    )
    memo_path = OUT / "quikmemo.csv"
    memo_tmp = memo_path.with_suffix(".csv.tmp")
    memo_df.to_csv(memo_tmp, index=False, encoding="utf-8")
    memo_tmp.replace(memo_path)
    print("quikmemo re-emit:", {k: memo_stats.get(k) for k in (
        "pnote_source_rows", "skipped_file_type_b", "emitted_pnote", "emitted_pense", "emitted_rows"
    )})
    print(f"  after 21J rows={len(memo_df)} conv={conv_stats} orphans={len(memo_orphan)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
