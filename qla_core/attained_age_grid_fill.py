"""
Issue #140 — attained-age slot-axis housekeeping.

QLAdmin reads factor column n as slot n + CNTL*10 (Help 7.94 QuikGps / 7.82 QuikDbs),
and the rate-file import rule (Help p556) is explicit that a grid starts at duration 00
and uses 0.00 where there is nothing to rate:

    "Rates must begin starting with age 00 and duration 00 and up. If there are no
     rates for the lower ages, use 0.00."

An attained-age series starts at the first age the plan rates (1L14SC premiums begin at
45), so the pages below it would be absent. This fills those slots with zero so every
attained-age grid runs from CNTL=00 up to its highest populated page.

Only the plan/table pairs the loaders actually emitted on the slot axis are touched —
membership is carried from the loaders, never inferred from row shape, because a genuine
issue-age-0 row is indistinguishable from an attained-age key by shape alone.
"""
from __future__ import annotations

import json
import os

from qla_core import rate_dbf_schema as S

# Emit-time record of which plans went out on the slot axis. quikplan VARGP/VARDB
# derivation reads this instead of guessing from grid shape, because once the series
# sits on the slot axis an attained-age grid and a policy-year grid look identical.
MANIFEST_PARTS = ("QLA_Migration", "Reports", "rates", "attained_age_grid_manifest.json")

# (value, raw_value, lineno, age_capped, segment_tier, band_priority) — matches the cell
# tuple built by rate_factor_loader.build_factor_grid. lineno 0 marks a synthesized cell.
ZERO_CELL = (0.0, "0.00", 0, False, 0, 99)

SEGMENTATION_SLICE = slice(3, 9)  # GENDER, UWCLASS, BAND, ISSCNTRY, ISSUEST, EFFDATE


def _slot(cntl: str, col: int) -> int:
    return (int(cntl) if str(cntl).isdigit() else 0) * S.N_DURATION_COLS + col


def apply_attained_age_slot_fill(grids, slot_plans_by_table):
    """Zero-fill slots below the top populated slot of each attained-age grid.

    grids: {table: {key_tuple: {col: cell}}} from build_factor_grid
    slot_plans_by_table: {table: set(PLAN)} emitted on the slot axis

    Returns a list of audit dicts, one per synthesized cell run.
    """
    filled = []
    for table, plans in (slot_plans_by_table or {}).items():
        grid = grids.get(table)
        if not grid or not plans:
            continue

        # Highest populated slot per (plan, segmentation); AGE is the attained-age key.
        top_slot: dict[tuple, int] = {}
        for key, cells in grid.items():
            plan, age = key[0], key[1]
            if plan not in plans or age != S.ATTAINED_AGE_KEY:
                continue
            for col in cells:
                sig = (plan,) + tuple(key[SEGMENTATION_SLICE])
                slot = _slot(key[2], col)
                if slot > top_slot.get(sig, -1):
                    top_slot[sig] = slot

        for sig, top in sorted(top_slot.items()):
            plan = sig[0]
            segmentation = sig[1:]
            added = 0
            for slot in range(top + 1):
                cntl, col = S.duration_to_cntl_col(slot)
                key = (plan, S.ATTAINED_AGE_KEY, cntl) + segmentation
                cells = grid.setdefault(key, {})
                if col not in cells:
                    cells[col] = ZERO_CELL
                    added += 1
            if added:
                filled.append({
                    "TABLE": table,
                    "PLAN": plan,
                    "GENDER": segmentation[0],
                    "UWCLASS": segmentation[1],
                    "BAND": segmentation[2],
                    "TOP_SLOT": top,
                    "SLOTS_ZERO_FILLED": added,
                })
    return filled


def manifest_path(repo_root: str) -> str:
    return os.path.normpath(os.path.join(repo_root, *MANIFEST_PARTS))


def write_manifest(repo_root: str, slot_plans_by_table) -> str:
    """Record the attained-age plan set alongside the rates it was emitted with."""
    path = manifest_path(repo_root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        table: sorted(plans)
        for table, plans in sorted((slot_plans_by_table or {}).items())
        if plans
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def load_manifest(repo_root: str) -> dict:
    """Attained-age plans by table. Empty dict when absent — callers must fail safe."""
    path = manifest_path(repo_root)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        str(table): {str(p).strip() for p in plans if str(p).strip()}
        for table, plans in data.items()
        if isinstance(plans, list)
    }
