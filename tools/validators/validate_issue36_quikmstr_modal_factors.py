#!/usr/bin/env python3
"""Issue #36 — validate quikmstr policy-level modal factors (Names tab)."""

from __future__ import annotations

import csv
import os
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from qla_core.modal_premium_factors import (
    PAC_GL85_PLANS,
    PAC_QTR_FACTOR,
    PAC_SEMI_FACTOR,
)
from qla_core.normalize_utils import format_qladmin_mpolicy

OUTPUT = os.path.join(REPO, "QLA_Migration", "Output")

TRACE = {
    "010148856C": {
        "MSEMI": "51.0140",
        "MQTRL": "26.0010",
        "MMTHD": "8.9964",
        "MMTHB": "8.9989",
    },
    "010713704C": {
        "MSEMI": "52.5000",
        "MQTRL": "27.0000",
        "MMTHD": "9.1999",
        "MMTHB": "8.8018",
    },
    "010560185C": {  # PAC quarterly special mode
        "MSEMI": "52.0000",
        "MQTRL": PAC_QTR_FACTOR,
        "MMTHD": "9.0000",
        "MMTHB": "8.3333",
    },
    "010442216C": {  # PAC semiannual special mode
        "MSEMI": PAC_SEMI_FACTOR,
        "MQTRL": "26.5000",
        "MMTHD": "9.0000",
        "MMTHB": "8.3333",
    },
}


def _read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="latin1", errors="replace") as f:
        return list(csv.DictReader(f))


def _norm_mode(val: str) -> str:
    v = (val or "").strip()
    if v.endswith(".0") and v[:-2].isdigit():
        v = v[:-2]
    return v.lstrip("0") or "0"


def main() -> int:
    failures: list[str] = []
    mstr_path = os.path.join(OUTPUT, "quikmstr.csv")
    qr_path = os.path.join(OUTPUT, "quikridr.csv")
    qp_path = os.path.join(OUTPUT, "quikplan.csv")

    if not os.path.isfile(mstr_path):
        print(f"SKIP: {mstr_path} not found — run batch first")
        return 0

    mstr = _read_csv(mstr_path)
    total = len(mstr)
    if total == 0:
        failures.append("quikmstr empty")

    blank = {f: 0 for f in ("MSEMI", "MQTRL", "MMTHD", "MMTHB")}
    for r in mstr:
        for f in blank:
            if not (r.get(f) or "").strip():
                blank[f] += 1

    for f, n in blank.items():
        pct = 100.0 * (total - n) / total if total else 0
        print(f"{f}: non-blank {total - n}/{total} ({pct:.1f}%)")
        if n > 0:
            failures.append(f"{f} blank on {n}/{total} policies")

    # Trace policies
    by_pol = {format_qladmin_mpolicy((r.get("MPOLICY") or "").strip()): r for r in mstr}
    for pol, exp in TRACE.items():
        key = format_qladmin_mpolicy(pol)
        row = by_pol.get(key)
        if not row:
            failures.append(f"trace policy missing: {pol}")
            continue
        for f, ev in exp.items():
            got = (row.get(f) or "").strip()
            if got != ev:
                failures.append(f"{pol} {f}: expected {ev}, got {got!r}")
        print(
            f"trace {pol}: MSEMI={row.get('MSEMI')} MQTRL={row.get('MQTRL')} "
            f"MMTHD={row.get('MMTHD')} MMTHB={row.get('MMTHB')} MMODEPREM={row.get('MMODEPREM')}"
        )

    # PAC special modes
    if os.path.isfile(qr_path):
        phase1 = {}
        for r in _read_csv(qr_path):
            if (r.get("MPHASE") or "").strip() not in ("1", "01"):
                continue
            pol = format_qladmin_mpolicy((r.get("MPOLICY") or "").strip())
            if pol:
                phase1[pol] = (r.get("MPLAN") or "").strip()

        qtr = semi = 0
        for r in mstr:
            pol = format_qladmin_mpolicy((r.get("MPOLICY") or "").strip())
            mplan = phase1.get(pol, "")
            if mplan not in PAC_GL85_PLANS:
                continue
            bf = (r.get("MBILLFRM") or "").strip().upper()
            mode = _norm_mode(r.get("MMODE") or "")
            if bf in ("PAC", "2") and mode == "3":
                qtr += 1
                if (r.get("MQTRL") or "").strip() != PAC_QTR_FACTOR:
                    failures.append(f"{pol}: PAC Q MQTRL expected {PAC_QTR_FACTOR}")
            elif bf in ("PAC", "2") and mode == "6":
                semi += 1
                if (r.get("MSEMI") or "").strip() != PAC_SEMI_FACTOR:
                    failures.append(f"{pol}: PAC S MSEMI expected {PAC_SEMI_FACTOR}")
        print(f"PAC special modes: quarterly={qtr} semiannual={semi}")
        if qtr < 1 or semi < 1:
            failures.append(f"expected PAC Q and S populations, got Q={qtr} S={semi}")

    # MMTHD vs MMTHB independence where quikplan differs
    if os.path.isfile(qp_path) and os.path.isfile(qr_path):
        qp = {
            (r.get("PLAN") or "").strip(): r
            for r in _read_csv(qp_path)
            if (r.get("PLAN") or "").strip()
        }
        phase1 = {}
        for r in _read_csv(qr_path):
            if (r.get("MPHASE") or "").strip() not in ("1", "01"):
                continue
            pol = format_qladmin_mpolicy((r.get("MPOLICY") or "").strip())
            if pol:
                phase1[pol] = (r.get("MPLAN") or "").strip()

        checked = collapsed = 0
        for r in mstr:
            pol = format_qladmin_mpolicy((r.get("MPOLICY") or "").strip())
            plan = phase1.get(pol, "")
            prow = qp.get(plan)
            if not prow:
                continue
            pmthd = (prow.get("MTHD") or "").strip()
            pmthb = (prow.get("MTHB") or "").strip()
            if not pmthd or not pmthb or pmthd == pmthb:
                continue
            checked += 1
            mthd = (r.get("MMTHD") or "").strip()
            mthb = (r.get("MMTHB") or "").strip()
            if mthd == mthb:
                collapsed += 1
                if collapsed <= 5:
                    failures.append(f"{pol}: MMTHD/MMTHB collapsed to {mthd!r} (plan {plan} {pmthd}/{pmthb})")
            elif mthd != pmthd or mthb != pmthb:
                failures.append(
                    f"{pol}: MMTHD/MMTHB {mthd}/{mthb} != plan {pmthd}/{pmthb}"
                )
        print(f"MMTHD!=MMTHB plan policies checked: {checked}, collapsed: {collapsed}")

    # MMODEPREM must remain populated (Issue #26 guard)
    blank_prem = sum(1 for r in mstr if not (r.get("MMODEPREM") or "").strip())
    print(f"MMODEPREM blank: {blank_prem}/{total}")
    if blank_prem:
        failures.append(f"MMODEPREM blank on {blank_prem} policies")

    if failures:
        print("FAIL")
        for f in failures[:40]:
            print(" ", f)
        if len(failures) > 40:
            print(f"  ... and {len(failures) - 40} more")
        return 1

    print("PASS — Issue #36 quikmstr modal factors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
