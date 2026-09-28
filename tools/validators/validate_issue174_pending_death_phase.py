"""Issue #174 — pending death keeps policy status 50 and coverage status 22.

Fail-closed. Exit 1 if a Suspended/Death Pending policy does not have header 50
and every coverage phase at 22, or if the engine block list starts copying 50
onto the phase again.

The LifePRO extract is the one named by the current Output cut
(Reports/cut_manifest_latest.json QLA_VALUATION_DATE), so a later cut that
moves a policy to a real death (T/DC → 53) is not forced to stay 22.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output"
SRC = ROOT / "QLA_Migration" / "Source"
MANIFEST = ROOT / "QLA_Migration" / "Reports" / "cut_manifest_latest.json"

# Phase-1 premium that must not move on Brianna's example.
GOLD_MPREM = {
    "9011085655C": "52.656708",
}


def _s(value: object) -> str:
    return str(value or "").strip()


def _load(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _valuation_date() -> str:
    if MANIFEST.is_file():
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for key in ("QLA_VALUATION_DATE", "valuation_date"):
            raw = data.get(key)
            if isinstance(raw, str) and raw.isdigit() and len(raw) == 8:
                return raw
            if isinstance(raw, dict):
                nested = raw.get("QLA_VALUATION_DATE") or raw.get("valuation_date")
                if isinstance(nested, str) and nested.isdigit() and len(nested) == 8:
                    return nested
        # cut_manifest stores the date under runs / env blocks.
        blob = json.dumps(data)
        marker = '"QLA_VALUATION_DATE": "'
        idx = blob.find(marker)
        if idx >= 0:
            token = blob[idx + len(marker): idx + len(marker) + 8]
            if token.isdigit():
                return token
    return "20260630"


def _unit_checks() -> list[str]:
    sys.path.insert(0, str(ROOT))
    from qla_core.quikmstr_active_phase_status import (
        PHASE1_INHERIT_BLOCK,
        select_mstatus_from_active_phase,
        simulate_display_phase_statuses,
    )

    errors: list[str] = []
    if "50" not in PHASE1_INHERIT_BLOCK:
        errors.append("PHASE1_INHERIT_BLOCK no longer excludes status 50")
    bare = {"A": "22", "T": "56"}
    display = simulate_display_phase_statuses(
        "50",
        [(1, 0, "A", "BA"), (2, 1, "A", "PU")],
        bare,
    )
    final, overridden = select_mstatus_from_active_phase(
        "50",
        [(1, 0, "A", "BA"), (2, 1, "A", "PU")],
        bare,
    )
    if display != ["22", "22"]:
        errors.append(f"pending-death phases displayed {display}, expected ['22', '22']")
    if final != "50" or overridden:
        errors.append(f"pending-death header became {final!r} overridden={overridden}")
    death_display = simulate_display_phase_statuses("53", [(1, 0, "T", "BA")], bare)
    if death_display != ["53"]:
        errors.append(f"terminated death phase displayed {death_display}, expected ['53']")
    return errors


def main() -> int:
    errors = _unit_checks()
    val_date = _valuation_date()
    ppolc = SRC / f"PPOLC_PolicyMaster_Extract_{val_date}.csv"
    qm_path = OUT / "quikmstr.csv"
    qr_path = OUT / "quikridr.csv"
    print("Issue #174 pending-death phase validator")
    print(f"valuation date {val_date}")
    if not ppolc.is_file() or not qm_path.is_file() or not qr_path.is_file():
        print(f"FAIL: missing source or output ({ppolc.name})")
        return 1

    pending: set[str] = set()
    deaths = 0
    with ppolc.open(newline="", encoding="latin1") as handle:
        for row in csv.DictReader(handle):
            code = _s(row.get("CONTRACT_CODE")).upper()
            reason = _s(row.get("CONTRACT_REASON")).upper()
            policy = _s(row.get("POLICY_NUMBER"))
            if not policy:
                continue
            qla = policy if policy.endswith("C") else policy + "C"
            if code == "S" and reason == "DP":
                pending.add(qla)
            elif code == "T" and reason == "DC":
                deaths += 1

    mstatus = {_s(row.get("MPOLICY")): _s(row.get("MSTATUS")) for row in _load(qm_path)}
    phases: dict[str, list[dict]] = defaultdict(list)
    for row in _load(qr_path):
        phases[_s(row.get("MPOLICY"))].append(row)

    checked = 0
    for policy in sorted(pending):
        if policy not in mstatus:
            continue
        checked += 1
        if mstatus[policy] != "50":
            errors.append(f"{policy} header is {mstatus[policy]!r}, expected 50")
        rows = phases.get(policy, [])
        if not rows:
            errors.append(f"{policy} has no quikridr row")
            continue
        for row in rows:
            if _s(row.get("MPHSTAT")) != "22" or _s(row.get("MSAVESTAT")) != "22":
                errors.append(
                    f"{policy} phase {_s(row.get('MPHASE'))} "
                    f"MPHSTAT={_s(row.get('MPHSTAT'))!r} "
                    f"MSAVESTAT={_s(row.get('MSAVESTAT'))!r}, expected 22"
                )
        expected_prem = GOLD_MPREM.get(policy)
        if expected_prem:
            phase1 = next((row for row in rows if _s(row.get("MPHASE")) in {"1", "01"}), None)
            if phase1 is None or _s(phase1.get("MPREM")) != expected_prem:
                actual = _s(phase1.get("MPREM")) if phase1 else "missing"
                errors.append(f"{policy} MPREM {actual!r}, expected {expected_prem}")

    if checked == 0:
        errors.append(f"no S/DP policies from {ppolc.name} are in Output")

    # A real death on this extract must still be terminal somewhere.
    terminal_deaths = 0
    with ppolc.open(newline="", encoding="latin1") as handle:
        for row in csv.DictReader(handle):
            if _s(row.get("CONTRACT_CODE")).upper() != "T":
                continue
            if _s(row.get("CONTRACT_REASON")).upper() != "DC":
                continue
            policy = _s(row.get("POLICY_NUMBER"))
            qla = policy if policy.endswith("C") else policy + "C"
            status = mstatus.get(qla, "")
            if status == "53":
                phase1 = next(
                    (
                        item
                        for item in phases.get(qla, [])
                        if _s(item.get("MPHASE")) in {"1", "01"}
                    ),
                    None,
                )
                if phase1 is not None and _s(phase1.get("MPHSTAT")) == "53":
                    terminal_deaths += 1
                    break
    if deaths and terminal_deaths == 0:
        errors.append("no T/DC policy still has header 53 and phase 53")

    print(f"S/DP policies checked in Output: {checked}")
    if errors:
        print(f"FAIL: {len(errors)}")
        for item in errors[:30]:
            print(f"  {item}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
