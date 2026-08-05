"""
QLAdmin MPOLICY fixed-width validation (Issue #2 / v58.29).

Verifies every emitted MPOLICY field is exactly 11 characters (leading-space padded).
Supersedes Issue #25 width-10 contract.

Usage:
  python tools/validators/validate_mpolicy_width.py
  python tools/validators/validate_mpolicy_width.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "2.0"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
MPOLICY_WIDTH = 11

# Issue #2 samples: LifePRO source → QLA (source + C, rjust 11)
ISSUE2_SAMPLES = {
    "9010143726": "9010143726C",
    "901222DC": "  901222DCC",
    "9014059": "   9014059C",
    "9014100C": "  9014100CC",
}

ISSUE2_PADDED = set(ISSUE2_SAMPLES.values())

TABLES_WITH_MPOLICY = [
    "quikmstr.csv",
    "quikridr.csv",
    "quikclid.csv",
    "quikclnt.csv",
    "quikbenf.csv",
    "quikprmh.csv",
    "quikdvdp.csv",
    "quikdvpr.csv",
    "quikagts.csv",
    "quikclms.csv",
    "quikclmp.csv",
    "quikloan.csv",
    "quikbenh.csv",
    "QuikIsrr.csv",
    "QuikIswl.csv",
    "quikrmst.csv",
]


def _read_csv(path: Path) -> pd.DataFrame | None:
    if not path.is_file():
        return None
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def _mpolicy_col(df: pd.DataFrame) -> str | None:
    for c in df.columns:
        if c.upper() == "MPOLICY":
            return c
    return None


def validate(output_dir: Path) -> int:
    print("=" * 72)
    print(f"MPOLICY WIDTH VALIDATION (Issue #2, script v{SCRIPT_VERSION})")
    print(f"Output: {output_dir}")
    print(f"Required width: {MPOLICY_WIDTH}")
    print("=" * 72)

    total_checked = 0
    short_count = 0
    long_count = 0
    blank_count = 0
    affected_tables: list[str] = []
    table_stats: dict[str, dict] = {}
    errors: list[str] = []

    scan_paths: list[Path] = []
    for name in TABLES_WITH_MPOLICY:
        scan_paths.append(output_dir / name)
    staging = output_dir / "claims_uat_staging"
    if staging.is_dir():
        for name in ("quikclms.csv", "quikclmp.csv"):
            scan_paths.append(staging / name)

    for path in scan_paths:
        df = _read_csv(path)
        if df is None:
            continue
        col = _mpolicy_col(df)
        if not col:
            continue

        values = [
            str(v)
            for v in df[col].tolist()
            if str(v).strip() and str(v).strip().lower() not in ("nan", "none")
        ]
        if not values:
            continue

        t_short = sum(1 for v in values if len(v) < MPOLICY_WIDTH)
        t_long = sum(1 for v in values if len(v) > MPOLICY_WIDTH)
        t_blank = len(df[col]) - len(values)
        total_checked += len(values)
        short_count += t_short
        long_count += t_long
        blank_count += t_blank

        rel = path.relative_to(output_dir) if path.is_relative_to(output_dir) else path.name
        table_stats[str(rel)] = {
            "rows": len(values),
            "short": t_short,
            "long": t_long,
        }
        if t_short or t_long:
            affected_tables.append(str(rel))

    print(f"\nTotal MPOLICY fields checked: {total_checked}")
    print(f"Shorter than {MPOLICY_WIDTH} characters: {short_count}  (must be 0)")
    print(f"Longer than {MPOLICY_WIDTH} characters:  {long_count}  (must be 0)")
    print(f"Blank / skipped:               {blank_count}")

    print("\nPer-table summary:")
    for tbl, stats in sorted(table_stats.items()):
        flag = "OK" if stats["short"] == 0 and stats["long"] == 0 else "FAIL"
        print(f"  [{flag}] {tbl}: {stats['rows']} values, short={stats['short']}, long={stats['long']}")

    if affected_tables:
        errors.append(f"Width violations in: {', '.join(affected_tables)}")

    print("\nIssue #2 expected sample keys:")
    for lifepro, expected in ISSUE2_SAMPLES.items():
        print(f"  LifePRO {lifepro} -> {repr(expected)} (len={len(expected)})")

    mstr = _read_csv(output_dir / "quikmstr.csv")
    if mstr is not None and _mpolicy_col(mstr):
        col = _mpolicy_col(mstr)
        for expected in ISSUE2_PADDED:
            row = mstr[mstr[col] == expected]
            status = "FOUND" if len(row) else "MISSING"
            print(f"  quikmstr {repr(expected)}: {status}")
            if not len(row):
                errors.append(f"Missing sample MPOLICY {repr(expected)} in quikmstr")

    print("\n" + "=" * 72)
    if short_count or long_count or errors:
        for e in errors:
            print(f"FAIL — {e}")
        print("OVERALL: FAIL")
        print("=" * 72)
        return 1

    print(f"OVERALL: PASS - all MPOLICY fields are exactly {MPOLICY_WIDTH} characters")
    print("=" * 72)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate QLAdmin MPOLICY fixed-width 11-char emit (Issue #2)")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()
    return validate(args.output_dir.resolve())


if __name__ == "__main__":
    sys.exit(main())
