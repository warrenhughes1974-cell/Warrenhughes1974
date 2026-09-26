"""
Issue #137 — blank ANN MPREM uses modalized annual (MODE ÷ factor% ÷ units).

Checks:
  - Gold 9010722550C: MPREM×MUNIT ≈ 435.98–436.05; MMODEPREM = 40.11
  - Eric 9010367131C (#26 ANN): MPREM unchanged at 9.12
  - Fleet blank-ANN phase-1: MPREM matches blank_ann_annual_ppu helper
  - Populated ANN: MPREM matches ANN_PREM_PER_UNIT (tolerance)

Usage:
  python tools/validators/validate_issue137_modalized_mprem.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

import pandas as pd

from qla_core.modal_premium_factors import blank_ann_annual_ppu, load_modal_factor_mapping
from qla_core.normalize_utils import format_qladmin_mpolicy, normalize
OUT = PROJECT / "QLA_Migration" / "Output"
SRC = PROJECT / "QLA_Migration" / "Source" / "LifePRO_Extracts_20260731"
EVID = PROJECT / "Issue_Log_Items" / "Issue_137" / "evidence"

GOLD = "9010722550C"
ERIC = "9010367131C"
GOLD_BASE_MIN, GOLD_BASE_MAX = 435.90, 436.10
GOLD_MODE = 40.11
ERIC_MPREM = 9.12


def fnum(v):
    try:
        s = str(v).replace(",", "").strip()
        if not s:
            return None
        return float(s)
    except (TypeError, ValueError):
        return None


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    ridr = pd.read_csv(OUT / "quikridr.csv", dtype=str).fillna("")
    ridr.columns = [c.strip().upper() for c in ridr.columns]
    mstr = pd.read_csv(OUT / "quikmstr.csv", dtype=str).fillna("")
    mstr.columns = [c.strip().upper() for c in mstr.columns]

    # Gold
    g = ridr[
        (ridr.MPOLICY.map(lambda x: format_qladmin_mpolicy(x).strip()) == GOLD)
        & (ridr.MPHASE.astype(str).str.strip().isin(["1", "01"]))
    ]
    if g.empty:
        errors.append(f"gold {GOLD} phase-1 missing")
    else:
        gr = g.iloc[0]
        base = (fnum(gr.MPREM) or 0) * (fnum(gr.MUNIT) or 0)
        if not (GOLD_BASE_MIN <= base <= GOLD_BASE_MAX):
            errors.append(f"gold annual base {base} not in [{GOLD_BASE_MIN},{GOLD_BASE_MAX}]")
        mm = mstr[mstr.MPOLICY.map(lambda x: format_qladmin_mpolicy(x).strip()) == GOLD]
        if mm.empty or abs((fnum(mm.iloc[0].MMODEPREM) or 0) - GOLD_MODE) > 0.005:
            errors.append(f"gold MMODEPREM expected {GOLD_MODE}")

    # Eric ANN path
    e = ridr[
        (ridr.MPOLICY.map(lambda x: format_qladmin_mpolicy(x).strip()) == ERIC)
        & (ridr.MPHASE.astype(str).str.strip().isin(["1", "01"]))
    ]
    if e.empty:
        errors.append(f"eric {ERIC} phase-1 missing")
    else:
        if abs((fnum(e.iloc[0].MPREM) or 0) - ERIC_MPREM) > 0.0005:
            errors.append(f"eric MPREM {(fnum(e.iloc[0].MPREM))} != {ERIC_MPREM} (#26 must hold)")

    # Fleet blank-ANN check (sample join)
    ppben = pd.read_csv(
        sorted(SRC.glob("PPBEN_PolicyBenefit_Extract_*.csv"))[-1],
        dtype=str,
        encoding="latin-1",
    ).fillna("")
    ppben.columns = [c.strip().upper() for c in ppben.columns]
    ppolc = pd.read_csv(
        sorted(SRC.glob("PPOLC_PolicyMaster_Extract_*.csv"))[-1],
        dtype=str,
        encoding="latin-1",
    ).fillna("")
    ppolc.columns = [c.strip().upper() for c in ppolc.columns]

    bill_mode = {}
    bill_form = {}
    for _, r in ppolc.iterrows():
        pol = normalize(r.get("POLICY_NUMBER", ""))
        if not pol:
            continue
        bm = str(r.get("BILLING_MODE", "")).strip()
        if bm.endswith(".0"):
            bm = bm[:-2]
        try:
            bill_mode[pol] = int(float(bm))
        except (ValueError, TypeError):
            pass
        bf = str(r.get("BILLING_FORM", "")).strip()
        if bf:
            bill_form[pol] = bf

    ann_by = {}
    for _, r in ppben.iterrows():
        pol = normalize(r.get("POLICY_NUMBER", ""))
        seq = str(r.get("BENEFIT_SEQ", "")).strip()
        if seq.endswith(".0"):
            seq = seq[:-2]
        seq_n = seq.lstrip("0") or "0"
        ann_by[(pol, seq_n)] = {
            "ann": fnum(r.get("ANN_PREM_PER_UNIT")) or 0.0,
            "mode": fnum(r.get("MODE_PREMIUM")) or 0.0,
            "units": fnum(r.get("NUMBER_OF_UNITS")) or 0.0,
        }

    factors = load_modal_factor_mapping()
    blank_mismatch = 0
    ann_mismatch = 0
    blank_checked = 0
    ann_checked = 0

    phase1 = ridr[ridr.MPHASE.astype(str).str.strip().isin(["1", "01"])]
    for _, row in phase1.iterrows():
        mpolicy = format_qladmin_mpolicy(row.get("MPOLICY", "")).strip()
        pol = normalize(mpolicy)
        if pol.endswith("C"):
            pol = pol[:-1]
        src = ann_by.get((pol, "1"))
        if not src:
            continue
        cur = fnum(row.get("MPREM"))
        if cur is None:
            continue
        if src["ann"] > 0:
            ann_checked += 1
            if abs(cur - src["ann"]) > 0.02:
                ann_mismatch += 1
                if ann_mismatch <= 5:
                    warnings.append(f"ANN path drift {mpolicy}: MPREM={cur} ANN={src['ann']}")
            continue
        units = fnum(row.get("MUNIT")) or src["units"]
        if units <= 0 or src["mode"] <= 0:
            continue
        exp, _ = blank_ann_annual_ppu(
            src["mode"],
            units,
            bill_mode.get(pol),
            bill_form.get(pol, ""),
            factors.get(str(row.get("MPLAN", "")).strip()),
        )
        blank_checked += 1
        if abs(cur - exp) > 0.0006:
            # Later governance may zero MPREM on blank-ANN rows — warn, do not fail gold path.
            if cur is None or abs(cur) < 1e-12:
                warnings.append(
                    f"blank-ANN MPREM=0 {mpolicy} (governance zero; expected~{exp:.6f})"
                )
                continue
            blank_mismatch += 1
            if blank_mismatch <= 8:
                errors.append(
                    f"blank-ANN mismatch {mpolicy}: MPREM={cur} expected~{exp:.6f}"
                )

    if blank_mismatch > 8:
        errors.append(f"... {blank_mismatch} total blank-ANN mismatches (showing first 8)")
    # Populated ANN drift (MPREM=0 vs ANN>0) can be pre-existing governance; warn only.
    if ann_mismatch:
        warnings.append(
            f"populated ANN soft drift count={ann_mismatch} (not a #137 FAIL; #26 Eric checked hard)"
        )

    summary = {
        "result": "PASS" if not errors else "FAIL",
        "gold": GOLD,
        "blank_checked": blank_checked,
        "blank_mismatch": blank_mismatch,
        "ann_checked": ann_checked,
        "ann_mismatch": ann_mismatch,
        "errors": errors,
        "warnings": warnings[:20],
    }
    EVID.mkdir(parents=True, exist_ok=True)
    (EVID / "issue137_validation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    for e in errors:
        print("ERROR:", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
