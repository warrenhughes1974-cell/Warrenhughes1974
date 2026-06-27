"""
QLAdmin MPOLICY fixed-width validation (Issue #25 / v57.30).

Verifies every emitted MPOLICY field is exactly 10 characters (leading-space padded).

Usage:
  python QLA_Migration/_validate_mpolicy_width.py
  python QLA_Migration/_validate_mpolicy_width.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"

ISSUE25_SAMPLES = {
    "9018510": "   018510C",
    "9018495B": "  018495BC",
    "9018499C": "  018499CC",
}

ISSUE25_PADDED = set(ISSUE25_SAMPLES.values())

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
    "quikplan.csv",
    "quikclms.csv",
    "quikclmp.csv",
    "quikloan.csv",
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
    print(f"MPOLICY WIDTH VALIDATION (Issue #25, script v{SCRIPT_VERSION})")
    print(f"Output: {output_dir}")
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

        values = [str(v) for v in df[col].tolist() if str(v).strip() and str(v).strip().lower() not in ("nan", "none")]
        if not values:
            continue

        t_short = sum(1 for v in values if len(v) < 10)
        t_long = sum(1 for v in values if len(v) > 10)
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
    print(f"Shorter than 10 characters:    {short_count}  (must be 0)")
    print(f"Longer than 10 characters:     {long_count}  (must be 0)")
    print(f"Blank / skipped:               {blank_count}")

    print("\nPer-table summary:")
    for tbl, stats in sorted(table_stats.items()):
        flag = "OK" if stats["short"] == 0 and stats["long"] == 0 else "FAIL"
        print(f"  [{flag}] {tbl}: {stats['rows']} values, short={stats['short']}, long={stats['long']}")

    if affected_tables:
        errors.append(f"Width violations in: {', '.join(affected_tables)}")

    print("\nIssue #25 expected padded values (cross-table consistency):")
    core_tables = ["quikmstr.csv", "quikclid.csv", "quikridr.csv", "quikplan.csv"]
    for padded in sorted(ISSUE25_PADDED):
        print(f"\n  Target: {repr(padded)}")
        for tbl in core_tables:
            path = output_dir / tbl
            df = _read_csv(path)
            if df is None or _mpolicy_col(df) is None:
                print(f"    {tbl}: (no file or no MPOLICY column)")
                continue
            col = _mpolicy_col(df)
            hits = df[df[col] == padded]
            print(f"    {tbl}: {len(hits)} row(s)")

    print("\nBefore/after samples (Issue #25 LifePRO -> QLAdmin MPOLICY):")
    for lifepro, expected in ISSUE25_SAMPLES.items():
        print(f"  LifePRO {lifepro} -> {repr(expected)} (len={len(expected)})")

    mstr = _read_csv(output_dir / "quikmstr.csv")
    if mstr is not None and _mpolicy_col(mstr):
        col = _mpolicy_col(mstr)
        for expected in ISSUE25_PADDED:
            row = mstr[mstr[col] == expected]
            if len(row):
                print(f"  quikmstr sample row MPOLICY={repr(row.iloc[0][col])}")

    clid = _read_csv(output_dir / "quikclid.csv")
    ridr = _read_csv(output_dir / "quikridr.csv")
    if mstr is not None and clid is not None and ridr is not None:
        mcol = _mpolicy_col(mstr)
        ccol = _mpolicy_col(clid)
        rcol = _mpolicy_col(ridr)
        if mcol and ccol and rcol:
            m_set = set(mstr[mcol].unique())
            c_set = set(clid[ccol].unique())
            r_set = set(ridr[rcol].unique())
            for padded in ISSUE25_PADDED:
                in_m = padded in m_set
                in_c = padded in c_set
                in_r = padded in r_set
                if not (in_m and in_c and in_r):
                    errors.append(
                        f"Inconsistent MPOLICY {repr(padded)} across master/child: "
                        f"quikmstr={in_m}, quikclid={in_c}, quikridr={in_r}"
                    )
                else:
                    print(f"\n  Consistency PASS for {repr(padded)} in quikmstr, quikclid, quikridr")

    print("\n" + "=" * 72)
    if short_count or long_count or errors:
        for e in errors:
            print(f"FAIL — {e}")
        print("OVERALL: FAIL")
        print("=" * 72)
        return 1

    print("OVERALL: PASS - all MPOLICY fields are exactly 10 characters")
    print("=" * 72)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate QLAdmin MPOLICY fixed-width 10-char emit")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()
    return validate(args.output_dir.resolve())


if __name__ == "__main__":
    sys.exit(main())
