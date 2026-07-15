"""Issue #71 — validate rate BAND standardization to 00 (NOT APPLICABLE)."""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RATES = ROOT / "QLA_Migration" / "Output" / "rates"
RIDR = ROOT / "QLA_Migration" / "Output" / "quikridr.csv"

SAMPLE_POLICY = "010718309C"
SAMPLE_PLAN = "1658C1"
EXPECTED_MCV0 = "986.00"  # approximate; allow small formatting variance


def _band_values(path: Path, field: str) -> Counter:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return Counter((r.get(field) or "").strip() for r in csv.DictReader(f))


def _mcv0_for_policy(policy: str) -> str | None:
    with RIDR.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("MPOLICY") or "").strip() == policy:
                return (row.get("MCV0") or "").strip()
    return None


def _plan_cv_key_exists(plan: str) -> bool:
    path = RATES / "QuikPlCv.csv"
    if not path.is_file():
        return False
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("PLAN") or "").strip() != plan:
                continue
            if (row.get("BAND") or "").strip() == "00":
                return True
    return False


def main() -> int:
    ok = True
    print("Issue #71 BAND validation (v57.90)")

    checks = [
        ("QuikCvs.csv", "BAND"),
        ("QuikPlCv.csv", "BAND"),
        ("QuikNps.csv", "BAND"),
        ("QuikGps.csv", "BAND"),
    ]
    for fname, field in checks:
        path = RATES / fname
        if not path.is_file():
            print(f"  FAIL: missing {path}")
            ok = False
            continue
        bands = _band_values(path, field)
        uniq = set(bands)
        if uniq == {"00"}:
            print(f"  OK: {fname} {field} unique={{00}} rows={sum(bands.values())}")
        else:
            print(f"  FAIL: {fname} {field} unique={sorted(uniq)} counts={dict(bands)}")
            ok = False

    plbd = RATES / "QuikPlBd.csv"
    if plbd.is_file():
        bd = _band_values(plbd, "BDCODE")
        if set(bd) == {"00"}:
            print(f"  OK: QuikPlBd BDCODE unique={{00}} rows={sum(bd.values())}")
        else:
            print(f"  FAIL: QuikPlBd BDCODE unique={sorted(set(bd))} counts={dict(bd)}")
            ok = False
    else:
        print(f"  FAIL: missing {plbd}")
        ok = False

    if RIDR.is_file():
        mb = _band_values(RIDR, "MBAND")
        non00 = {k: v for k, v in mb.items() if k != "00"}
        if not non00 and mb.get("00", 0) > 0:
            print(f"  OK: quikridr MBAND 100% 00 ({mb['00']} rows)")
        else:
            print(f"  FAIL: quikridr MBAND not all 00: {dict(mb)}")
            ok = False
    else:
        print(f"  FAIL: missing {RIDR}")
        ok = False

    mcv0 = _mcv0_for_policy(SAMPLE_POLICY)
    if mcv0:
        try:
            val = float(mcv0.replace(",", ""))
            exp = float(EXPECTED_MCV0)
            if abs(val - exp) < 1.0:
                print(f"  OK: {SAMPLE_POLICY} MCV0={mcv0} (unchanged ~{EXPECTED_MCV0})")
            else:
                print(f"  FAIL: {SAMPLE_POLICY} MCV0={mcv0} expected ~{EXPECTED_MCV0}")
                ok = False
        except ValueError:
            print(f"  WARN: {SAMPLE_POLICY} MCV0={mcv0!r} (non-numeric)")
    else:
        print(f"  FAIL: {SAMPLE_POLICY} not found in quikridr")
        ok = False

    if _plan_cv_key_exists(SAMPLE_PLAN):
        print(f"  OK: QuikPlCv key exists for plan {SAMPLE_PLAN} BAND=00")
    else:
        print(f"  FAIL: no QuikPlCv BAND=00 key for plan {SAMPLE_PLAN}")
        ok = False

    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
