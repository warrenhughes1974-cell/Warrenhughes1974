"""CFIC Issue #01 Wave 1 — validate P7MN staging vs Access illustration checkpoints."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STAGING = ROOT / "extracted_green_sheets" / "staging" / "P7MN"
ACCESS = ROOT / "extracted" / "PermaLife7AdultBefore.csv"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence"

CHECKPOINTS = [
    ("cash_value", 10, "CashValueIn10"),
    ("cash_value", 20, "CashValueIn20"),
    ("paid_up", 10, "PaidUpIn10"),
    ("paid_up", 20, "PaidUpIn20"),
]


def load_access(age: int, sex: str = "Male", smoker: str = "No") -> dict[str, str]:
    with ACCESS.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["Age"]) == age and row["Sex"] == sex and row["Smoker"] == smoker:
                return row
    raise KeyError(f"No Access row for age={age} sex={sex} smoker={smoker}")


def load_staging(age: int) -> list[dict[str, str]]:
    path = STAGING / f"{age}.csv"
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compare_age(age: int) -> list[dict[str, str]]:
    access = load_access(age)
    staging = load_staging(age)
    by_dur = {int(r["duration"]): r for r in staging}
    results = []
    for field, dur, access_col in CHECKPOINTS:
        st = by_dur.get(dur, {})
        got = st.get(field, "")
        exp = access.get(access_col, "")
        try:
            got_n = float(got) if got else None
            exp_n = float(exp) if exp else None
            delta = abs(got_n - exp_n) if got_n is not None and exp_n is not None else None
            match = delta is not None and delta < 1.0
        except ValueError:
            delta = None
            match = got == exp
        results.append(
            {
                "issue_age": str(age),
                "duration": str(dur),
                "field": field,
                "expected": exp,
                "extracted": got,
                "delta": "" if delta is None else f"{delta:.4f}",
                "match": "PASS" if match else "FAIL",
                "confidence": st.get("extract_confidence", ""),
            }
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ages", default="18,30,50")
    args = parser.parse_args()
    ages = [int(a.strip()) for a in args.ages.split(",") if a.strip()]
    all_rows: list[dict[str, str]] = []
    for age in ages:
        try:
            all_rows.extend(compare_age(age))
        except FileNotFoundError as exc:
            print(f"SKIP age {age}: {exc}")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    out = EVIDENCE / "cfic_issue01_p7mn_validation.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()) if all_rows else [])
        if all_rows:
            w.writeheader()
            w.writerows(all_rows)
    passes = sum(1 for r in all_rows if r["match"] == "PASS")
    print(f"Validation: {passes}/{len(all_rows)} PASS -> {out}")
    for row in all_rows:
        print(
            f"  age {row['issue_age']} dur {row['duration']} {row['field']}: "
            f"got={row['extracted']} exp={row['expected']} {row['match']}"
        )


if __name__ == "__main__":
    main()
