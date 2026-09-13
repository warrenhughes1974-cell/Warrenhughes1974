"""
Issue #166 — quikdvdp MDEPINT buckets + year-end MINTDATE overlay.

Fail-closed against full QLA_Migration/Output/.

Usage:
  python tools/validators/validate_issue166_mdepint.py
  python tools/validators/validate_issue166_mdepint.py --output-dir QLA_Migration/Output
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from qla_core.cso_mortality_crosswalk import is_iswl_mplan
from qla_core.mdepint_buckets import mdepint_for_mplan, prior_anniversary_yyyymmdd

SCRIPT_VERSION = "1.0"
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
DEFAULT_VALUATION = "20260831"
GOLD = "9010728947C"
GOLD_DEPOSIT = 1875.38
ISWL_CONTROL = "9010713704C"
SP_CONTROL = "9010824098C"
SAL_CONTROL = "901122D991C"
ISSUE116_CONTROL = "9010380808C"
ALLOWED_RATES = {"2.00", "3.50", "4.50", "4.00"}


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def _rate(v) -> str:
    try:
        return f"{float(str(v).strip()):.2f}"
    except (TypeError, ValueError):
        return str(v).strip()


def _money(v) -> float:
    try:
        return float(str(v).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def _digits(v) -> str:
    return "".join(c for c in str(v or "") if c.isdigit())[:8]


def _valuation() -> str:
    env = "".join(c for c in os.environ.get("QLA_VALUATION_DATE", "") if c.isdigit())[:8]
    return env if len(env) == 8 else DEFAULT_VALUATION


def validate(output_dir: Path) -> int:
    dvdp_path = output_dir / "quikdvdp.csv"
    ridr_path = output_dir / "quikridr.csv"
    missing = [p.name for p in (dvdp_path, ridr_path) if not p.is_file()]
    if missing:
        print(f"FAIL — missing: {', '.join(missing)}")
        return 1

    dvdp = _read_csv(dvdp_path)
    ridr = _read_csv(ridr_path)
    errors: list[str] = []
    val_date = _valuation()

    print("=" * 72)
    print(f"ISSUE #166 MDEPINT / MINTDATE VALIDATION (script v{SCRIPT_VERSION})")
    print(f"Output: {output_dir}")
    print(f"Valuation: {val_date}")
    print("=" * 72)

    base1 = ridr[ridr["MPHASE"].astype(str).str.strip().isin(["1", ""])]
    mplan_by_pol: dict[str, str] = {}
    meff_by_pol: dict[str, str] = {}
    for _, row in base1.iterrows():
        pol = str(row.get("MPOLICY", "")).strip()
        if pol and pol not in mplan_by_pol:
            mplan_by_pol[pol] = str(row.get("MPLAN", "")).strip()
            meff_by_pol[pol] = str(row.get("MEFFDATE", "")).strip()

    rates = {_rate(r) for r in dvdp["MDEPINT"].astype(str)}
    print(f"Unique MDEPINT: {sorted(rates)}")
    extra = rates - ALLOWED_RATES
    if extra:
        errors.append(f"Unexpected MDEPINT values: {sorted(extra)}")

    bucket_fail = 0
    overlay_fail = 0
    overlay_ok = 0
    iswl_bad = 0
    for _, row in dvdp.iterrows():
        pol = str(row["MPOLICY"]).strip()
        mplan = mplan_by_pol.get(pol, "")
        got = _rate(row["MDEPINT"])
        exp = mdepint_for_mplan(mplan)
        if is_iswl_mplan(mplan) and got != "4.50":
            iswl_bad += 1
        if exp and got != exp:
            bucket_fail += 1
        if _money(row["MDEPOSIT"]) > 0:
            expected_ann = prior_anniversary_yyyymmdd(meff_by_pol.get(pol, ""), val_date)
            got_dt = _digits(row["MINTDATE"])
            if expected_ann and got_dt == expected_ann:
                overlay_ok += 1
            elif expected_ann and got_dt[4:8] == "1231":
                overlay_fail += 1
                if overlay_fail <= 5:
                    errors.append(f"{pol}: still year-end MINTDATE {got_dt} expected {expected_ann}")

    if iswl_bad:
        errors.append(f"{iswl_bad} ISWL rows have MDEPINT != 4.50")
    if bucket_fail:
        errors.append(f"{bucket_fail} rows have MDEPINT != #95 bucket")

    traces = [
        (GOLD, "3.50", prior_anniversary_yyyymmdd(meff_by_pol.get(GOLD, "19840904"), val_date), GOLD_DEPOSIT),
        (ISWL_CONTROL, "4.50", None, None),
        (SP_CONTROL, "4.50", None, None),
        (SAL_CONTROL, "2.00", None, None),
        (
            ISSUE116_CONTROL,
            "3.50",
            prior_anniversary_yyyymmdd(meff_by_pol.get(ISSUE116_CONTROL, ""), val_date),
            9220.33,
        ),
    ]
    print("\nTraces:")
    for pol, exp_rate, exp_date, exp_dep in traces:
        rows = dvdp[dvdp["MPOLICY"].astype(str).str.strip() == pol]
        if rows.empty:
            errors.append(f"Trace missing: {pol}")
            print(f"  {pol}: MISSING")
            continue
        r = rows.iloc[0]
        got_rate = _rate(r["MDEPINT"])
        got_dt = _digits(r["MINTDATE"])
        got_dep = _money(r["MDEPOSIT"])
        ok_rate = got_rate == exp_rate
        ok_date = exp_date is None or got_dt == exp_date
        ok_dep = exp_dep is None or abs(got_dep - exp_dep) < 0.01
        if exp_dep is not None and got_dt > val_date:
            errors.append(f"{pol}: future MINTDATE {got_dt} > {val_date}")
            ok_date = False
        flag = "OK" if ok_rate and ok_date and ok_dep else "FAIL"
        print(
            f"  {pol}: MPLAN={mplan_by_pol.get(pol,'?')} MDEPINT={got_rate} "
            f"MINTDATE={got_dt} MDEPOSIT={got_dep:.2f} {flag}"
        )
        if not ok_rate:
            errors.append(f"{pol}: MDEPINT {got_rate} expected {exp_rate}")
        if not ok_date:
            errors.append(f"{pol}: MINTDATE {got_dt} expected {exp_date}")
        if not ok_dep:
            errors.append(f"{pol}: MDEPOSIT {got_dep} expected {exp_dep}")

    print(f"\nBucket mismatches: {bucket_fail}")
    print(f"Year-end leftover on deposit rows: {overlay_fail}")
    print(f"Deposit rows on prior anniversary: {overlay_ok}")

    print("\n" + "=" * 72)
    if errors:
        print(f"RESULT: FAIL ({len(errors)} issue(s))")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("RESULT: PASS — #166 MDEPINT buckets and gold MINTDATE overlay")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Validate Issue #166 MDEPINT / MINTDATE")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    sys.exit(validate(args.output_dir.resolve()))


if __name__ == "__main__":
    main()
