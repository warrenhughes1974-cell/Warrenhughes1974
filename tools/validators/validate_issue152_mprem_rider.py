"""Issue #152 — blank-ANN base Prem/Unit excludes active rider mode premium.

Fail-closed against full QLA_Migration/Output/quikridr.csv and quikmstr.csv.

Rule (Warren 2026-09-22 exception to Closed #88):
  phase-1 BF, ANN_PREM_PER_UNIT blank/zero, active SU/SL/OR MODE_PREMIUM > 0:
      MPREM = blank_ann_annual_ppu(base MODE - sum of those rider modes, ...)
  Rider-phase MPREM and quikmstr.MMODEPREM stay unchanged.

Usage:
  python tools/validators/validate_issue152_mprem_rider.py
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
from qla_core.modal_premium_factors import (
    blank_ann_annual_ppu,
    format_mprem_ppu,
    load_modal_factor_mapping,
)
from qla_core.normalize_utils import format_qladmin_mpolicy, normalize

OUT = PROJECT / "QLA_Migration" / "Output"
SRC = PROJECT / "QLA_Migration" / "Source"

# Client examples and the two-rider quarterly case. Values are annual Prem/Unit.
GOLDS = {
    "9010723388C": 7.82,
    "9010723386C": 7.52,
    "9011069655C": 8.47,
    "9010987095C": 7.48,
}
# Populated ANN, terminated riders, or no positive active rider. Must not move.
HOLDS = {
    "9010779552C": 7.73,
    "9010767171C": 2.168,
    "9010722550C": 8.71966,
    "9010779727C": 5.8615,
}
# Billed mode premium after Issue 139. This issue must not change it.
BILLED = {
    "9010723388C": 857.00,
    "9010723386C": 827.00,
    "9011069655C": 844.00,
    "9010987095C": 46.18,
}
# Rider phases that must stay.
RIDER_HOLDS = {
    ("9010723388C", "2"): 1.00,
    ("9010723386C", "2"): 1.00,
    ("9011069655C", "2"): 0.22,
    ("9010987095C", "2"): 0.18,
    ("9010987095C", "3"): 0.19520,
}


def fnum(v):
    try:
        s = str(v).replace(",", "").strip()
        if not s:
            return None
        return float(s)
    except (TypeError, ValueError):
        return None


def _phase(v) -> str:
    n = fnum(v)
    if n is None:
        return str(v or "").strip()
    return str(int(n))


def _prefer_extract(name_prefix: str) -> Path | None:
    root_hits = list(SRC.glob(f"{name_prefix}_*.csv"))
    if root_hits:
        return max(root_hits, key=lambda p: p.stat().st_mtime)
    hits = list(SRC.glob(f"**/{name_prefix}_*.csv"))
    if not hits:
        return None
    return max(hits, key=lambda p: p.stat().st_mtime)


def _read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="latin1", errors="replace") as f:
        return [
            {k.strip().upper(): (v or "").strip() for k, v in row.items()}
            for row in csv.DictReader(f)
        ]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    errors = []
    ppben_path = _prefer_extract("PPBEN_PolicyBenefit_Extract")
    ppolc_path = _prefer_extract("PPOLC_PolicyMaster_Extract")
    ridr_path = OUT / "quikridr.csv"
    mstr_path = OUT / "quikmstr.csv"
    if not ppben_path or not ppolc_path or not ridr_path.is_file() or not mstr_path.is_file():
        print("FAIL: missing PPBEN, PPOLC, quikridr, or quikmstr")
        return 1

    ppben = _read_rows(ppben_path)
    ppolc = _read_rows(ppolc_path)
    bill_mode = {}
    bill_form = {}
    for row in ppolc:
        pol = normalize(row.get("POLICY_NUMBER"))
        if not pol:
            continue
        bm = fnum(row.get("BILLING_MODE"))
        if bm is not None:
            bill_mode[pol] = int(bm)
        bf = row.get("BILLING_FORM", "")
        if bf:
            bill_form[pol] = bf

    factors = load_modal_factor_mapping()
    # Plan factors are keyed by QLAdmin MPLAN, which is not always PPBEN PLAN_CODE.
    # Recompute with the emitted MPLAN so the check matches the converter.
    sums = active_rider_modal_sums(ppben)
    base_src = {}
    for row in ppben:
        if not is_phase1_bf(row.get("BENEFIT_TYPE"), row.get("BENEFIT_SEQ")):
            continue
        pol = normalize(row.get("POLICY_NUMBER"))
        base_src[format_qladmin_mpolicy(pol).strip()] = row

    ridr = {}
    with ridr_path.open(newline="", encoding="latin1", errors="replace") as f:
        for row in csv.DictReader(f):
            rec = {k.strip().upper(): (v or "").strip() for k, v in row.items()}
            ridr.setdefault(rec.get("MPOLICY", "").strip(), {})[_phase(rec.get("MPHASE"))] = rec

    mstr = {}
    with mstr_path.open(newline="", encoding="latin1", errors="replace") as f:
        for row in csv.DictReader(f):
            rec = {k.strip().upper(): (v or "").strip() for k, v in row.items()}
            mstr[rec.get("MPOLICY", "").strip()] = rec

    scoped = 0
    matched = 0
    for qla, src in base_src.items():
        ann = fnum(src.get("ANN_PREM_PER_UNIT")) or 0.0
        if abs(ann) > 1e-12:
            continue
        pol = normalize(src.get("POLICY_NUMBER"))
        rider_sum = sums.get(pol, 0.0)
        if rider_sum <= 0.0:
            continue
        units = fnum(src.get("NUMBER_OF_UNITS")) or 0.0
        if units <= 0.0:
            continue
        phase1 = ridr.get(qla, {}).get("1")
        if not phase1:
            errors.append(f"{qla} phase 1 missing from quikridr")
            continue
        mplan = (phase1.get("MPLAN") or "").strip()
        mode = mode_after_active_riders(fnum(src.get("MODE_PREMIUM")) or 0.0, rider_sum)
        expected, _ = blank_ann_annual_ppu(
            mode,
            fnum(phase1.get("MUNIT")) or units,
            bill_mode.get(pol),
            bill_form.get(pol, ""),
            factors.get(mplan),
        )
        got = fnum(phase1.get("MPREM"))
        scoped += 1
        if got is None or abs(got - expected) > 0.0006:
            if len(errors) < 12:
                errors.append(
                    f"{qla} phase 1 MPREM={got} expected {format_mprem_ppu(expected)} "
                    f"(rider mode {rider_sum:.2f})"
                )
        else:
            matched += 1

    for qla, exp in GOLDS.items():
        got = fnum((ridr.get(qla, {}).get("1") or {}).get("MPREM"))
        if got is None or abs(got - exp) > 0.0006:
            errors.append(f"Gold {qla} phase 1 MPREM={got} expected {exp}")

    for qla, exp in HOLDS.items():
        got = fnum((ridr.get(qla, {}).get("1") or {}).get("MPREM"))
        if got is None or abs(got - exp) > 0.0006:
            errors.append(f"Hold {qla} phase 1 MPREM={got} expected unchanged {exp}")

    for qla, exp in BILLED.items():
        got = fnum((mstr.get(qla) or {}).get("MMODEPREM"))
        if got is None or abs(got - exp) > 0.02:
            errors.append(f"Billed {qla} MMODEPREM={got} expected {exp}")

    for (qla, phase), exp in RIDER_HOLDS.items():
        got = fnum((ridr.get(qla, {}).get(phase) or {}).get("MPREM"))
        if got is None or abs(got - exp) > 0.0006:
            errors.append(f"Rider {qla} phase {phase} MPREM={got} expected {exp}")

    print(f"PPBEN {ppben_path.name}; in-scope {scoped}; matched {matched}")
    if errors or matched != scoped or scoped == 0:
        print("FAIL Issue #152")
        for err in errors:
            print(" ", err)
        if matched != scoped:
            print(f"  matched {matched} of {scoped}")
        return 1
    print(
        "PASS Issue #152 "
        f"in_scope={scoped} "
        + " ".join(f"{qla}={fnum(ridr[qla]['1']['MPREM'])}" for qla in GOLDS)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
