"""
Issue #88 — validate blank ANN_PREM_PER_UNIT MPREM fallback.

Rule:
  if ANN_PREM_PER_UNIT != 0: MPREM == ANN
  else if units > 0: MPREM == (MODE_PREMIUM * ann_factor(BILLING_MODE)) / units
  MMODEPREM / policy modal premium untouched (checked on quikmstr for anchor)

Usage:
  python tools/validators/validate_issue88_mprem_unit_fallback.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
SRC = PROJECT / "QLA_Migration" / "Source"
OUT = PROJECT / "QLA_Migration" / "Output"
CW = PROJECT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"

ANCHOR = "010779727C"
ANN_FACTOR = {12: 1.0, 6: 2.0, 3: 4.0, 1: 12.0}
TRACE_ANN = {
    ("010310404C", "1"): 13.20,
    ("010331768C", "1"): 10.96,
    ("010367131C", "1"): 9.12,
}


def fnum(v):
    try:
        s = str(v).replace(",", "").strip()
        if not s:
            return None
        return float(s)
    except (TypeError, ValueError):
        return None


def load_cw():
    cw = {}
    with open(CW, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.reader(f):
            if len(row) < 2:
                continue
            lp, ql = row[0].strip(), row[1].strip()
            if lp and ql and lp.lower() != "policy_number":
                cw[lp] = ql
    return cw


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    errors = []
    warnings = []

    cw = load_cw()
    ridr = {}
    with open(OUT / "quikridr.csv", newline="", encoding="latin1", errors="replace") as f:
        for r in csv.DictReader(f):
            r = {k.strip().upper(): (v or "").strip() for k, v in r.items()}
            phase = str(int(float(r["MPHASE"]))) if fnum(r.get("MPHASE")) is not None else r.get("MPHASE", "")
            ridr[(r["MPOLICY"], phase)] = r

    mstr = {}
    mstr_path = OUT / "quikmstr.csv"
    if mstr_path.exists():
        with open(mstr_path, newline="", encoding="latin1", errors="replace") as f:
            for r in csv.DictReader(f):
                r = {k.strip().upper(): (v or "").strip() for k, v in r.items()}
                mstr[r["MPOLICY"]] = r

    ppolc_mode = {}
    ppolc = next(SRC.glob("PPOLC_PolicyMaster_Extract_*.csv"), None)
    if ppolc:
        with open(ppolc, newline="", encoding="latin1", errors="replace") as f:
            for r in csv.DictReader(f):
                r = {k.strip().upper(): (v or "").strip() for k, v in r.items()}
                bm = fnum(r.get("BILLING_MODE"))
                if bm is not None:
                    ppolc_mode[r["POLICY_NUMBER"]] = int(bm)

    ppben = next(SRC.glob("PPBEN_PolicyBenefit_Extract_*.csv"), None)
    if not ppben:
        print("FAIL: PPBEN extract not found")
        return 1

    checked = mismatches = 0
    with open(ppben, newline="", encoding="latin1", errors="replace") as f:
        for r in csv.DictReader(f):
            r = {k.strip().upper(): (v or "").strip() for k, v in r.items()}
            lp = r.get("POLICY_NUMBER", "")
            ql = cw.get(lp)
            if not ql:
                continue
            phase = str(int(float(r["BENEFIT_SEQ"]))) if fnum(r.get("BENEFIT_SEQ")) is not None else r.get("BENEFIT_SEQ")
            out = ridr.get((ql, phase))
            if not out:
                continue
            ann = fnum(r.get("ANN_PREM_PER_UNIT"))
            mode_prem = fnum(r.get("MODE_PREMIUM")) or 0.0
            units = fnum(r.get("NUMBER_OF_UNITS")) or 0.0
            cur = fnum(out.get("MPREM"))
            if ann is not None and abs(ann) > 1e-12:
                expected = ann
            elif units > 0:
                factor = ANN_FACTOR.get(ppolc_mode.get(lp, 12), 1.0)
                expected = (mode_prem * factor) / units
            else:
                expected = None

            checked += 1
            if expected is None:
                if cur not in (None, 0.0):
                    # blank allowed
                    pass
                continue
            if cur is None or abs(cur - expected) > 0.02:
                mismatches += 1
                if mismatches <= 15:
                    errors.append(
                        f"{ql} ph{phase}: MPREM={cur} expected≈{expected:.6f} "
                        f"(ANN={ann} MODE={mode_prem} units={units} bill={ppolc_mode.get(lp)})"
                    )

    # Anchor checks
    a = ridr.get((ANCHOR, "1"))
    if not a:
        errors.append(f"Anchor {ANCHOR} ph1 missing from quikridr")
    else:
        mprem = fnum(a.get("MPREM"))
        if mprem is None or abs(mprem - 5.8615) > 0.01:
            errors.append(f"Anchor {ANCHOR} ph1 MPREM={mprem} expected≈5.8615")
        else:
            print(f"PASS anchor Prem/Unit: {ANCHOR} ph1 MPREM={mprem}")
        if mstr.get(ANCHOR):
            mm = fnum(mstr[ANCHOR].get("MMODEPREM"))
            if mm is None or abs(mm - 2930.75) > 0.02:
                warnings.append(f"Anchor Mode Prem MMODEPREM={mm} (expected 2930.75 if unchanged)")
            else:
                print(f"PASS anchor Mode Prem: {ANCHOR} MMODEPREM={mm}")

    for (pol, ph), exp in TRACE_ANN.items():
        row = ridr.get((pol, ph))
        if not row:
            warnings.append(f"Trace {pol} ph{ph} missing")
            continue
        got = fnum(row.get("MPREM"))
        if got is None or abs(got - exp) > 0.01:
            errors.append(f"Issue #26 trace {pol} ph{ph}: MPREM={got} expected {exp}")
        else:
            print(f"PASS #26 trace {pol} ph{ph} MPREM={got}")

    print(f"Checked joined rows: {checked}; MPREM mismatches (>0.02): {mismatches}")
    for w in warnings:
        print("WARN:", w)
    if errors:
        print("FAIL:")
        for e in errors:
            print(" ", e)
        return 1
    if mismatches:
        print(f"FAIL: {mismatches} MPREM mismatches")
        return 1
    print("PASS Issue #88 MPREM unit fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
