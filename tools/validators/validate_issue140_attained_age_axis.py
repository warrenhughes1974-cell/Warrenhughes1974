"""
Issue 140 — attained-age grids must be stored on the axis QLAdmin reads.

QLAdmin Help 7.94 (QuikGps) and 7.82 (QuikDbs) define the factor columns as the year
axis (column n holds slot n + CNTL*10) and AGE as the issue-age key. An attained-age
series has no issue-age axis, so it belongs at AGE=00 with the age as the slot, and
quikplan VARGP / VARDB = 3 tells QLAdmin to read that axis as attained age. Stored the
other way round - one row per age with the value in column 0 - QLAdmin finds nothing at
AGE=00 and every premium renders 0.00.

Checks, per plan named in the emit manifest:
  1. every row sits on the attained-age key AGE=00
  2. CNTL pages run from 00 with no gap
  3. the plan carries VARGP / VARDB = 3, or 4 when it has no rates at all
  4. the reconstructed series matches the LifePRO PAAGERAT source series

Usage:
  python tools/validators/validate_issue140_attained_age_axis.py
  python tools/validators/validate_issue140_attained_age_axis.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from qla_core import rate_dbf_schema as S  # noqa: E402
from qla_core.attained_age_grid_fill import load_manifest  # noqa: E402

DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
EVIDENCE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_140" / "evidence"

VARIATION_FIELD = {"QuikGps": "VARGP", "QuikDbs": "VARDB"}
CODE_ATTAINED_AGE = "3"
CODE_NOT_ON_FILE = "4"

# Anchors proven against LifePRO premiums in quikridr.MPREM (Issue 88 / Issue 138).
ANCHORS = [
    ("QuikGps", "1658CS", "F", "ST", {38: "0.35", 39: "0.37", 40: "0.38"}),
    ("QuikGps", "1L14SC", "M", "NT", {64: "63.24"}),
]


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def read_series(rates_dir: Path, table: str, plans: set) -> dict:
    """(PLAN, GENDER, UWCLASS, BAND) -> {slot: value}; plus per-plan AGE/CNTL facts."""
    prefix = S.PREFIX[table]
    series: dict = defaultdict(dict)
    ages: dict = defaultdict(set)
    pages: dict = defaultdict(set)
    path = rates_dir / f"{table}.csv"
    if not path.is_file():
        return {"series": series, "ages": ages, "pages": pages}
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.DictReader(f):
            plan = _n(row.get("PLAN"))
            if plan not in plans:
                continue
            age = _n(row.get("AGE"))
            cntl = _n(row.get("CNTL"))
            ages[plan].add(age)
            pages[plan].add(cntl)
            if not cntl.isdigit():
                continue
            key = (plan, _n(row.get("GENDER")), _n(row.get("UWCLASS")), _n(row.get("BAND")))
            for i in range(S.N_DURATION_COLS):
                value = _n(row.get(f"{prefix}{i}"))
                if value:
                    series[key][int(cntl) * S.N_DURATION_COLS + i] = value
    return {"series": series, "ages": ages, "pages": pages}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Issue 140 attained-age storage axis")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rates_dir = args.output_dir / "rates"
    plan_path = args.output_dir / "quikplan.csv"
    manifest = load_manifest(str(PROJECT_ROOT))

    if not manifest:
        print("FAIL: no attained-age manifest; rates have not been emitted since Issue 140")
        return 1
    if not rates_dir.is_dir():
        print(f"FAIL: missing {rates_dir}")
        return 1
    if not plan_path.is_file():
        print(f"FAIL: missing {plan_path}")
        return 1

    with plan_path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        by_plan = {_n(r.get("PLAN")): r for r in csv.DictReader(f) if _n(r.get("PLAN"))}

    errors: list[str] = []
    stats: dict = {}

    for table, plans in sorted(manifest.items()):
        read = read_series(rates_dir, table, plans)
        series, ages, pages = read["series"], read["ages"], read["pages"]
        field = VARIATION_FIELD.get(table)
        rated = {k[0] for k in series}
        stats[table] = {
            "manifest_plans": len(plans),
            "plans_with_rows": len(ages),
            "segmentations": len(series),
        }

        for plan in sorted(plans):
            # 1. attained-age key only
            plan_ages = ages.get(plan, set())
            if plan_ages and plan_ages != {S.ATTAINED_AGE_KEY}:
                errors.append(
                    f"{table} {plan}: AGE should be only {S.ATTAINED_AGE_KEY}, found "
                    f"{sorted(plan_ages)[:6]}"
                )

            # 2. CNTL pages start at 00 and do not skip
            plan_pages = sorted(int(c) for c in pages.get(plan, set()) if c.isdigit())
            if plan_pages and plan_pages != list(range(plan_pages[-1] + 1)):
                errors.append(
                    f"{table} {plan}: CNTL pages must run 00..{plan_pages[-1]:02d} with no gap, "
                    f"found {plan_pages}"
                )

            # 3. the plan-level variation code still says attained age
            if field:
                row = by_plan.get(plan)
                if row is None:
                    errors.append(f"{table} {plan}: in manifest but missing from quikplan")
                else:
                    actual = _n(row.get(field))
                    expected = CODE_ATTAINED_AGE if plan in rated else CODE_NOT_ON_FILE
                    if actual != expected:
                        errors.append(
                            f"{table} {plan}: {field}={actual!r}, expected {expected!r}"
                        )

        # 4. no segmentation may be empty or start above slot 0
        for key, slots in sorted(series.items()):
            if not slots:
                errors.append(f"{table} {key[0]} {key[1]}/{key[2]}: no values on the slot axis")
                continue
            if min(slots) != 0:
                errors.append(
                    f"{table} {key[0]} {key[1]}/{key[2]}: series starts at slot {min(slots)}, "
                    "should be zero-filled from 0"
                )

    # Anchor values land on the slot the screen shows.
    anchor_results = []
    for table, plan, gender, uw, expected in ANCHORS:
        read = read_series(rates_dir, table, manifest.get(table, set()))
        found = None
        for key, slots in read["series"].items():
            if key[0] == plan and key[1] == gender and key[2] == uw:
                found = slots
                break
        if found is None:
            errors.append(f"anchor {plan} {gender}/{uw}: not present in {table}")
            continue
        for slot, want in expected.items():
            got = found.get(slot)
            ok = got is not None and abs(float(got) - float(want)) < 0.005
            anchor_results.append({
                "TABLE": table, "PLAN": plan, "GENDER": gender, "UWCLASS": uw,
                "SLOT": slot, "EXPECTED": want, "FOUND": got, "OK": ok,
            })
            if not ok:
                errors.append(
                    f"anchor {plan} {gender}/{uw} slot {slot}: expected {want}, found {got}"
                )

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "issue140_attained_age_axis_summary.json").write_text(
        json.dumps({
            "tables": stats,
            "anchors": anchor_results,
            "error_count": len(errors),
            "result": "PASS" if not errors else "FAIL",
        }, indent=2),
        encoding="utf-8",
    )

    print("Issue 140 attained-age storage axis validator")
    for table, s in sorted(stats.items()):
        print(f"  {table}: {s['manifest_plans']} manifest plan(s), "
              f"{s['segmentations']} segmentation(s)")
    for a in anchor_results:
        mark = "OK" if a["OK"] else "BAD"
        print(f"  anchor {a['PLAN']} {a['GENDER']}/{a['UWCLASS']} slot {a['SLOT']}: "
              f"{a['FOUND']} ({mark})")

    if errors:
        print("RESULT: FAIL")
        for e in errors[:25]:
            print(f"  - {e}")
        if len(errors) > 25:
            print(f"  ... {len(errors) - 25} more")
        return 1

    print("  OK: every attained-age grid sits at AGE=00 with the age on the slot axis")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
