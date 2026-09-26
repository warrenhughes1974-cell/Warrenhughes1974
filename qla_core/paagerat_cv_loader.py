"""
PAAGERAT paid-up-addition (PUA) cash value loader — QUIKCVS attained-age.

Eric 'Rates of Identified Issues - 8.13.26': PUA plans carried QuikPlCv keys but
no CV factors, so QLAdmin could not value PUA riders (implied LifePRO factors
668.16 = '670 PUA' M attained 60 interpolated; 840.52 = '960 PO PUA' M attained
84-85 interpolated). LifePRO stores PUA CV per unit by ATTAINED AGE in PAAGERAT
(SEQ = attained age), so these grids ride the Issue 140 slot axis exactly like
Wave 2 QuikDbs.

Business rules:
  * TYPE_CODE = 'CV' only, PAAGERAT primary table (RECORD_SEQ 1).
  * Attained-age series on the slot axis: AGE=00, CNTL=SEQ//10, column SEQ%10.
  * Scope: PUA MPLANs with no Rate_Table CV (direct or inherited). Plans already
    fed by CV inheritance (261PUA, 265PUA, 280PUA) are excluded to avoid grid
    collisions with their issue-age/duration CV.
  * Segment resolution: PAAGERAT.COVERAGE_ID -> PCOVRSGT -> PCOVR -> crosswalk PLAN.
"""
from __future__ import annotations

import os

from qla_core import rate_segment_resolution as SR
from qla_core.paagerat_pr_loader import transform_paagerat_attained_age
from qla_core.rate_factor_loader import LoaderConfig, load_plan_crosswalk

CV_TYPE_CODE = "CV"

# PUA plans whose only CV source is PAAGERAT (no Rate_Table slice, no inheritance).
PUA_CV_MPLAN_ALLOWLIST = frozenset({
    "121PUA", "165PUA", "170PUA", "185PUA", "1OLPUA", "1POPUA", "1970PA",
})


def pua_cv_mplan_allowlist(cfg: dict) -> frozenset:
    block = cfg.get("pua_cv", {})
    allow = block.get("cv_mplan_allowlist")
    if allow:
        return frozenset(str(p).strip() for p in allow)
    return PUA_CV_MPLAN_ALLOWLIST


def load_paagerat_cv_plan_set(paagerat_csv, pcovrsgt_csv, pcovr_csv, crosswalk_xlsx,
                              plan_allowlist: frozenset | None = None):
    """Return PLAN codes with resolved PAAGERAT PUA CV attained-age rates."""
    allow = plan_allowlist or PUA_CV_MPLAN_ALLOWLIST
    cov2plan, _ = load_plan_crosswalk(crosswalk_xlsx)
    resolver = SR.SegmentResolver.from_files(pcovrsgt_csv, pcovr_csv, cov2plan)
    config = LoaderConfig()
    plans = set()
    for t in transform_paagerat_pua_cv(paagerat_csv, resolver, config, plan_allowlist=allow):
        if t.get("status") == "IN_SCOPE":
            plans.add(t["plan"])
    return frozenset(plans)


def load_paagerat_cv_plan_set_from_config(repo_root, cfg) -> frozenset:
    if not cfg.get("pua_cv", {}).get("quikcvs_pua_enabled", False):
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
    return load_paagerat_cv_plan_set(
        pa_path, psgt_path, pcovr_path, xwalk_path,
        plan_allowlist=pua_cv_mplan_allowlist(cfg),
    )


def transform_paagerat_pua_cv(paagerat_csv, resolver: SR.SegmentResolver, config: LoaderConfig,
                              plan_allowlist: frozenset | None = None):
    """Stream PAAGERAT TYPE=CV rows for PUA QuikCvs (attained-age slot axis)."""
    allow = plan_allowlist or PUA_CV_MPLAN_ALLOWLIST
    return transform_paagerat_attained_age(
        paagerat_csv, resolver, config,
        type_code=CV_TYPE_CODE,
        plan_allowlist=allow,
        slot_axis=True,
    )
