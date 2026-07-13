"""
Issue #55 — quikridr MUNIT floor + leading-zero decimal emit (v57.78).

Checks:
  - No rows with 0 < MUNIT < 0.001
  - No leading-dot decimal strings in quikridr numeric fields
  - Trace policies Phase 1 = 0; Phase 2 units unchanged numerically
  - Issue #25 MPOLICY 10-char width preserved
  - Issue #26 MPREM numeric values preserved (leading-zero fix allowed)

Usage:
  python tools/validators/validate_issue55_munit_floor.py
  python tools/validators/validate_issue55_munit_floor.py --output-dir QLA_Migration/Output
  python tools/validators/validate_issue55_munit_floor.py --simulate-only
  python tools/validators/validate_issue55_munit_floor.py --publish-test-validation
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

SCRIPT_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
TEST_VALIDATION = DEFAULT_OUTPUT / "Test_Validation"
BASELINE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_55" / "evidence" / "quikridr_pre_v5778_baseline.csv"

sys.path.insert(0, str(PROJECT_ROOT))
from qla_core.quikridr_decimal_emit import (  # noqa: E402
    MUNIT_FLOOR_THRESHOLD,
    QUIKRIDR_DECIMAL_FIELDS,
    apply_quikridr_decimal_emit,
    format_quikridr_decimal_field,
)
from qla_core.normalize_utils import format_qladmin_mpolicy  # noqa: E402

EXPECTED_FLOOR_COUNT = 148
EXPECTED_ROW_COUNT = 6934

TRACE_EXPECTED = {
    ("018495BC", "1"): 0.0,
    ("018495BC", "2"): 0.53,
    ("018499CC", "1"): 0.0,
    ("018499CC", "2"): 1.05,
    ("018510C", "1"): 0.0,
    ("018510C", "2"): 0.647,
}

PUA_FLOOR_KEY = ("010434419C", "2")


def _s(v) -> str:
    return str(v).strip() if v is not None else ""


def _num(v) -> float:
    try:
        return float(_s(v).replace(",", "") or 0)
    except ValueError:
        return 0.0


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="latin1", newline="", errors="replace") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for row in reader:
            out = {}
            for k, v in row.items():
                key = k.strip().upper() if k else k
                # Preserve MPOLICY padding (#25) — do not strip spaces.
                out[key] = v if key == "MPOLICY" else _s(v)
            rows.append(out)
        return rows


def _leading_dot_fields(row: dict[str, str]) -> list[str]:
    bad = []
    for field in QUIKRIDR_DECIMAL_FIELDS:
        val = row.get(field, "")
        if val.startswith("."):
            bad.append(field)
    return bad


def simulate_transform(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for row in rows:
        copy = dict(row)
        apply_quikridr_decimal_emit(copy)
        out.append(copy)
    return out


def validate_mpolicy_width(rows: list[dict[str, str]], keys: set[tuple[str, str]] | None = None) -> list[str]:
    errs = []
    for row in rows:
        key = (_s(row.get("MPOLICY")), _s(row.get("MPHASE")))
        if keys is not None and key not in keys:
            continue
        mp = row.get("MPOLICY", "")
        if mp and len(mp) != 10:
            errs.append(f"MPOLICY width != 10: {mp!r} ({key})")
            if len(errs) >= 5:
                break
    return errs


def validate(output_dir: Path, simulate_only: bool = False, publish_test_validation: bool = False) -> int:
    errors: list[str] = []
    ridr_path = output_dir / "quikridr.csv"

    print(f"Issue #55 validator v{SCRIPT_VERSION}")
    print(f"Output: {ridr_path}")

    if not ridr_path.is_file():
        print("RESULT: FAIL (quikridr.csv missing)")
        return 1

    rows = _read_csv(ridr_path)
    print(f"Row count: {len(rows)} (expected {EXPECTED_ROW_COUNT})")

    if simulate_only:
        print("Mode: simulate-only (logic check on current CSV; batch re-run not required)")
        sim = simulate_transform(rows)
        sim_sub = sum(1 for r in sim if 0 < _num(r.get("MUNIT", "")) < MUNIT_FLOOR_THRESHOLD)
        sim_lead = sum(len(_leading_dot_fields(r)) for r in sim)
        print(f"After simulate: sub-floor={sim_sub}, leading-dot hits={sim_lead}")
        sim_ok = sim_sub == 0 and sim_lead == 0
        sim_index = {(_s(r.get("MPOLICY")), _s(r.get("MPHASE"))): r for r in sim}
        for key, exp in TRACE_EXPECTED.items():
            row = sim_index.get(key)
            got = _num(row.get("MUNIT", "")) if row else -1
            ok = row is not None and abs(got - exp) < 1e-5 and not _s(row.get("MUNIT", "")).startswith(".")
            print(f"  {key[0]} P{key[1]}: MUNIT={row.get('MUNIT','') if row else 'MISSING'} expected={exp} [{'PASS' if ok else 'FAIL'}]")
            if not ok:
                errors.append(f"Sim trace failed {key}")
        pua = sim_index.get(PUA_FLOOR_KEY)
        if not pua or _num(pua.get("MUNIT", "")) != 0.0:
            errors.append(f"Sim PUA floor failed {PUA_FLOOR_KEY}")
        print("\nRESULT:", "PASS (simulate-only)" if sim_ok and not errors else "FAIL")
        for err in errors:
            print(f"  - {err}")
        return 0 if sim_ok and not errors else 1

    if len(rows) != EXPECTED_ROW_COUNT:
        errors.append(f"Row count {len(rows)} != {EXPECTED_ROW_COUNT}")

    sub_floor = 0
    leading_dot_total = 0
    for row in rows:
        mu = _num(row.get("MUNIT", ""))
        if 0 < mu < MUNIT_FLOOR_THRESHOLD:
            sub_floor += 1
        leading_dot_total += len(_leading_dot_fields(row))

    print(f"Sub-floor MUNIT (0 < x < {MUNIT_FLOOR_THRESHOLD}): {sub_floor}")
    if sub_floor:
        errors.append(f"Found {sub_floor} rows with 0 < MUNIT < {MUNIT_FLOOR_THRESHOLD}")

    print(f"Leading-dot decimal fields (total field hits): {leading_dot_total}")
    if leading_dot_total:
        errors.append(f"Found {leading_dot_total} leading-dot decimal field values")

    # Trace policies
    index = {(_s(r.get("MPOLICY")), _s(r.get("MPHASE"))): r for r in rows}
    print("Trace policies:")
    for key, exp in TRACE_EXPECTED.items():
        row = index.get(key)
        if not row:
            errors.append(f"Missing trace row {key}")
            print(f"  {key[0]} P{key[1]}: MISSING")
            continue
        got = _num(row.get("MUNIT", ""))
        munit_str = row.get("MUNIT", "")
        ok = abs(got - exp) < 1e-5
        if not ok:
            errors.append(f"{key[0]} P{key[1]} MUNIT={got} expected {exp}")
        lead_ok = not munit_str.startswith(".")
        if not lead_ok:
            errors.append(f"{key[0]} P{key[1]} MUNIT leading-dot: {munit_str!r}")
        status = "PASS" if ok and lead_ok else "FAIL"
        print(f"  {key[0]} P{key[1]}: MUNIT={munit_str} ({got}) expected={exp} [{status}]")

    pua = index.get(PUA_FLOOR_KEY)
    if pua:
        pua_mu = _num(pua.get("MUNIT", ""))
        if pua_mu != 0.0:
            errors.append(f"PUA {PUA_FLOOR_KEY[0]} P{PUA_FLOOR_KEY[1]} MUNIT={pua_mu} expected 0")
        print(f"  PUA {PUA_FLOOR_KEY[0]} P{PUA_FLOOR_KEY[1]}: MUNIT={pua.get('MUNIT','')} [{('PASS' if pua_mu == 0 else 'FAIL')}]")
    else:
        errors.append(f"Missing PUA trace row {PUA_FLOOR_KEY}")

    mpolicy_errs = validate_mpolicy_width(rows, set(TRACE_EXPECTED.keys()))
    if mpolicy_errs:
        errors.extend(mpolicy_errs[:3])
    print(f"Issue #25 MPOLICY width (trace policies): {'PASS' if not mpolicy_errs else 'FAIL'}")

    # Issue #26: MPREM numeric preserved (compare to baseline if present)
    if BASELINE.is_file():
        base_rows = _read_csv(BASELINE)
        base_index = {(_s(r.get("MPOLICY")), _s(r.get("MPHASE"))): r for r in base_rows}
        mprem_mismatch = 0
        for key, row in index.items():
            base = base_index.get(key)
            if not base:
                continue
            if abs(_num(row.get("MPREM", "")) - _num(base.get("MPREM", ""))) > 1e-9:
                mprem_mismatch += 1
        print(f"Issue #26 MPREM numeric vs baseline: {mprem_mismatch} mismatches")
        if mprem_mismatch:
            errors.append(f"MPREM numeric mismatch count={mprem_mismatch}")
    else:
        print("Issue #26 MPREM: baseline not found — spot-check leading-dot only")
        mprem_lead = sum(1 for r in rows if _s(r.get("MPREM", "")).startswith("."))
        if mprem_lead:
            errors.append(f"MPREM leading-dot count={mprem_lead}")
        print(f"  MPREM leading-dot count: {mprem_lead}")

    # Simulate transform when output still stale (pre-batch)
    if sub_floor or leading_dot_total:
        print("\nStale-output simulate check (re-run batch to refresh quikridr.csv):")
        sim = simulate_transform(rows)
        sim_sub = sum(1 for r in sim if 0 < _num(r.get("MUNIT", "")) < MUNIT_FLOOR_THRESHOLD)
        sim_lead = sum(len(_leading_dot_fields(r)) for r in sim)
        print(f"  After simulate: sub-floor={sim_sub}, leading-dot hits={sim_lead}")
        if sim_sub or sim_lead:
            errors.append(f"Transform logic failed sub_floor={sim_sub} leading_dot={sim_lead}")

    if publish_test_validation and not errors:
        TEST_VALIDATION.mkdir(parents=True, exist_ok=True)
        dest = TEST_VALIDATION / "quikridr.csv"
        shutil.copy2(ridr_path, dest)
        print(f"Published {dest}")

    print("\nRESULT:", "PASS" if not errors else "FAIL")
    for err in errors[:20]:
        print(f"  - {err}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more")
    return 0 if not errors else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Issue #55 quikridr MUNIT floor validator")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--simulate-only", action="store_true")
    ap.add_argument("--publish-test-validation", action="store_true")
    args = ap.parse_args()
    return validate(args.output_dir, simulate_only=args.simulate_only, publish_test_validation=args.publish_test_validation)


if __name__ == "__main__":
    raise SystemExit(main())
