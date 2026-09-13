"""
Issue #166 — quikdvdp.MDEPINT plan buckets (Eric / #95 rates on the policy table).

Warren override 2026-09-13: replace Closed #21D non-ISWL 4.00 default with these
buckets. ISWL / named 4.50 plans stay 4.50. Do not expand ISWL_MPLAN_ALLOWLIST.
"""
from __future__ import annotations

from datetime import datetime

from qla_core.quikuint_loader import DEFAULT_RATE_200_PLANS, DEFAULT_RATE_450_PLANS

MDEPINT_450 = "4.50"
MDEPINT_350 = "3.50"
MDEPINT_200 = "2.00"
YEAR_END_MMDD = "1231"


def _clean_plan(mplan) -> str:
    if mplan is None:
        return ""
    return str(mplan).strip()


def mdepint_for_mplan(mplan) -> str | None:
    """Return MDEPINT percent, or None to keep the rulebook 4.00 fallback."""
    plan = _clean_plan(mplan)
    if not plan:
        return None
    if plan in DEFAULT_RATE_450_PLANS:
        return MDEPINT_450
    if plan in DEFAULT_RATE_200_PLANS:
        return MDEPINT_200
    if plan[:1] in ("9", "A"):
        return None
    return MDEPINT_350


def is_year_end_mintdate(raw) -> bool:
    digits = "".join(c for c in str(raw or "") if c.isdigit())
    return len(digits) >= 8 and digits[:8][4:8] == YEAR_END_MMDD


def prior_anniversary_yyyymmdd(issue_raw, valuation_raw) -> str:
    """Last completed policy anniversary on or before the valuation date."""
    iss = "".join(c for c in str(issue_raw or "") if c.isdigit())[:8]
    val = "".join(c for c in str(valuation_raw or "") if c.isdigit())[:8]
    if len(iss) != 8 or len(val) != 8:
        return ""
    try:
        im, iday = int(iss[4:6]), int(iss[6:8])
        vy, vm, vday = int(val[:4]), int(val[4:6]), int(val[6:8])
    except ValueError:
        return ""
    year = vy - 1 if (vm, vday) < (im, iday) else vy
    if im == 2 and iday == 29:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        if not leap:
            iday = 28
    try:
        datetime(year, im, iday)
    except ValueError:
        return ""
    out = f"{year:04d}{im:02d}{iday:02d}"
    return out if out <= val else ""


def overlay_year_end_mintdate(mintdate_raw, deposit_raw, issue_raw, valuation_raw) -> str:
    """If paid-to is year-end and deposit > 0, return prior anniversary; else blank (no overlay)."""
    try:
        deposit = float(str(deposit_raw or "0").replace(",", "").strip() or 0)
    except ValueError:
        deposit = 0.0
    if deposit <= 0 or not is_year_end_mintdate(mintdate_raw):
        return ""
    return prior_anniversary_yyyymmdd(issue_raw, valuation_raw)
