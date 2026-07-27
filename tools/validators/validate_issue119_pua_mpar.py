"""
Issue #119 — PUA coverages must have quikridr.MPAR = 0 (non-participating).

Usage:
  python tools/validators/validate_issue119_pua_mpar.py
  python tools/validators/validate_issue119_pua_mpar.py --publish-test-validation
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_VERSION = "1.0"
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
TRACE = (
    ("9010310404C", "1960PA"),
    ("9010150910C", "221EPA"),
    ("9010360290C", "1708PA"),
    ("9010391228C", "1970PA"),
    ("9010143726C", "221END"),  # non-PUA control — must stay MPAR=1
)


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _is_pua_code(mplan: str) -> bool:
    return len(mplan) == 6 and mplan.upper().endswith("PA")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Issue #119 PUA MPAR=0")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--publish-test-validation", action="store_true")
    args = ap.parse_args()

    ridr_path = args.output_dir / "quikridr.csv"
    if not ridr_path.exists():
        print(f"FAIL: missing {ridr_path}")
        return 1

    with ridr_path.open(newline="", encoding="utf-8", errors="replace") as f:
        ridr = list(csv.DictReader(f))

    pua = [r for r in ridr if _is_pua_code(_n(r.get("MPLAN")))]
    bad = [r for r in pua if _n(r.get("MPAR")) != "0"]
    mpar_counts = Counter(_n(r.get("MPAR")) for r in pua)

    print(f"validate_issue119_pua_mpar.py v{SCRIPT_VERSION}")
    print(f"output: {args.output_dir}")
    print(f"PUA rows: {len(pua)}")
    print(f"PUA MPAR counts: {dict(mpar_counts)}")
    print("trace:")
    for pol, plan in TRACE:
        hits = [
            r
            for r in ridr
            if _n(r.get("MPOLICY")) == pol and _n(r.get("MPLAN")) == plan
        ]
        if not hits:
            # fall back to any row for control policies
            hits = [r for r in ridr if _n(r.get("MPOLICY")) == pol]
        if not hits:
            print(f"  {pol} / {plan}: NOT FOUND")
            continue
        r = hits[0]
        print(
            f"  {pol} phase={_n(r.get('MPHASE'))} MPLAN={_n(r.get('MPLAN'))} "
            f"MPAR={_n(r.get('MPAR'))}"
        )

    if not pua:
        print("FAIL: no PUA rows found")
        return 1
    if bad:
        print(f"FAIL: {len(bad)} PUA rows with MPAR!=0")
        for r in bad[:10]:
            print(
                f"  - {_n(r.get('MPOLICY'))} phase={_n(r.get('MPHASE'))} "
                f"MPLAN={_n(r.get('MPLAN'))} MPAR={_n(r.get('MPAR'))}"
            )
        return 1

    # Control: participating base must still be 1
    ctrl = [
        r
        for r in ridr
        if _n(r.get("MPOLICY")) == "9010143726C" and _n(r.get("MPHASE")) in ("1", "01")
    ]
    if ctrl and _n(ctrl[0].get("MPAR")) != "1":
        print(
            f"FAIL: non-PUA control 9010143726C MPAR={_n(ctrl[0].get('MPAR'))!r} "
            f"(expected 1)"
        )
        return 1

    print("PASS")
    if args.publish_test_validation:
        tv = args.output_dir / "Test_Validation"
        tv.mkdir(parents=True, exist_ok=True)
        dest = tv / "quikridr.csv"
        shutil.copy2(ridr_path, dest)
        with (tv / "manifest.txt").open("a", encoding="utf-8") as f:
            f.write(
                f"{datetime.now().isoformat(timespec='seconds')} Issue_119 "
                f"published quikridr.csv ({len(ridr)} rows)\n"
            )
        print(f"Published {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
