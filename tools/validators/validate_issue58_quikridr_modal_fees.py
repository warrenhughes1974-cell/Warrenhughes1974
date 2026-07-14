#!/usr/bin/env python3
"""Issue #58 — validate quikridr modal policy fees (Names-tab premium amounts)."""

from __future__ import annotations

import csv
import os
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from qla_core.modal_premium_factors import PAC_QTR_FACTOR, PAC_SEMI_FACTOR
from qla_core.normalize_utils import format_qladmin_mpolicy

OUTPUT = os.path.join(REPO, "QLA_Migration", "Output")

FEE_TRACE = {
    "010367131C": {
        "MANNLFEE": "10.44",
        "MSEMIFEE": "5.4288",
        "MQTRLFEE": "2.7666",
        "MMTHDFEE": "0.9396",
        "MMTHBFEE": "0.8700",
        "AFTER_Q": "15.90",
        "AFTER_MTHD": "5.40",
    },
    "010560185C": {
        "MQTRLFEE": "2.6100",
    },
    "010442216C": {
        "MSEMIFEE": "5.2200",
    },
}


def _read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="latin1", errors="replace") as f:
        return list(csv.DictReader(f))


def _num(val: str) -> float:
    try:
        return float((val or "").strip().replace(",", "") or 0)
    except ValueError:
        return 0.0


def _blank(val: str) -> bool:
    return (val or "").strip() in ("", "0", "0.0", "0.00", "0.0000")


def _phase1_row(ridr: list[dict], pol: str) -> dict | None:
    key = format_qladmin_mpolicy(pol)
    for r in ridr:
        if format_qladmin_mpolicy((r.get("MPOLICY") or "").strip()) != key:
            continue
        if (r.get("MPHASE") or "").strip() in ("1", "01"):
            return r
    return None


def main() -> int:
    failures: list[str] = []
    ridr_path = os.path.join(OUTPUT, "quikridr.csv")
    mstr_path = os.path.join(OUTPUT, "quikmstr.csv")

    if not os.path.isfile(ridr_path):
        print(f"SKIP: {ridr_path} not found — run batch first")
        return 0

    ridr = _read_csv(ridr_path)
    mstr = _read_csv(mstr_path) if os.path.isfile(mstr_path) else []
    mstr_by = {format_qladmin_mpolicy((r.get("MPOLICY") or "").strip()): r for r in mstr}

    base = [r for r in ridr if (r.get("MPHASE") or "").strip() in ("1", "01")]
    fee_positive = 0
    fee_populated = 0
    for r in base:
        ann = _num(r.get("MANNLFEE", ""))
        if ann <= 0:
            continue
        fee_positive += 1
        if not all(_blank(r.get(f)) for f in ("MSEMIFEE", "MQTRLFEE", "MMTHDFEE", "MMTHBFEE")):
            fee_populated += 1

    print(f"base rows={len(base)} MANNLFEE>0={fee_positive} modal_fees_populated={fee_populated}")
    if fee_positive and fee_populated < fee_positive:
        failures.append(
            f"modal fees blank on {fee_positive - fee_populated}/{fee_positive} fee-bearing base rows"
        )

    for pol, exp in FEE_TRACE.items():
        row = _phase1_row(ridr, pol)
        if not row:
            failures.append(f"trace policy missing: {pol}")
            continue
        mm = mstr_by.get(format_qladmin_mpolicy(pol), {})
        for field, want in exp.items():
            if field.startswith("AFTER_"):
                base_prem = _num(row.get("MPREM")) * _num(row.get("MUNIT"))
                if field == "AFTER_Q":
                    got = base_prem * _num(mm.get("MQTRL")) / 100 + _num(row.get("MQTRLFEE"))
                else:
                    got = base_prem * _num(mm.get("MMTHD")) / 100 + _num(row.get("MMTHDFEE"))
                if abs(got - _num(want)) > 0.015:
                    failures.append(f"{pol} {field}: expected {want}, got {got:.2f}")
                continue
            got = (row.get(field) or "").strip()
            if got != want:
                failures.append(f"{pol} {field}: expected {want}, got {got!r}")
        print(
            f"trace {pol}: MANNLFEE={row.get('MANNLFEE')} "
            f"MSEMIFEE={row.get('MSEMIFEE')} MQTRLFEE={row.get('MQTRLFEE')} "
            f"MMTHDFEE={row.get('MMTHDFEE')} MMTHBFEE={row.get('MMTHBFEE')}"
        )

    # PAC fee uses overridden factors
    for pol, qfee, sfee in (
        ("010560185C", PAC_QTR_FACTOR, None),
        ("010442216C", None, PAC_SEMI_FACTOR),
    ):
        row = _phase1_row(ridr, pol)
        mm = mstr_by.get(format_qladmin_mpolicy(pol), {})
        if not row or not mm:
            continue
        ann = _num(row.get("MANNLFEE"))
        if qfee and (row.get("MQTRLFEE") or "").strip():
            want = f"{ann * _num(qfee) / 100:.4f}"
            if (row.get("MQTRLFEE") or "").strip() != want:
                failures.append(f"{pol} PAC MQTRLFEE expected {want}")
        if sfee and (row.get("MSEMIFEE") or "").strip():
            want = f"{ann * _num(sfee) / 100:.4f}"
            if (row.get("MSEMIFEE") or "").strip() != want:
                failures.append(f"{pol} PAC MSEMIFEE expected {want}")

    # MPHASE > 1 should stay blank on modal fees when phase 1 has fee
    for r in ridr:
        if (r.get("MPHASE") or "").strip() in ("1", "01"):
            continue
        if any(not _blank(r.get(f)) for f in ("MSEMIFEE", "MQTRLFEE", "MMTHDFEE", "MMTHBFEE")):
            failures.append(
                f"non-phase1 {r.get('MPOLICY')} has modal fees populated"
            )
            break

    if failures:
        print("FAIL")
        for f in failures:
            print(" ", f)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
