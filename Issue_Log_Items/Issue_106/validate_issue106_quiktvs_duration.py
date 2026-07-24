"""Issue #106 — validate RV QuikTvs duration identity (LifePRO Dur N == QL Dur N)."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TVS = ROOT / "QLA_Migration" / "Output" / "rates" / "QuikTvs.csv"

# (plan, gender, age, uw or None, {dur: expected float})
PROOFS = [
    ("170858", "M", 17, None, {1: 0.0, 2: 8.76, 83: 1000.0}),
    ("17085M", "M", 17, None, {1: 0.0, 2: 8.76, 83: 1000.0}),
    ("170588", "M", 17, None, {1: 0.0, 2: 8.76, 83: 1000.0}),
    ("1659C2", "M", 17, "SM", {1: 1.0, 83: 978.0}),
    ("221END", "M", 17, None, {1: 0.0}),
    ("1960OL", "M", 17, None, {1: 4.0}),
]


def _load_slice(path: Path, plan: str, gender: str, age: int, uw: str | None) -> dict[int, str]:
    age_s = str(age).zfill(2)
    vals: dict[int, str] = {}
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            if r["PLAN"].strip() != plan:
                continue
            if r["GENDER"].strip() != gender:
                continue
            if r["AGE"].strip() != age_s:
                continue
            if uw is not None and r["UWCLASS"].strip() != uw:
                continue
            cntl = int(r["CNTL"])
            for i in range(10):
                v = (r.get(f"TV{i}") or "").strip()
                if v:
                    vals[cntl * 10 + i] = v
    return vals


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiktvs", type=Path, default=DEFAULT_TVS)
    args = ap.parse_args()
    if not args.quiktvs.is_file():
        print(f"FAIL: missing {args.quiktvs}")
        return 1

    failures = 0
    for plan, gender, age, uw, expect in PROOFS:
        vals = _load_slice(args.quiktvs, plan, gender, age, uw)
        print(f"=== {plan} {gender}/{age} uw={uw}")
        # Dur 0 must not hold the former Dur-1 nonzero for these proofs
        d0 = vals.get(0)
        if d0 is not None and float(d0) != 0.0:
            # GL85/CEN proofs: Dur0 should be blank after identity (source starts at 1)
            if plan in ("170858", "17085M", "170588", "1659C2", "221END", "1960OL"):
                print(f"  FAIL Dur0 unexpected nonzero/present: {d0}")
                failures += 1
        for dur, exp in expect.items():
            got = vals.get(dur)
            if got is None:
                print(f"  FAIL Dur{dur}: missing (expected {exp})")
                failures += 1
                continue
            if abs(float(got) - exp) > 0.001:
                print(f"  FAIL Dur{dur}: got {got} expected {exp}")
                failures += 1
            else:
                print(f"  PASS Dur{dur}={got}")

    print("OVERALL", "PASS" if failures == 0 else f"FAIL ({failures})")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
