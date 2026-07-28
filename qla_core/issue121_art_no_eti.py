"""Issue #121 — Annual Renewable Term must not emit ETI (MSTATUS/MPHSTAT 44).

LifePRO PAID_UP_TYPE LE/ET maps to ST_PUT_LE/ET → 44. ART products have no
Extended Term path; suppress PUT LE/ET and use CONTRACT_CODE+REASON instead.
"""

from __future__ import annotations

import os
from typing import Callable, FrozenSet, Set

# LifePRO PPBEN PLAN_CODE (phase 1)
ART_LIFEPRO_PLANS: FrozenSet[str] = frozenset(
    {
        "667 ART",
        "646 ART",
        "667 ART CR",
    }
)

# QLAdmin emit MPLAN
ART_QL_PLANS: FrozenSet[str] = frozenset(
    {
        "5667AT",
        "5646AT",
        "57ATCR",
    }
)

PUT_CODES_BLOCKED_ON_ART: FrozenSet[str] = frozenset({"LE", "ET"})


def normalize_plan(plan: object) -> str:
    return ("" if plan is None else str(plan)).strip().upper()


def is_art_lifepro_plan(plan: object) -> bool:
    p = ("" if plan is None else str(plan)).strip()
    return p in ART_LIFEPRO_PLANS or normalize_plan(p) in {
        normalize_plan(x) for x in ART_LIFEPRO_PLANS
    }


def is_art_ql_plan(plan: object) -> bool:
    return ("" if plan is None else str(plan)).strip().upper() in {
        x.upper() for x in ART_QL_PLANS
    }


def should_suppress_art_put_nfo(put: object, is_art_policy: bool) -> bool:
    """True when PUT LE/ET must not win on an ART policy."""
    if not is_art_policy:
        return False
    return ("" if put is None else str(put)).strip().upper() in PUT_CODES_BLOCKED_ON_ART


def build_art_lifepro_policy_cache(
    ppben_path: str,
    normalize_fn: Callable[[str], str],
) -> Set[str]:
    """Return normalized LifePRO POLICY_NUMBER set for phase-1 ART coverages."""
    import pandas as pd

    if not ppben_path or not os.path.exists(ppben_path):
        return set()

    df = pd.read_csv(
        ppben_path, encoding="latin1", low_memory=False, dtype=str, on_bad_lines="skip"
    ).fillna("")
    df.columns = [str(c).strip().upper() for c in df.columns]
    if "POLICY_NUMBER" not in df.columns or "PLAN_CODE" not in df.columns:
        return set()

    df = df[~df.iloc[:, 0].astype(str).str.contains("---", regex=False)]
    if "BENEFIT_TYPE" in df.columns:
        bt = df["BENEFIT_TYPE"].astype(str).str.strip().str.upper()
        df = df[~bt.isin(["UV", "FV", "SL"])]

    out: Set[str] = set()
    for _, row in df.iterrows():
        plan = str(row.get("PLAN_CODE", "")).strip()
        if not is_art_lifepro_plan(plan):
            continue
        seq_raw = str(row.get("BENEFIT_SEQ", "1")).strip()
        if seq_raw.endswith(".0"):
            seq_raw = seq_raw[:-2]
        if seq_raw and seq_raw.isdigit() and int(seq_raw) != 1:
            continue
        pol = normalize_fn(str(row.get("POLICY_NUMBER", "")))
        if pol:
            out.add(pol)
    return out
