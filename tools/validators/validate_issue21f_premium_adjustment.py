"""Validate Issue #21F conversion premium adjustment on quikprmh (v58.79+ all plans)."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "1.2"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output"
REPORTS = ROOT / "QLA_Migration" / "Reports"
# Midyear closure golden (20260630). Active cuts supersede via the 21F validation report.
MIDYEAR_GOLDEN_ADJ = 15193.85
MIDYEAR_LIFEPRO_TOTAL = 17040.05
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
    print(
        f"ISSUE #21F — CONVERSION PREMIUM ADJUSTMENT VALIDATION "
        f"(engine v58.79+ / validator {SCRIPT_VERSION})"
    )
    print("=" * 72)
    errors: list[str] = []

    prmh_path = OUT / "quikprmh.csv"
    if not prmh_path.is_file():
        errors.append("quikprmh.csv missing in Output")
        print("FAIL: quikprmh.csv not found")
        return 1

    prmh = pd.read_csv(prmh_path, dtype=str, encoding="utf-8-sig").fillna("")
    prmh.columns = [str(c).strip().upper().lstrip("\ufeff") for c in prmh.columns]
    print(f"\nquikprmh rows: {len(prmh)}")

    # Schema
    if list(prmh.columns) != SCHEMA:
        errors.append(f"schema drift: {list(prmh.columns)}")
        print("FAIL: column order mismatch")
    else:
        print("  schema order: PASS")

    # Golden policy — Issue #2 loadable key 9010310404C (legacy alias 010310404C)
    golden_pol = "9010310404C"
    golden_aliases = {golden_pol, "010310404C"}
    golden_adj = MIDYEAR_GOLDEN_ADJ
    lifepro_total = MIDYEAR_LIFEPRO_TOTAL
    golden_src = f"midyear golden ({MIDYEAR_LIFEPRO_TOTAL})"
    val_report_early = REPORTS / "issue21f_premium_adjustment_validation.csv"
    if val_report_early.is_file():
        _val_early = pd.read_csv(val_report_early, dtype=str).fillna("")
        _g = _val_early[_val_early["MPOLICY"].astype(str).str.strip().isin(golden_aliases)]
        if len(_g) == 1:
            _gr = _g.iloc[0]
            try:
                lifepro_total = float(str(_gr.get("LIFEPRO_TOTAL", "")).strip() or 0)
                golden_adj = float(str(_gr.get("ADJUSTMENT", "")).strip() or 0)
                golden_src = (
                    f"report LIFEPRO_TOTAL={lifepro_total:.2f} "
                    f"ADJUSTMENT={golden_adj:.2f}"
                )
            except ValueError:
                pass
    print(f"\n[Golden expectations] {golden_src}")

    adj_rows = prmh[
        (prmh["MPOLICY"].astype(str).str.strip().isin(golden_aliases))
        & (prmh["MSOURCE"].astype(str).str.strip().str.upper() == CONV_ADJ_MSOURCE)
    ]
    print(f"\n[Golden] {golden_pol} CONV_ADJ rows: {len(adj_rows)}")
    if len(adj_rows) != 1:
        errors.append(f"golden: expected 1 CONV_ADJ on {golden_pol}, got {len(adj_rows)}")
    else:
        row = adj_rows.iloc[0]
        got_key = str(row["MPOLICY"]).strip()
        prem = float(str(row["PREMIUM"]).strip() or 0)
        datepaid = str(row["DATEPAID"]).strip()
        user_id = str(row["USER_ID"]).strip().upper()
        ok_key = got_key == golden_pol
        ok_prem = abs(prem - golden_adj) < 0.02
        ok_date = datepaid == CONV_ADJ_DATEPAID
        ok_user = user_id == CONV_ADJ_USER_ID
        print(f"  MPOLICY={got_key!r} expect={golden_pol!r} -> {'PASS' if ok_key else 'FAIL'}")
        print(f"  PREMIUM={prem} expect={golden_adj} -> {'PASS' if ok_prem else 'FAIL'}")
        print(f"  DATEPAID={datepaid} expect={CONV_ADJ_DATEPAID} -> {'PASS' if ok_date else 'FAIL'}")
        print(f"  USER_ID={user_id} -> {'PASS' if ok_user else 'FAIL'}")
        if not (ok_key and ok_prem and ok_date and ok_user):
            errors.append(f"golden {golden_pol} adjustment mismatch")

        # Total reconcile for golden
        hist_mask = ~prmh.apply(lambda r: is_conversion_adjustment_row(r.to_dict()), axis=1)
        hist_sum = prmh.loc[
            (prmh["MPOLICY"].astype(str).str.strip() == golden_pol) & hist_mask,
            "PREMIUM",
        ].map(lambda x: float(str(x).strip() or 0) if str(x).strip() else 0.0).sum()
        total = hist_sum + prem
        print(f"  hist={hist_sum:.2f} + adj={prem:.2f} = {total:.2f} (LifePRO {lifepro_total})")
        if abs(total - lifepro_total) > 0.02:
            errors.append(f"golden total reconcile failed: {total}")

    # ISWL must HAVE CONV_ADJ (v58.79+ — FV_GUAR_DEPOSITS authority)
    iswl_pol = "9010718309C"
    iswl_aliases = {iswl_pol, "010718309C"}
    iswl_adj = prmh[
        (prmh["MPOLICY"].astype(str).str.strip().isin(iswl_aliases))
        & (prmh["MSOURCE"].astype(str).str.strip().str.upper() == CONV_ADJ_MSOURCE)
    ]
    print(f"\n[ISWL] {iswl_pol} CONV_ADJ rows: {len(iswl_adj)}")
    if len(iswl_adj) != 1:
        errors.append(f"ISWL {iswl_pol}: expected 1 CONV_ADJ, got {len(iswl_adj)}")
    else:
        irow = iswl_adj.iloc[0]
        iprem = float(str(irow["PREMIUM"]).strip() or 0)
        idate = str(irow["DATEPAID"]).strip()
        ok_i = idate == CONV_ADJ_DATEPAID and iprem > 0
        print(f"  DATEPAID={idate} PREMIUM={iprem:.2f} -> {'PASS' if ok_i else 'FAIL'}")
        if not ok_i:
            errors.append(f"ISWL {iswl_pol} CONV_ADJ marker/amount mismatch")
        # Prefer report ADJUSTMENT when present
        expect_iswl = None
        if val_report_early.is_file():
            _val_iswl = pd.read_csv(val_report_early, dtype=str).fillna("")
            _vi = _val_iswl[_val_iswl["MPOLICY"].astype(str).str.strip().isin(iswl_aliases)]
            if len(_vi) == 1:
                try:
                    expect_iswl = float(str(_vi.iloc[0].get("ADJUSTMENT", "")).strip() or 0)
                except ValueError:
                    expect_iswl = None
        if expect_iswl is not None and abs(iprem - expect_iswl) > 0.02:
            errors.append(
                f"ISWL {iswl_pol} PREMIUM={iprem} != report ADJUSTMENT={expect_iswl}"
            )
        elif expect_iswl is None and abs(iprem - 4243.06) > 0.02:
            # UAT-proven 7/31 gold when report missing
            errors.append(f"ISWL {iswl_pol} PREMIUM={iprem} expected ~4243.06")
        else:
            print("  PASS: ISWL CONV_ADJ present (FV deposits - history)")

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

    # Join to quikmstr + no orphan *CC keys (Wave 0 / Cut Completeness)
    mstr_path = OUT / "quikmstr.csv"
    if mstr_path.is_file() and len(adj_all):
        mstr = pd.read_csv(mstr_path, dtype=str, encoding="latin1").fillna("")
        mstr_set = set(mstr["MPOLICY"].astype(str).str.strip())
        adj_keys = set(adj_all["MPOLICY"].astype(str).str.strip())
        orphan = sorted(adj_keys - mstr_set)
        # *CC alone is not a defect when source policy already ends in C and mstr matches
        # (Issue #2 grain). Fail only when *CC keys are orphans vs quikmstr.
        cc_orphan = [k for k in orphan if k.endswith("CC")]
        print(f"\n[Join mstr] CONV_ADJ={len(adj_keys)} join={len(adj_keys) - len(orphan)} orphan={len(orphan)}")
        if orphan:
            errors.append(f"CONV_ADJ orphan vs quikmstr: {len(orphan)} (sample={orphan[:5]})")
        else:
            print("  PASS: every CONV_ADJ MPOLICY in quikmstr")
        if cc_orphan:
            errors.append(f"CONV_ADJ *CC orphan vs mstr: {len(cc_orphan)} (sample={cc_orphan[:5]})")
        else:
            print("  PASS: no orphan *CC CONV_ADJ keys")
    elif len(adj_all):
        errors.append("quikmstr.csv missing — cannot prove CONV_ADJ join")

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
