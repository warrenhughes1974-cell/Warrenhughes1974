#!/usr/bin/env python3
"""Issue #21J — validate plan modal factors, PAC overrides, and conversion memos."""

from __future__ import annotations

import csv
import os
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from qla_core.modal_premium_factors import (
    CONVERSION_MEMO_TAG,
    PAC_GL85_PLANS,
    PAC_QTR_FACTOR,
    PAC_SEMI_FACTOR,
    default_mapping_path,
    load_modal_factor_mapping,
)

OUTPUT = os.path.join(REPO, "QLA_Migration", "Output")
EXPECTED_VERSIONS = ("v57.45", "v57.46")


def _read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="latin1", errors="replace") as f:
        return list(csv.DictReader(f))


def main() -> int:
    failures: list[str] = []
    qp_path = os.path.join(OUTPUT, "quikplan.csv")
    mstr_path = os.path.join(OUTPUT, "quikmstr.csv")
    qr_path = os.path.join(OUTPUT, "quikridr.csv")
    memo_path = os.path.join(OUTPUT, "quikmemo.csv")
    mapping = load_modal_factor_mapping(default_mapping_path(REPO))

    if not os.path.isfile(qp_path):
        print(f"SKIP: {qp_path} not found — run batch first")
        return 0

    qp_rows = {r["PLAN"].strip(): r for r in _read_csv(qp_path) if r.get("PLAN", "").strip()}
    updated = 0
    for plan, factors in mapping.items():
        if plan not in qp_rows:
            continue
        row = qp_rows[plan]
        for field in ("ANNL", "SEMI", "QTRL", "MTHD", "MTHB"):
            exp = factors.get(field, "")
            got = (row.get(field) or "").strip()
            if exp and got != exp:
                failures.append(f"quikplan {plan} {field}: expected {exp}, got {got}")
            elif exp:
                updated += 1
    print(f"quikplan factor cells checked: {updated}")

    for plan in ("1659C2", "170858", "17085M"):
        exp = mapping.get(plan, {})
        row = qp_rows.get(plan)
        if not row:
            failures.append(f"quikplan missing plan {plan}")
            continue
        if (row.get("SEMI") or "").strip() != exp.get("SEMI", ""):
            failures.append(f"trace plan {plan} SEMI mismatch")

    if os.path.isfile(mstr_path) and os.path.isfile(qr_path):
        phase1 = {}
        for r in _read_csv(qr_path):
            if (r.get("MPHASE") or "").strip() not in ("1", "01"):
                continue
            pol = (r.get("MPOLICY") or "").strip()
            if pol:
                phase1[pol] = (r.get("MPLAN") or "").strip()

        qtr = semi = 0
        for r in _read_csv(mstr_path):
            pol = (r.get("MPOLICY") or "").strip()
            mplan = phase1.get(pol, "")
            if mplan not in PAC_GL85_PLANS:
                continue
            bf = (r.get("MBILLFRM") or "").strip().upper()
            mode = (r.get("MMODE") or "").strip().lstrip("0") or "0"
            if bf in ("PAC", "2") and mode == "3":
                qtr += 1
                if (r.get("MQTRL") or "").strip() != PAC_QTR_FACTOR:
                    failures.append(f"{pol}: PAC quarterly MQTRL expected {PAC_QTR_FACTOR}")
            elif bf in ("PAC", "2") and mode == "6":
                semi += 1
                if (r.get("MSEMI") or "").strip() != PAC_SEMI_FACTOR:
                    failures.append(f"{pol}: PAC semiannual MSEMI expected {PAC_SEMI_FACTOR}")
        print(f"PAC GL85 overrides: quarterly={qtr} semiannual={semi}")

    if os.path.isfile(memo_path) and os.path.isfile(mstr_path):
        memos = {r["MEMOKEY"].strip(): r for r in _read_csv(memo_path)}
        mstr_count = len(_read_csv(mstr_path))
        conv_count = sum(1 for r in memos.values() if (r.get("MEMOTEXT") or "").startswith(CONVERSION_MEMO_TAG))
        if conv_count != mstr_count:
            failures.append(f"quikmemo conversion segments {conv_count} != quikmstr rows {mstr_count}")
        if not any(v in (r.get("MEMOTEXT") or "") for r in memos.values() for v in EXPECTED_VERSIONS):
            failures.append(f"memo missing conversion version ({'/'.join(EXPECTED_VERSIONS)})")
        print(f"quikmemo: {len(memos)} rows, conversion segments={conv_count}, quikmstr={mstr_count}")

    if failures:
        print("FAIL")
        for f in failures[:30]:
            print(" ", f)
        if len(failures) > 30:
            print(f"  ... and {len(failures) - 30} more")
        return 1

    print("PASS — Issue #21J modal factor validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
