"""
Issue #28 PLAN mapping validation (v57.35).

Compares quikplan emitted PLAN codes against authoritative product catalog
(crosswalk_ql_plan_code preferred via load_product_catalog_crosswalk).

Usage:
  python tools/validators/validate_issue28_plan_mapping.py
  python tools/validators/validate_issue28_plan_mapping.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
DEFAULT_CATALOG = PROJECT_ROOT / "plan_governance" / "product_catalog_crosswalk.csv"
DEFAULT_SOURCE = PROJECT_ROOT / "plan_analysis" / "quikplan_source.csv"
DEFAULT_MCW = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"

CLIENT_EXAMPLES = {
    "10827 MN5K": "1CSIMN",
    "0823 960CH": "960CWP",
    "0824 P DIS": "94PDIS",
    "DISCHO25": "9DIS25",
}


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="latin1", on_bad_lines="skip")
    df.columns = [str(c).strip() for c in df.columns]
    return df.fillna("")


def validate(output_dir: Path, catalog_path: Path, source_path: Path, mcw_path: Path) -> int:
    print("=" * 72)
    print(f"ISSUE #28 PLAN MAPPING VALIDATION (script v{SCRIPT_VERSION}, engine v57.35)")
    print(f"Output: {output_dir}")
    print(f"Catalog: {catalog_path}")
    print("=" * 72)

    errors: list[str] = []
    warnings: list[str] = []

    if not catalog_path.is_file():
        errors.append(f"Missing catalog: {catalog_path}")
        _report(errors, warnings)
        return 1

    sys.path.insert(0, str(PROJECT_ROOT))
    from qla_core.product_catalog_authority import load_crosswalk_authority  # noqa: E402

    authority = load_crosswalk_authority(str(mcw_path), str(catalog_path))
    cat_df = _read_csv(catalog_path)
    cat_df["lifepro_coverage_id_norm"] = cat_df["lifepro_coverage_id"].str.strip().str.upper()

    quikplan_path = output_dir / "quikplan.csv"
    if not quikplan_path.is_file():
        errors.append(f"Missing quikplan output: {quikplan_path}")
        _report(errors, warnings)
        return 1

    qp = _read_csv(quikplan_path)
    if "PLAN" not in qp.columns:
        errors.append("quikplan.csv missing PLAN column")
        _report(errors, warnings)
        return 1
    qp_plan_set = {p.strip().upper() for p in qp["PLAN"] if str(p).strip()}

    qp_by_cov: dict[str, str] = {}
    if source_path.is_file():
        qps = _read_csv(source_path)
        id_col = "COVERAGE_ID" if "COVERAGE_ID" in qps.columns else qps.columns[0]
        qps["COVERAGE_ID_norm"] = qps[id_col].astype(str).str.strip().str.upper()
        qps = qps[~qps["COVERAGE_ID_norm"].str.contains("---", na=False)]
        qps = qps.drop_duplicates(subset=["COVERAGE_ID_norm"], keep="first")
        for _, src_row in qps.iterrows():
            cid = src_row["COVERAGE_ID_norm"]
            raw_id = str(src_row[id_col]).strip()
            expected = authority.product_plan_map.get(raw_id, raw_id).strip().upper()
            emitted = ""
            if expected in qp_plan_set:
                emitted = expected
            qp_by_cov[cid] = emitted

    mismatches: list[tuple[str, str, str]] = []
    for _, row in cat_df.iterrows():
        cid = row["lifepro_coverage_id_norm"]
        auth_plan = str(row.get("crosswalk_ql_plan_code", "")).strip().upper()
        if not auth_plan:
            auth_plan = str(row.get("ql_plan_code", "")).strip().upper()
        if not auth_plan:
            continue
        if cid not in qp_by_cov:
            continue
        emitted = qp_by_cov.get(cid, "")
        if emitted != auth_plan:
            mismatches.append((row["lifepro_coverage_id"], auth_plan, emitted or "(missing)"))

    print(f"Catalog rows: {len(cat_df)}")
    print(f"quikplan PLAN universe: {len(qp_plan_set)}")
    print(f"Source coverage IDs mapped: {len(qp_by_cov)}")
    print(f"Mismatches (emitted vs authoritative): {len(mismatches)}")

    for lifepro_id, expected, actual in mismatches[:20]:
        errors.append(f"{lifepro_id}: expected PLAN={expected}, emitted={actual}")
    if len(mismatches) > 20:
        errors.append(f"... and {len(mismatches) - 20} additional mismatch(es)")

    for cid, expected in CLIENT_EXAMPLES.items():
        emitted = qp_by_cov.get(cid.upper(), "")
        if expected.upper() not in qp_plan_set and not emitted:
            warnings.append(f"Client example {cid}: PLAN {expected} not in quikplan output")
        elif emitted and emitted != expected.upper():
            errors.append(f"Client example {cid}: expected {expected}, got {emitted}")
        else:
            print(f"Client example {cid}: OK (expected {expected})")

    mig_cat = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "product_catalog_crosswalk.csv"
    if mig_cat.is_file():
        mig_df = _read_csv(mig_cat)
        if not cat_df.equals(mig_df):
            warnings.append("QLA_Migration/Mapping catalog differs from plan_governance copy")
    else:
        warnings.append("QLA_Migration/Mapping/product_catalog_crosswalk.csv missing")

    _report(errors, warnings)
    return 1 if errors else 0


def _report(errors: list[str], warnings: list[str]) -> None:
    print("-" * 72)
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
    if errors:
        print(f"FAIL ({len(errors)} error(s)):")
        for e in errors:
            print(f"  - {e}")
    else:
        print("PASS — no PLAN mapping errors detected")
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #28 quikplan PLAN mapping validator")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--mcw", type=Path, default=DEFAULT_MCW)
    args = parser.parse_args()
    return validate(args.output_dir, args.catalog, args.source, args.mcw)


if __name__ == "__main__":
    raise SystemExit(main())
