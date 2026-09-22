"""Issue 152 — base Prem/Unit must not include a rider that is loaded on its own row.

Closed Issue 88 still annualizes MODE_PREMIUM and divides by units when
ANN_PREM_PER_UNIT is blank. Warren's written exception on 2026-09-22 narrows
that MODE input on phase-1 base (BF) rows only: subtract active SU/SL/OR
MODE_PREMIUM values that are already stored on the rider rows.

The per-unit helper itself is unchanged. Rider-row premiums and billed
quikmstr mode premium are not inputs to this module.
"""

from __future__ import annotations

RIDER_BENEFIT_TYPES = frozenset({"SU", "SL", "OR"})


def _norm(val) -> str:
    if val is None:
        return ""
    s = str(val).strip().upper()
    if s.endswith(".0"):
        s = s[:-2]
    if s in {"", "NAN", "NONE", "NULL"}:
        return ""
    return s


def _money(val) -> float:
    s = _norm(val).replace(",", "")
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def is_phase1_bf(benefit_type, benefit_seq) -> bool:
    seq = _norm(benefit_seq)
    return _norm(benefit_type) == "BF" and seq in {"1", "01"}


def active_rider_modal_sums(rows) -> dict[str, float]:
    """Policy number -> sum of active SU/SL/OR MODE_PREMIUM where that mode is > 0."""
    sums: dict[str, float] = {}
    for row in rows:
        if _norm(row.get("BENEFIT_TYPE")) not in RIDER_BENEFIT_TYPES:
            continue
        if _norm(row.get("STATUS_CODE")) != "A":
            continue
        mode = _money(row.get("MODE_PREMIUM"))
        if mode <= 0.0:
            continue
        pol = _norm(row.get("POLICY_NUMBER"))
        if not pol:
            continue
        sums[pol] = sums.get(pol, 0.0) + mode
    return sums


def mode_after_active_riders(mode_prem: float, rider_sum: float) -> float:
    """Return base mode premium with separately loaded rider mode premium removed."""
    if rider_sum <= 0.0:
        return mode_prem
    adjusted = mode_prem - rider_sum
    if adjusted < 0.0:
        return 0.0
    return adjusted
