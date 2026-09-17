"""Issue #169 -- scope the QuikTvs rows that must be added for 5667AT.

Confirms, before any write:
  1. the QuikTvs.csv column list (so the patch can clone rows field-for-field)
  2. the (AGE, CNTL) footprint of the real ST grid vs the QuikNps footprint --
     the terminal-reserve grid must cover every address the net premium uses
  3. exactly which (GENDER, UWCLASS, AGE, CNTL, EFFDATE) keys already exist,
     so the patch can be duplicate-safe and idempotent
  4. that every TV cell on the plan is .00 (so cloning cannot move a real value)
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RATES = ROOT / "QLA_Migration" / "Output" / "rates"
PLAN = "5667AT"


def load(table):
    with (RATES / f"{table}.csv").open(encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh)
        return rd.fieldnames, [r for r in rd if r["PLAN"] == PLAN]


def main() -> int:
    tv_cols, tvs = load("QuikTvs")
    np_cols, nps = load("QuikNps")

    print("QuikTvs.csv columns:")
    print(f"  {tv_cols}")
    print("QuikNps.csv columns:")
    print(f"  {np_cols}")
    print(f"  identical layout apart from the factor prefix: "
          f"{[c for c in tv_cols if not c.startswith('TV')] == [c for c in np_cols if not c.startswith('NP')]}")

    print()
    print("Non-key field values on the plan (must be uniform for a safe clone):")
    for col in ("BAND", "ISSCNTRY", "ISSUEST"):
        if col in tv_cols:
            vals = {r[col] for r in tvs}
            print(f"  QuikTvs {col}: {sorted(vals)}")
        if col in np_cols:
            vals = {r[col] for r in nps}
            print(f"  QuikNps {col}: {sorted(vals)}")

    print()
    print("Every TV cell on the plan is .00?")
    bad = [r for r in tvs
           if any((r.get(f"TV{i}") or "").strip() not in ("", ".00") for i in range(10))]
    print(f"  rows with a non-.00 cell: {len(bad)}  -> "
          f"{'safe to clone (zeros only)' if not bad else 'STOP -- real values present'}")

    tv_addr = defaultdict(set)   # (gender, uwclass, effdate) -> {(age, cntl)}
    for r in tvs:
        tv_addr[(r["GENDER"], r["UWCLASS"], r["EFFDATE"])].add((r["AGE"], r["CNTL"]))
    np_addr = defaultdict(set)
    for r in nps:
        np_addr[(r["GENDER"], r["UWCLASS"], r["EFFDATE"])].add((r["AGE"], r["CNTL"]))

    print()
    print("Existing QuikTvs address sets:")
    for k in sorted(tv_addr):
        print(f"  {k}  rows={len(tv_addr[k])}")
    print("Existing QuikNps address sets:")
    for k in sorted(np_addr):
        print(f"  {k}  rows={len(np_addr[k])}")

    st_m = tv_addr[("M", "ST", "19950101")]
    st_f = tv_addr[("F", "ST", "19950101")]
    print()
    print(f"Real ST template grid: M={len(st_m)} addresses, F={len(st_f)}, "
          f"identical footprint={st_m == st_f}")
    ages = sorted({a for a, _ in st_m})
    print(f"  ages {ages[0]}..{ages[-1]} ({len(ages)} ages)")
    per_age = defaultdict(set)
    for a, c in st_m:
        per_age[a].add(c)
    widths = {len(v) for v in per_age.values()}
    print(f"  CNTL blocks per age: min={min(widths)} max={max(widths)} "
          f"(varies because the grid runs to attained age 100)")
    for a in (ages[0], "22", "39", ages[-1]):
        if a in per_age:
            print(f"    AGE={a}: CNTL {sorted(per_age[a])}")

    print()
    print("Does the ST template cover every QuikNps address? (must be YES)")
    for k in sorted(np_addr):
        gender = k[0]
        template = st_m if gender == "M" else st_f
        missing = np_addr[k] - template
        print(f"  {k}: uncovered={len(missing)}"
              f"{'' if not missing else '  ' + str(sorted(missing)[:6])}")

    print()
    print("Rows the patch would add (clone ST template to the missing keys),")
    print("skipping any address that already exists:")
    total = 0
    for gender in ("M", "F"):
        template = st_m if gender == "M" else st_f
        for uw in ("ST", "PR"):
            for eff in ("19000101", "19950101"):
                have = tv_addr.get((gender, uw, eff), set())
                add = template - have
                if add:
                    total += len(add)
                    print(f"  {gender}/{uw} @ {eff}: +{len(add)} "
                          f"(already had {len(have)})")
    print(f"  TOTAL rows to add: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
