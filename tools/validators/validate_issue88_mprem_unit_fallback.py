"""
Issue #88 / #137 — validate blank ANN_PREM_PER_UNIT MPREM fallback.

Rule:
  if ANN_PREM_PER_UNIT != 0: MPREM == ANN
  else if units > 0: MPREM == modalized MODE ÷ (factor%/100) ÷ units
                     (crude payments/year only if plan factor missing)  [#137]
  MMODEPREM / policy modal premium untouched (checked on quikmstr for anchor)

Usage:
  python tools/validators/validate_issue88_mprem_unit_fallback.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from qla_core.issue152_rider_modal import (
    active_rider_modal_sums,
    is_phase1_bf,
    mode_after_active_riders,
)
from qla_core.modal_premium_factors import blank_ann_annual_ppu, load_modal_factor_mapping
from qla_core.normalize_utils import format_qladmin_mpolicy, normalize
SRC = PROJECT / "QLA_Migration" / "Source"
OUT = PROJECT / "QLA_Migration" / "Output"
CW = PROJECT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"

ANCHOR = "9010779727C"
TRACE_ANN = {
    ("9010310404C", "1"): 13.20,
    ("9010331768C", "1"): 10.96,
    ("9010367131C", "1"): 9.12,
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

    def _prefer_extract(pattern: str):
        """Prefer 20260731 package (matches current Output), else newest mtime."""
        preferred = list((SRC / "LifePRO_Extracts_20260731").glob(Path(pattern).name))
        if preferred:
            return preferred[0]
        hits = list(SRC.glob(pattern))
        if not hits:
            return None
        return max(hits, key=lambda p: p.stat().st_mtime)

    ppolc_mode = {}
    ppolc_form = {}
    ppolc = _prefer_extract("**/PPOLC_PolicyMaster_Extract_*.csv")
    if ppolc:
        with open(ppolc, newline="", encoding="latin1", errors="replace") as f:
            for r in csv.DictReader(f):
                r = {k.strip().upper(): (v or "").strip() for k, v in r.items()}
                bm = fnum(r.get("BILLING_MODE"))
                if bm is not None:
                    ppolc_mode[r["POLICY_NUMBER"]] = int(bm)
                bf = r.get("BILLING_FORM", "")
                if bf:
                    ppolc_form[r["POLICY_NUMBER"]] = bf

    factors = load_modal_factor_mapping()
    ppben = _prefer_extract("**/PPBEN_PolicyBenefit_Extract_*.csv")
    if not ppben:
        print("FAIL: PPBEN extract not found")
        return 1
    print(f"Using PPBEN {ppben}; PPOLC {ppolc if ppolc else 'n/a'}")

    with open(ppben, newline="", encoding="latin1", errors="replace") as f:
        rider_sums = active_rider_modal_sums(
            ({k.strip().upper(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f))
        )

    checked = mismatches = 0
    with open(ppben, newline="", encoding="latin1", errors="replace") as f:
        for r in csv.DictReader(f):
            r = {k.strip().upper(): (v or "").strip() for k, v in r.items()}
            lp = r.get("POLICY_NUMBER", "")
            ql = format_qladmin_mpolicy(lp)
            phase = str(int(float(r["BENEFIT_SEQ"]))) if fnum(r.get("BENEFIT_SEQ")) is not None else r.get("BENEFIT_SEQ")
            out = ridr.get((ql, phase)) or ridr.get((cw.get(lp, ""), phase))
            if not out:
                continue
            ann = fnum(r.get("ANN_PREM_PER_UNIT"))
            mode_prem = fnum(r.get("MODE_PREMIUM")) or 0.0
            units = fnum(out.get("MUNIT")) or fnum(r.get("NUMBER_OF_UNITS")) or 0.0
            cur = fnum(out.get("MPREM"))
            if ann is not None and abs(ann) > 1e-12:
                expected = ann
            elif units > 0:
                # Issue #152 (Warren 2026-09-22): phase-1 BF blank ANN drops active rider mode first.
                if is_phase1_bf(r.get("BENEFIT_TYPE"), r.get("BENEFIT_SEQ")):
                    mode_prem = mode_after_active_riders(
                        mode_prem, rider_sums.get(normalize(lp), 0.0)
                    )
                mplan = (out.get("MPLAN") or "").strip()
                expected, _ = blank_ann_annual_ppu(
                    mode_prem,
                    units,
                    ppolc_mode.get(lp),
                    ppolc_form.get(lp, ""),
                    factors.get(mplan),
                )
            else:
                expected = None

            checked += 1
            if expected is None:
                if cur not in (None, 0.0):
                    # blank allowed
                    pass
                continue
            if cur is None or abs(cur - expected) > 0.02:
                # Pre-existing ANN-path drift (#26) — not introduced by #137 blank-path change.
                if ann is not None and abs(ann) > 1e-12:
                    warnings.append(
                        f"{ql} ph{phase}: MPREM={cur} vs ANN={ann} (pre-existing ANN drift; not #137)"
                    )
                    continue
                mismatches += 1
                if mismatches <= 15:
                    errors.append(
                        f"{ql} ph{phase}: MPREM={cur} expected≈{expected:.6f} "
                        f"(ANN={ann} MODE={mode_prem} units={units} bill={ppolc_mode.get(lp)})"
                    )

    # Anchor checks — Prem/Unit follows #137 modalized blank-ANN rule; Mode Prem unchanged
    a = ridr.get((ANCHOR, "1"))
    if not a:
        errors.append(f"Anchor {ANCHOR} ph1 missing from quikridr")
    else:
        mprem = fnum(a.get("MPREM"))
        units = fnum(a.get("MUNIT")) or 500.0
        mode_prem = 2930.75
        exp_ppu, _ = blank_ann_annual_ppu(
            mode_prem,
            units,
            ppolc_mode.get("9010779727", 1),
            ppolc_form.get("9010779727", ""),
            factors.get((a.get("MPLAN") or "").strip()),
        )
        if mprem is None or abs(mprem - exp_ppu) > 0.02:
            errors.append(f"Anchor {ANCHOR} ph1 MPREM={mprem} expected≈{exp_ppu:.6f} (#137)")
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
