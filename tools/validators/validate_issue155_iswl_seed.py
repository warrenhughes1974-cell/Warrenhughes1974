"""
Issue #155 — QuikIswl full PFNDRDET history + MISWL stamping (fail-closed).

Usage:
  set QLA_VALUATION_DATE=YYYYMMDD
  python tools/validators/validate_issue155_iswl_seed.py
"""
from __future__ import annotations

import csv
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qla_core.cso_mortality_crosswalk import ISWL_MPLAN_ALLOWLIST  # noqa: E402
from qla_core.quikiswl_loader import (  # noqa: E402
    OUTPUT_FILENAME,
    QUIKISWL_FIELDS,
    _load_pfndr_by_mpolicy,
    _load_issue_dates,
    _parse_money,
    _s,
)

SCRIPT_VERSION = "2.1"
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
ROW_COUNT_FLOOR = 500_000
POLICY_FLOOR = 2_000
MISWL = "MISWL"

GOLD_20260630 = {
    "9010713704C": {
        "first_MLASTANNV": "20030331",
        "last_MLASTANNV": "20260619",
        "last_MMONTH": "506",
        "last_MACCTBAL": 45551.94,
        "last_MSUMPREM": 22292.52,
        "last_MINT_min": 0.01,
        "last_MCOI_min": 0.01,
    },
    "9010713705C": {"last_MACCTBAL": 26251.74},
    "9010713707C": {"last_MACCTBAL": 8146.88},
    "9010779727C": {"last_MACCTBAL": -172395.45},
}


def _f(v: object) -> float | None:
    t = _s(v)
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _norm_date(v: object) -> str:
    d = "".join(ch for ch in _s(v) if ch.isdigit())
    return d[:8] if len(d) >= 8 else ""


def _require_valdate() -> str:
    raw = os.environ.get("QLA_VALUATION_DATE", "").strip()
    if len(raw) != 8 or not raw.isdigit():
        print("FAIL: QLA_VALUATION_DATE must be set to YYYYMMDD")
        sys.exit(1)
    return raw


def _load_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        return fields, list(reader)


def _iswl_base_pols(out: Path) -> set[str]:
    pols: set[str] = set()
    ridr = out / "quikridr.csv"
    with ridr.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.DictReader(f):
            if _s(row.get("MPLAN")) in ISWL_MPLAN_ALLOWLIST and _s(row.get("MPHASE")) == "1":
                p = _s(row.get("MPOLICY"))
                if p:
                    pols.add(p)
    return pols


def _rows_by_policy(rows: list[dict]) -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by[_s(r.get("MPOLICY"))].append(r)
    for pol in by:
        by[pol].sort(key=lambda r: _norm_date(r.get("MLASTANNV")))
    return by


