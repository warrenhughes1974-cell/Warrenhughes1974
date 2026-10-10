"""
PAAGERAT policy premium (PR) loader — segment-resolved attained-age rates.

Business rules:
  * PAAGERAT.COVERAGE_ID is a segment ID (PCOVRSGT.SEGT_ID), not a policy form.
  * Resolve: PAAGERAT -> PCOVRSGT -> PCOVR -> Policy Form Crosswalk -> PLAN.
  * Only TYPE_CODE = 'PR' rows are in scope for policy gross premium rates.
  * QuikPlan.VARGP = 3 (attained age): SEQ -> slot, rate at AGE=00 / CNTL=slot//10,
    column slot%10 (Issue 140). NF keeps the pre-140 single-cell layout.
  * Plans in paagerat_pr_level_period are the exception: their PR rows are
    rewritten to an issue-age by policy-year grid (VARGP 2). See
    qla_core.level_period_premium. Every other plan stays on the slot axis.
  * ISWL MPLANs with PAAGERAT BP authority suppress PR emit (Phase 2 — Issue #31).
"""
import csv
import os

from qla_core import rate_dbf_schema as S
from qla_core import rate_segment_resolution as SR
from qla_core.level_period_premium import (
    level_period_enabled,
    renewal_periods,
    reshape_pr_stream,
)
from qla_core.rate_factor_loader import LoaderConfig, _to_float, load_plan_crosswalk

VARGP_ATTAINED_AGE = "3"

# Issue 138: PR SEQ is 1-based, so the rate it carries belongs to SEQ-1.
# Verified against LifePRO ANN_PREM_PER_UNIT on 22 plans (100% of policies) with
# zero contradicting plans; see Issue_Log_Items/Issue_138.
PR_AGE_OFFSET = -1

# Phase 2 — ISWL billable premium MPLANs (PAAGERAT BP); PR suppressed on these plans.
ISWL_BP_MPLAN_ALLOWLIST = frozenset({"1658CS", "1659CS", "1669SR", "1679CS"})

# Issue #158: PCOVRSGT.SEQ is the rate-type slot; premium segments sit at SEQ 1.
# Resolving PR ownership on that slot stops riders/PUAs that reference a segment
# elsewhere in their list from capturing its premium grid, and lets a segment
# carried at SEQ 1 by two coverages reach both plans.
PR_OWNERSHIP_SLOT = 1
SLOT_OWNERSHIP_ENV = "QLA_PR_SEGMENT_SLOT_OWNERSHIP"


def pr_slot_ownership_enabled() -> bool:
    """Issue #158 kill switch: QLA_PR_SEGMENT_SLOT_OWNERSHIP=0 restores single-parent PR routing."""
    raw = (os.environ.get(SLOT_OWNERSHIP_ENV) or "1").strip().lower()
    return raw not in ("0", "false", "no", "off")

# Issue 140: QLAdmin reads factor column n as year n + CNTL*10 and uses AGE as the
# issue-age key (Help 7.94 QuikGps / 7.82 QuikDbs). An attained-age series therefore
# rides the slot axis with AGE=00, and VARGP/VARDB=3 tells QLAdmin to read that axis
# as attained age. Only callers with a plan-level variation code opt in.
SLOT_AXIS_ENV = "QLA_ATTAINED_AGE_SLOT_AXIS"


