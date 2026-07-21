"""
PAAGERAT death benefit (DB) loader — Wave 2 QUIKDBS / QUIKPLDB.

Business rules:
  * TYPE_CODE = 'DB' only.
  * Attained-age scalar: SEQ -> QuikDbs.AGE, CNTL=00, VALUE_INFO -> DB0 (VARDB=3).
  * Scope: Wave 2 PAAGERAT-only DB MPLAN allowlist.
  * Segment resolution: PAAGERAT.COVERAGE_ID -> PCOVRSGT -> PCOVR -> crosswalk PLAN.
"""
from __future__ import annotations

import os

from qla_core import rate_segment_resolution as SR
from qla_core.paagerat_pr_loader import transform_paagerat_attained_age
from qla_core.rate_factor_loader import LoaderConfig, load_plan_crosswalk

DB_TYPE_CODE = "DB"

WAVE2_DB_MPLAN_ALLOWLIST = frozenset({
    "130JEB", "1970JB", "542STR", "578STR", "719CDT",
    "7619DT", "7619PU", "7647FP", "7647SP", "7690DT",
})


def wave2_db_mplan_allowlist(cfg: dict) -> frozenset:
    block = cfg.get("wave2_db", {})
    allow = block.get("db_mplan_allowlist")
    if allow:
        return frozenset(str(p).strip() for p in allow)
    return WAVE2_DB_MPLAN_ALLOWLIST


def load_paagerat_db_plan_set(paagerat_csv, pcovrsgt_csv, pcovr_csv, crosswalk_xlsx,
                              plan_allowlist: frozenset | None = None):
    """Return PLAN codes with resolved PAAGERAT DB attained-age rates."""
    allow = plan_allowlist or WAVE2_DB_MPLAN_ALLOWLIST
    cov2plan, _ = load_plan_crosswalk(crosswalk_xlsx)
    resolver = SR.SegmentResolver.from_files(pcovrsgt_csv, pcovr_csv, cov2plan)
    config = LoaderConfig()
    plans = set()
    for t in transform_paagerat_db(paagerat_csv, resolver, config, plan_allowlist=allow):
        if t.get("status") == "IN_SCOPE":
            plans.add(t["plan"])
    return frozenset(plans)


def load_paagerat_db_plan_set_from_config(repo_root, cfg) -> frozenset:
    if not cfg.get("wave2_db", {}).get("quikdbs_enabled", False):
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
    return load_paagerat_db_plan_set(
        pa_path, psgt_path, pcovr_path, xwalk_path,
        plan_allowlist=wave2_db_mplan_allowlist(cfg),
    )


def transform_paagerat_db(paagerat_csv, resolver: SR.SegmentResolver, config: LoaderConfig,
                          plan_allowlist: frozenset | None = None):
    """Stream PAAGERAT TYPE=DB rows for Wave 2 QuikDbs (VARDB=3 attained-age)."""
    allow = plan_allowlist or WAVE2_DB_MPLAN_ALLOWLIST
    return transform_paagerat_attained_age(
        paagerat_csv, resolver, config,
        type_code=DB_TYPE_CODE,
        plan_allowlist=allow,
    )
