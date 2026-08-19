"""Issue 139 always-on ISWL policy-fee withhold smoke.

Warren 2026-08-09 / 08-11: ISWL and UNKNOWN fees stay off; non-ISWL keep #21C/#58.
A later quikridr rebatch that skips suppress_policy_fees puts the $25 ISWL fee
back on — this smoke is the hard stop so that drop cannot ship.
"""
from __future__ import annotations

import csv
from pathlib import Path

from qla_core.cso_mortality_crosswalk import is_iswl_mplan
from qla_core.modal_premium_factors import POLICY_FEE_FIELDS

MIN_ISWL = 2000
MIN_NON_ISWL_FEE = 2000
FLEET_ISWL_MIN = 500

ISWL_GOLD = "9010713704C"
ISWL_GOLD_MMODEPREM = "41.71"
NON_ISWL_GOLD = "9010367131C"


def _num(val) -> float:
    try:
        return float(str(val or "").strip().replace(",", "") or 0)
    except ValueError:
        return 0.0


def _any_fee(row: dict) -> bool:
    return any(_num(row.get(f)) > 0 for f in POLICY_FEE_FIELDS)


def evaluate_fee_withhold(
    ridr_path: Path, mstr_path: Path | None = None
) -> tuple[bool, list[str], dict]:
    errors: list[str] = []
    stats = {
        "phase1": 0,
        "iswl": 0,
        "iswl_fee": 0,
        "non_iswl": 0,
        "non_iswl_fee": 0,
        "unknown": 0,
        "unknown_fee": 0,
        "traces": {},
    }
    if not ridr_path.is_file():
        return False, [f"Missing output: {ridr_path}"], stats

    with ridr_path.open(newline="", encoding="latin1", errors="replace") as fh:
        for row in csv.DictReader(fh):
            if str(row.get("MPHASE") or "").strip() not in ("1", "01"):
                continue
            stats["phase1"] += 1
            pol = str(row.get("MPOLICY") or "").strip()
            plan = str(row.get("MPLAN") or "").strip()
            if pol in (ISWL_GOLD, NON_ISWL_GOLD):
                stats["traces"][pol] = {
                    f: str(row.get(f) or "").strip() for f in POLICY_FEE_FIELDS
                }
                stats["traces"][pol]["MPLAN"] = plan
            if not plan:
                stats["unknown"] += 1
                if _any_fee(row):
                    stats["unknown_fee"] += 1
                continue
            if is_iswl_mplan(plan):
                stats["iswl"] += 1
                if _any_fee(row):
                    stats["iswl_fee"] += 1
            else:
                stats["non_iswl"] += 1
                if _num(row.get("MANNLFEE")) > 0:
                    stats["non_iswl_fee"] += 1

    if stats["phase1"] >= FLEET_ISWL_MIN and stats["iswl"] < MIN_ISWL:
        errors.append(f"ISWL phase-1 count {stats['iswl']} < {MIN_ISWL}")
    if stats["iswl_fee"]:
        errors.append(f"ISWL rows with nonzero fees = {stats['iswl_fee']} (must be 0)")
    if stats["unknown_fee"]:
        errors.append(f"UNKNOWN rows with nonzero fees = {stats['unknown_fee']} (must be 0)")
    if stats["unknown"]:
        errors.append(f"UNKNOWN phase-1 MPLAN count = {stats['unknown']} (must be 0)")
    if stats["non_iswl_fee"] < MIN_NON_ISWL_FEE:
        errors.append(
            f"non-ISWL MANNLFEE>0 = {stats['non_iswl_fee']} < {MIN_NON_ISWL_FEE} "
            "(#21C/#58 wiped or still fleet-suppressed)"
        )

    gold = stats["traces"].get(ISWL_GOLD) or {}
    if not gold:
        errors.append(f"missing ISWL gold {ISWL_GOLD}")
    elif any(_num(gold.get(f)) > 0 for f in POLICY_FEE_FIELDS):
        errors.append(f"{ISWL_GOLD} still has ISWL policy fees {gold}")

    non = stats["traces"].get(NON_ISWL_GOLD) or {}
    if not non:
        errors.append(f"missing non-ISWL gold {NON_ISWL_GOLD}")
    elif _num(non.get("MANNLFEE")) <= 0:
        errors.append(f"{NON_ISWL_GOLD} non-ISWL MANNLFEE missing")

    if mstr_path and mstr_path.is_file():
        with mstr_path.open(newline="", encoding="latin1", errors="replace") as fh:
            for row in csv.DictReader(fh):
                if str(row.get("MPOLICY") or "").strip() != ISWL_GOLD:
                    continue
                got = str(row.get("MMODEPREM") or "").strip()
                stats["traces"][ISWL_GOLD + "_MMODEPREM"] = got
                if got != ISWL_GOLD_MMODEPREM:
                    errors.append(
                        f"{ISWL_GOLD} MMODEPREM={got} expected {ISWL_GOLD_MMODEPREM} "
                        "(fee still inside mode premium, or withhold not applied)"
                    )
                break
        if ISWL_GOLD + "_MMODEPREM" not in stats["traces"]:
            errors.append(f"missing {ISWL_GOLD} on quikmstr")

    return not errors, errors, stats