def attained_age_slot_axis_enabled() -> bool:
    """Issue 140 kill switch: QLA_ATTAINED_AGE_SLOT_AXIS=0 restores the prior layout."""
    raw = (os.environ.get(SLOT_AXIS_ENV) or "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _iswl_bp_suppress_plans(cfg: dict) -> frozenset:
    """Plans where PR is suppressed because BP is billable-premium authority."""
    if not cfg.get("iswl_phase2", {}).get("quikgps_enabled", False):
        return frozenset()
    phase2 = cfg.get("iswl_phase2", {})
    allow = phase2.get("bp_mplan_allowlist")
    if allow:
        return frozenset(str(p).strip() for p in allow)
    return ISWL_BP_MPLAN_ALLOWLIST


def transform_paagerat_attained_age(
    paagerat_csv,
    resolver: SR.SegmentResolver,
    config: LoaderConfig,
    *,
    type_code: str,
    target_table: str | None = None,
    plan_allowlist: frozenset | None = None,
    plan_exclude: frozenset | None = None,
    age_offset: int = 0,
    slot_axis: bool = False,
    ownership_slot: int | None = None,
):
    """
    Stream PAAGERAT rows for a single TYPE_CODE, segment-resolved to PLAN.

    Yields dicts with status:
      IN_SCOPE | EXCLUDED | SEGMENT_UNRESOLVED | PLAN_INVALID | BAD_VALUE
    """
    table = target_table or S.TYPE_TO_TABLE.get(type_code)
    if table is None:
        return

    with open(paagerat_csv, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        hdr = [c.strip() for c in next(rd)]
        col = {n: i for i, n in enumerate(hdr)}
        lineno = 1
        for row in rd:
            lineno += 1
            seg = row[col["COVERAGE_ID"]].strip()
            typ = row[col["TYPE_CODE"]].strip()
            if seg and set(seg) == {"-"}:
                continue

            if typ != type_code:
                yield {"status": "EXCLUDED", "type_code": typ, "coverage_id": seg,
                       "lineno": lineno, "note": f"non-{type_code} PAAGERAT row"}
                continue

            rec_seq = row[col["RECORD_SEQ"]].strip() if "RECORD_SEQ" in col else "1"
            if rec_seq != "1":
                yield {"status": "EXCLUDED", "type_code": typ, "coverage_id": seg,
                       "lineno": lineno, "note": f"RECORD_SEQ={rec_seq} (primary table is 1)"}
                continue

            # Issue #158: when the caller names a SEQ slot, ownership comes from that
            # slot and a segment may legitimately belong to more than one coverage.
            if ownership_slot is None:
                single = resolver.resolve(seg, source="paagerat")
                resolutions = [single] if single else []
            else:
                resolutions = resolver.resolve_all(seg, slot=ownership_slot)
            if not resolutions:
                yield {"status": "SEGMENT_UNRESOLVED", "type_code": typ,
                       "coverage_id": seg, "lineno": lineno}
                continue

            for resolved in resolutions:
                plan = resolved.plan
                if " " in plan or not plan:
                    yield {"status": "PLAN_INVALID", "type_code": typ, "coverage_id": seg,
                           "plan": plan, "parent_coverage_id": resolved.parent_coverage_id,
                           "lineno": lineno}
                    continue

                if plan_allowlist is not None and plan not in plan_allowlist:
                    yield {"status": "EXCLUDED", "type_code": typ, "coverage_id": seg,
                           "plan": plan, "lineno": lineno,
                           "note": f"plan {plan} outside allowlist"}
                    continue

                if plan_exclude and plan in plan_exclude:
                    yield {"status": "EXCLUDED", "type_code": typ, "coverage_id": seg,
                           "plan": plan, "lineno": lineno,
                           "note": f"PR suppressed — BP authority for ISWL MPLAN {plan}"}
                    continue

                sex = row[col["SEX"]].strip()
                band = row[col["BAND"]].strip()
                uw = row[col["UWCLS"]].strip()
                seq = row[col["SEQ"]].strip()
                vi = col.get("VALUE_INFO")
                vf = col.get("VALUE_FLOAT")
                val_raw = row[vi].strip() if vi is not None else row[vf].strip()

                value = _to_float(val_raw)
                if value is None:
                    yield {"status": "BAD_VALUE", "type_code": typ, "coverage_id": seg,
                           "plan": plan, "raw_value": val_raw, "lineno": lineno}
                    continue

                gender = S.map_sex(sex)
                uwclass = S.map_uwclass(uw, plan=plan, coverage_id=seg)
                if band not in S.BAND_MAP:
                    yield {"status": "BAD_VALUE", "type_code": typ, "coverage_id": seg,
                           "plan": plan, "note": f"unsupported BAND {band}", "lineno": lineno}
                    continue
                band2 = S.map_band(band)
                if gender is None or uwclass is None or band2 is None:
                    yield {"status": "BAD_VALUE", "type_code": typ, "coverage_id": seg,
                           "plan": plan, "note": "segmentation crosswalk", "lineno": lineno}
                    continue

                # SEQ -> factor AGE; cap at QLAdmin C2 width.
                # Issue 138: PR SEQ is a 1-based LifePRO ordinal, so it sits one year
                # above the issue age it rates (SEQ 46 -> age 45). Callers that carry a
                # verified offset pass it; other TYPE_CODEs stay unshifted until proven.
                original_age = seq
                age_capped = False
                if seq.isdigit():
                    age_int = int(seq) + age_offset
                    if age_int < 0:
                        yield {"status": "BAD_VALUE", "type_code": typ, "coverage_id": seg,
                               "plan": plan, "raw_age": seq, "lineno": lineno,
                               "note": f"SEQ {seq} below age floor at offset {age_offset}"}
                        continue
                    if age_int > S.MAX_AGE:
                        age_int = S.MAX_AGE
                        age_capped = True
                    age2 = str(age_int).zfill(2)
                else:
                    yield {"status": "BAD_VALUE", "type_code": typ, "coverage_id": seg,
                           "plan": plan, "raw_age": seq, "lineno": lineno}
                    continue

                # Issue 138 left the storage axis open; Issue 140 closes it. Callers whose
                # table carries a VARGP/VARDB attained-age code place the age on the slot
                # axis (AGE=00, slot = attained age); the rest keep the single-cell layout.
                use_slot_axis = slot_axis and attained_age_slot_axis_enabled()
                if use_slot_axis:
                    age2, cntl, col_idx = S.attained_age_to_age_cntl_col(age_int)
                    ql_duration = age_int
                else:
                    cntl, col_idx = S.duration_to_cntl_col(0)
                    ql_duration = 0
                segment_tier = 0 if seg == resolved.parent_coverage_id else 1

                yield {
                    "status": "IN_SCOPE",
                    "source": "PAAGERAT",
                    "coverage_id": seg,
                    "parent_coverage_id": resolved.parent_coverage_id,
                    "segment_tier": segment_tier,
                    "resolution_path": resolved.resolution_path,
                    "pcovr_description": resolved.pcovr_description,
                    "type_code": typ,
                    "table": table,
                    "plan": plan,
                    "age": age2,
                    "cntl": cntl,
                    "col": col_idx,
                    "gender": gender,
                    "uwclass": uwclass,
                    "band": band2,
                    "source_band_raw": band,
                    "isscntry": config.isscntry,
                    "issuest": config.issuest,
                    "effdate": config.effdate,
                    "source_duration": "1",
                    "ql_duration": ql_duration,
                    "attained_age_slot": use_slot_axis,
                    "attained_age_seq": seq,
                    "value": value,
                    "raw_value": val_raw,
                    "lineno": lineno,
                    "original_age": original_age,
                    "age_capped": age_capped,
                }


def load_pr_slot_owner_plans(paagerat_csv, resolver: SR.SegmentResolver) -> frozenset:
    """
    Issue #158 — plans that own a PCOVRSGT SEQ 1 segment which has PAAGERAT PR rows.

    These plans get their premium grid from PAAGERAT directly, so a shared/inherited
    rate candidate must not also write their QuikGps cells. The shared-candidate
    manifest was authored while PR segments were misrouted (every L10 row records
    `current_issuing_plan_keys: 0`), and its non-SEQ-1 entries disagree with the
    corrected attribution.

    Light scan: only COVERAGE_ID and TYPE_CODE are read.
    """
    if not paagerat_csv or not os.path.isfile(paagerat_csv) or resolver is None:
        return frozenset()
    if not pr_slot_ownership_enabled():
        return frozenset()
    plans = set()
    seen_segments = set()
    with open(paagerat_csv, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        hdr = [c.strip() for c in next(rd)]
        try:
            ci = hdr.index("COVERAGE_ID")
            ti = hdr.index("TYPE_CODE")
        except ValueError:
            return frozenset()
        for row in rd:
            if len(row) <= max(ci, ti) or row[ti].strip() != "PR":
                continue
            seg = row[ci].strip()
            if not seg or seg in seen_segments or set(seg) == {"-"}:
                continue
            seen_segments.add(seg)
            for res in resolver.resolve_all(seg, slot=PR_OWNERSHIP_SLOT):
                if res.plan and " " not in res.plan:
                    plans.add(res.plan)
    return frozenset(plans)


def load_paagerat_vargp3_plan_set(paagerat_csv, pcovrsgt_csv, pcovr_csv, crosswalk_xlsx):
    """Return authoritative PLAN codes with resolved PAAGERAT PR attained-age rates."""
    cov2plan, _ = load_plan_crosswalk(crosswalk_xlsx)
    resolver = SR.SegmentResolver.from_files(pcovrsgt_csv, pcovr_csv, cov2plan)
    config = LoaderConfig()
    plans = set()
    for t in transform_paagerat_pr(paagerat_csv, resolver, config):
        if t.get("status") == "IN_SCOPE":
            plans.add(t["plan"])
    return frozenset(plans)


def load_paagerat_vargp3_plan_set_from_config(repo_root, cfg):
    """Resolve VARGP=3 plan set: PR plans + ISWL BP plans when Phase 2 enabled."""
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
    pr_plans = load_paagerat_vargp3_plan_set(pa_path, psgt_path, pcovr_path, xwalk_path)
    if cfg.get("iswl_phase2", {}).get("quikgps_enabled", False):
        from qla_core import paagerat_bp_loader as BP
        bp_plans = BP.load_paagerat_bp_plan_set_from_config(repo_root, cfg)
        pr_plans = pr_plans | bp_plans
    if cfg.get("iswl_phase3", {}).get("quikcoi_enabled", False):
        from qla_core import paagerat_ul_coi_loader as COI
        coi_plans = COI.load_paagerat_coi_plan_set_from_config(repo_root, cfg)
        pr_plans = pr_plans | coi_plans
    if cfg.get("iswl_phase4", {}).get("quikgcoi_enabled", False):
        from qla_core import paagerat_ul_coi_loader as COI
        gcoi_plans = COI.load_paagerat_gcoi_plan_set_from_config(repo_root, cfg)
        pr_plans = pr_plans | gcoi_plans
    return pr_plans


def transform_paagerat_pr(paagerat_csv, resolver: SR.SegmentResolver, config: LoaderConfig,
                          plan_exclude: frozenset | None = None,
                          level_periods: dict | None = None,
                          hiage_by_plan: dict | None = None):
    """Stream PAAGERAT rows filtered to TYPE_CODE='PR', segment-resolved to PLAN.

    Level-period plans are rewritten onto an issue-age by policy-year grid.
    ``QLA_TL10_LEVEL_PERIOD_PR=0`` yields the slot-axis rows unchanged.
    """
    base = transform_paagerat_attained_age(
        paagerat_csv, resolver, config,
        type_code="PR",
        plan_exclude=plan_exclude,
        age_offset=PR_AGE_OFFSET,
        slot_axis=True,
        ownership_slot=PR_OWNERSHIP_SLOT if pr_slot_ownership_enabled() else None,
    )
    if not level_period_enabled():
        return base
    periods = renewal_periods() if level_periods is None else level_periods
    if not periods:
        return base
    return reshape_pr_stream(base, periods, hiage_by_plan)


def transform_paagerat_nf(paagerat_csv, resolver: SR.SegmentResolver, config: LoaderConfig):
    """Stream PAAGERAT rows filtered to TYPE_CODE='NF', segment-resolved to QuikNff."""
    return transform_paagerat_attained_age(
        paagerat_csv, resolver, config,
        type_code="NF",
        target_table="QuikNff",
    )
