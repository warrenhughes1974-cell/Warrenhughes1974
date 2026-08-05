"""
Issue #124 — QuikIswl month-0 seed validation against full Output.

Usage:
  python tools/validators/validate_issue124_quikiswl.py
  python tools/validators/validate_issue124_quikiswl.py --publish-test-validation
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qla_core.cso_mortality_crosswalk import ISWL_MPLAN_ALLOWLIST  # noqa: E402
from qla_core.quikiswl_loader import (  # noqa: E402
    OUTPUT_FILENAME,
    QUIKISWL_FIELDS,
    build_quikiswl_seed_rows,
)

SCRIPT_VERSION = "1.0"
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
EVIDENCE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_124" / "evidence"
TRACE = (
    "9010713704C",
    "9010715467C",
    "9010717447C",
    "9010716974C",  # terminated status — included under all-status scope
)


def _s(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _f(v: object) -> float | None:
    t = _s(v)
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Issue #124 QuikIswl seeds")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--publish-test-validation", action="store_true")
    args = ap.parse_args()

    out = args.output_dir
    mstr_path = out / "quikmstr.csv"
    ridr_path = out / "quikridr.csv"
    iswl_path = out / OUTPUT_FILENAME
    if not iswl_path.exists():
        alt = out / "quikiswl.csv"
        if alt.exists():
            iswl_path = alt

    print(f"validate_issue124_quikiswl.py v{SCRIPT_VERSION}")
    print(f"output: {out}")

    fails: list[str] = []
    if not mstr_path.is_file() or not ridr_path.is_file():
        print("FAIL: missing quikmstr.csv or quikridr.csv")
        return 1
    if not iswl_path.is_file():
        print(f"FAIL: missing {OUTPUT_FILENAME}")
        return 1

    expected = build_quikiswl_seed_rows(mstr_path, ridr_path)
    exp_by_pol = {r["MPOLICY"]: r for r in expected.rows}

    with iswl_path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        actual = list(reader)

    if fields != QUIKISWL_FIELDS:
        fails.append(f"schema mismatch: got {fields[:5]}... expected QUIKISWL_FIELDS")

    if len(actual) != len(expected.rows):
        fails.append(f"row count {len(actual)} != expected {len(expected.rows)}")

    # Join ridr units for MDB check
    unit_by_pol: dict[str, float] = {}
    plan_by_pol: dict[str, str] = {}
    with ridr_path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.DictReader(f):
            if _s(row.get("MPLAN")) in ISWL_MPLAN_ALLOWLIST and _s(row.get("MPHASE")) == "1":
                pol = _s(row.get("MPOLICY"))
                u = _f(row.get("MUNIT"))
                if pol and u is not None:
                    unit_by_pol[pol] = u
                    plan_by_pol[pol] = _s(row.get("MPLAN"))

    missdt: dict[str, str] = {}
    with mstr_path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.DictReader(f):
            pol = _s(row.get("MPOLICY"))
            if pol:
                d = "".join(ch for ch in _s(row.get("MISSDT")) if ch.isdigit())[:8]
                missdt[pol] = d

    keys = Counter()
    non_iswl = 0
    bad_mlob = 0
    bad_month = 0
    bad_annv = 0
    bad_mdb = 0
    for row in actual:
        pol = _s(row.get("MPOLICY"))
        annv = _s(row.get("MLASTANNV"))
        keys[(pol, annv)] += 1
        if pol not in plan_by_pol:
            non_iswl += 1
        if _s(row.get("MLOB")) != "I":
            bad_mlob += 1
        if _s(row.get("MMONTH")) != "0":
            bad_month += 1
        if annv != missdt.get(pol, ""):
            bad_annv += 1
        unit = unit_by_pol.get(pol)
        mdb = _f(row.get("MDB"))
        if unit is None or mdb is None or abs(mdb - unit * 1000.0) > 0.011:
            bad_mdb += 1

    dups = sum(1 for _, c in keys.items() if c > 1)
    if non_iswl:
        fails.append(f"{non_iswl} rows not in ISWL phase-1 population")
    if bad_mlob:
        fails.append(f"{bad_mlob} rows with MLOB != I")
    if bad_month:
        fails.append(f"{bad_month} rows with MMONTH != 0")
    if bad_annv:
        fails.append(f"{bad_annv} rows with MLASTANNV != MISSDT")
    if bad_mdb:
        fails.append(f"{bad_mdb} rows with MDB != MUNIT*1000")
    if dups:
        fails.append(f"{dups} duplicate MPOLICY+MLASTANNV keys")

    # Expected set equality
    act_pols = {_s(r.get("MPOLICY")) for r in actual}
    exp_pols = set(exp_by_pol)
    if act_pols != exp_pols:
        fails.append(
            f"policy set mismatch missing={len(exp_pols - act_pols)} "
            f"extra={len(act_pols - exp_pols)}"
        )

    print(f"QuikIswl rows: {len(actual)}")
    print(f"expected: {len(expected.rows)}")
    print(f"by_plan: {expected.by_plan}")
    print("trace:")
    for pol in TRACE:
        hits = [r for r in actual if _s(r.get("MPOLICY")) == pol]
        if not hits:
            print(f"  {pol}: NOT FOUND")
            continue
        r = hits[0]
        print(
            f"  {pol} MLOB={_s(r.get('MLOB'))} MLASTANNV={_s(r.get('MLASTANNV'))} "
            f"MMONTH={_s(r.get('MMONTH'))} MDB={_s(r.get('MDB'))} "
            f"unit={unit_by_pol.get(pol)} plan={plan_by_pol.get(pol)}"
        )

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    summary = {
        "validator": "validate_issue124_quikiswl.py",
        "version": SCRIPT_VERSION,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "rows": len(actual),
        "expected": len(expected.rows),
        "by_plan": expected.by_plan,
        "fails": fails,
        "pass": not fails,
    }
    (EVIDENCE / "issue124_validation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    if fails:
        print("FAIL:")
        for f in fails:
            print(f"  - {f}")
        return 1

    print("PASS")
    if args.publish_test_validation:
        tv = out / "Test_Validation"
        tv.mkdir(parents=True, exist_ok=True)
        dest = tv / OUTPUT_FILENAME
        shutil.copy2(iswl_path, dest)
        print(f"Published {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
