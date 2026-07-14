"""
Issue #54 — validate QuikBenh loan history rows (PACTG → MBENTYP 10/11/12 + PLOAN opening seed).

Checks:
  1. quikbenh.csv schema (MPOLICY, MBENTYP, MDATE, MBEN)
  2. MBENTYP=8 row count preserved (#34 ISRR companion)
  3. Loan types 10/11/12 present; MBENTYP 20 absent (deferred)
  4. Opening seed on UAT policy 010822238C (20171220 / 8373.99)
  5. quikloan.csv row count unchanged (footer companion)
  6. Sample policy trace (010331768C / 9010331768)

Usage:
  python tools/validators/validate_issue54_quikbenh_loan_history.py
  python tools/validators/validate_issue54_quikbenh_loan_history.py --publish-test-validation
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_VERSION = "1.2"
ENGINE_VERSION = "v57.82"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
TEST_VALIDATION = DEFAULT_OUTPUT / "Test_Validation"
BASELINE_TYPE8 = 3657
EXPECTED_LOAN_ROWS_MIN = 37300
EXPECTED_LOAN_ROWS_MAX = 37600
EXPECTED_SEED_MIN = 550
EXPECTED_SEED_MAX = 565
EXPECTED_LOAN_POLICIES_MIN = 650
QUIKLOAN_BASELINE_ROWS = 356
SAMPLE_MPOLICY = "010331768C"
UAT_SEED_MPOLICY = "010822238C"
UAT_SEED_MDATE = "20171220"
UAT_SEED_MBEN = "8373.99"
UAT_CURRENT_BALANCE = 9731.08
UAT_FIRST_BALANCE_TOL = 0.02
LOAN_TYPES = frozenset({"10", "11", "12"})
SCHEMA = ["MPOLICY", "MBENTYP", "MDATE", "MBEN"]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [{k.strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def validate(
    output_dir: Path,
    *,
    publish_test_validation: bool = False,
) -> int:
    print("=" * 72)
    print(
        f"ISSUE #54 QUIKBENH LOAN HISTORY VALIDATION "
        f"(script v{SCRIPT_VERSION}, engine {ENGINE_VERSION})"
    )
    print("=" * 72)

    errors: list[str] = []
    warnings: list[str] = []

    benh_path = output_dir / "quikbenh.csv"
    if not benh_path.is_file():
        errors.append(f"Missing quikbenh.csv: {benh_path}")
        _report(errors, warnings)
        return 1

    rows = _read_csv(benh_path)
    if not rows:
        errors.append("quikbenh.csv is empty")
        _report(errors, warnings)
        return 1

    header = list(rows[0].keys())
    if header != SCHEMA:
        errors.append(f"Schema mismatch: header={header} expected={SCHEMA}")
    else:
        print(f"OK: quikbenh schema ({len(SCHEMA)} fields)")

    type_counts = Counter(r.get("MBENTYP", "") for r in rows)
    type8 = type_counts.get("8", 0)
    loan_rows = sum(type_counts.get(t, 0) for t in LOAN_TYPES)
    type20 = type_counts.get("20", 0)

    print(f"OK: quikbenh.csv rows={len(rows)} MBENTYP counts={dict(type_counts)}")

    if type8 != BASELINE_TYPE8:
        errors.append(f"MBENTYP=8 count={type8} expected preserved baseline {BASELINE_TYPE8}")
    else:
        print(f"OK: MBENTYP=8 preserved ({type8} rows)")

    if loan_rows < EXPECTED_LOAN_ROWS_MIN or loan_rows > EXPECTED_LOAN_ROWS_MAX:
        errors.append(
            f"Loan-type rows (10/11/12)={loan_rows} outside expected "
            f"{EXPECTED_LOAN_ROWS_MIN}–{EXPECTED_LOAN_ROWS_MAX}"
        )
    else:
        print(f"OK: loan history rows (10/11/12)={loan_rows}")

    loan_pols = {r.get("MPOLICY", "").strip() for r in rows if r.get("MBENTYP", "") in LOAN_TYPES}
    if len(loan_pols) < EXPECTED_LOAN_POLICIES_MIN:
        errors.append(
            f"Loan-history policies={len(loan_pols)} expected >= {EXPECTED_LOAN_POLICIES_MIN}"
        )
    else:
        print(f"OK: loan-history policies={len(loan_pols)}")

    if type20:
        errors.append(f"MBENTYP=20 present ({type20} rows) — deferred per Issue #54 scope")
    else:
        print("OK: no MBENTYP=20 rows (deferred)")

    for t in ("10", "11", "12"):
        if type_counts.get(t, 0) == 0:
            errors.append(f"Missing MBENTYP={t} loan rows")

    bad_mpolicy = [r for r in rows if len(r.get("MPOLICY", "")) != 10]
    if bad_mpolicy:
        errors.append(f"MPOLICY width violations: {len(bad_mpolicy)} row(s)")
    else:
        print("OK: all MPOLICY values are 10 characters")

    bad_date = [r for r in rows if r.get("MDATE", "") and not r["MDATE"].isdigit()]
    if bad_date:
        errors.append(f"MDATE not YYYYMMDD: {len(bad_date)} row(s)")
    else:
        print("OK: MDATE YYYYMMDD format")

    # Opening seed assert — 010822238C
    uat_seeds = [
        r
        for r in rows
        if r.get("MPOLICY", "").strip() == UAT_SEED_MPOLICY
        and r.get("MBENTYP", "") == "10"
        and r.get("MDATE", "") == UAT_SEED_MDATE
    ]
    if not uat_seeds:
        errors.append(
            f"Missing opening seed for {UAT_SEED_MPOLICY}: "
            f"expected MBENTYP=10 MDATE={UAT_SEED_MDATE}"
        )
    else:
        amt = uat_seeds[0].get("MBEN", "")
        if amt != UAT_SEED_MBEN:
            errors.append(
                f"Opening seed amount for {UAT_SEED_MPOLICY}: got {amt} expected {UAT_SEED_MBEN}"
            )
        else:
            print(
                f"OK: opening seed {UAT_SEED_MPOLICY} "
                f"{UAT_SEED_MDATE} / type 10 / ${UAT_SEED_MBEN}"
            )

    # Balance close: forward net of type effects should equal QuikLoan current
    # (QLAdmin Balance after first row ≈ first amount when chain closes)
    uat_loan_rows = [
        r
        for r in rows
        if r.get("MPOLICY", "").strip() == UAT_SEED_MPOLICY
        and r.get("MBENTYP", "") in LOAN_TYPES
    ]
    uat_loan_rows.sort(key=lambda r: (r.get("MDATE", ""), r.get("MBENTYP", "")))
    if uat_loan_rows:
        fwd = 0.0
        for r in uat_loan_rows:
            try:
                amt = float(r.get("MBEN", "") or 0)
            except ValueError:
                amt = 0.0
            t = r.get("MBENTYP", "")
            fwd += amt if t in ("10", "11") else -amt
        if abs(fwd - UAT_CURRENT_BALANCE) > UAT_FIRST_BALANCE_TOL:
            errors.append(
                f"{UAT_SEED_MPOLICY} forward Benh net={fwd:.2f} "
                f"expected QuikLoan {UAT_CURRENT_BALANCE:.2f}"
            )
        else:
            print(
                f"OK: {UAT_SEED_MPOLICY} forward Benh net={fwd:.2f} "
                f"matches QuikLoan {UAT_CURRENT_BALANCE:.2f}"
            )
        # Implied Balance on first row under QLAdmin backward formula
        first_amt = float(uat_loan_rows[0].get("MBEN", "") or 0)
        later = fwd - (
            first_amt
            if uat_loan_rows[0].get("MBENTYP") in ("10", "11")
            else -first_amt
        )
        implied_first_bal = UAT_CURRENT_BALANCE - later
        if abs(implied_first_bal - first_amt) > UAT_FIRST_BALANCE_TOL:
            errors.append(
                f"{UAT_SEED_MPOLICY} implied first Balance={implied_first_bal:.2f} "
                f"expected ~{first_amt:.2f}"
            )
        else:
            print(
                f"OK: {UAT_SEED_MPOLICY} implied first Balance={implied_first_bal:.2f} "
                f"(~ seed {first_amt:.2f})"
            )

    # Fleet seed count — type-10 rows include PACTG 0411 + synthetic seeds
    type10 = type_counts.get("10", 0)
    pactg_type10_expected_min = 3500
    if type10 < pactg_type10_expected_min:
        errors.append(f"MBENTYP=10 count={type10} unexpectedly low (expect PACTG + seeds)")
    seed_estimate = type10 - 3562
    if seed_estimate < EXPECTED_SEED_MIN or seed_estimate > EXPECTED_SEED_MAX:
        warnings.append(
            f"Estimated opening seeds (type10 - 3562 PACTG)={seed_estimate}; "
            f"expected {EXPECTED_SEED_MIN}–{EXPECTED_SEED_MAX}"
        )
    else:
        print(f"OK: estimated opening seeds={seed_estimate}")

    sample = [
        r
        for r in rows
        if r.get("MPOLICY", "").strip() == SAMPLE_MPOLICY and r.get("MBENTYP", "") in LOAN_TYPES
    ]
    if not sample:
        warnings.append(f"No loan rows for sample MPOLICY={SAMPLE_MPOLICY}")
    else:
        sample_types = Counter(r.get("MBENTYP", "") for r in sample)
        print(f"OK: sample {SAMPLE_MPOLICY} loan rows={len(sample)} types={dict(sample_types)}")

    loan_path = output_dir / "quikloan.csv"
    if loan_path.is_file():
        loan_count = len(_read_csv(loan_path))
        if loan_count != QUIKLOAN_BASELINE_ROWS:
            warnings.append(
                f"quikloan.csv rows={loan_count} (baseline {QUIKLOAN_BASELINE_ROWS}) — "
                "Issue #54 should not modify quikloan"
            )
        else:
            print(f"OK: quikloan.csv unchanged ({loan_count} rows)")
    else:
        warnings.append(f"quikloan.csv absent: {loan_path}")

    return _finish(errors, warnings, benh_path, publish_test_validation)


def _report(errors: list[str], warnings: list[str]) -> None:
    for w in warnings:
        print(f"WARN: {w}")
    if errors:
        print("-" * 72)
        print("RESULT: FAIL")
        for e in errors:
            print(f"FAIL: {e}")


def _finish(
    errors: list[str],
    warnings: list[str],
    benh_path: Path,
    publish_test_validation: bool,
) -> int:
    for w in warnings:
        print(f"WARN: {w}")

    if errors:
        print("-" * 72)
        print("RESULT: FAIL")
        for e in errors:
            print(f"FAIL: {e}")
        return 1

    if publish_test_validation:
        dest = TEST_VALIDATION / "quikbenh.csv"
        TEST_VALIDATION.mkdir(parents=True, exist_ok=True)
        shutil.copy2(benh_path, dest)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        manifest = TEST_VALIDATION / "manifest.txt"
        manifest.write_text(
            "\n".join(
                [
                    f"Published: {stamp}",
                    "Issue: Issue_54",
                    f"Source: {benh_path.parent}",
                    "Tables:",
                    "  - quikbenh.csv",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"OK: published quikbenh.csv to {dest}")

    print("-" * 72)
    print("RESULT: PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Issue #54 QuikBenh loan history")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument(
        "--publish-test-validation",
        action="store_true",
        help="copy quikbenh.csv to Output/Test_Validation/ on PASS",
    )
    args = ap.parse_args()
    return validate(args.output_dir, publish_test_validation=args.publish_test_validation)


if __name__ == "__main__":
    sys.exit(main())
