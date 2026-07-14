"""
Issue #51 — validate QuikAint stubs for A60MIR / A96DAR closed riders.

Checks:
  1. QuikAint.csv exists under Output/rates/
  2. A60MIR and A96DAR present with MINTRATE/MINTRATE1 = 0.0000
  3. QuikUint does NOT contain A60MIR or A96DAR
  4. quikridr still has 6 target rows with MPHSTAT=56 (regression)

Usage:
  python tools/validators/validate_issue51_quikaint.py
  python tools/validators/validate_issue51_quikaint.py --publish-test-validation
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_VERSION = "1.0"
ENGINE_VERSION = "v57.76"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RATES = PROJECT_ROOT / "QLA_Migration" / "Output" / "rates"
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
TEST_VALIDATION = DEFAULT_OUTPUT / "Test_Validation"
RIDR_BASELINE = (
    PROJECT_ROOT
    / "Issue_Log_Items"
    / "Issue_51"
    / "evidence"
    / "issue51_quikridr_population.csv"
)

TARGET_PLANS = ("A60MIR", "A96DAR")
EXPECTED_RIDR_ROWS = 6
STUB_MEFFDATE = "19000101"
STUB_RATE = "0.0000"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [{k.strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def _rate_ok(value: str) -> bool:
    s = (value or "").strip()
    if not s:
        return False
    try:
        return abs(float(s)) < 1e-9
    except ValueError:
        return s in ("0", "0.0", "0.0000", ".0000")


def _load_quikridr_target_rows(output_dir: Path) -> tuple[list[dict[str, str]], str]:
    live = output_dir / "quikridr.csv"
    if live.is_file():
        rows = [r for r in _read_csv(live) if r.get("MPLAN") in TARGET_PLANS]
        return rows, str(live)
    if RIDR_BASELINE.is_file():
        rows = _read_csv(RIDR_BASELINE)
        return rows, str(RIDR_BASELINE)
    return [], ""


def validate(
    rates_dir: Path,
    output_dir: Path,
    *,
    publish_test_validation: bool = False,
) -> int:
    print("=" * 72)
    print(f"ISSUE #51 QUIKAINT VALIDATION (script v{SCRIPT_VERSION}, engine {ENGINE_VERSION})")
    print("=" * 72)

    errors: list[str] = []
    warnings: list[str] = []

    quikaint_path = rates_dir / "QuikAint.csv"
    if not quikaint_path.is_file():
        errors.append(f"Missing QuikAint.csv: {quikaint_path}")
    else:
        rows = _read_csv(quikaint_path)
        by_plan = {r.get("MPLAN", ""): r for r in rows}
        print(f"OK: QuikAint.csv found ({len(rows)} row(s))")
        for plan in TARGET_PLANS:
            row = by_plan.get(plan)
            if row is None:
                errors.append(f"QuikAint missing MPLAN={plan}")
                continue
            if row.get("MEFFDATE") != STUB_MEFFDATE:
                errors.append(f"{plan} MEFFDATE={row.get('MEFFDATE')!r} expected {STUB_MEFFDATE}")
            if not _rate_ok(row.get("MINTRATE", "")):
                errors.append(f"{plan} MINTRATE={row.get('MINTRATE')!r} expected 0.0000")
            if not _rate_ok(row.get("MINTRATE1", "")):
                errors.append(f"{plan} MINTRATE1={row.get('MINTRATE1')!r} expected 0.0000")
            if not errors or plan not in "".join(errors):
                print(f"OK: {plan} stub @ {STUB_MEFFDATE} / 0.0000 / 0.0000")

    uint_path = rates_dir / "QuikUint.csv"
    if uint_path.is_file():
        uint_plans = {r.get("MPLAN", "") for r in _read_csv(uint_path)}
        polluted = [p for p in TARGET_PLANS if p in uint_plans]
        if polluted:
            errors.append(f"QuikUint must not contain MIR/DAR plans: {polluted}")
        else:
            print("OK: QuikUint has no A60MIR/A96DAR rows")
    else:
        warnings.append(f"QuikUint.csv absent (skip pollution check): {uint_path}")

    ridr_rows, ridr_source = _load_quikridr_target_rows(output_dir)
    if not ridr_source:
        errors.append("quikridr.csv missing and no Issue #51 baseline for regression check")
    else:
        if len(ridr_rows) != EXPECTED_RIDR_ROWS:
            errors.append(
                f"quikridr target rows={len(ridr_rows)} expected {EXPECTED_RIDR_ROWS} "
                f"(source: {ridr_source})"
            )
        else:
            bad_stat = [r for r in ridr_rows if r.get("MPHSTAT") != "56"]
            if bad_stat:
                errors.append(
                    f"quikridr MPHSTAT regression: {len(bad_stat)} row(s) not 56 "
                    f"(source: {ridr_source})"
                )
            else:
                print(
                    f"OK: quikridr regression — {EXPECTED_RIDR_ROWS} rows, "
                    f"all MPHSTAT=56 ({ridr_source})"
                )

    manifest_path = rates_dir / "rate_csv_manifest.csv"
    if manifest_path.is_file():
        manifest_rows = _read_csv(manifest_path)
        aint_listed = any(r.get("TABLE") == "QuikAint" for r in manifest_rows)
        if aint_listed:
            print("OK: rate_csv_manifest.csv lists QuikAint")
        else:
            warnings.append("rate_csv_manifest.csv does not list QuikAint yet")
    else:
        warnings.append(f"rate_csv_manifest.csv missing: {manifest_path}")

    for w in warnings:
        print(f"WARN: {w}")

    if errors:
        print("-" * 72)
        print("RESULT: FAIL")
        for e in errors:
            print(f"FAIL: {e}")
        return 1

    if publish_test_validation:
        dest_dir = TEST_VALIDATION / "rates"
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(quikaint_path, dest_dir / "QuikAint.csv")
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        manifest = TEST_VALIDATION / "manifest.txt"
        manifest.write_text(
            "\n".join(
                [
                    f"Published: {stamp}",
                    "Issue: Issue_51",
                    f"Source: {rates_dir}",
                    "Tables:",
                    "  - rates/QuikAint.csv",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"OK: published QuikAint.csv to {dest_dir}")

    print("-" * 72)
    print("RESULT: PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Issue #51 QuikAint stubs")
    ap.add_argument("--rates-dir", type=Path, default=DEFAULT_RATES)
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument(
        "--publish-test-validation",
        action="store_true",
        help="copy QuikAint.csv to Output/Test_Validation/rates/ on PASS",
    )
    args = ap.parse_args()
    return validate(
        args.rates_dir,
        args.output_dir,
        publish_test_validation=args.publish_test_validation,
    )


if __name__ == "__main__":
    sys.exit(main())
