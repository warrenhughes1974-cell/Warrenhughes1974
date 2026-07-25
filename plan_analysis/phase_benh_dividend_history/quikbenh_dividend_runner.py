"""Issue #114 — emit QuikBenh dividend history from PACTG + PPBENTYP (CLI runner)."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qla_core.issue21_open_item_decisions import resolve_ppbentyp_extract_path
from qla_core.lifepro_source_resolver import resolve_table_source
from qla_core.quikbenh_dividend_history_converter import (
    convert_quikbenh_dividend_history,
    load_dividend_rules,
    write_quikbenh_csv,
)


def _load_crosswalk(path: Path) -> dict[str, str]:
    m: dict[str, str] = {}
    if not path.is_file():
        return m
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            old = str(row.get("Old_Value", "")).strip()
            new = str(row.get("New_Value", "")).strip()
            if old and new:
                m[old] = new
    return m


def main() -> int:
    ap = argparse.ArgumentParser(description="Issue #114 QuikBenh dividend history emit")
    ap.add_argument(
        "--write-output",
        action="store_true",
        help="write QLA_Migration/Output/quikbenh.csv (otherwise dry run)",
    )
    args = ap.parse_args()

    src_dir = ROOT / "QLA_Migration" / "Source"
    out_dir = ROOT / "QLA_Migration" / "Output"
    reports_dir = ROOT / "QLA_Migration" / "Reports"
    cw_path = ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
    phase_dir = ROOT / "plan_analysis" / "phase_benh_dividend_history"

    pactg_path, label = resolve_table_source(str(src_dir), "quikbenh")
    if not pactg_path:
        print("FAIL: no PACTG extract found")
        return 1
    print(f"PACTG source: {pactg_path} ({label})")

    ppbentyp_path = resolve_ppbentyp_extract_path(str(src_dir))
    if not ppbentyp_path:
        print("FAIL: no PPBENTYP extract found (required for lifetime dividend totals)")
        return 1
    print(f"PPBENTYP source: {ppbentyp_path}")

    cw = _load_crosswalk(cw_path)
    existing = out_dir / "quikbenh.csv"
    merged, dividend_df, plug_df, exceptions_df, stats = convert_quikbenh_dividend_history(
        pactg_path,
        ppbentyp_path,
        cw_map=cw,
        rules=load_dividend_rules(),
        output_dir=str(phase_dir),
        existing_benh_path=str(existing) if existing.is_file() else None,
        reports_dir=str(reports_dir),
    )

    print(
        f"Layer A: {len(dividend_df)} PACTG dividend rows / "
        f"{stats.get('layer_a_policies')} policies / "
        f"${stats.get('layer_a_dollars', 0):,.2f}"
    )
    print(
        f"Layer B: {len(plug_df)} conversion adjustments / "
        f"${stats.get('plug_dollars', 0):,.2f}"
    )
    print(
        f"Reconciled ${stats.get('reconciled_dollars', 0):,.2f} of "
        f"${stats.get('lifetime_target_dollars', 0):,.2f} across "
        f"{stats.get('lifetime_target_policies')} policies"
    )
    print(f"Exceptions: {len(exceptions_df)} (see {reports_dir})")
    print(
        f"Preserved non-dividend rows: {stats.get('existing_preserved_rows')} "
        f"(of {stats.get('existing_rows')} existing)"
    )

    if args.write_output:
        write_quikbenh_csv(merged, str(existing))
        print(f"Wrote {existing} ({len(merged)} rows)")
    else:
        print(f"DRY RUN — would write {len(merged)} rows. Re-run with --write-output.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
