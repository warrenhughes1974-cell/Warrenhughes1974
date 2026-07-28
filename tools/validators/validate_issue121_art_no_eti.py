"""
Issue #121 — Annual Renewable Term must not emit ETI (MSTATUS/MPHSTAT 44).

Usage:
  python tools/validators/validate_issue121_art_no_eti.py
  python tools/validators/validate_issue121_art_no_eti.py --publish-test-validation
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
sys.path.insert(0, str(PROJECT_ROOT))

from qla_core.issue121_art_no_eti import ART_QL_PLANS, is_art_ql_plan  # noqa: E402

SCRIPT_VERSION = "1.0"
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"

# Defect traces (were ETI) + sibling controls + permanent ETI control
TRACE = (
    ("9010764158C", "5667AT", "22"),  # Active+LE → Active
    ("9010780202C", "5667AT", "22"),  # Active/RI/LE → Active
    ("9010761450C", "5667AT", "54"),  # T/LP/LE → Lapsed
    ("9010516211C", "5646AT", "54"),  # sibling ART — stay Lapsed
    ("9010916282C", "57ATCR", "54"),  # sibling ART CR — stay Lapsed
)


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Issue #121 ART no ETI")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--publish-test-validation", action="store_true")
    args = ap.parse_args()

    mstr_path = args.output_dir / "quikmstr.csv"
    ridr_path = args.output_dir / "quikridr.csv"
    if not mstr_path.exists() or not ridr_path.exists():
        print(f"FAIL: missing quikmstr/quikridr under {args.output_dir}")
        return 1

    with mstr_path.open(newline="", encoding="utf-8", errors="replace") as f:
        mrows = {_n(r.get("MPOLICY")): r for r in csv.DictReader(f)}
    with ridr_path.open(newline="", encoding="utf-8", errors="replace") as f:
        ridr = list(csv.DictReader(f))

    art_p1 = [
        r
        for r in ridr
        if is_art_ql_plan(_n(r.get("MPLAN"))) and _n(r.get("MPHASE")) in ("1", "01", "")
    ]
    art_pols = {_n(r.get("MPOLICY")) for r in art_p1}
    print(f"validate_issue121_art_no_eti.py v{SCRIPT_VERSION}")
    print(f"output: {args.output_dir}")
    print(f"ART QL plans: {sorted(ART_QL_PLANS)}")
    print(f"ART phase-1 coverages: {len(art_p1)} policies={len(art_pols)}")

    by_plan = Counter(_n(r.get("MPLAN")) for r in art_p1)
    print(f"by plan: {dict(by_plan)}")

    eti_mstr = []
    for pol in sorted(art_pols):
        m = mrows.get(pol)
        if not m:
            print(f"FAIL: ART policy missing from quikmstr: {pol}")
            return 1
        if _n(m.get("MSTATUS")) == "44":
            eti_mstr.append(pol)

    eti_ridr = [
        r for r in art_p1 if _n(r.get("MPHSTAT")) == "44"
    ]

    st_counts = Counter(_n(mrows[p].get("MSTATUS")) for p in art_pols)
    print(f"ART MSTATUS counts: {dict(st_counts)}")
    print(f"ART MSTATUS=44 (ETI): {len(eti_mstr)}")
    print(f"ART MPHSTAT=44: {len(eti_ridr)}")

    print("trace:")
    for pol, plan, expect in TRACE:
        m = mrows.get(pol)
        cov = [
            r
            for r in art_p1
            if _n(r.get("MPOLICY")) == pol and _n(r.get("MPLAN")) == plan
        ]
        if not m or not cov:
            print(f"  {pol} / {plan}: NOT FOUND")
            continue
        st = _n(m.get("MSTATUS"))
        mph = _n(cov[0].get("MPHSTAT"))
        ok = st == expect and mph != "44" and (mph == expect or expect == "22")
        # Active 22: MPHSTAT may be 22 from benefit A (inherit blocks copying 22)
        if expect == "22":
            ok = st == "22" and mph == "22"
        elif expect == "54":
            ok = st == "54" and mph == "54"
        print(
            f"  {pol} MPLAN={plan} MSTATUS={st} MPHSTAT={mph} "
            f"expect={expect} {'OK' if ok else 'FAIL'}"
        )
        if not ok:
            eti_mstr.append(f"TRACE_FAIL:{pol}")

    # Non-ART ETI must still exist (regression: do not wipe permanent ETI)
    non_art_eti = [
        pol
        for pol, m in mrows.items()
        if _n(m.get("MSTATUS")) == "44" and pol not in art_pols
    ]
    print(f"non-ART MSTATUS=44 (control population): {len(non_art_eti)}")
    if len(non_art_eti) < 1:
        print("FAIL: expected some non-ART ETI policies to remain")
        return 1

    fails = [p for p in eti_mstr if not str(p).startswith("TRACE_FAIL")]
    trace_fails = [p for p in eti_mstr if str(p).startswith("TRACE_FAIL")]
    if fails or eti_ridr or trace_fails:
        print(
            f"FAIL: ART ETI remain mstr={len(fails)} ridr={len(eti_ridr)} "
            f"trace_fails={len(trace_fails)}"
        )
        for p in fails[:10]:
            print(f"  - mstr ETI {p}")
        for r in eti_ridr[:10]:
            print(
                f"  - ridr ETI {_n(r.get('MPOLICY'))} "
                f"MPLAN={_n(r.get('MPLAN'))} MPHSTAT={_n(r.get('MPHSTAT'))}"
            )
        return 1

    print("PASS: zero ART ETI; traces OK; non-ART ETI preserved")
    if args.publish_test_validation:
        tv = args.output_dir / "Test_Validation"
        tv.mkdir(parents=True, exist_ok=True)
        for name in ("quikmstr.csv", "quikridr.csv"):
            shutil.copy2(args.output_dir / name, tv / name)
        stamp = tv / f"_issue121_publish_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        stamp.write_text("Issue #121 validator PASS — published quikmstr+quikridr\n", encoding="utf-8")
        print(f"Published to {tv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
