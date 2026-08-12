#!/usr/bin/env python3
"""Issue #58 — validate quikridr modal policy fees (Names-tab premium amounts).

Under Issue 139 mixed suppression (QLA_SUPPRESS_POLICY_FEES default/on):
  - Confirmed non-ISWL fee-bearing rows must still carry #21C/#58 modal fees.
  - ISWL / UNKNOWN phase-1 rows must remain at 0.0000 (intentional suppression).
Never blanket-SKIP when suppression is on — that would hide a non-ISWL wipe.
"""

from __future__ import annotations

import csv
import os
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from qla_core.modal_premium_factors import (
    PAC_QTR_FACTOR,
    PAC_SEMI_FACTOR,
    POLICY_FEE_FIELDS,
    issue139_fee_class,
    policy_fees_suppressed,
)

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


def _canon(v: str) -> str:
    """Match accountability policy keying (strip trailing C / leading 9)."""
    s = (v or "").strip().upper()
    if s.endswith("C"):
        s = s[:-1]
    if s.startswith("9"):
        s = s[1:]
    return s.lstrip("0") or "0"


def _phase1_row(ridr: list[dict], pol: str) -> dict | None:
    want = _canon(pol)
    for r in ridr:
        if _canon(r.get("MPOLICY") or "") != want:
            continue
        if (r.get("MPHASE") or "").strip() in ("1", "01"):
            return r
    return None


def _mstr_row(mstr: list[dict], pol: str) -> dict:
    want = _canon(pol)
    for r in mstr:
        if _canon(r.get("MPOLICY") or "") == want:
            return r
    return {}


def _any_fee_positive(row: dict) -> bool:
    return any(_num(row.get(f, "")) > 0 for f in POLICY_FEE_FIELDS)


def main() -> int:
    failures: list[str] = []
    ridr_path = os.path.join(OUTPUT, "quikridr.csv")
    mstr_path = os.path.join(OUTPUT, "quikmstr.csv")

    if not os.path.isfile(ridr_path):
        print(f"SKIP: {ridr_path} not found — run batch first")
        return 0

    suppressed = policy_fees_suppressed()
    ridr = _read_csv(ridr_path)
    mstr = _read_csv(mstr_path) if os.path.isfile(mstr_path) else []

    base = [r for r in ridr if (r.get("MPHASE") or "").strip() in ("1", "01")]
    iswl_base = [r for r in base if issue139_fee_class(r.get("MPLAN")) == "ISWL"]
    non_iswl_base = [r for r in base if issue139_fee_class(r.get("MPLAN")) == "NON_ISWL"]
    unknown_base = [r for r in base if issue139_fee_class(r.get("MPLAN")) == "UNKNOWN"]
    unknown_pols = sorted(
        {(r.get("MPOLICY") or "").strip() for r in unknown_base if (r.get("MPOLICY") or "").strip()}
    )

    print(
        f"base rows={len(base)} iswl={len(iswl_base)} non_iswl={len(non_iswl_base)} "
        f"unknown={len(unknown_base)} suppress_flag={'on' if suppressed else 'off'}"
    )
    if unknown_pols:
        print(f"UNKNOWN phase-1 MPLAN policies ({len(unknown_pols)}): {', '.join(unknown_pols[:25])}")
        if len(unknown_pols) > 25:
            print(f"  ... +{len(unknown_pols) - 25} more")

    if suppressed:
        iswl_fee_pos = sum(1 for r in iswl_base if _any_fee_positive(r))
        unk_fee_pos = sum(1 for r in unknown_base if _any_fee_positive(r))
        if iswl_fee_pos:
            failures.append(
                f"Issue 139: {iswl_fee_pos} ISWL phase-1 rows still have non-zero policy fees"
            )
        if unk_fee_pos:
            failures.append(
                f"Issue 139: {unk_fee_pos} UNKNOWN phase-1 rows still have non-zero policy fees"
            )
        non_iswl_fee_pos = sum(1 for r in non_iswl_base if _num(r.get("MANNLFEE", "")) > 0)
        print(f"non_iswl MANNLFEE>0={non_iswl_fee_pos} iswl_fee_pos={iswl_fee_pos}")
        if non_iswl_base and non_iswl_fee_pos == 0:
            failures.append(
                "Issue 139/#58: confirmed non-ISWL phase-1 rows have 0 MANNLFEE — "
                "non-ISWL fee wipe (mixed suppression must restore #21C/#58 fees)"
            )
        for pol, exp in FEE_TRACE.items():
            row = _phase1_row(ridr, pol)
            if not row:
                failures.append(f"trace policy missing: {pol}")
                continue
            cls = issue139_fee_class(row.get("MPLAN"))
            if cls != "NON_ISWL":
                failures.append(f"{pol} expected NON_ISWL for #58 trace, got {cls}")
                continue
            mm = _mstr_row(mstr, pol)
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
                if abs(_num(row.get(field)) - _num(want)) > 0.00015:
                    failures.append(
                        f"{pol} {field}: expected {want}, got {(row.get(field) or '').strip()!r}"
                    )
            print(
                f"trace {pol}: class={cls} MANNLFEE={row.get('MANNLFEE')} "
                f"MSEMIFEE={row.get('MSEMIFEE')} MQTRLFEE={row.get('MQTRLFEE')}"
            )
    else:
        fee_positive = 0
        fee_populated = 0
        for r in base:
            ann = _num(r.get("MANNLFEE", ""))
            if ann <= 0:
                continue
            fee_positive += 1
            if not all(_blank(r.get(f)) for f in ("MSEMIFEE", "MQTRLFEE", "MMTHDFEE", "MMTHBFEE")):
                fee_populated += 1

        print(f"MANNLFEE>0={fee_positive} modal_fees_populated={fee_populated}")
        if fee_positive and fee_populated < fee_positive:
            failures.append(
                f"modal fees blank on {fee_positive - fee_populated}/{fee_positive} fee-bearing base rows"
            )

        for pol, exp in FEE_TRACE.items():
            row = _phase1_row(ridr, pol)
            if not row:
                failures.append(f"trace policy missing: {pol}")
                continue
            mm = _mstr_row(mstr, pol)
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
                if abs(_num(row.get(field)) - _num(want)) > 0.00015:
                    failures.append(
                        f"{pol} {field}: expected {want}, got {(row.get(field) or '').strip()!r}"
                    )
            print(
                f"trace {pol}: MANNLFEE={row.get('MANNLFEE')} "
                f"MSEMIFEE={row.get('MSEMIFEE')} MQTRLFEE={row.get('MQTRLFEE')} "
                f"MMTHDFEE={row.get('MMTHDFEE')} MMTHBFEE={row.get('MMTHBFEE')}"
            )

        for pol, qfee, sfee in (
            ("010560185C", PAC_QTR_FACTOR, None),
            ("010442216C", None, PAC_SEMI_FACTOR),
        ):
            row = _phase1_row(ridr, pol)
            mm = _mstr_row(mstr, pol)
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
