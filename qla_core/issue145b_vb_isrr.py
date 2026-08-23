"""Issue 145B — exclude vanishing (VB) PACT 0561 events from QuikIsrr emit.

VB identity is PPOLC.BILLING_REASON=VB via the same helper as Issue 145.
Do not use quikspec.VANISH as the emit source of truth.
"""
from __future__ import annotations

from qla_core.quikspec_resrvcat import _policy_lookup_keys
from qla_core.quikspec_vanish import load_ppolc_billing_reason


def is_vb_policy(policy: str, reasons: dict[str, str]) -> bool:
    for key in _policy_lookup_keys(policy):
        if reasons.get(key) == "VB":
            return True
    return False


def filter_vb_events(events, src_dir: str) -> tuple[list, list]:
    """Split #34-eligible events into (keep non-VB, drop VB)."""
    reasons = load_ppolc_billing_reason(src_dir)
    keep = []
    drop = []
    for ev in events:
        pol = getattr(ev, "mpolicy", None) or getattr(ev, "policy_number", "")
        if is_vb_policy(str(pol), reasons):
            drop.append(ev)
        else:
            keep.append(ev)
    return keep, drop
