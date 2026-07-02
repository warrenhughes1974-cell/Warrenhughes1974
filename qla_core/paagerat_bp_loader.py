"""
PAAGERAT billable premium (BP) loader — ISWL Phase 2 QUIKGPS.

Business rules:
  * TYPE_CODE = 'BP' only (not PR — waiver/rider PR remains on separate path).
  * Same attained-age scalar as PR: SEQ -> QuikGps.AGE, CNTL=00, VALUE_INFO -> GP0.
  * Scope: ISWL BP MPLAN allowlist only (1658CS, 1659CS, 1669SR, 1679CS).
  * Segment resolution: PAAGERAT.COVERAGE_ID -> PCOVRSGT -> PCOVR -> crosswalk PLAN.
"""
from __future__ import annotations

import os

from qla_core import rate_segment_resolution as SR
from qla_core.paagerat_pr_loader import (
    ISWL_BP_MPLAN_ALLOWLIST,
    transform_paagerat_attained_age,
)
from qla_core.rate_factor_loader import LoaderConfig, load_plan_crosswalk

BP_TYPE_CODE = "BP"


def iswl_bp_mplan_allowlist(cfg: dict) -> frozenset:
    phase2 = cfg.get("iswl_phase2", {})
    allow = phase2.get("bp_mplan_allowlist")
    if allow:
        return frozenset(str(p).strip() for p in allow)
    return ISWL_BP_MPLAN_ALLOWLIST


def load_paagerat_bp_plan_set(paagerat_csv, pcovrsgt_csv, pcovr_csv, crosswalk_xlsx,
                              plan_allowlist: frozenset | None = None):
    """Return PLAN codes with resolved PAAGERAT BP attained-age rates."""
    allow = plan_allowlist or ISWL_BP_MPLAN_ALLOWLIST
    cov2plan, _ = load_plan_crosswalk(crosswalk_xlsx)
    resolver = SR.SegmentResolver.from_files(pcovrsgt_csv, pcovr_csv, cov2plan)
    config = LoaderConfig()
    plans = set()
    for t in transform_paagerat_bp(paagerat_csv, resolver, config, plan_allowlist=allow):
        if t.get("status") == "IN_SCOPE":
            plans.add(t["plan"])
    return frozenset(plans)


def load_paagerat_bp_plan_set_from_config(repo_root, cfg) -> frozenset:
    if not cfg.get("iswl_phase2", {}).get("quikgps_enabled", False):
        return frozenset()
    pa = cfg.get("paagerat_pr_extract")
    if not pa:
        return frozenset()
    pa_path = pa if os.path.isabs(pa) else os.path.join(repo_root, pa)
    psgt = cfg.get("pcovrsgt_csv", "")
    pcovr = cfg.get("pcovr_csv", "")
    xwalk = cfg.get("plan_form_crosswalk", "")
    psgt_path = psgt if os.path.isabs(psgt) else os.path.join(repo_root, psgt)
    pcovr_path = pcovr if os.path.isabs(pcovr) else os.path.join(repo_root, pcovr)
    xwalk_path = xwalk if os.path.isabs(xwalk) else os.path.join(repo_root, xwalk)
    if not all(os.path.isfile(p) for p in (pa_path, psgt_path, pcovr_path, xwalk_path)):
        return frozenset()
    return load_paagerat_bp_plan_set(
        pa_path, psgt_path, pcovr_path, xwalk_path,
        plan_allowlist=iswl_bp_mplan_allowlist(cfg),
    )


def transform_paagerat_bp(paagerat_csv, resolver: SR.SegmentResolver, config: LoaderConfig,
                          plan_allowlist: frozenset | None = None):
    """Stream PAAGERAT TYPE=BP rows for ISWL billable premium (QuikGps / VARGP=3)."""
    allow = plan_allowlist or ISWL_BP_MPLAN_ALLOWLIST
    return transform_paagerat_attained_age(
        paagerat_csv, resolver, config,
        type_code=BP_TYPE_CODE,
        plan_allowlist=allow,
    )
