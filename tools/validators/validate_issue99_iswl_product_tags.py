"""
Issue #99 — ISWL quikplan MKTG / PRODUCT / HLOB = ISWLFE.

Usage:
  python tools/validators/validate_issue99_iswl_product_tags.py
  python tools/validators/validate_issue99_iswl_product_tags.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from qla_core.cso_mortality_crosswalk import (
    ISWL_MPLAN_ALLOWLIST,
    ISWL_PRODUCT_TAG,
    ISWL_PRODUCT_TAG_FIELDS,
    is_iswl_mplan,
)

SCRIPT_VERSION = "1.0"
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
EXPECTED_ROW_COUNT = 141
NON_ISWL_PRODUCT_BASELINE = {
    "03": 51,
    "12": 17,
    "10": 10,
    "07": 10,
    "CF": 9,
    "08": 8,
    "13": 8,
    "09": 5,
    "19": 4,
    "70": 4,
    "06": 3,
    "05": 3,
    "11": 1,
}


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Issue #99 ISWL quikplan product tags")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Directory containing quikplan.csv",
    )
    args = parser.parse_args()

    plan_path = args.output_dir / "quikplan.csv"
    if not plan_path.exists():
        print(f"FAIL: missing {plan_path}")
        return 1

    rows = _load_csv(plan_path)
    errors: list[str] = []

    if len(rows) != EXPECTED_ROW_COUNT:
        errors.append(f"row count {len(rows)} != expected {EXPECTED_ROW_COUNT}")

    iswl_rows = [r for r in rows if is_iswl_mplan(_n(r.get("PLAN")))]
    if len(iswl_rows) != len(ISWL_MPLAN_ALLOWLIST):
        errors.append(
            f"ISWL plan count {len(iswl_rows)} != allowlist {len(ISWL_MPLAN_ALLOWLIST)}"
        )

    missing_plans = sorted(ISWL_MPLAN_ALLOWLIST - {_n(r.get("PLAN")) for r in iswl_rows})
    if missing_plans:
        errors.append(f"missing ISWL plans in quikplan: {', '.join(missing_plans)}")

    for row in iswl_rows:
        plan = _n(row.get("PLAN"))
        for col in ISWL_PRODUCT_TAG_FIELDS:
            val = _n(row.get(col))
            if val != ISWL_PRODUCT_TAG:
                errors.append(f"{plan}: {col}={val!r} expected {ISWL_PRODUCT_TAG!r}")

    non_iswl = [r for r in rows if not is_iswl_mplan(_n(r.get("PLAN")))]
    if len(non_iswl) != EXPECTED_ROW_COUNT - len(ISWL_MPLAN_ALLOWLIST):
        errors.append(f"non-ISWL count {len(non_iswl)} unexpected")

    for row in non_iswl:
        plan = _n(row.get("PLAN"))
        for col in ISWL_PRODUCT_TAG_FIELDS:
            if _n(row.get(col)) == ISWL_PRODUCT_TAG:
                errors.append(f"non-ISWL {plan}: {col} must not be {ISWL_PRODUCT_TAG!r}")

    from collections import Counter

    product_counts = Counter(_n(r.get("PRODUCT")) for r in non_iswl)
    for code, expected in NON_ISWL_PRODUCT_BASELINE.items():
        if product_counts.get(code, 0) != expected:
            errors.append(
                f"non-ISWL PRODUCT count {code}: got {product_counts.get(code, 0)} "
                f"expected {expected}"
            )
    if product_counts.get(ISWL_PRODUCT_TAG, 0) != 0:
        errors.append("non-ISWL rows must not carry PRODUCT=ISWLFE")

    evidence_dir = PROJECT_ROOT / "Issue_Log_Items" / "Issue_99" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / "issue99_iswl_product_tag_validation.csv"
    with evidence_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["PLAN", "MKTG", "PRODUCT", "HLOB", "IS_ISWL"])
        for row in rows:
            plan = _n(row.get("PLAN"))
            if is_iswl_mplan(plan) or plan in ("1658CS", "1659C2", "920ADB"):
                w.writerow([
                    plan,
                    _n(row.get("MKTG")),
                    _n(row.get("PRODUCT")),
                    _n(row.get("HLOB")),
                    "Y" if is_iswl_mplan(plan) else "N",
                ])

    print(f"Issue #99 validator v{SCRIPT_VERSION}")
    print(f"quikplan: {plan_path}")
    print(f"ISWL plans tagged: {len(iswl_rows)}")
    print(f"Evidence: {evidence_path}")

    if errors:
        print("RESULT: FAIL")
        for err in errors[:20]:
            print(f"  - {err}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more")
        return 1

    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