def main() -> int:
    valdate = _require_valdate()
    out = DEFAULT_OUTPUT
    print(f"validate_issue155_iswl_seed.py v{SCRIPT_VERSION}")
    print(f"QLA_VALUATION_DATE={valdate}")
    print(f"output: {out}")

    fails: list[str] = []
    checks: list[tuple[str, bool, str]] = []

    iswl_path = out / OUTPUT_FILENAME
    if not iswl_path.is_file():
        print("FAIL: missing QuikIswl.csv")
        return 1

    fields, iswl_rows = _load_csv(iswl_path)
    if fields != QUIKISWL_FIELDS:
        fails.append("QuikIswl schema mismatch")
        checks.append(("schema", False, str(fields[:5])))

    issue_dates = _load_issue_dates(out / "quikmstr.csv")
    month0 = [
        r
        for r in iswl_rows
        if _s(r.get("MMONTH")) == "0"
        and _s(r.get("MACCTBAL")) == "0.00"
        and _norm_date(r.get("MLASTANNV")) == issue_dates.get(_s(r.get("MPOLICY")), "")
    ]
    ok_no_m0 = len(month0) == 0
    checks.append(("no_issue124_month0", ok_no_m0, f"month0_pattern_rows={len(month0)}"))
    if not ok_no_m0:
        fails.append(f"{len(month0)} Issue #124 month-0 rows still present")

    ok_row_floor = len(iswl_rows) >= ROW_COUNT_FLOOR
    by_pol = _rows_by_policy(iswl_rows)
    ok_pol_floor = len(by_pol) >= POLICY_FLOOR
    checks.append(("row_count_floor", ok_row_floor, str(len(iswl_rows))))
    checks.append(("policy_count_floor", ok_pol_floor, str(len(by_pol))))
    if not ok_row_floor:
        fails.append(f"row count {len(iswl_rows)} < {ROW_COUNT_FLOOR}")
    if not ok_pol_floor:
        fails.append(f"policy count {len(by_pol)} < {POLICY_FLOOR}")

    try:
        pfndr = _load_pfndr_by_mpolicy(valdate)
    except FileNotFoundError as exc:
        fails.append(str(exc))
        pfndr = {}

    dup_keys = 0
    order_fails = 0
    pfndr_mismatch = 0
    after_val = 0
    for pol, pol_rows in by_pol.items():
        prev_annv = ""
        prev_month = -1
        for row in pol_rows:
            annv = _norm_date(row.get("MLASTANNV"))
            if annv > valdate:
                after_val += 1
            month_i = int(_s(row.get("MMONTH")) or "0")
            if prev_annv and annv <= prev_annv:
                order_fails += 1
            if month_i < prev_month:
                order_fails += 1
            prev_annv = annv
            prev_month = month_i
        last = pol_rows[-1]
        pf = pfndr.get(pol)
        if not pf:
            continue
        exp_bal = _parse_money(pf.get("FUND_BALANCE"))
        act_bal = _f(last.get("MACCTBAL"))
        if act_bal is None or abs(act_bal - exp_bal) > 0.011:
            pfndr_mismatch += 1

    key_ctr: Counter[tuple[str, str]] = Counter()
    for row in iswl_rows:
        key_ctr[(_s(row.get("MPOLICY")), _norm_date(row.get("MLASTANNV")))] += 1
    dup_keys = sum(1 for _, c in key_ctr.items() if c > 1)

    ok_shape = dup_keys == 0 and order_fails == 0 and after_val == 0
    checks.append(
        (
            "history_shape",
            ok_shape,
            f"dups={dup_keys} order_fails={order_fails} after_val={after_val}",
        )
    )
    if dup_keys:
        fails.append(f"{dup_keys} duplicate MPOLICY+MLASTANNV")
    if order_fails:
        fails.append(f"{order_fails} MLASTANNV/MMONTH ordering violations")
    if after_val:
        fails.append(f"{after_val} rows with MLASTANNV > QLA_VALUATION_DATE")

    ok_pfndr = pfndr_mismatch == 0
    checks.append(
        ("last_row_pfndr_balance", ok_pfndr, f"mismatch_policies={pfndr_mismatch}")
    )
    if pfndr_mismatch:
        fails.append(f"{pfndr_mismatch} policies last MACCTBAL != PFNDR FUND_BALANCE")

    seed_mlastannv_by_pol = {
        pol: _norm_date(rows[-1]["MLASTANNV"]) for pol, rows in by_pol.items() if rows
    }
    iswl_pols = _iswl_base_pols(out)

    prmh_path = out / "quikprmh.csv"
    isrr_path = out / "QuikIsrr.csv"
    prmh_fields, prmh_rows = _load_csv(prmh_path) if prmh_path.is_file() else ([], [])
    isrr_fields, isrr_rows = _load_csv(isrr_path) if isrr_path.is_file() else ([], [])

    ok_prmh_col = MISWL in prmh_fields
    ok_isrr_col = MISWL in isrr_fields
    checks.append(("quikprmh_miswl_col", ok_prmh_col, str(prmh_fields[-3:])))
    checks.append(("QuikIsrr_miswl_col", ok_isrr_col, str(isrr_fields[-3:])))
    if not ok_prmh_col:
        fails.append("quikprmh missing MISWL column")
    if not ok_isrr_col:
        fails.append("QuikIsrr missing MISWL column")

    miswl_after_seed = 0
    miswl_non_iswl = 0
    prmh_stamped = 0
    for row in prmh_rows:
        pol = _s(row.get("MPOLICY"))
        mv = _norm_date(row.get(MISWL))
        if mv:
            prmh_stamped += 1
            seed_max = seed_mlastannv_by_pol.get(pol)
            if seed_max and mv > seed_max:
                miswl_after_seed += 1
            if pol not in iswl_pols:
                miswl_non_iswl += 1

    isrr_stamped = 0
    for row in isrr_rows:
        pol = _s(row.get("MPOLICY"))
        mv = _norm_date(row.get(MISWL))
        if mv:
            isrr_stamped += 1
            seed_max = seed_mlastannv_by_pol.get(pol)
            if seed_max and mv > seed_max:
                miswl_after_seed += 1
            if pol not in iswl_pols:
                miswl_non_iswl += 1

    ok_miswl = miswl_after_seed == 0 and miswl_non_iswl == 0 and prmh_stamped > 0
    checks.append(
        (
            "miswl_bounds",
            ok_miswl,
            f"prmh_stamped={prmh_stamped} isrr_stamped={isrr_stamped} "
            f"after_seed={miswl_after_seed} non_iswl={miswl_non_iswl}",
        )
    )
    if miswl_after_seed:
        fails.append(f"{miswl_after_seed} MISWL values after max MLASTANNV")
    if miswl_non_iswl:
        fails.append(f"{miswl_non_iswl} MISWL on non-ISWL policies")
    if prmh_stamped <= 0:
        fails.append("no quikprmh rows stamped with MISWL")

    gold_fails = 0
    if valdate == "20260630":
        for pol, exp in GOLD_20260630.items():
            pol_rows = by_pol.get(pol)
            if not pol_rows:
                gold_fails += 1
                fails.append(f"gold policy {pol} missing history")
                continue
            first = pol_rows[0]
            last = pol_rows[-1]
            if "first_MLASTANNV" in exp:
                if _norm_date(first.get("MLASTANNV")) != exp["first_MLASTANNV"]:
                    gold_fails += 1
                    fails.append(
                        f"gold {pol} first MLASTANNV got {first.get('MLASTANNV')} "
                        f"expected {exp['first_MLASTANNV']}"
                    )
            if "last_MLASTANNV" in exp:
                if _norm_date(last.get("MLASTANNV")) != exp["last_MLASTANNV"]:
                    gold_fails += 1
                    fails.append(
                        f"gold {pol} last MLASTANNV got {last.get('MLASTANNV')} "
                        f"expected {exp['last_MLASTANNV']}"
                    )
            if "last_MMONTH" in exp:
                if _s(last.get("MMONTH")) != exp["last_MMONTH"]:
                    gold_fails += 1
                    fails.append(
                        f"gold {pol} last MMONTH got {last.get('MMONTH')} expected {exp['last_MMONTH']}"
                    )
            if "last_MACCTBAL" in exp:
                act = _f(last.get("MACCTBAL"))
                if act is None or abs(act - float(exp["last_MACCTBAL"])) > 0.011:
                    gold_fails += 1
                    fails.append(
                        f"gold {pol} last MACCTBAL got {last.get('MACCTBAL')} "
                        f"expected {exp['last_MACCTBAL']}"
                    )
            if "last_MSUMPREM" in exp:
                act = _f(last.get("MSUMPREM"))
                if act is None or abs(act - float(exp["last_MSUMPREM"])) > 0.011:
                    gold_fails += 1
                    fails.append(
                        f"gold {pol} last MSUMPREM got {last.get('MSUMPREM')} "
                        f"expected {exp['last_MSUMPREM']}"
                    )
            if "last_MINT_min" in exp:
                act = _f(last.get("MINT"))
                if act is None or act < float(exp["last_MINT_min"]):
                    gold_fails += 1
                    fails.append(f"gold {pol} last MINT got {last.get('MINT')} expected > 0")
            if "last_MCOI_min" in exp:
                act = _f(last.get("MCOI"))
                if act is None or act < float(exp["last_MCOI_min"]):
                    gold_fails += 1
                    fails.append(f"gold {pol} last MCOI got {last.get('MCOI')} expected > 0")
        checks.append(("gold_traces", gold_fails == 0, f"fails={gold_fails}"))
    else:
        checks.append(("gold_traces", True, "skipped (not 20260630)"))

    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'}: {name} — {detail}")

    if fails:
        print("FAIL summary:")
        for fline in fails[:25]:
            print(f"  - {fline}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
