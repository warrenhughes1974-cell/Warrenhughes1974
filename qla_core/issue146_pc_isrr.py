"""Issue 146 — exclude locked former-vanish 0561 events from QuikIsrr emit.

Identity is the 20-policy allowlist (19 PC + 9010808831).
Do not use BILLING_REASON=PC as a fleet filter.
Do not set quikspec.VANISH.
"""
from __future__ import annotations

from qla_core.quikspec_resrvcat import _policy_lookup_keys

# Source keys without the Issue #2 C suffix.
ALLOWLIST_SOURCE = (
    "9010758550",
    "9010765198",
    "9010770062",
    "9010771070",
    "9010773468",
    "9010776813",
    "9010777059",
    "9010787639",
    "9010788679",
    "9010810228",
    "9010811998",
    "9010816969",
    "9010817956",
    "9010821435",
    "9010826551",
    "9010849882",
    "9010943849",
    "9011048543",
    "9011077629",
    "9010808831",
)

KEEP_SOURCE = (
    "9010761639",
    "9010760840",
)


def _expand_keys(policies: tuple[str, ...]) -> frozenset[str]:
    keys: set[str] = set()
    for pol in policies:
        keys.update(_policy_lookup_keys(pol))
        keys.update(_policy_lookup_keys(pol + "C"))
    return frozenset(keys)


ALLOWLIST_KEYS = _expand_keys(ALLOWLIST_SOURCE)
KEEP_KEYS = _expand_keys(KEEP_SOURCE)


def is_issue146_policy(policy: str) -> bool:
    return any(key in ALLOWLIST_KEYS for key in _policy_lookup_keys(policy))


def is_issue146_keep_policy(policy: str) -> bool:
    return any(key in KEEP_KEYS for key in _policy_lookup_keys(policy))


def filter_issue146_events(events) -> tuple[list, list]:
    """Split leftover #34 events into (keep, drop allowlist)."""
    keep = []
    drop = []
    for ev in events:
        pol = getattr(ev, "mpolicy", None) or getattr(ev, "policy_number", "")
        if is_issue146_policy(str(pol)):
            drop.append(ev)
        else:
            keep.append(ev)
    return keep, drop
