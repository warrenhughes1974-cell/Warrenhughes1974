"""Issue #59 — validate quikridr MUWCLASS is rate-key codes, not status mistranslations."""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RIDR = ROOT / "QLA_Migration" / "Output" / "quikridr.csv"

# Status mistranslations that must not appear on MUWCLASS after v57.83
FORBIDDEN = {"55", "41", "56"}
# T was N→T (boolean) corruption; after fix N→NS so bare T should be rare (true LifePRO T only)
SAMPLE_EXPECT = {
    "011208260C": "SM",  # LifePRO S
    "011208334C": "SM",  # LifePRO S
    "011207563C": "NS",  # LifePRO Q → NS
}


def main() -> int:
    if not RIDR.is_file():
        print(f"FAIL: missing {RIDR}")
        return 1
    rows = list(csv.DictReader(RIDR.open(encoding="utf-8-sig", newline="")))
    phase1 = [r for r in rows if (r.get("MPHASE") or "").strip() in ("1", "01")]
    uw = Counter((r.get("MUWCLASS") or "").strip() for r in phase1)
    bad = {k: uw[k] for k in FORBIDDEN if uw.get(k)}
    print(f"Issue #59 MUWCLASS validation (phase1={len(phase1)})")
    print("  MUWCLASS counts:", dict(uw.most_common()))
    ok = True
    if bad:
        print("  FAIL: forbidden status-code UW values present:", bad)
        ok = False
    else:
        print("  OK: no 55/41/56 on MUWCLASS")
    by_pol = {}
    for r in phase1:
        by_pol[(r.get("MPOLICY") or "").strip()] = (r.get("MUWCLASS") or "").strip()
    for pol, expect in SAMPLE_EXPECT.items():
        got = by_pol.get(pol)
        if got != expect:
            print(f"  FAIL: {pol} MUWCLASS={got!r} expected {expect!r}")
            ok = False
        else:
            print(f"  OK: {pol} MUWCLASS={got}")
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
