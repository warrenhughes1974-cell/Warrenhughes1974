"""Write Issue 152 phase-1 base MPREM onto the current quikridr.csv.

Recomputes from PPBEN / PPOLC. Safe to run again: it sets the field to the
formula result rather than subtracting from the value already in the file.
Does not change rider rows, units, or quikmstr.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from qla_core.issue152_rider_modal import (
    active_rider_modal_sums,
    is_phase1_bf,
    mode_after_active_riders,
)
from qla_core.modal_premium_factors import (
    blank_ann_annual_ppu,
    format_mprem_ppu,
    load_modal_factor_mapping,
)
from qla_core.normalize_utils import format_qladmin_mpolicy, normalize

OUT = PROJECT / "QLA_Migration" / "Output" / "quikridr.csv"
SRC = PROJECT / "QLA_Migration" / "Source"

GOLDS = {
    "9010723388C": 7.82,
    "9010723386C": 7.52,
    "9011069655C": 8.47,
    "9010987095C": 7.48,
}


def fnum(v):
    try:
        s = str(v).replace(",", "").strip()
        if not s:
            return None
        return float(s)
    except (TypeError, ValueError):
        return None


def _prefer(prefix: str) -> Path:
    hits = list(SRC.glob(f"{prefix}_*.csv")) or list(SRC.glob(f"**/{prefix}_*.csv"))
    if not hits:
        raise SystemExit(f"FAIL: {prefix} not found")
    return max(hits, key=lambda p: p.stat().st_mtime)


def _rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="latin1", errors="replace") as f:
        return [
            {k.strip().upper(): (v or "").strip() for k, v in row.items()}
            for row in csv.DictReader(f)
        ]


def expected_by_policy() -> dict[str, str]:
    ppben = _rows(_prefer("PPBEN_PolicyBenefit_Extract"))
    ppolc = _rows(_prefer("PPOLC_PolicyMaster_Extract"))
    bill_mode = {}
    bill_form = {}
    for row in ppolc:
        pol = normalize(row.get("POLICY_NUMBER"))
        if not pol:
            continue
        bm = fnum(row.get("BILLING_MODE"))
        if bm is not None:
            bill_mode[pol] = int(bm)
        if row.get("BILLING_FORM"):
            bill_form[pol] = row["BILLING_FORM"]
    sums = active_rider_modal_sums(ppben)
    factors = load_modal_factor_mapping()

    # MPLAN on the emitted base row is the factor key. Read it from current quikridr.
    mplan = {}
    munit = {}
    with OUT.open(newline="", encoding="latin1", errors="replace") as f:
        for row in csv.DictReader(f):
            rec = {k.strip().upper(): (v or "").strip() for k, v in row.items()}
            phase = fnum(rec.get("MPHASE"))
            if phase is None or int(phase) != 1:
                continue
            pol = rec.get("MPOLICY", "").strip()
            mplan[pol] = rec.get("MPLAN", "")
            munit[pol] = fnum(rec.get("MUNIT"))

    out = {}
    for row in ppben:
        if not is_phase1_bf(row.get("BENEFIT_TYPE"), row.get("BENEFIT_SEQ")):
            continue
        ann = fnum(row.get("ANN_PREM_PER_UNIT")) or 0.0
        if abs(ann) > 1e-12:
            continue
        pol = normalize(row.get("POLICY_NUMBER"))
        rider_sum = sums.get(pol, 0.0)
        if rider_sum <= 0.0:
            continue
        qla = format_qladmin_mpolicy(pol).strip()
        units = munit.get(qla) or fnum(row.get("NUMBER_OF_UNITS")) or 0.0
        if units <= 0.0 or qla not in mplan:
            continue
        mode = mode_after_active_riders(fnum(row.get("MODE_PREMIUM")) or 0.0, rider_sum)
        annual, _ = blank_ann_annual_ppu(
            mode,
            units,
            bill_mode.get(pol),
            bill_form.get(pol, ""),
            factors.get(mplan[qla]),
        )
        out[qla] = format_mprem_ppu(annual)
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    expected = expected_by_policy()
    for qla, exp in GOLDS.items():
        got = fnum(expected.get(qla))
        if got is None or abs(got - exp) > 0.0006:
            print(f"ABORT {qla} computed {expected.get(qla)} expected {exp}")
            return 1
    print(f"Computed {len(expected)} phase-1 updates. Golds match.")

    raw = OUT.read_bytes()
    eol = "\r\n" if b"\r\n" in raw[:4096] else "\n"
    encoding = "latin1"
    text = raw.decode(encoding)
    lines = text.splitlines()
    reader = csv.reader(lines)
    header = next(reader)
    idx = {name.strip().upper(): i for i, name in enumerate(header)}
    changed = 0
    new_lines = [",".join(header)]
    # Preserve original header text exactly.
    new_lines = [lines[0]]
    for line, row in zip(lines[1:], reader):
        if not row:
            new_lines.append(line)
            continue
        pol = row[idx["MPOLICY"]].strip()
        phase = fnum(row[idx["MPHASE"]])
        if phase is not None and int(phase) == 1 and pol in expected:
            current = row[idx["MPREM"]].strip()
            if current != expected[pol]:
                row[idx["MPREM"]] = expected[pol]
                changed += 1
                new_lines.append(",".join(row))
                continue
        new_lines.append(line)
    OUT.write_bytes((eol.join(new_lines) + eol).encode(encoding))
    print(f"Updated {changed} quikridr phase-1 MPREM values in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
