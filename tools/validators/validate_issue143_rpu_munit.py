"""
Issue #143 — BF RPU MUNIT = BF_CURRENT_DB / VALUE_PER_UNIT on the 23-row set.

Checks A–G against full QLA_Migration/Output/quikridr.csv and the locked
20260630 LifePRO extracts.

Usage:
  python tools/validators/validate_issue143_rpu_munit.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from qla_core.issue143_rpu_munit import (  # noqa: E402
    ISSUE143_EPS,
    apply_issue143_rpu_munit,
    classify_issue143_row,
    is_rpu_paid_up_type,
    seq_is_phase1,
)
from qla_core.normalize_utils import normalize  # noqa: E402

SRC = PROJECT / "QLA_Migration" / "Source"
OUT = PROJECT / "QLA_Migration" / "Output"
EVID = PROJECT / "Issue_Log_Items" / "Issue_143" / "evidence"
LOCKED_CUT = "20260630"
GOLD = "9010757606C"
GOLD_BEFORE = 25.0
GOLD_AFTER = 19.10196
GOLD_AMOUNT = 19101.96
EXPECTED_CANDIDATES = 23
EXPECTED_ALIGNED = 82
EXPECTED_BA = 199
ISWL_PLANS = {"1658C1", "1659C2", "1659CR"}


def _fnum(v) -> float | None:
    s = str(v or "").replace(",", "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _src(name: str) -> Path:
    return SRC / f"{name}_Extract_{LOCKED_CUT}.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="latin1", errors="replace") as fh:
        raw = list(csv.DictReader(fh))
    out = []
    for row in raw:
        out.append({str(k).strip().upper() if k else k: ("" if v is None else v) for k, v in row.items()})
    return out


def _inventory() -> dict[str, dict]:
    rpu: set[str] = set()
    for row in _rows(_src("PPOLC_PolicyMaster")):
        if is_rpu_paid_up_type(row.get("PAID_UP_TYPE")):
            pol = normalize(row.get("POLICY_NUMBER", ""))
            if pol:
                rpu.add(pol)
    typ = {}
    for row in _rows(_src("PPBENTYP_BenefitType")):
        pol = normalize(row.get("POLICY_NUMBER", ""))
        if pol in rpu and seq_is_phase1(row.get("BENEFIT_SEQ")):
            typ[pol] = row
    by_kind = {"candidate": {}, "aligned_bf": {}, "ba": {}}
    for row in _rows(_src("PPBEN_PolicyBenefit")):
        pol = normalize(row.get("POLICY_NUMBER", ""))
        if pol not in rpu or not seq_is_phase1(row.get("BENEFIT_SEQ")):
            continue
        trow = typ.get(pol, {})
        rec = classify_issue143_row(
            policy=pol,
            units=row.get("NUMBER_OF_UNITS"),
            value_per_unit=row.get("VALUE_PER_UNIT"),
            type_code=trow.get("TYPE_CODE"),
            bf_current_db=trow.get("BF_CURRENT_DB"),
            is_rpu=True,
        )
        if rec.kind in by_kind:
            by_kind[rec.kind][pol] = rec
    return by_kind


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    gold_row = {"MUNIT": "25.00000"}
    if not apply_issue143_rpu_munit(
        gold_row,
        is_rpu=True,
        type_code="BF",
        bf_current_db=19101.96,
        value_per_unit=1000.0,
    ):
        errors.append("unit rule did not remap gold 25 → 19.10196")
    elif abs(float(gold_row["MUNIT"]) - GOLD_AFTER) > 1e-9:
        errors.append(f"unit rule gold MUNIT={gold_row['MUNIT']}")

    pops = _inventory()
    cand, aligned, ba = pops["candidate"], pops["aligned_bf"], pops["ba"]
    if len(cand) != EXPECTED_CANDIDATES:
        errors.append(f"A: candidate count {len(cand)} != {EXPECTED_CANDIDATES}")
    if len(aligned) != EXPECTED_ALIGNED:
        errors.append(f"C: aligned BF count {len(aligned)} != {EXPECTED_ALIGNED}")
    if len(ba) != EXPECTED_BA:
        errors.append(f"D: BA count {len(ba)} != {EXPECTED_BA}")

    ridr_path = OUT / "quikridr.csv"
    if not ridr_path.is_file():
        errors.append(f"missing {ridr_path}")
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1

    ridr = {}
    for row in _rows(ridr_path):
        key = (str(row.get("MPOLICY", "")).strip(), str(row.get("MPHASE", "")).strip())
        ridr[key] = row

    changed = 0
    for pol, rec in cand.items():
        qla = pol if pol.endswith("C") else pol + "C"
        row = ridr.get((qla, "1")) or ridr.get((qla, "01"))
        if row is None:
            errors.append(f"B: candidate {qla} missing from Output")
            continue
        munit = _fnum(row.get("MUNIT"))
        if munit is None or rec.expected_munit is None or abs(munit - rec.expected_munit) > ISSUE143_EPS:
            errors.append(f"B: {qla} MUNIT={row.get('MUNIT')} expected {rec.expected_munit}")
        else:
            changed += 1
        if rec.source_units is not None and abs((munit or 0) - rec.source_units) <= ISSUE143_EPS:
            errors.append(f"B: {qla} still at source units {rec.source_units}")

    aligned_unchanged = 0
    for pol, rec in aligned.items():
        qla = pol if pol.endswith("C") else pol + "C"
        row = ridr.get((qla, "1")) or ridr.get((qla, "01"))
        if row is None:
            errors.append(f"C: aligned {qla} missing from Output")
            continue
        munit = _fnum(row.get("MUNIT"))
        if rec.source_units is None or munit is None or abs(munit - rec.source_units) > ISSUE143_EPS:
            errors.append(f"C: aligned {qla} MUNIT={row.get('MUNIT')} source={rec.source_units}")
        else:
            aligned_unchanged += 1

    ba_unchanged = 0
    for pol, rec in ba.items():
        qla = pol if pol.endswith("C") else pol + "C"
        row = ridr.get((qla, "1")) or ridr.get((qla, "01"))
        if row is None:
            warnings.append(f"D: BA {qla} not in Output (environmental)")
            continue
        munit = _fnum(row.get("MUNIT"))
        if rec.source_units is None or munit is None or abs(munit - rec.source_units) > ISSUE143_EPS:
            errors.append(f"D: BA {qla} MUNIT={row.get('MUNIT')} source={rec.source_units}")
        else:
            ba_unchanged += 1

    gold = ridr.get((GOLD, "1")) or ridr.get((GOLD, "01"))
    gold_ok = False
    if gold is None:
        errors.append(f"E: gold {GOLD} missing")
    else:
        munit = _fnum(gold.get("MUNIT"))
        mvpu = _fnum(gold.get("MVPU")) or 0.0
        amount = round((munit or 0) * mvpu, 2)
        if munit is None or abs(munit - GOLD_AFTER) > 1e-6:
            errors.append(f"E: gold MUNIT={gold.get('MUNIT')} expected {GOLD_AFTER}")
        elif abs(amount - GOLD_AMOUNT) > 0.02:
            errors.append(f"E: gold Amount Ins={amount} expected {GOLD_AMOUNT}")
        else:
            gold_ok = True
        if str(gold.get("MPREM", "")).strip() != "9.77037":
            errors.append(f"F: gold MPREM changed to {gold.get('MPREM')}")
        if abs((mvpu or 0) - 1000.0) > 0.01:
            errors.append(f"F: gold MVPU changed to {gold.get('MVPU')}")
        if str(gold.get("MSAVEUNIT", "")).strip() != "":
            errors.append(f"F: gold MSAVEUNIT={gold.get('MSAVEUNIT')!r} (must stay blank)")
        if str(gold.get("MPOLICY", "")).strip() != GOLD:
            errors.append(f"F: gold MPOLICY={gold.get('MPOLICY')!r}")

    protected_hits = 0
    for pol, rec in {**cand, **aligned, **ba}.items():
        qla = pol if pol.endswith("C") else pol + "C"
        row = ridr.get((qla, "1")) or ridr.get((qla, "01"))
        if row is None:
            continue
        if rec.value_per_unit is not None:
            mvpu = _fnum(row.get("MVPU"))
            if mvpu is None or abs(mvpu - rec.value_per_unit) > 0.01:
                errors.append(f"F: {qla} MVPU={row.get('MVPU')} source VPU={rec.value_per_unit}")
                continue
        if str(row.get("MPOLICY", "")).strip() != qla:
            errors.append(f"F: {qla} MPOLICY drifted")
            continue
        protected_hits += 1

    iswl = []
    iswl_path = OUT / "QuikIswl.csv"
    iswl_now = {}
    if iswl_path.is_file():
        with iswl_path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
            for row in csv.DictReader(fh):
                iswl_now[str(row.get("MPOLICY", "")).strip()] = row
    for pol, rec in cand.items():
        qla = pol if pol.endswith("C") else pol + "C"
        row = ridr.get((qla, "1")) or ridr.get((qla, "01"))
        if row is None:
            continue
        plan = str(row.get("MPLAN", "")).strip()
        if plan not in ISWL_PLANS:
            continue
        expected_mdb = round((rec.expected_munit or 0) * 1000.0, 2)
        cur = _fnum((iswl_now.get(qla) or {}).get("MDB"))
        iswl.append(
            {
                "mpolicy": qla,
                "mplan": plan,
                "corrected_munit": rec.expected_munit,
                "current_quikiswl_mdb": cur,
                "expected_mdb_next_seed": expected_mdb,
            }
        )

    summary = {
        "result": "PASS" if not errors else "FAIL",
        "A_candidates": len(cand),
        "B_changed": changed,
        "C_aligned_unchanged": aligned_unchanged,
        "D_ba_unchanged": ba_unchanged,
        "E_gold_ok": gold_ok,
        "F_protected_checked": protected_hits,
        "G_issue124_iswl_rows": iswl,
        "gold_before_expected": GOLD_BEFORE,
        "errors": errors,
        "warnings": warnings,
    }
    EVID.mkdir(parents=True, exist_ok=True)
    outp = EVID / "issue143_validation_summary.json"
    outp.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "G_issue124_iswl_rows"}, indent=2))
    print("Issue #124 expected MDB rows:", len(iswl))
    for rec in iswl[:8]:
        print(" ", rec)
    print("wrote", outp)
    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
