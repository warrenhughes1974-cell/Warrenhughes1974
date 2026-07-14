"""Issue #54 — emit QuikBenh loan history from PACTG (CLI runner)."""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qla_core.lifepro_source_resolver import resolve_table_source
from qla_core.quikbenh_loan_history_converter import (
    convert_quikbenh_loan_history_from_pactg,
    load_derivation_rules,
    write_quikbenh_csv,
)


def _load_crosswalk(path: Path) -> dict[str, str]:
    m: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            old = str(row.get("Old_Value", "")).strip()
            new = str(row.get("New_Value", "")).strip()
            if old and new:
                m[old] = new
    return m


def main() -> int:
    src_dir = ROOT / "QLA_Migration" / "Source"
    out_dir = ROOT / "QLA_Migration" / "Output"
    cw_path = ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
    report_dir = ROOT / "plan_analysis" / "phase_benh_loan_history"

    pactg_path, label = resolve_table_source(str(src_dir), "quikbenh")
    if not pactg_path:
        print("FAIL: no PACTG extract found")
        return 1
    print(f"PACTG source: {pactg_path} ({label})")

    ploan_path, ploan_label = resolve_table_source(str(src_dir), "quikloan")
    if not ploan_path:
        print("FAIL: no PLOAN extract found (required for opening balance seeds)")
        return 1
    print(f"PLOAN seed source: {ploan_path} ({ploan_label})")

    cw = _load_crosswalk(cw_path)
    existing = out_dir / "quikbenh.csv"
    rules = load_derivation_rules()
    merged, loan_df, _trace, _exc, stats = convert_quikbenh_loan_history_from_pactg(
        pactg_path,
        cw_map=cw,
        rules=rules,
        ploan_path=ploan_path,
        output_dir=str(report_dir),
        existing_benh_path=str(existing) if existing.is_file() else None,
    )
    out_path = out_dir / "quikbenh.csv"
    write_quikbenh_csv(merged, str(out_path))
    print(f"Wrote {out_path} ({len(merged)} rows)")
    print(
        f"Loan emit: {stats.get('emit_passed')} PACTG rows + "
        f"{stats.get('seed_emit', 0)} opening seeds / {stats.get('policy_count')} policies"
    )
    print(f"Type-8 preserved: {stats.get('existing_type8_rows')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
