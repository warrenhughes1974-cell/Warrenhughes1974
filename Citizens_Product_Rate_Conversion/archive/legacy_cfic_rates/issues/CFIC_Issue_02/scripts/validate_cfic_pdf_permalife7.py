"""Validate CFIC PDF extract vs Access PermaLife7 reference CSV."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # CFIC_Rates
STAGING = ROOT / "extracted_pdf_rates" / "staging"
ACCESS = ROOT / "extracted" / "PermaLife7AdultBefore.csv"
REPORT = ROOT / "Issue_Log" / "CFIC_Issue_02" / "evidence" / "cfic_issue02_pdf_validation.csv"

TOL = 0.06  # premium tolerance (OCR + Access float)


def load_access() -> dict[tuple[str, str, str], dict]:
    lookup: dict[tuple[str, str, str], dict] = {}
    with ACCESS.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sex = row["Sex"][0].upper()
            uw = "NS" if row["Smoker"].strip().lower() == "no" else "SM"
            key = (sex, uw, row["Age"].strip())
            lookup[key] = row
    return lookup


def load_staging(plan: str) -> list[dict[str, str]]:
    plan_dir = STAGING / plan
    rows: list[dict[str, str]] = []
    for path in sorted(plan_dir.glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as f:
            rows.extend(csv.DictReader(f))
    return rows


def fnum(s: str) -> float | None:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default="P7MN")
    args = parser.parse_args()

    access = load_access()
    staging = load_staging(args.plan.upper())
    if not staging:
        raise SystemExit(f"No staging rows for {args.plan}")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    checks = []
    pass_n = 0
    for row in staging:
        age = row["age"]
        if int(age) < 18:
            continue
        key = (row["gender"], row["uwclass"], age)
        ref = access.get(key)
        if not ref:
            continue
        for field, ref_col in [
            ("rate_under_100k", "RateUnder100K"),
            ("rate_over_100k", "RateOver100K"),
            ("cash_value_10", "CashValueIn10"),
            ("cash_value_20", "CashValueIn20"),
            ("cash_value_65", "CashValueAt65"),
            ("paid_up_10", "PaidUpIn10"),
            ("paid_up_20", "PaidUpIn20"),
            ("paid_up_65", "PaidUpAt65"),
        ]:
            got = fnum(row.get(field, ""))
            exp = fnum(ref.get(ref_col, ""))
            if got is None and exp is None:
                status = "SKIP"
            elif got is None or exp is None:
                status = "FAIL"
            elif field.startswith("rate_"):
                status = "PASS" if abs(got - exp) <= TOL else "FAIL"
            else:
                status = "PASS" if int(round(got)) == int(round(exp)) else "FAIL"
            if status == "PASS":
                pass_n += 1
            checks.append(
                {
                    "plan": args.plan,
                    "gender": row["gender"],
                    "uwclass": row["uwclass"],
                    "age": age,
                    "field": field,
                    "extracted": row.get(field, ""),
                    "expected": ref.get(ref_col, ""),
                    "status": status,
                }
            )

    with REPORT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["plan", "gender", "uwclass", "age", "field", "extracted", "expected", "status"],
        )
        writer.writeheader()
        writer.writerows(checks)

    total = len(checks)
    fail = sum(1 for c in checks if c["status"] == "FAIL")
    print(f"Validation: {pass_n}/{total} PASS, {fail} FAIL -> {REPORT}")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
