#!/usr/bin/env python3
"""Issue 151 — fail-closed gold for 9010969231C former-vanish 0561 history.

Warren approved 2026-09-22 adding this 21st key to the Issue 146 allowlist.
This smoke is named and standalone: it must still FAIL if 9010969231C history
returns even if the #146 allowlist job is later weakened.

Exit 1 if full QLA_Migration/Output is missing/invalid, if 9010969231C has any
QuikIsrr rows, quikclms PS-/partial-surrender companions, quikclmp phase-0
companions, or quikbenh type-8 rows, or if rider/master golds drift.
Does not claim a fresh QLAdmin valuation has cleared $2,899.79.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "QLA_Migration" / "Output"

GOLD_POLICY = "9010969231C"
GOLD_MUNIT = 5.0
GOLD_MPREM = 37.62
GOLD_MCV0 = -812.49
GOLD_MMODEPREM = 163.10

ISRR_NAMES = ("QuikIsrr.csv", "quikisrr.csv")
REQUIRED = {
    "isrr": (("MPOLICY",), ISRR_NAMES),
    "clms": (("MPOLICY", "CLAIMNUM", "CAUSE", "MPHASE"), ("quikclms.csv",)),
    "clmp": (("MPOLICY", "MPHASE"), ("quikclmp.csv",)),
    "benh": (("MPOLICY", "MBENTYP"), ("quikbenh.csv",)),
    "ridr": (("MPOLICY", "MPHASE", "MUNIT", "MPREM", "MCV0"), ("quikridr.csv",)),
    "mstr": (("MPOLICY", "MMODEPREM"), ("quikmstr.csv",)),
}


def _digits_key(pol: str) -> str:
    raw = str(pol or "").strip()
    if not raw:
        return ""
    if raw[-1] in "Cc":
        return raw[:-1] + "C"
    return raw + "C"


def _is_gold(pol: str) -> bool:
    return _digits_key(pol).upper() == GOLD_POLICY.upper()


def _num(val) -> float | None:
    text = str(val or "").strip().replace(",", "")
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _resolve_table(out: Path, names: tuple[str, ...]) -> Path | None:
    wanted = {n.lower() for n in names}
    if not out.is_dir():
        return None
    by_lower: dict[str, Path] = {}
    for path in out.iterdir():
        if path.is_file() and path.name.lower() in wanted:
            by_lower[path.name.lower()] = path
    for name in names:
        hit = by_lower.get(name.lower())
        if hit is not None:
            return hit
    for name in names:
        path = out / name
        if path.is_file():
            return path
    return None


def _read(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fields = [str(c) for c in (reader.fieldnames or [])]
        return fields, [dict(row) for row in reader]


def _phase(row: dict) -> str:
    return str(row.get("MPHASE") or "").strip()


def _is_ps_clms(row: dict) -> bool:
    claim = str(row.get("CLAIMNUM") or "")
    cause = str(row.get("CAUSE") or "").strip().upper()
    return claim.startswith("PS-") or cause == "SRR" or _phase(row) in ("0", "0.0")


def _is_phase0(row: dict) -> bool:
    return _phase(row) in ("0", "0.0")


def _is_phase1(row: dict) -> bool:
    return _phase(row) in ("1", "1.0", "01")


def _is_type8(row: dict) -> bool:
    return str(row.get("MBENTYP") or "").strip() in ("8", "8.0")


def main() -> int:
    errors: list[str] = []
    if not OUT.is_dir():
        print(f"FAIL missing Output directory {OUT}")
        return 1

    loaded: dict[str, tuple[Path, list[str], list[dict]]] = {}
    for key, (need_cols, names) in REQUIRED.items():
        path = _resolve_table(OUT, names)
        if path is None:
            print(f"FAIL missing {names[0]} under {OUT}")
            return 1
        try:
            fields, rows = _read(path)
        except (OSError, csv.Error, UnicodeError) as exc:
            print(f"FAIL invalid {path.name}: {exc}")
            return 1
        have = {c.strip() for c in fields}
        missing = [c for c in need_cols if c not in have]
        if missing:
            print(f"FAIL {path.name} missing columns {missing}")
            return 1
        loaded[key] = (path, fields, rows)

    _isrr_path, _isrr_fields, isrr = loaded["isrr"]
    _clms_path, _clms_fields, clms = loaded["clms"]
    _clmp_path, _clmp_fields, clmp = loaded["clmp"]
    _benh_path, _benh_fields, benh = loaded["benh"]
    _ridr_path, _ridr_fields, ridr = loaded["ridr"]
    _mstr_path, _mstr_fields, mstr = loaded["mstr"]

    n_isrr = sum(1 for r in isrr if _is_gold(r.get("MPOLICY") or ""))
    n_clms = sum(
        1 for r in clms if _is_gold(r.get("MPOLICY") or "") and _is_ps_clms(r)
    )
    n_clmp = sum(
        1 for r in clmp if _is_gold(r.get("MPOLICY") or "") and _is_phase0(r)
    )
    n_benh8 = sum(
        1 for r in benh if _is_gold(r.get("MPOLICY") or "") and _is_type8(r)
    )
    if n_isrr:
        errors.append(f"{GOLD_POLICY} QuikIsrr rows={n_isrr} expected 0")
    if n_clms:
        errors.append(f"{GOLD_POLICY} quikclms PS-/SRR/phase-0 rows={n_clms} expected 0")
    if n_clmp:
        errors.append(f"{GOLD_POLICY} quikclmp phase-0 rows={n_clmp} expected 0")
    if n_benh8:
        errors.append(f"{GOLD_POLICY} quikbenh type-8 rows={n_benh8} expected 0")

    ridr_gold = [
        r
        for r in ridr
        if _is_gold(r.get("MPOLICY") or "") and _is_phase1(r)
    ]
    if not ridr_gold:
        errors.append(f"{GOLD_POLICY} quikridr phase-1 row missing")
    else:
        got_u = _num(ridr_gold[0].get("MUNIT"))
        got_p = _num(ridr_gold[0].get("MPREM"))
        got_cv = _num(ridr_gold[0].get("MCV0"))
        if got_u is None or abs(got_u - GOLD_MUNIT) > 0.00001:
            errors.append(f"{GOLD_POLICY} MUNIT={got_u} expected {GOLD_MUNIT:.5f}")
        if got_p is None or abs(got_p - GOLD_MPREM) > 0.005:
            errors.append(f"{GOLD_POLICY} MPREM={got_p} expected {GOLD_MPREM}")
        if got_cv is None or abs(got_cv - GOLD_MCV0) > 0.005:
            errors.append(f"{GOLD_POLICY} MCV0={got_cv} expected {GOLD_MCV0}")

    mstr_gold = [r for r in mstr if _is_gold(r.get("MPOLICY") or "")]
    if not mstr_gold:
        errors.append(f"{GOLD_POLICY} quikmstr row missing")
    else:
        got_m = _num(mstr_gold[0].get("MMODEPREM"))
        if got_m is None or abs(got_m - GOLD_MMODEPREM) > 0.005:
            errors.append(
                f"{GOLD_POLICY} MMODEPREM={got_m} expected {GOLD_MMODEPREM}"
            )

    print(
        f"{GOLD_POLICY} isrr={n_isrr} clms_ps={n_clms} clmp0={n_clmp} "
        f"benh8={n_benh8}"
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
