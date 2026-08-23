#!/usr/bin/env python3
"""Issue 145B — fail-closed: no VB 0561 history in QuikIsrr / PR-7 companions.

Exit 1 if vanishing policies still have QuikIsrr or matching PS companions,
or if #146 leftovers / gold units / #54 loan benh are missing.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from qla_core.issue145b_vb_isrr import is_vb_policy
from qla_core.quikspec_vanish import load_ppolc_billing_reason

OUT = REPO / "QLA_Migration" / "Output"
SRC = REPO / "QLA_Migration" / "Source"

GOLD_VB = {
    "9010815236C": {"munit": 25.0},
    "9011050114C": {"munit": 25.0},
    "9011069610C": {"munit": 50.0},
}
GOLD_146 = {
    "9010761639C": {"isrr_rows": 1, "isrr_amt": 271.0, "munit": 25.0},
    "9010760840C": {"isrr_rows": 2, "isrr_amt": 716.4, "munit": 35.0},
}
LOAN_BENH_FLOOR = {"10": 4118, "11": 14156, "12": 19135}


def _digits_key(pol: str) -> str:
    raw = str(pol or "").strip()
    if raw.endswith("C"):
        return raw
    return raw + "C" if raw else raw


def _read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    errors: list[str] = []
    isrr_path = OUT / "QuikIsrr.csv"
    ridr_path = OUT / "quikridr.csv"
    spec_path = OUT / "quikspec.csv"
    clms_path = OUT / "quikclms.csv"
    clmp_path = OUT / "quikclmp.csv"
    benh_path = OUT / "quikbenh.csv"
    for p in (isrr_path, ridr_path, spec_path, clms_path, clmp_path, benh_path):
        if not p.is_file():
            print(f"FAIL missing {p}")
            return 1

    reasons = load_ppolc_billing_reason(str(SRC))
    isrr = _read(isrr_path)
    vb_isrr = [r for r in isrr if is_vb_policy(str(r.get("MPOLICY") or ""), reasons)]
    if vb_isrr:
        errors.append(f"QuikIsrr still has {len(vb_isrr)} VB rows")

    by_isrr: dict[str, list[dict]] = {}
    for r in isrr:
        by_isrr.setdefault(_digits_key(r.get("MPOLICY") or ""), []).append(r)

    for pol in GOLD_VB:
        n = len(by_isrr.get(pol, []))
        if n != 0:
            errors.append(f"{pol} QuikIsrr rows={n} expected 0")

    for pol, exp in GOLD_146.items():
        rows = by_isrr.get(pol, [])
        amt = round(sum(float(r.get("MSURRAMT") or 0) for r in rows), 2)
        if len(rows) != exp["isrr_rows"] or abs(amt - exp["isrr_amt"]) > 0.02:
            errors.append(f"{pol} QuikIsrr n={len(rows)} amt={amt} expected {exp}")

    clms = _read(clms_path)
    clmp = _read(clmp_path)
    benh = _read(benh_path)

    def _ps_clms(r: dict) -> bool:
        return (
            str(r.get("CLAIMNUM") or "").startswith("PS-")
            or str(r.get("CAUSE") or "").strip().upper() == "SRR"
            or str(r.get("MPHASE") or "").strip() in ("0", "0.0")
        )

    for pol in GOLD_VB:
        n_clms = sum(1 for r in clms if _digits_key(r.get("MPOLICY") or "") == pol and _ps_clms(r))
        n_clmp = sum(
            1
            for r in clmp
            if _digits_key(r.get("MPOLICY") or "") == pol
            and str(r.get("MPHASE") or "").strip() in ("0", "0.0")
        )
        n_benh8 = sum(
            1
            for r in benh
            if _digits_key(r.get("MPOLICY") or "") == pol
            and str(r.get("MBENTYP") or "").strip() in ("8", "8.0")
        )
        if n_clms or n_clmp or n_benh8:
            errors.append(f"{pol} companions clms={n_clms} clmp={n_clmp} benh8={n_benh8}")

    loan = {"10": 0, "11": 0, "12": 0}
    for r in benh:
        typ = str(r.get("MBENTYP") or "").strip()
        if typ in loan:
            loan[typ] += 1
    for typ, floor in LOAN_BENH_FLOOR.items():
        if loan[typ] < floor:
            errors.append(f"quikbenh type {typ}={loan[typ]} below floor {floor}")

    ridr = _read(ridr_path)
    spec = _read(spec_path)
    vanish = {str(r.get("MPOLICY") or "").strip(): str(r.get("VANISH") or "").strip() for r in spec}
    for pol, exp in {**GOLD_VB, **{k: {"munit": v["munit"]} for k, v in GOLD_146.items()}}.items():
        units = [
            float(r.get("MUNIT") or 0)
            for r in ridr
            if _digits_key(r.get("MPOLICY") or "") == pol
            and str(r.get("MPHASE") or "").strip() in ("1", "1.0")
        ]
        if not units or abs(units[0] - exp["munit"]) > 0.00001:
            errors.append(f"{pol} MUNIT={units} expected {exp['munit']}")
        want = "T" if pol in GOLD_VB else "F"
        if vanish.get(pol) != want:
            errors.append(f"{pol} VANISH={vanish.get(pol)!r} expected {want}")

    print(
        f"isrr={len(isrr)} vb_isrr={len(vb_isrr)} "
        f"loan_benh={loan} leftover_ok={len(isrr) > 0}"
    )
    if errors:
        print("FAIL")
        for err in errors:
            print(" ", err)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
