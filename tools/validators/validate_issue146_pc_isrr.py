#!/usr/bin/env python3
"""Issue 146 — fail-closed: no allowlist 0561 history in QuikIsrr / PR-7 companions.

Exit 1 if the 20 former-vanish policies still have QuikIsrr or matching
companions, or if #145B leftover golds / gold units are missing.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from qla_core.issue146_pc_isrr import ALLOWLIST_SOURCE, is_issue146_policy

OUT = REPO / "QLA_Migration" / "Output"

GOLD_REMOVE = {
    "9011077629C": {"munit": 5.0},
    "9010817956C": {"munit": 5.0},
    "9010808831C": {"munit": 25.0},
}
GOLD_KEEP = {
    "9010761639C": {"isrr_rows": 1, "isrr_amt": 271.0, "munit": 25.0},
    "9010760840C": {"isrr_rows": 2, "isrr_amt": 716.4, "munit": 35.0},
}


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
    clms_path = OUT / "quikclms.csv"
    clmp_path = OUT / "quikclmp.csv"
    benh_path = OUT / "quikbenh.csv"
    for p in (isrr_path, ridr_path, clms_path, clmp_path, benh_path):
        if not p.is_file():
            print(f"FAIL missing {p}")
            return 1

    isrr = _read(isrr_path)
    allow_isrr = [r for r in isrr if is_issue146_policy(str(r.get("MPOLICY") or ""))]
    if allow_isrr:
        errors.append(f"QuikIsrr still has {len(allow_isrr)} Issue 146 allowlist rows")

    by_isrr: dict[str, list[dict]] = {}
    for r in isrr:
        by_isrr.setdefault(_digits_key(r.get("MPOLICY") or ""), []).append(r)

    for src in ALLOWLIST_SOURCE:
        n = len(by_isrr.get(_digits_key(src), []))
        if n != 0:
            errors.append(f"{src}C QuikIsrr rows={n} expected 0")

    for pol, exp in GOLD_KEEP.items():
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

    for src in ALLOWLIST_SOURCE:
        pol = _digits_key(src)
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

    ridr = _read(ridr_path)
    for pol, exp in {**GOLD_REMOVE, **{k: {"munit": v["munit"]} for k, v in GOLD_KEEP.items()}}.items():
        units = [
            float(r.get("MUNIT") or 0)
            for r in ridr
            if _digits_key(r.get("MPOLICY") or "") == pol
            and str(r.get("MPHASE") or "").strip() in ("1", "1.0")
        ]
        if not units or abs(units[0] - exp["munit"]) > 0.00001:
            errors.append(f"{pol} MUNIT={units} expected {exp['munit']}")

    if len(isrr) < 1:
        errors.append("QuikIsrr leftover is empty — #145B keep golds should remain")

    print(
        f"isrr={len(isrr)} allow_isrr={len(allow_isrr)} "
        f"leftover_ok={len(isrr) > 0}"
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
