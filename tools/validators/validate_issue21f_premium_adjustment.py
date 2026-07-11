"""Validate Issue #21F conversion premium adjustment on quikprmh (v57.73)."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output"
REPORTS = ROOT / "QLA_Migration" / "Reports"
SCHEMA = [
    "MPOLICY", "DATEPAID", "RENEWAL", "PREMIUM", "MLIFE", "MTERM", "MSUPP",
    "MANN", "MHEALTH", "XS", "MPAIDTO", "POSTDATE", "MPOSTDATE", "MSOURCE",
    "MBATCH", "USER_ID", "MBILLFRM", "MMODEPD",
]

sys.path.insert(0, str(ROOT))
from qla_core.issue21f_premium_adjustment import (  # noqa: E402
    CONV_ADJ_DATEPAID,
    CONV_ADJ_MSOURCE,
    CONV_ADJ_USER_ID,
    is_conversion_adjustment_row,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Issue 21F quikprmh adjustment validator")
    ap.add_argument(
        "--publish-test-validation",
        action="store_true",
        help="On PASS, copy quikprmh.csv to Output/Test_Validation/",
    )
    ap.add_argument(
        "--before",
        type=Path,
        help="Optional before snapshot quikprmh.csv for non-candidate regression",
    )
    args = ap.parse_args()

    print("=" * 72)
    print("ISSUE #21F — CONVERSION PREMIUM ADJUSTMENT VALIDATION (v57.73)")
    print("=" * 72)
    errors: list[str] = []

    prmh_path = OUT / "quikprmh.csv"
    if not prmh_path.is_file():
        errors.append("quikprmh.csv missing in Output")
        print("FAIL: quikprmh.csv not found")
        return 1

    prmh = pd.read_csv(prmh_path, dtype=str, encoding="latin1").fillna("")
    print(f"\nquikprmh rows: {len(prmh)}")

    # Schema
    if list(prmh.columns) != SCHEMA:
        errors.append(f"schema drift: {list(prmh.columns)}")
        print("FAIL: column order mismatch")
    else:
        print("  schema order: PASS")

    # Golden policy 010310404C
    golden_pol = "010310404C"
    golden_adj = 15193.85
    adj_rows = prmh[
        (prmh["MPOLICY"].astype(str).str.strip() == golden_pol)
        & (prmh["MSOURCE"].astype(str).str.strip().str.upper() == CONV_ADJ_MSOURCE)
    ]
    print(f"\n[Golden] {golden_pol} CONV_ADJ rows: {len(adj_rows)}")
    if len(adj_rows) != 1:
        errors.append(f"golden: expected 1 CONV_ADJ row, got {len(adj_rows)}")
    else:
        row = adj_rows.iloc[0]
        prem = float(str(row["PREMIUM"]).strip() or 0)
        datepaid = str(row["DATEPAID"]).strip()
        user_id = str(row["USER_ID"]).strip().upper()
        ok_prem = abs(prem - golden_adj) < 0.02
        ok_date = datepaid == CONV_ADJ_DATEPAID
        ok_user = user_id == CONV_ADJ_USER_ID
        print(f"  PREMIUM={prem} expect={golden_adj} -> {'PASS' if ok_prem else 'FAIL'}")
        print(f"  DATEPAID={datepaid} expect={CONV_ADJ_DATEPAID} -> {'PASS' if ok_date else 'FAIL'}")
        print(f"  USER_ID={user_id} -> {'PASS' if ok_user else 'FAIL'}")
        if not (ok_prem and ok_date and ok_user):
            errors.append("golden 010310404C adjustment mismatch")

        # Total reconcile for golden
        hist_mask = ~prmh.apply(lambda r: is_conversion_adjustment_row(r.to_dict()), axis=1)
        hist_sum = prmh.loc[
            (prmh["MPOLICY"].astype(str).str.strip() == golden_pol) & hist_mask,
            "PREMIUM",
        ].map(lambda x: float(str(x).strip() or 0)).sum()
        total = hist_sum + prem
        print(f"  hist={hist_sum:.2f} + adj={prem:.2f} = {total:.2f} (LifePRO 17040.05)")
        if abs(total - 17040.05) > 0.02:
            errors.append(f"golden total reconcile failed: {total}")

    # ISWL must not have CONV_ADJ
    iswl_pol = "010713704C"
    iswl_adj = prmh[
        (prmh["MPOLICY"].astype(str).str.strip() == iswl_pol)
        & (prmh["MSOURCE"].astype(str).str.strip().str.upper() == CONV_ADJ_MSOURCE)
    ]
    print(f"\n[ISWL] {iswl_pol} CONV_ADJ rows: {len(iswl_adj)}")
    if len(iswl_adj) != 0:
        errors.append(f"ISWL {iswl_pol} must not have CONV_ADJ row")
    else:
        print("  PASS: ISWL excluded")

    # Idempotency: at most one CONV_ADJ per MPOLICY
    adj_all = prmh[prmh["MSOURCE"].astype(str).str.strip().str.upper() == CONV_ADJ_MSOURCE]
    dup = adj_all.groupby(adj_all["MPOLICY"].astype(str).str.strip()).size()
    multi = dup[dup > 1]
    print(f"\n[Idempotency] CONV_ADJ policies: {adj_all['MPOLICY'].nunique()} rows: {len(adj_all)}")
    if len(multi) > 0:
        errors.append(f"duplicate CONV_ADJ per policy: {len(multi)}")
        print(f"  FAIL: duplicates on {list(multi.index[:5])}")
    else:
        print("  PASS: one CONV_ADJ max per policy")

    # Validation report reconcile
    val_report = REPORTS / "issue21f_premium_adjustment_validation.csv"
    exc_report = REPORTS / "issue21f_premium_adjustment_exceptions.csv"
    print(f"\n[Reports] validation={val_report.is_file()} exceptions={exc_report.is_file()}")
    if not val_report.is_file():
        errors.append("validation report missing")
    if not exc_report.is_file():
        errors.append("exception report missing")
    if val_report.is_file():
        val = pd.read_csv(val_report, dtype=str).fillna("")
        loaded_like = val[val["STATUS"].isin(["LOADED", "OPENING_BALANCE"])]
        print(f"  report LOADED+OPENING_BALANCE={len(loaded_like)} adj_rows={len(adj_all)}")
        if len(loaded_like) != len(adj_all):
            errors.append(
                f"report LOADED+OPENING ({len(loaded_like)}) != CONV_ADJ rows ({len(adj_all)})"
            )
        else:
            print("  report row count vs CONV_ADJ: PASS")
        loaded_like = loaded_like.copy()
        loaded_like["VAR"] = pd.to_numeric(
            loaded_like["REMAINING_VARIANCE"], errors="coerce"
        ).fillna(999)
        bad_var = loaded_like[loaded_like["VAR"].abs() > 0.02]
        if len(bad_var):
            errors.append(f"{len(bad_var)} LOADED/OPENING rows with nonzero variance in report")
            print(f"  report variance: FAIL ({len(bad_var)} rows)")
        else:
            print("  report variance ~0 for loaded: PASS")
        golden_rep = val[val["MPOLICY"].astype(str).str.strip() == golden_pol]
        if len(golden_rep) == 1:
            gr = golden_rep.iloc[0]
            if str(gr["STATUS"]).strip() not in ("LOADED", "OPENING_BALANCE"):
                errors.append(f"golden report status={gr['STATUS']}")
            if abs(float(str(gr["ADJUSTMENT"]).strip() or 0) - golden_adj) > 0.02:
                errors.append("golden report ADJUSTMENT mismatch")
            if abs(float(str(gr["REMAINING_VARIANCE"]).strip() or 0)) > 0.02:
                errors.append("golden report REMAINING_VARIANCE not zero")
            else:
                print("  golden report reconcile: PASS")

    # Non-candidate history unchanged (optional before snapshot)
    if args.before and args.before.is_file():
        before = pd.read_csv(args.before, dtype=str, encoding="latin1").fillna("")
        before_hist = before[~before.apply(lambda r: is_conversion_adjustment_row(r.to_dict()), axis=1)]
        after_hist = prmh[~prmh.apply(lambda r: is_conversion_adjustment_row(r.to_dict()), axis=1)]
        if len(before_hist) != len(after_hist):
            errors.append(
                f"history row count changed: {len(before_hist)} -> {len(after_hist)}"
            )
            print(f"\n[Regression] history rows changed: FAIL")
        elif not before_hist.equals(after_hist):
            errors.append("history row content changed vs before snapshot")
            print(f"\n[Regression] history content: FAIL")
        else:
            print(f"\n[Regression] existing history rows unchanged: PASS")

    print("\n" + "=" * 72)
    if errors:
        print(f"RESULT: FAIL ({len(errors)} issues)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("RESULT: PASS")
    if args.publish_test_validation:
        pub = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "publish_test_validation.py"),
                "quikprmh",
                "--issue",
                "Issue_21F",
            ],
            cwd=str(ROOT),
            check=False,
        )
        if pub.returncode != 0:
            print("WARN: Test_Validation publish failed")
            return pub.returncode
        print("Published quikprmh -> Output/Test_Validation/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
