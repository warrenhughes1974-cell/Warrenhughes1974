"""Validate reserve staging vs Access illustration checkpoints."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
STAGING_ROOT = ROOT / "extracted_reserve" / "staging"
ACCESS_ADULT = ROOT / "extracted" / "PermaLife7AdultBefore.csv"
EVIDENCE = SCRIPT_DIR.parent / "evidence"

# Access milestone columns keyed by (policy_year for age-18 issue)
ACCESS_MILESTONES = {
    10: ("CashValueIn10", "PaidUpIn10"),
    20: ("CashValueIn20", "PaidUpIn20"),
    47: ("CashValueAt65", "PaidUpAt65"),
}


def load_staging(plan: str) -> list[dict[str, str]]:
    path = STAGING_ROOT / plan.upper() / "reserve_grid.csv"
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_access_row(age: str, sex: str, smoker: str) -> dict[str, str] | None:
    if not ACCESS_ADULT.exists():
        return None
    with ACCESS_ADULT.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Age"] == age and row["Sex"] == sex and row["Smoker"] == smoker:
                return row
    return None


def compare(plan: str, gender: str, uwclass: str, issue_age: str = "18") -> list[dict]:
    rows = load_staging(plan)
    sex = "Male" if gender == "M" else "Female"
    smoker = "No" if uwclass == "NS" else "Yes"
    access = load_access_row(issue_age, sex, smoker)
    results = []
    subset = [r for r in rows if r["issue_age"] == issue_age and r["gender"] == gender and r["uwclass"] == uwclass]

    for pol_year, (cv_field, pu_field) in ACCESS_MILESTONES.items():
        res_row = next((r for r in subset if r["policy_year"] == str(pol_year)), None)
        if not res_row:
            results.append({
                "cfic_plan": plan,
                "issue_age": issue_age,
                "policy_year": pol_year,
                "field": "missing",
                "reserve": "",
                "access": "",
                "delta": "",
                "pass": "N",
            })
            continue
        for field, res_key, acc_field in (
            ("cash_value", "cash_value", cv_field),
            ("paid_up", "pup_ins", pu_field),
        ):
            try:
                res_val = float(res_row[res_key])
            except (ValueError, KeyError):
                res_val = None
            acc_val = float(access[acc_field]) if access and acc_field in access else None
            if res_val is None or acc_val is None:
                ok = "N"
                delta = ""
            else:
                delta = round(res_val - acc_val, 2)
                ok = "Y" if abs(delta) <= 1.0 else "N"
            results.append({
                "cfic_plan": plan,
                "issue_age": issue_age,
                "policy_year": pol_year,
                "field": field,
                "reserve": res_val,
                "access": acc_val,
                "delta": delta,
                "pass": ok,
            })
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default="P7MN")
    parser.add_argument("--gender", default="M")
    parser.add_argument("--uwclass", default="NS")
    parser.add_argument("--issue-age", default="18")
    args = parser.parse_args()

    results = compare(args.plan.upper(), args.gender.upper(), args.uwclass.upper(), args.issue_age)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    out_path = EVIDENCE / f"cfic_issue03_{args.plan.lower()}_validation.csv"
    fields = list(results[0].keys()) if results else []
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    passed = sum(1 for r in results if r["pass"] == "Y")
    print(f"Validation {passed}/{len(results)} PASS -> {out_path}")
    for r in results:
        status = "PASS" if r["pass"] == "Y" else "FAIL"
        print(f"  yr{r['policy_year']} {r['field']}: reserve={r['reserve']} access={r['access']} ({status})")


if __name__ == "__main__":
    main()
