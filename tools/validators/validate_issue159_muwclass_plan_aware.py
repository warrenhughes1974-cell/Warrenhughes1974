"""Issue #159 — fail-closed: quikridr MUWCLASS is plan-aware (#118 form map).

Exit 1 if L10 smokers are ST, L14 N-class is 00, or UAT anchors drift.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output"
RIDR = OUT / "quikridr.csv"

sys.path.insert(0, str(ROOT))
from qla_core import rate_dbf_schema as S  # noqa: E402

UAT = {
    "9011189929C": "BL",
    "9011190516C": "SM",
    "9011193156C": "PR",
    "9011059291C": "ST",
    "9011052719C": "PR",
    "9011206462C": "NT",
    "9011208194C": "ST",
    "9011207210C": "PQ",
}

L10_FOCUS = ("1L1095", "1L10OD", "1L10PR")


def main() -> int:
    if not RIDR.is_file():
        print(f"FAIL: missing {RIDR}")
        return 1

    ok = True
    uat_got = {}
    l10_st_p1 = Counter()
    l14_00 = 0
    l10_st_all = 0
    n_ridr = 0
    non_l10_st = 0

    with RIDR.open(newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            n_ridr += 1
            pol = (r.get("MPOLICY") or "").strip()
            plan = (r.get("MPLAN") or "").strip()
            phase = (r.get("MPHASE") or "").strip()
            muw = (r.get("MUWCLASS") or "").strip()
            is_p1 = phase in ("1", "01", "1.0")
            if pol in UAT and is_p1:
                uat_got[pol] = muw
            if plan in S.L10_PLANS and muw == "ST":
                l10_st_all += 1
                if is_p1 and plan in L10_FOCUS:
                    l10_st_p1[plan] += 1
            if plan in S.L14_PLANS and muw == "00":
                l14_00 += 1
            if plan not in S.L10_PLANS and muw == "ST":
                non_l10_st += 1

    print(f"Issue #159 MUWCLASS plan-aware (rows={n_ridr})")

    for pol, expect in UAT.items():
        got = uat_got.get(pol)
        if got != expect:
            print(f"  FAIL: UAT {pol} MUWCLASS={got!r} expected {expect!r}")
            ok = False
        else:
            print(f"  OK: UAT {pol}={got}")

    for plan, n in l10_st_p1.items():
        print(f"  FAIL: {plan} phase-1 ST count={n} (L10 S must be SM)")
        ok = False
    if not l10_st_p1:
        print("  OK: 1L1095/1L10OD/1L10PR phase-1 ST count=0")

    if l14_00:
        print(f"  FAIL: 1L14SC MUWCLASS=00 count={l14_00} (N/Q/T/R must not collapse)")
        ok = False
    else:
        print("  OK: 1L14SC 00 count=0")

    if l10_st_all:
        print(f"  WARN: other L10_PLANS still have ST rows={l10_st_all} (riders; check if LifePRO S)")

    print(f"  INFO: non-L10 ST rows={non_l10_st} (must remain ST for form-sheet S)")
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
