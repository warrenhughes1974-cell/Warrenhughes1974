"""
Issue #26 MPREM mapping validation (v57.34).

Validates quikridr.MPREM = ANN_PREM_PER_UNIT when populated, else MODE_PREMIUM fallback.
Confirms unrelated premium fields and row counts are unchanged.

Usage:
  python QLA_Migration/_validate_issue26_mprem.py
  python QLA_Migration/_validate_issue26_mprem.py --before-dir QLA_Migration/Output/_issue26_before
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
SRC = PROJECT_ROOT / "QLA_Migration" / "Source"
CW = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"

TRACE_POLICIES = {
    "010310404C": {"phase": "1", "expected_mprem": 13.20},
    "010331768C": {"phase": "1", "expected_mprem": 10.96},
    "010367131C": {"phase": "1", "expected_mprem": 9.12},
}
EDGE_CASE = {"010718276C": {"phase": "4", "expected_mprem": 1641.30}}

ROW_COUNT_TABLES = [
    "quikridr.csv",
    "quikmstr.csv",
    "quikprmh.csv",
    "quikplan.csv",
    "quikclid.csv",
    "quikclnt.csv",
]


def _num(s) -> float | None:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    t = str(s).strip().replace(",", "")
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _read(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def _close(a, b, tol: float = 0.01) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(a - b) <= tol


def validate(output_dir: Path, before_dir: Path | None) -> int:
    print("=" * 72)
    print(f"ISSUE #26 MPREM VALIDATION (script v{SCRIPT_VERSION}, engine v57.34)")
    print(f"Output: {output_dir}")
    if before_dir:
        print(f"Before snapshot: {before_dir}")
    print("=" * 72)

    errors: list[str] = []
    warnings: list[str] = []

    ridr_path = output_dir / "quikridr.csv"
    mstr_path = output_dir / "quikmstr.csv"
    prmh_path = output_dir / "quikprmh.csv"
    ppben_path = SRC / "PPBEN_PolicyBenefit_Extract_20260530.csv"
    ppolc_path = SRC / "PPOLC_PolicyMaster_Extract_20260530.csv"

    for p in (ridr_path, mstr_path, prmh_path, ppben_path, ppolc_path):
        if not p.is_file():
            errors.append(f"Missing required file: {p}")
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1

    ridr = _read(ridr_path)
    mstr = _read(mstr_path)
    prmh = _read(prmh_path)
    ppben = _read(ppben_path)
    ppolc = _read(ppolc_path)
    cw = pd.read_csv(CW, dtype=str, header=None, names=["LP", "QLA"])
    cw["LP"] = cw["LP"].str.strip()
    cw["QLA"] = cw["QLA"].str.strip()

    ppben = ppben.merge(cw, left_on=ppben["POLICY_NUMBER"].astype(str).str.strip(), right_on="LP", how="left")
    ppben["MPHASE"] = ppben["BENEFIT_SEQ"].astype(str).str.strip().str.lstrip("0").replace("", "0")

    merged = ppben.merge(
        ridr,
        left_on=["QLA", "MPHASE"],
        right_on=["MPOLICY", "MPHASE"],
        how="inner",
        suffixes=("_SRC", "_OUT"),
    )

    # --- Trace policies ---
    print("\n--- Trace policies (phase 1) ---")
    for qla, spec in TRACE_POLICIES.items():
        row = ridr[(ridr["MPOLICY"].str.strip() == qla) & (ridr["MPHASE"].astype(str).str.strip() == spec["phase"])]
        if row.empty:
            errors.append(f"Trace policy {qla} phase {spec['phase']} not found in quikridr")
            print(f"  {qla}: NOT FOUND")
            continue
        mprem = _num(row.iloc[0]["MPREM"])
        ok = _close(mprem, spec["expected_mprem"])
        status = "PASS" if ok else "FAIL"
        print(f"  {qla} MPREM={mprem} expected={spec['expected_mprem']} [{status}]")
        if not ok:
            errors.append(f"Trace {qla}: MPREM={mprem}, expected {spec['expected_mprem']}")

    # --- Edge case ---
    print("\n--- UAT edge case ---")
    for qla, spec in EDGE_CASE.items():
        row = ridr[(ridr["MPOLICY"].str.strip() == qla) & (ridr["MPHASE"].astype(str).str.strip() == spec["phase"])]
        if row.empty:
            errors.append(f"Edge case {qla} phase {spec['phase']} not found")
            print(f"  {qla}: NOT FOUND")
            continue
        mprem = _num(row.iloc[0]["MPREM"])
        ok = _close(mprem, spec["expected_mprem"])
        status = "PASS" if ok else "FAIL"
        print(f"  {qla} phase {spec['phase']} MPREM={mprem} expected={spec['expected_mprem']} [{status}]")
        if not ok:
            errors.append(f"Edge case {qla}: MPREM={mprem}, expected {spec['expected_mprem']}")

    # --- MPREM source alignment ---
    print("\n--- MPREM source alignment ---")
    ann_pop = 0
    ann_match = 0
    fallback_used = 0
    fallback_ok = 0
    for _, r in merged.iterrows():
        ann = _num(r.get("ANN_PREM_PER_UNIT"))
        mode = _num(r.get("MODE_PREMIUM"))
        mprem = _num(r.get("MPREM"))
        if ann is not None and ann != 0:
            ann_pop += 1
            if _close(mprem, ann):
                ann_match += 1
            else:
                errors.append(
                    f"Populated ANN mismatch: {r.get('QLA')} phase {r.get('MPHASE')} "
                    f"MPREM={mprem} ANN={ann}"
                )
        else:
            fallback_used += 1
            if _close(mprem, mode):
                fallback_ok += 1
            elif mprem is None and mode is None:
                fallback_ok += 1
            else:
                errors.append(
                    f"Fallback mismatch: {r.get('QLA')} phase {r.get('MPHASE')} "
                    f"MPREM={mprem} MODE={mode}"
                )

    print(f"  ANN populated rows: {ann_pop}, MPREM matches ANN: {ann_match}")
    print(f"  Fallback rows (blank/zero ANN): {fallback_used}, MPREM matches MODE: {fallback_ok}")
    if ann_pop and ann_match != ann_pop:
        errors.append(f"Only {ann_match}/{ann_pop} populated ANN rows match MPREM")
    if fallback_used and fallback_ok != fallback_used:
        errors.append(f"Only {fallback_ok}/{fallback_used} fallback rows match MODE_PREMIUM")

    # --- MPREM impact count ---
    if before_dir and (before_dir / "quikridr.csv").is_file():
        before_ridr = _read(before_dir / "quikridr.csv")
        key_cols = ["MPOLICY", "MPHASE"]
        b = before_ridr[key_cols + ["MPREM"]].copy()
        b.columns = key_cols + ["MPREM_BEFORE"]
        a = ridr[key_cols + ["MPREM"]].copy()
        a.columns = key_cols + ["MPREM_AFTER"]
        cmp_df = b.merge(a, on=key_cols, how="outer")
        cmp_df["MPREM_BEFORE_N"] = cmp_df["MPREM_BEFORE"].map(_num)
        cmp_df["MPREM_AFTER_N"] = cmp_df["MPREM_AFTER"].map(_num)
        changed = cmp_df[
            ~cmp_df.apply(lambda x: _close(x["MPREM_BEFORE_N"], x["MPREM_AFTER_N"]), axis=1)
        ]
        print(f"\n--- MPREM impact (vs before snapshot) ---")
        print(f"  Rows changed: {len(changed)}")
        print(f"  Rows unchanged: {len(cmp_df) - len(changed)}")
    else:
        ann_diff = merged[
            merged.apply(
                lambda r: not _close(_num(r.get("ANN_PREM_PER_UNIT")), _num(r.get("MPREM")))
                and _num(r.get("ANN_PREM_PER_UNIT")) not in (None, 0),
                axis=1,
            )
        ]
        print(f"\n--- MPREM impact (no before snapshot) ---")
        print(f"  Rows with populated ANN != current MPREM logic: {len(ann_diff)} (expected ~3718)")

    # --- MMODPREM unchanged ---
    print("\n--- quikmstr.MMODPREM (policy modal premium) ---")
    ppolc = ppolc.merge(cw, left_on=ppolc["POLICY_NUMBER"].astype(str).str.strip(), right_on="LP", how="left")
    chk = mstr.merge(ppolc[["QLA", "MODE_PREMIUM"]], left_on="MPOLICY", right_on="QLA", how="inner")
    chk["MMODEPREM_N"] = chk["MMODEPREM"].map(_num)
    chk["MODE_N"] = chk["MODE_PREMIUM"].map(_num)
    mmod_ok = chk.apply(lambda r: _close(r["MMODEPREM_N"], r["MODE_N"]), axis=1).sum()
    print(f"  MMODPREM matches PPOLC MODE_PREMIUM: {mmod_ok}/{len(chk)}")
    if mmod_ok != len(chk):
        errors.append(f"MMODPREM mismatch on {len(chk) - mmod_ok} policies")

    if before_dir and (before_dir / "quikmstr.csv").is_file():
        before_mstr = _read(before_dir / "quikmstr.csv")
        if len(before_mstr) != len(mstr):
            errors.append(f"quikmstr row count changed: {len(before_mstr)} -> {len(mstr)}")
        else:
            diff = before_mstr.merge(mstr, on="MPOLICY", suffixes=("_B", "_A"))
            mmod_changed = diff[diff["MMODEPREM_B"] != diff["MMODEPREM_A"]]
            if len(mmod_changed):
                errors.append(f"MMODPREM changed on {len(mmod_changed)} policies vs before snapshot")
            else:
                print("  MMODPREM unchanged vs before snapshot: PASS")

    # --- MVPU / MUNIT unchanged ---
    print("\n--- MVPU / MUNIT ---")
    mvpu_ok = merged.apply(
        lambda r: _close(_num(r.get("VALUE_PER_UNIT")), _num(r.get("MVPU"))), axis=1
    ).sum()
    munit_ok = merged.apply(
        lambda r: _close(_num(r.get("NUMBER_OF_UNITS")), _num(r.get("MUNIT"))), axis=1
    ).sum()
    print(f"  MVPU matches VALUE_PER_UNIT: {mvpu_ok}/{len(merged)}")
    print(f"  MUNIT matches NUMBER_OF_UNITS: {munit_ok}/{len(merged)}")
    if mvpu_ok != len(merged):
        errors.append(f"MVPU mismatch on {len(merged) - mvpu_ok} rows")
    if munit_ok != len(merged):
        errors.append(f"MUNIT mismatch on {len(merged) - munit_ok} rows")

    # --- Premium history unchanged ---
    print("\n--- quikprmh (premium history) ---")
    if before_dir and (before_dir / "quikprmh.csv").is_file():
        before_prmh = _read(before_dir / "quikprmh.csv")
        if len(before_prmh) != len(prmh):
            errors.append(f"quikprmh row count changed: {len(before_prmh)} -> {len(prmh)}")
        else:
            cols = [c for c in prmh.columns if c in before_prmh.columns]
            if not before_prmh[cols].equals(prmh[cols]):
                errors.append("quikprmh content changed vs before snapshot")
            else:
                print("  quikprmh unchanged vs before snapshot: PASS")
    else:
        print(f"  quikprmh row count: {len(prmh)} (no before snapshot for diff)")

    # --- Row counts ---
    print("\n--- Row counts ---")
    for name in ROW_COUNT_TABLES:
        path = output_dir / name
        count = len(_read(path)) if path.is_file() else 0
        line = f"  {name}: {count}"
        if before_dir:
            bpath = before_dir / name
            bcount = len(_read(bpath)) if bpath.is_file() else None
            if bcount is not None:
                line += f" (before: {bcount})"
                if bcount != count:
                    errors.append(f"{name} row count changed: {bcount} -> {count}")
        print(line)

    # --- Non-MPREM quikridr fields unchanged ---
    if before_dir and (before_dir / "quikridr.csv").is_file():
        print("\n--- quikridr non-MPREM fields ---")
        before_ridr = _read(before_dir / "quikridr.csv")
        non_mprem = sorted({c for c in ridr.columns if c != "MPREM" and c in before_ridr.columns})
        compare_cols = ["MPOLICY", "MPHASE"] + [c for c in non_mprem if c not in ("MPOLICY", "MPHASE")]
        left = before_ridr.loc[:, [c for c in compare_cols if c in before_ridr.columns]].copy()
        right = ridr.loc[:, [c for c in compare_cols if c in ridr.columns]].copy()
        left = left.loc[:, ~left.columns.duplicated()]
        right = right.loc[:, ~right.columns.duplicated()]
        diff = left.merge(right, on=["MPOLICY", "MPHASE"], suffixes=("_B", "_A"), how="outer")
        field_changes = {}
        for col in non_mprem:
            if col in ("MPOLICY", "MPHASE"):
                continue
            bcol, acol = f"{col}_B", f"{col}_A"
            if bcol not in diff.columns or acol not in diff.columns:
                continue
            changed = diff[diff[bcol].fillna("").astype(str) != diff[acol].fillna("").astype(str)]
            if len(changed):
                field_changes[col] = len(changed)
        if field_changes:
            for col, cnt in sorted(field_changes.items(), key=lambda x: -x[1])[:10]:
                errors.append(f"quikridr.{col} changed on {cnt} rows")
            print(f"  Non-MPREM field changes detected: {len(field_changes)} columns")
        else:
            print("  All non-MPREM quikridr fields unchanged: PASS")

    print("\n" + "=" * 72)
    if errors:
        print(f"RESULT: FAIL ({len(errors)} issue(s))")
        for e in errors[:25]:
            print(f"  - {e}")
        if len(errors) > 25:
            print(f"  ... and {len(errors) - 25} more")
        return 1

    print("RESULT: PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Issue #26 MPREM validation")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--before-dir", type=Path, default=None, help="Pre-fix output snapshot for diff")
    args = ap.parse_args()
    return validate(args.output_dir.resolve(), args.before_dir.resolve() if args.before_dir else None)


if __name__ == "__main__":
    sys.exit(main())
