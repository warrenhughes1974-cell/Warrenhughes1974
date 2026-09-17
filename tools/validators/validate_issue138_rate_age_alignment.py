"""
Issue 138 — QuikGps age axis must line up with the issue age that was rated.

LifePRO PAAGERAT SEQ is a 1-based ordinal, so the rate carried on SEQ n belongs to
issue age n-1. Filed a year high, QLAdmin reads a neighbouring age or nothing at all
and the premium screen renders zeros.

The check is deliberately anchored outside our own rate emit: quikridr.MPREM comes
from LifePRO ANN_PREM_PER_UNIT (Issue 88), so a policy issued at MAGE must find its
own premium at grid age MAGE. A plan that instead matches at MAGE+1 or MAGE-1 is
still shifted.

Plans whose premium is not a plain per-unit grid read (banded / ISWL) match at no
offset; they are reported UNTESTABLE, not failed, because this check cannot see them.

Usage:
  python tools/validators/validate_issue138_rate_age_alignment.py
  python tools/validators/validate_issue138_rate_age_alignment.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
EVIDENCE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_138" / "evidence"

OFFSETS = (-1, 0, 1)
MIN_POLICIES = 5      # below this a plan cannot outvote noise
MATCH_TOLERANCE = 0.005
ALIGNED_SHARE = 0.80  # share of testable policies that must hit offset 0


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def load_grid(rates_dir: Path, attained_age_plans: set | None = None) -> dict:
    """(PLAN, GENDER, UWCLASS) -> {age: rate}.

    Issue 140 moved attained-age plans onto the slot axis: AGE is the fixed key 00
    and the age is CNTL*10 + column. Issue-age plans still carry the age in AGE and
    the first duration in column 0. The business fact under test is unchanged - a
    policy issued at MAGE must find its own premium at age MAGE.
    """
    path = rates_dir / "QuikGps.csv"
    slot_plans = attained_age_plans or set()
    grid: dict = defaultdict(dict)
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for r in csv.DictReader(f):
            plan = _n(r.get("PLAN"))
            key = (plan, _n(r.get("GENDER")), _n(r.get("UWCLASS")))
            age = _n(r.get("AGE"))
            cntl = _n(r.get("CNTL"))
            if plan in slot_plans:
                if not cntl.isdigit():
                    continue
                for i in range(10):
                    value = _n(r.get(f"GP{i}"))
                    if not value:
                        continue
                    try:
                        rate = round(float(value), 2)
                    except ValueError:
                        continue
                    if rate:
                        grid[key][int(cntl) * 10 + i] = rate
                continue
            value = _n(r.get("GP0"))
            if not value or not age.isdigit():
                continue
            try:
                grid[key][int(age)] = round(float(value), 2)
            except ValueError:
                continue
    return grid


def score_plans(grid: dict, quikridr: Path) -> dict:
    """Per plan, how many policies find their own premium at each age offset."""
    hits: dict = defaultdict(lambda: defaultdict(int))
    totals: dict = defaultdict(int)
    with quikridr.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for p in csv.DictReader(f):
            key = (_n(p.get("MPLAN")), _n(p.get("MSEX")), _n(p.get("MUWCLASS")))
            if key not in grid:
                continue
            try:
                age = int(_n(p.get("MAGE")))
                prem = round(float(_n(p.get("MPREM"))), 2)
            except ValueError:
                continue
            if prem <= 0:
                continue
            totals[key[0]] += 1
            ages = grid[key]
            for off in OFFSETS:
                rate = ages.get(age + off)
                if rate is not None and abs(rate - prem) < MATCH_TOLERANCE:
                    hits[key[0]][off] += 1
    return {
        plan: {"policies": totals[plan], **{str(o): hits[plan][o] for o in OFFSETS}}
        for plan in sorted(totals)
    }


def classify(row: dict) -> str:
    total = row["policies"]
    at0, up, down = row["0"], row["1"], row["-1"]
    if total < MIN_POLICIES:
        return "SKIPPED_TOO_FEW"
    if at0 == 0 and up == 0 and down == 0:
        return "UNTESTABLE"
    if at0 >= up and at0 >= down and at0 >= total * ALIGNED_SHARE:
        return "ALIGNED"
    if max(up, down) > at0:
        return "MISALIGNED"
    return "PARTIAL"


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Issue 138 QuikGps age alignment")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()

    rates_dir = args.output_dir / "rates"
    quikridr = args.output_dir / "quikridr.csv"
    if not (rates_dir / "QuikGps.csv").is_file():
        print(f"FAIL: missing {rates_dir / 'QuikGps.csv'}")
        return 1
    if not quikridr.is_file():
        print(f"FAIL: missing {quikridr}")
        return 1

    sys.path.insert(0, str(PROJECT_ROOT))
    from qla_core.attained_age_grid_fill import load_manifest

    slot_plans = load_manifest(str(PROJECT_ROOT)).get("QuikGps", set())
    scored = score_plans(load_grid(rates_dir, slot_plans), quikridr)
    verdicts = {plan: classify(row) for plan, row in scored.items()}
    misaligned = [p for p, v in verdicts.items() if v == "MISALIGNED"]
    partial = [p for p, v in verdicts.items() if v == "PARTIAL"]
    counts: dict = defaultdict(int)
    for v in verdicts.values():
        counts[v] += 1

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "issue138_age_alignment_summary.json").write_text(
        json.dumps(
            {
                "plans_scored": len(scored),
                "verdicts": dict(sorted(counts.items())),
                "misaligned_plans": misaligned,
                "partial_plans": partial,
                "result": "PASS" if not misaligned else "FAIL",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    with (EVIDENCE / "issue138_age_alignment_by_plan.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.writer(f)
        w.writerow(["PLAN", "POLICIES", "MATCH_AT_MINUS1", "MATCH_AT_0", "MATCH_AT_PLUS1", "VERDICT"])
        for plan, row in scored.items():
            w.writerow([plan, row["policies"], row["-1"], row["0"], row["1"], verdicts[plan]])

    print("Issue 138 rate age alignment validator")
    print(f"  attained-age plans read on the slot axis: {len(slot_plans)}")
    print(f"  plans scored: {len(scored)}")
    for verdict in sorted(counts):
        print(f"    {verdict}: {counts[verdict]}")

    if misaligned:
        print("\nRESULT: FAIL")
        for plan in misaligned:
            row = scored[plan]
            print(
                f"  - {plan}: {row['policies']} policies, matches "
                f"-1={row['-1']} 0={row['0']} +1={row['1']}"
            )
        return 1

    if partial:
        print(f"\n  note: {len(partial)} plan(s) match at age but below the "
              f"{ALIGNED_SHARE:.0%} share ({', '.join(sorted(partial)[:8])})")

    print("\n  OK: no plan rates a policy better at a neighbouring age")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
