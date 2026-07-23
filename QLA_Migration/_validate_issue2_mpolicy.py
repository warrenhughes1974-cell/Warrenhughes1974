"""
Issue #2 validator — source POLICY_NUMBER + C, width 11, right-justified.

Usage:
  python QLA_Migration/_validate_issue2_mpolicy.py
  python QLA_Migration/_validate_issue2_mpolicy.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from qla_core.normalize_utils import format_qladmin_mpolicy  # noqa: E402
from tools.validators.validate_mpolicy_width import validate as validate_width  # noqa: E402

DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
DEFAULT_SOURCE = PROJECT_ROOT / "QLA_Migration" / "Source"

TRACE = [
    ("9010143726", "9010143726C"),
    ("9010148272", "9010148272C"),
    ("901222DC", "  901222DCC"),
    ("9014059", "   9014059C"),
    ("9014100C", "  9014100CC"),
]


def _read(path: Path) -> pd.DataFrame | None:
    if not path.is_file():
        return None
    df = pd.read_csv(path, dtype=str, encoding="latin-1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def _find_ppolc(source_dir: Path) -> Path | None:
    for name in (
        "PPOLC_PolicyMaster_Extract_20260630.csv",
        "PPOLC_PolicyMaster_Extract_20260102.csv",
        "PPOLC_PolicyMaster_Extract_20260530.csv",
    ):
        p = source_dir / name
        if p.is_file():
            return p
    for p in sorted(source_dir.glob("PPOLC*.csv")):
        return p
    return None


def validate_identity(output_dir: Path, source_dir: Path) -> list[str]:
    errors: list[str] = []
    mstr = _read(output_dir / "quikmstr.csv")
    if mstr is None or "MPOLICY" not in mstr.columns:
        return ["quikmstr.csv missing or has no MPOLICY"]

    keys = set(mstr["MPOLICY"].astype(str))
    print("\nTrace policies (must be present in quikmstr):")
    for lp, expected in TRACE:
        got = format_qladmin_mpolicy(lp)
        ok_fmt = got == expected
        ok_out = expected in keys
        print(f"  LP {lp} -> fmt {repr(got)} match_expected={ok_fmt} in_quikmstr={ok_out}")
        if not ok_fmt:
            errors.append(f"Formatter mismatch for {lp}: got {repr(got)} expected {repr(expected)}")
        if not ok_out:
            errors.append(f"Missing {repr(expected)} in quikmstr")

    # No classic strip-9 identity for standard 90xxxxxxxx sources
    strip9_style = [k for k in keys if k.strip().endswith("C") and len(k.strip()) == 10 and k.strip()[0] == "0"]
    # Allow short padded keys; flag exact old pattern 010......C (10 visible chars starting 010)
    old_numeric = [
        k for k in keys
        if len(k) == 11 and k[0] == " " and k.strip().startswith("010") and k.strip().endswith("C") and len(k.strip()) == 10
    ]
    # Stronger: exact former full-width keys like 010143726C (no leading space, len 10) should be gone
    legacy_10 = [k for k in keys if len(k) == 10]
    if legacy_10:
        errors.append(f"Found {len(legacy_10)} MPOLICY values with raw len 10 (expect 11)")
        print(f"  FAIL: {len(legacy_10)} keys still raw-len 10 (sample {legacy_10[:5]!r})")

    # Spot-check: majority of keys should start with 90 after strip
    stripped = [k.strip() for k in keys if k.strip()]
    start90 = sum(1 for k in stripped if k.startswith("90"))
    print(f"\nquikmstr keys starting with 90 (after strip): {start90} / {len(stripped)}")
    if start90 < len(stripped) * 0.9:
        errors.append(f"Fewer than 90% of quikmstr keys start with 90 (got {start90}/{len(stripped)})")

    # Cross-check a sample of PPOLC → quikmstr
    ppolc = _find_ppolc(source_dir)
    if ppolc is not None:
        src = _read(ppolc)
        if src is not None and "POLICY_NUMBER" in src.columns:
            sample = src["POLICY_NUMBER"].astype(str).str.strip().head(200)
            missing = 0
            for lp in sample:
                if not lp or lp.startswith("----"):
                    continue
                exp = format_qladmin_mpolicy(lp)
                if exp and exp not in keys:
                    missing += 1
            print(f"PPOLC sample (200) missing from quikmstr: {missing}")
            if missing > 5:
                errors.append(f"PPOLC→quikmstr identity gaps: {missing} of first 200")

    # MEMOKEY width if present
    memo = _read(output_dir / "quikmemo.csv")
    if memo is not None and "MEMOKEY" in memo.columns:
        vals = [str(v) for v in memo["MEMOKEY"] if str(v).strip()]
        bad = [v for v in vals if len(v) != 11]
        print(f"quikmemo MEMOKEY width!=11: {len(bad)} / {len(vals)}")
        if bad:
            errors.append(f"MEMOKEY width violations: {len(bad)}")

    # Must not look like old strip9 for the main numeric example
    if "010143726C" in keys or " 010143726C" in keys:
        errors.append("Legacy strip-9 key 010143726C still present")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Issue #2 MPOLICY validation")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    args = ap.parse_args()
    out = args.output_dir.resolve()
    src = args.source_dir.resolve()

    print("=" * 72)
    print("ISSUE #2 VALIDATION — source + C, width 11")
    print(f"Output: {out}")
    print("=" * 72)

    rc = validate_width(out)
    errors = validate_identity(out, src)

    print("\n" + "=" * 72)
    if rc != 0 or errors:
        for e in errors:
            print(f"FAIL — {e}")
        print("OVERALL: FAIL")
        print("=" * 72)
        return 1
    print("OVERALL: PASS")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
