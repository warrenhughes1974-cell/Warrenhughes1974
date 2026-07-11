"""
Apply Issue 21F conversion adjustments to existing quikprmh.csv (offline rebatch).

Usage (repo root):
  python Issue_Log_Items/Issue_21/Issue_21F/_rebatch_quikprmh_21f.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from qla_core.issue21_open_item_decisions import resolve_ppbentyp_extract_path  # noqa: E402
from qla_core.issue21f_premium_adjustment import apply_issue21f_conversion_adjustments  # noqa: E402
from qla_core.normalize_utils import format_qladmin_mpolicy  # noqa: E402

OUT = ROOT / "QLA_Migration" / "Output"
SRC = ROOT / "QLA_Migration" / "Source"
REPORTS = ROOT / "QLA_Migration" / "Reports"
CW = ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
ARCHIVE = ROOT / "QLA_Migration" / "Archive"


def _normalize(val: str) -> str:
    s = str(val).strip().upper()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def main() -> int:
    prmh_path = OUT / "quikprmh.csv"
    if not prmh_path.is_file():
        print(f"Missing {prmh_path}")
        return 1

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    before_path = ARCHIVE / "quikprmh_pre_21f_v57.72.csv"
    if not before_path.is_file():
        import shutil
        shutil.copy2(prmh_path, before_path)
        print(f"Archived before snapshot -> {before_path}")

    qdf = pd.read_csv(prmh_path, dtype=str, encoding="latin1").fillna("")
    cw_df = pd.read_csv(CW, dtype=str).fillna("")
    cw_map = {_normalize(k): _normalize(v) for k, v in zip(cw_df.iloc[:, 0], cw_df.iloc[:, 1])}

    ppbentyp = resolve_ppbentyp_extract_path(str(SRC))
    if not ppbentyp:
        print("PPBENTYP extract not found")
        return 1

    qdf2, stats = apply_issue21f_conversion_adjustments(
        qdf,
        ppbentyp,
        normalize_fn=_normalize,
        format_mpolicy_fn=format_qladmin_mpolicy,
        crosswalk=cw_map,
        reports_dir=str(REPORTS),
    )
    qdf2.to_csv(prmh_path, index=False)
    print(f"Wrote {prmh_path} rows {len(qdf)} -> {len(qdf2)}")
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
