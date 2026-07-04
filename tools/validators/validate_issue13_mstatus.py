"""
Issue #13 MSTATUS validation (v57.48).

When CONTRACT_CODE=T, quikmstr.MSTATUS must follow CONTRACT_REASON (termination),
not PAID_UP_TYPE (non-forfeiture).

Usage:
  python tools/validators/validate_issue13_mstatus.py
  python tools/validators/validate_issue13_mstatus.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
SRC = PROJECT_ROOT / "QLA_Migration" / "Source"
MVT = PROJECT_ROOT / "Master_Value_Translation.csv"
CW = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"

TRACE_POLICIES = {
    "010516211C": "54",  # T/LP — Lapsed
    "011101663C": "56",  # T/EX — Expired
    "010397318C": "53",  # T/DC — Terminated/Death
    "010464590C": "53",  # T/DC — Terminated/Death
    "010784054C": "56",  # T/EX blank PUT — unchanged
}

EXPECTED_CHANGE_COUNT = 607
ROW_COUNT_TOLERANCE = 0

ST_KEYS = {
    "ST_A_": "22", "ST_A_RS": "22", "ST_A_RI": "22", "ST_A_SP": "42",
    "ST_T_DC": "53", "ST_T_SR": "55", "ST_T_LP": "54", "ST_T_MA": "57",
    "ST_T_EX": "56", "ST_T_CV": "90", "ST_S_DP": "50",
    "ST_P_": "41", "ST_P_PUP": "41", "ST_P_RPU": "45", "ST_P_ETI": "44",
    "ST_I_": "10", "ST_I_PND": "10", "ST_I_INP": "12",
    "ST_D_": "53", "ST_D_DTH": "53", "ST_D_PND": "50",
    "ST_PUT_PU": "41", "ST_PUT_RU": "45", "ST_PUT_ET": "44",
    "ST_PUT_LE": "44", "ST_PUT_LP": "54", "ST_PUT_SP": "42",
}


def _s(v) -> str:
    return str(v).strip() if v is not None else ""


def _read(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def load_st_map() -> dict[str, str]:
    df = pd.read_csv(MVT, dtype=str, keep_default_na=False)
    out = dict(ST_KEYS)
    for _, r in df.iterrows():
        k = _s(r.get("Source_Code", ""))
        if k.startswith("ST_"):
            out[k] = _s(r.get("QLA_Result", ""))
    return out


def proposed_key(cc: str, cr: str, put: str) -> str:
    cc = _s(cc).upper()
    cr = _s(cr).upper()
    put = _s(put).upper()
    if cc == "T":
        return f"ST_{cc}_{cr}" if cr else f"ST_{cc}_"
    if put in {"PU", "RU", "ET", "LE", "LP", "SP"}:
        return f"ST_PUT_{put}"
    return f"ST_{cc}_{cr}" if cr else f"ST_{cc}_"


def validate(output_dir: Path) -> int:
    print("=" * 72)
    print(f"ISSUE #13 MSTATUS VALIDATION (script v{SCRIPT_VERSION}, engine v57.48)")
    print(f"Output: {output_dir}")
    print("=" * 72)

    errors: list[str] = []
    warnings: list[str] = []

    mstr_path = output_dir / "quikmstr.csv"
    ridr_path = output_dir / "quikridr.csv"
    ppolc_path = SRC / "PPOLC_PolicyMaster_Extract_20260530.csv"

    for p in (mstr_path, ppolc_path, CW):
        if not Path(p).is_file():
            errors.append(f"Missing required file: {p}")
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1

    st_map = load_st_map()
    mstr = _read(mstr_path)
    ppolc = _read(ppolc_path)
    cw = pd.read_csv(CW, dtype=str, header=None, names=["LP", "QLA"])
    l2q = {_s(a): _s(b) for a, b in zip(cw["LP"], cw["QLA"]) if _s(a)}

    mstr_idx = {_s(r["MPOLICY"]): _s(r.get("MSTATUS", "")) for _, r in mstr.iterrows()}

    print("\n--- Trace policies ---")
    for qla, expected in TRACE_POLICIES.items():
        actual = mstr_idx.get(qla, "")
        ok = actual == expected
        print(f"  {qla}: expected MSTATUS={expected} got={actual or '(missing)'} {'PASS' if ok else 'FAIL'}")
        if not ok:
            errors.append(f"Trace {qla}: expected MSTATUS {expected}, got {actual!r}")

    print("\n--- Fleet derivation vs output ---")
    mismatches = 0
    changes_vs_old = 0
    for _, r in ppolc.iterrows():
        pol = _s(r.get("POLICY_NUMBER", ""))
        if not pol or pol.startswith("-"):
            continue
        qla = l2q.get(pol, pol)
        cc = _s(r.get("CONTRACT_CODE", ""))
        cr = _s(r.get("CONTRACT_REASON", ""))
        put = _s(r.get("PAID_UP_TYPE", ""))
        key = proposed_key(cc, cr, put)
        expected = st_map.get(key, "")
        actual = mstr_idx.get(qla, "")
        if expected and actual != expected:
            mismatches += 1
            if mismatches <= 5:
                errors.append(f"Mismatch {qla}: key={key} expected={expected} got={actual}")
        # count policies that would differ from old PUT-first logic
        old_key = (
            f"ST_PUT_{put.upper()}"
            if _s(put).upper() in {"PU", "RU", "ET", "LE", "LP", "SP"}
            else (f"ST_{cc.upper()}_{cr.upper()}" if cr else f"ST_{cc.upper()}_")
        )
        old_ms = st_map.get(old_key, "")
        if old_ms != expected:
            changes_vs_old += 1

    print(f"  Output mismatches vs Issue #13 rule: {mismatches}")
    print(f"  Policies in T+PUT change population (sim): {changes_vs_old}")

    if mismatches > 0 and len(errors) > len(TRACE_POLICIES):
        pass
    elif mismatches > 0:
        errors.append(f"Fleet mismatches: {mismatches}")

    if abs(changes_vs_old - EXPECTED_CHANGE_COUNT) > ROW_COUNT_TOLERANCE:
        warnings.append(
            f"Change population {changes_vs_old} != expected {EXPECTED_CHANGE_COUNT} "
            "(re-run risk sim if source changed)"
        )

    print("\n--- Row counts ---")
    row_count = len(mstr)
    print(f"  quikmstr rows: {row_count}")
    if row_count != len(ppolc) - 1:  # minus header garbage row
        warnings.append(f"quikmstr rows {row_count} vs PPOLC ~5084")

    if ridr_path.is_file():
        ridr = _read(ridr_path)
        sub = ridr[(ridr["MPOLICY"] == "010516211C") & (ridr["MPHASE"] == "1")]
        if not sub.empty:
            mph = _s(sub.iloc[0].get("MPHSTAT", ""))
            print(f"  quikridr 010516211C phase-1 MPHSTAT: {mph}")
            if mph != "54":
                errors.append(f"quikridr 010516211C MPHSTAT expected 54, got {mph}")

    print("\n--- Premium untouched spot check (#26) ---")
    if ridr_path.is_file():
        ridr = _read(ridr_path)
        row = ridr[(ridr["MPOLICY"] == "010516211C") & (ridr["MPHASE"] == "1")]
        if not row.empty:
            mprem = _s(row.iloc[0].get("MPREM", ""))
            print(f"  010516211C MPREM: {mprem} (unchanged check manual)")

    print("\n" + "=" * 72)
    if warnings:
        for w in warnings:
            print(f"WARN: {w}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        for e in errors[:20]:
            print(f"  - {e}")
        return 1
    print("RESULT: PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Issue #13 MSTATUS validation")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()
    return validate(args.output_dir.resolve())


if __name__ == "__main__":
    sys.exit(main())
