"""
Issue A7 — quikplan VARGP / VARDB must describe the rate grid QLAdmin will read.

A plan left at 4 while its factor table holds rates makes QLAdmin show
"Values Not on File" and ignore the loaded grid; the reverse (a code pointing at
a table that was never emitted) is a dangling pointer.

Codes (Warren 2026-08-09):
  0 = level, 1 = varies by policy year, 2 = varies by issue age and year,
  3 = varies by attained age, 4 = no rate table on file.

Issue 140 (Warren approved 2026-08-09): an attained-age series now sits on the slot
axis, where it is shape-identical to a policy-year grid. Membership therefore comes
from the emit manifest and the shape rule covers everything else. Code 3 still has to
mean a real grid, so a manifest plan whose rates vanished must still fall back to 4.

Usage:
  python tools/validators/validate_issueA7_variation_codes.py
  python tools/validators/validate_issueA7_variation_codes.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from qla_core.attained_age_grid_fill import load_manifest  # noqa: E402
from qla_core.quikplan_rate_variation_flags import (  # noqa: E402
    CODE_ATTAINED_AGE,
    CODE_LEVEL,
    CODE_NOT_ON_FILE,
    VARIATION_CODE_SOURCES,
    classify_factor_grid,
    scan_factor_grid,
)

DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
EVIDENCE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_A" / "evidence"

# A missing DB grid means a level death benefit off INITVAL (Issue #74), not "no file".
NOT_ON_FILE_FALLBACK = {"VARDB": CODE_LEVEL}

TRACE_PLANS = {
    "1L14SC": {"VARGP": "3"},
    "5L01MA": {"VARGP": "2"},
    "265PUA": {"VARGP": "1", "VARDB": "2"},
    "A60MIR": {"VARDB": "2"},
}


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Issue A7 quikplan variation codes")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    plan_path = args.output_dir / "quikplan.csv"
    rates_dir = args.output_dir / "rates"
    if not plan_path.is_file():
        print(f"FAIL: missing {plan_path}")
        return 1
    if not rates_dir.is_dir():
        print(f"FAIL: missing {rates_dir} (Issue A7 needs the emitted grids)")
        return 1

    with plan_path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        rows = list(csv.DictReader(f))
    by_plan = {_n(r.get("PLAN")): r for r in rows if _n(r.get("PLAN"))}

    errors: list[str] = []
    counts: dict[str, Counter] = {}
    mismatches: list[dict] = []

    manifest = load_manifest(str(PROJECT_ROOT))

    for field_name, (table, prefix) in VARIATION_CODE_SOURCES.items():
        shapes = scan_factor_grid(str(rates_dir), table, prefix)
        slot_plans = manifest.get(table, set())
        counts[field_name] = Counter()
        for plan, row in sorted(by_plan.items()):
            shape = shapes.get(plan)
            if plan in slot_plans:
                expected = (
                    CODE_NOT_ON_FILE
                    if shape is None or shape.real_rows == 0
                    else CODE_ATTAINED_AGE
                )
            else:
                expected = classify_factor_grid(shape)
            if expected == CODE_NOT_ON_FILE and field_name in NOT_ON_FILE_FALLBACK:
                expected = NOT_ON_FILE_FALLBACK[field_name]
            actual = _n(row.get(field_name))
            counts[field_name][actual] += 1
            if actual != expected:
                mismatches.append({
                    "PLAN": plan,
                    "FIELD": field_name,
                    "ACTUAL": actual,
                    "EXPECTED": expected,
                    "FACTOR_ROWS": shape.real_rows if shape else 0,
                    "DISTINCT_AGES": len(shape.ages) if shape else 0,
                    "DURATION_SLOTS": len(shape.duration_slots) if shape else 0,
                })
                errors.append(
                    f"{plan}: {field_name}={actual!r} but {table} grid says {expected!r}"
                )

    for plan, expected_fields in TRACE_PLANS.items():
        row = by_plan.get(plan)
        if not row:
            errors.append(f"trace plan missing from quikplan: {plan}")
            continue
        for field_name, expected in expected_fields.items():
            actual = _n(row.get(field_name))
            if actual != expected:
                errors.append(f"trace {plan}: {field_name}={actual!r}, expected {expected!r}")

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    summary = {
        "quikplan_rows": len(rows),
        "vargp_distribution": dict(sorted(counts["VARGP"].items())),
        "vardb_distribution": dict(sorted(counts["VARDB"].items())),
        "mismatch_count": len(mismatches),
        "result": "PASS" if not errors else "FAIL",
    }
    (EVIDENCE / "issueA7_variation_code_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    if mismatches:
        with (EVIDENCE / "issueA7_variation_code_mismatches.csv").open(
            "w", newline="", encoding="utf-8"
        ) as f:
            w = csv.DictWriter(f, fieldnames=list(mismatches[0].keys()))
            w.writeheader()
            w.writerows(mismatches)

    print("Issue A7 variation code validator")
    print(f"  quikplan rows: {len(rows)}")
    print(f"  attained-age plans from manifest: "
          f"{ {t: len(p) for t, p in sorted(manifest.items())} }")
    print(f"  VARGP distribution: {summary['vargp_distribution']}")
    print(f"  VARDB distribution: {summary['vardb_distribution']}")

    if errors:
        print("RESULT: FAIL")
        for e in errors[:25]:
            print(f"  - {e}")
        if len(errors) > 25:
            print(f"  ... {len(errors) - 25} more")
        return 1

    print("  OK: every VARGP/VARDB matches its emitted factor grid")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
