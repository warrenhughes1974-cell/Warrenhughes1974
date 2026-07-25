"""
Issue #114 — validate QuikBenh dividend history (PACTG elections + PPBENTYP lifetime plug).

Reconciliation is checked against the PPBENTYP source, not against the converter's
own report, so the validator can disagree with the converter.

Checks:
  1. quikbenh.csv schema (MPOLICY, MBENTYP, MDATE, MBEN)
  2. Non-dividend types preserved at baseline (8=#34, 10/11/12=#54)
  3. Dividend types 1-5 present; no type outside 1-5 / 8 / 10-12
  4. MPOLICY width 11, MDATE YYYYMMDD, MBEN positive 2-decimal
  5. At most one conversion adjustment row (20171231) per policy
  6. Per-policy dividend total ties to PPBENTYP.DIVIDENDS_CREDITED for every
     converted policy, and every withheld policy is genuinely absent
  7. Exception report accounts for each unconverted policy

Usage:
  python tools/validators/validate_issue114_dividend_history.py
  python tools/validators/validate_issue114_dividend_history.py --publish-test-validation
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_VERSION = "1.0"
ENGINE_VERSION = "v58.36"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
DEFAULT_SOURCE = PROJECT_ROOT / "QLA_Migration" / "Source"
DEFAULT_REPORTS = PROJECT_ROOT / "QLA_Migration" / "Reports"
TEST_VALIDATION = DEFAULT_OUTPUT / "Test_Validation"

# Pre-Issue-#114 quikbenh baseline (v58.35 full batch)
BASELINE_PRESERVED = {"8": 3657, "10": 3562, "11": 14156, "12": 19135}
BASELINE_TOTAL_ROWS = 40510

DIVIDEND_TYPES = ("1", "2", "3", "4", "5")
PLUG_DATE = "20171231"
MPOLICY_WIDTH = 11
MONEY_TOL = 0.01
EXPECTED_DIVIDEND_ROWS_MIN = 2900
EXPECTED_DIVIDEND_POLICIES_MIN = 550


def _read_csv(path: Path) -> list[dict[str, str]]:
    """Values are stripped; MPOLICY is space-padded to 11 in QLAdmin output."""
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [{k.strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def _raw_mpolicy_widths(path: Path) -> Counter:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return Counter(
            (len(r.get("MPOLICY") or ""), (r.get("MBENTYP") or "").strip()) for r in reader
        )


def _money(val: str) -> float:
    s = str(val or "").strip().replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _load_source_lifetime(source_dir: Path) -> dict[str, float]:
    """PPBENTYP BA-row DIVIDENDS_CREDITED per MPOLICY, computed independently."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from qla_core.normalize_utils import format_qladmin_mpolicy

    matches = sorted(source_dir.glob("PPBENTYP_BenefitType_Extract*.csv"))
    if not matches:
        return {}

    csv.field_size_limit(10 ** 7)
    totals: dict[str, float] = defaultdict(float)
    with matches[-1].open(encoding="latin-1", newline="") as f:
        reader = csv.reader(f)
        header = [c.replace("\ufeff", "").strip().upper() for c in next(reader)]
        try:
            i_pol = header.index("POLICY_NUMBER")
            i_tc = header.index("TYPE_CODE")
            i_div = header.index("DIVIDENDS_CREDITED")
        except ValueError:
            return {}
        for row in reader:
            if len(row) < len(header):
                continue
            pol = row[i_pol].strip()
            if not pol or pol.startswith("---"):
                continue
            if row[i_tc].strip().upper() != "BA":
                continue
            amount = _money(row[i_div])
            if amount == 0:
                continue
            mpolicy = format_qladmin_mpolicy(pol).strip()
            if mpolicy:
                totals[mpolicy] += amount
    return {k: round(v, 2) for k, v in totals.items() if v > 0}


