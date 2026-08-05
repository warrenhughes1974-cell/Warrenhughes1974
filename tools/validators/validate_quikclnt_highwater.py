#!/usr/bin/env python3
"""Smoke: TEMP quikclnt EOF high-water client (max+1) for QLAdmin New Client IDs.

See qla_core/quikclnt_highwater.py and Completed_Issues_Release_Validation_Guide.md.
Disable expectation with QLA_QUIKCLNT_HIGHWATER=0 (then last row must NOT be the sentinel).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from qla_core.quikclnt_highwater import (
    HIGHWATER_MLNAME,
    apply_quikclnt_highwater,
    highwater_enabled,
)

OUT = ROOT / "QLA_Migration" / "Output" / "quikclnt.csv"


def main() -> int:
    if not OUT.is_file():
        print(f"FAIL: missing {OUT}")
        return 1

    df = pd.read_csv(OUT, dtype=str, encoding="utf-8-sig").fillna("")
    if df.empty or "MCLIENTID" not in df.columns or "MLNAME" not in df.columns:
        print("FAIL: quikclnt missing MCLIENTID/MLNAME or empty")
        return 1

    last = df.iloc[-1]
    last_name = str(last.get("MLNAME", "")).strip().upper()
    last_id = str(last.get("MCLIENTID", "")).strip()

    if not highwater_enabled():
        if last_name == HIGHWATER_MLNAME:
            print(
                f"FAIL: QLA_QUIKCLNT_HIGHWATER=0 but last row is still sentinel "
                f"id={last_id!r} name={last_name!r}"
            )
            return 1
        print("PASS: high-water disabled; last row is not sentinel")
        return 0

    if last_name != HIGHWATER_MLNAME:
        print(
            f"FAIL: last quikclnt row is not high-water sentinel "
            f"(got MLNAME={last_name!r} MCLIENTID={last_id!r})"
        )
        return 1

    # Re-apply on a copy without the last sentinel: max_prior+1 must match last_id
    body = df.iloc[:-1].copy()
    rebuilt, stats = apply_quikclnt_highwater(body)
    expect = str(stats.get("highwater_id", "")).strip()
    if last_id != expect:
        print(
            f"FAIL: last MCLIENTID={last_id!r} != expected max+1={expect!r} "
            f"(max_prior={stats.get('max_prior')})"
        )
        return 1

    # Must be unique (not a duplicate of a real client)
    prior_ids = {str(x).strip() for x in body["MCLIENTID"] if str(x).strip()}
    if last_id in prior_ids:
        print(f"FAIL: high-water id {last_id!r} duplicates an existing MCLIENTID")
        return 1

    print(
        f"PASS: EOF high-water id={last_id} max_prior={stats.get('max_prior')} "
        f"rows={len(df)} (disable QLA_QUIKCLNT_HIGHWATER=0)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