def validate(
    output_dir: Path,
    source_dir: Path,
    reports_dir: Path,
    *,
    publish_test_validation: bool = False,
) -> int:
    print("=" * 72)
    print(
        f"ISSUE #114 QUIKBENH DIVIDEND HISTORY VALIDATION "
        f"(script v{SCRIPT_VERSION}, engine {ENGINE_VERSION})"
    )
    print("=" * 72)

    errors: list[str] = []
    warnings: list[str] = []

    benh_path = output_dir / "quikbenh.csv"
    if not benh_path.is_file():
        print(f"FAIL: Missing quikbenh.csv: {benh_path}")
        print("RESULT: FAIL")
        return 1

    rows = _read_csv(benh_path)
    if not rows:
        print("FAIL: quikbenh.csv is empty")
        print("RESULT: FAIL")
        return 1

    header = list(rows[0].keys())
    expected_schema = ["MPOLICY", "MBENTYP", "MDATE", "MBEN"]
    if header != expected_schema:
        errors.append(f"Schema mismatch: header={header} expected={expected_schema}")
    else:
        print(f"OK: quikbenh schema ({len(expected_schema)} fields)")

    type_counts = Counter(r.get("MBENTYP", "") for r in rows)
    print(f"OK: quikbenh.csv rows={len(rows)} MBENTYP counts={dict(type_counts)}")

    # 2. Prior-issue rows preserved untouched
    preserved_ok = True
    for t, expected in BASELINE_PRESERVED.items():
        actual = type_counts.get(t, 0)
        if actual != expected:
            preserved_ok = False
            errors.append(f"MBENTYP={t} count={actual} expected preserved baseline {expected}")
    if preserved_ok:
        print(
            "OK: prior-issue rows preserved "
            f"(8={type_counts.get('8', 0)}, 10={type_counts.get('10', 0)}, "
            f"11={type_counts.get('11', 0)}, 12={type_counts.get('12', 0)})"
        )

    div_rows = [r for r in rows if r.get("MBENTYP", "") in DIVIDEND_TYPES]
    if not div_rows:
        errors.append("No dividend rows (MBENTYP 1-5) present — Issue #114 emit did not run")
        _report(errors, warnings)
        return 1

    allowed = set(DIVIDEND_TYPES) | set(BASELINE_PRESERVED)
    stray = {t: n for t, n in type_counts.items() if t not in allowed}
    if stray:
        errors.append(f"Unexpected MBENTYP values present: {stray}")

    if len(div_rows) < EXPECTED_DIVIDEND_ROWS_MIN:
        errors.append(
            f"Dividend rows={len(div_rows)} below expected minimum {EXPECTED_DIVIDEND_ROWS_MIN}"
        )
    else:
        print(
            f"OK: dividend rows (1-5)={len(div_rows)} "
            f"types={dict((t, type_counts.get(t, 0)) for t in DIVIDEND_TYPES)}"
        )

    if len(rows) != BASELINE_TOTAL_ROWS + len(div_rows):
        errors.append(
            f"Row arithmetic off: total={len(rows)} but baseline {BASELINE_TOTAL_ROWS} "
            f"+ dividend {len(div_rows)} = {BASELINE_TOTAL_ROWS + len(div_rows)}"
        )
    else:
        print(f"OK: additive only ({BASELINE_TOTAL_ROWS} + {len(div_rows)} = {len(rows)})")

    # 4. Field-level format — MPOLICY is space-padded, so measure it unstripped
    widths = _raw_mpolicy_widths(benh_path)
    bad_width = sum(n for (w, t), n in widths.items() if t in DIVIDEND_TYPES and w != MPOLICY_WIDTH)
    if bad_width:
        offenders = {w for (w, t) in widths if t in DIVIDEND_TYPES and w != MPOLICY_WIDTH}
        errors.append(
            f"MPOLICY width != {MPOLICY_WIDTH} on {bad_width} dividend row(s); "
            f"widths seen={sorted(offenders)}"
        )
    else:
        print(f"OK: dividend MPOLICY values are {MPOLICY_WIDTH} characters (padded)")

    bad_date = [
        r for r in div_rows
        if not (r.get("MDATE", "").isdigit() and len(r.get("MDATE", "")) == 8)
    ]
    if bad_date:
        errors.append(f"MDATE not YYYYMMDD on {len(bad_date)} dividend row(s)")
    else:
        print("OK: dividend MDATE YYYYMMDD format")

    bad_amt = [r for r in div_rows if _money(r.get("MBEN", "")) <= 0]
    if bad_amt:
        errors.append(f"Non-positive MBEN on {len(bad_amt)} dividend row(s)")
    else:
        print("OK: all dividend MBEN values positive")

    bad_dp = [r for r in div_rows if "." not in r.get("MBEN", "")
              or len(r.get("MBEN", "").split(".")[-1]) != 2]
    if bad_dp:
        errors.append(f"MBEN not 2-decimal on {len(bad_dp)} dividend row(s)")
    else:
        print("OK: dividend MBEN formatted to 2 decimals")

    # 5. One conversion adjustment per policy
    plug_by_policy = Counter(
        r.get("MPOLICY", "") for r in div_rows if r.get("MDATE", "") == PLUG_DATE
    )
    dupes = {p: n for p, n in plug_by_policy.items() if n > 1}
    if dupes:
        errors.append(
            f"Multiple {PLUG_DATE} conversion adjustment rows on {len(dupes)} policy(ies)"
        )
    else:
        print(f"OK: at most one {PLUG_DATE} conversion adjustment per policy "
              f"({len(plug_by_policy)} policies)")

    emitted: dict[str, float] = defaultdict(float)
    for r in div_rows:
        emitted[r.get("MPOLICY", "")] += _money(r.get("MBEN", ""))
    emitted = {k: round(v, 2) for k, v in emitted.items()}
    if len(emitted) < EXPECTED_DIVIDEND_POLICIES_MIN:
        errors.append(
            f"Dividend-history policies={len(emitted)} below expected minimum "
            f"{EXPECTED_DIVIDEND_POLICIES_MIN}"
        )
    else:
        print(f"OK: dividend-history policies={len(emitted)}")

    # 6/7. Reconcile against PPBENTYP source and the exception report
    lifetime = _load_source_lifetime(source_dir)
    if not lifetime:
        warnings.append(f"PPBENTYP extract not found under {source_dir} — reconciliation skipped")
    else:
        # Only policy-level reasons mean "no conversion adjustment for this policy".
        # OR_ROW_DOLLARS_EXCLUDED and CONTRA_SIDE_NOT_EMITTED are informational rows
        # about dollars deliberately left out; those policies still convert.
        exc_path = reports_dir / "issue114_dividend_history_exceptions.csv"
        withheld: dict[str, str] = {}
        if exc_path.is_file():
            for r in _read_csv(exc_path):
                reason = r.get("REASON", "")
                if reason == "NEGATIVE_OR_ZERO_GAP" or reason.startswith("UNMAPPED_OPTION"):
                    withheld[r.get("MPOLICY", "")] = reason
        else:
            warnings.append(f"Exception report not found: {exc_path}")

        mismatched: list[str] = []
        unexplained: list[str] = []
        for mpolicy, target in lifetime.items():
            got = emitted.get(mpolicy, 0.0)
            if mpolicy in withheld:
                # Withheld policies keep their real PACTG rows; only the
                # conversion adjustment is suppressed.
                if plug_by_policy.get(mpolicy, 0):
                    mismatched.append(
                        f"{mpolicy} withheld as {withheld[mpolicy]} but a "
                        f"{PLUG_DATE} adjustment row was emitted"
                    )
                continue
            if got == 0.0:
                unexplained.append(f"{mpolicy} lifetime {target:.2f} not converted, no exception")
            elif abs(got - target) > MONEY_TOL:
                mismatched.append(f"{mpolicy} emitted {got:.2f} vs lifetime {target:.2f}")

        if mismatched:
            errors.append(
                f"{len(mismatched)} policy(ies) do not tie to PPBENTYP; "
                f"first: {mismatched[0]}"
            )
        if unexplained:
            errors.append(
                f"{len(unexplained)} policy(ies) silently dropped (no row, no exception); "
                f"first: {unexplained[0]}"
            )
        if not mismatched and not unexplained:
            converted = len(lifetime) - len(withheld)
            target_total = round(sum(lifetime.values()), 2)
            emitted_total = round(sum(emitted.values()), 2)
            pct = (emitted_total / target_total * 100) if target_total else 0.0
            print(
                f"OK: {converted} of {len(lifetime)} policies tie exactly to "
                f"PPBENTYP DIVIDENDS_CREDITED ({len(withheld)} withheld to exceptions)"
            )
            print(
                f"OK: converted ${emitted_total:,.2f} of ${target_total:,.2f} "
                f"lifetime dividends ({pct:.2f}%)"
            )

        orphan = sorted(set(emitted) - set(lifetime))
        if orphan:
            errors.append(
                f"{len(orphan)} policy(ies) have dividend rows but no PPBENTYP lifetime total; "
                f"first: {orphan[0]}"
            )

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
        TEST_VALIDATION.mkdir(parents=True, exist_ok=True)
        dest = TEST_VALIDATION / "quikbenh.csv"
        shutil.copy2(benh_path, dest)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        (TEST_VALIDATION / "manifest.txt").write_text(
            "\n".join(
                [
                    f"Published: {stamp}",
                    "Issue: Issue_114",
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
    ap = argparse.ArgumentParser(description="Validate Issue #114 QuikBenh dividend history")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS)
    ap.add_argument(
        "--publish-test-validation",
        action="store_true",
        help="copy quikbenh.csv to Output/Test_Validation/ on PASS",
    )
    args = ap.parse_args()
    return validate(
        args.output_dir,
        args.source_dir,
        args.reports_dir,
        publish_test_validation=args.publish_test_validation,
    )


if __name__ == "__main__":
    sys.exit(main())
