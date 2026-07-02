"""
PAAGERAT policy premium (PR) loader — segment-resolved attained-age rates.

Business rules:
  * PAAGERAT.COVERAGE_ID is a segment ID (PCOVRSGT.SEGT_ID), not a policy form.
  * Resolve: PAAGERAT -> PCOVRSGT -> PCOVR -> Policy Form Crosswalk -> PLAN.
  * Only TYPE_CODE = 'PR' rows are in scope for policy gross premium rates.
  * QuikPlan.VARGP = 3 (attained age): SEQ -> QuikGps.AGE, rate in CNTL=00 / GP0.
  * Do NOT unfold into issue-age x duration grids.
  * ISWL MPLANs with PAAGERAT BP authority suppress PR emit (Phase 2 — Issue #31).
"""
import csv
import os

from qla_core import rate_dbf_schema as S
from qla_core import rate_segment_resolution as SR
from qla_core.rate_factor_loader import LoaderConfig, _to_float, load_plan_crosswalk

VARGP_ATTAINED_AGE = "3"

# Phase 2 — ISWL billable premium MPLANs (PAAGERAT BP); PR suppressed on these plans.
ISWL_BP_MPLAN_ALLOWLIST = frozenset({"1658CS", "1659CS", "1669SR", "1679CS"})


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
    plan_allowlist: frozenset | None = None,
    plan_exclude: frozenset | None = None,
):
    """
    Stream PAAGERAT rows for a single TYPE_CODE, segment-resolved to PLAN.

    Yields dicts with status:
      IN_SCOPE | EXCLUDED | SEGMENT_UNRESOLVED | PLAN_INVALID | BAD_VALUE
    """
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

            resolved = resolver.resolve(seg, source="paagerat")
            if not resolved:
                yield {"status": "SEGMENT_UNRESOLVED", "type_code": typ,
                       "coverage_id": seg, "lineno": lineno}
                continue

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
            uwclass = S.map_uwclass(uw)
            if band not in S.BAND_MAP:
                yield {"status": "BAD_VALUE", "type_code": typ, "coverage_id": seg,
                       "plan": plan, "note": f"unsupported BAND {band}", "lineno": lineno}
                continue
            band2 = S.map_band(band)
            if gender is None or uwclass is None or band2 is None:
                yield {"status": "BAD_VALUE", "type_code": typ, "coverage_id": seg,
                       "plan": plan, "note": "segmentation crosswalk", "lineno": lineno}
                continue

            # Attained age (VARGP=3): SEQ -> QuikGps.AGE; cap at QLAdmin C2 width
            original_age = seq
            age_capped = False
            if seq.isdigit():
                age_int = int(seq)
                if age_int > S.MAX_AGE:
                    age_int = S.MAX_AGE
                    age_capped = True
                age2 = str(age_int).zfill(2)
            else:
                yield {"status": "BAD_VALUE", "type_code": typ, "coverage_id": seg,
                       "plan": plan, "raw_age": seq, "lineno": lineno}
                continue

            # VARGP=3 attained-age grid: single factor at CNTL=00 / GP0
            cntl, col_idx = S.duration_to_cntl_col(0)
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
                "table": "QuikGps",
                "plan": plan,
                "age": age2,
                "cntl": cntl,
                "col": col_idx,
                "gender": gender,
                "uwclass": uwclass,
                "band": band2,
                "isscntry": config.isscntry,
                "issuest": config.issuest,
                "effdate": config.effdate,
                "source_duration": "1",
                "ql_duration": 0,
                "attained_age_seq": seq,
                "value": value,
                "raw_value": val_raw,
                "lineno": lineno,
                "original_age": original_age,
                "age_capped": age_capped,
            }


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
                          plan_exclude: frozenset | None = None):
    """Stream PAAGERAT rows filtered to TYPE_CODE='PR', segment-resolved to PLAN."""
    return transform_paagerat_attained_age(
        paagerat_csv, resolver, config,
        type_code="PR",
        plan_exclude=plan_exclude,
    )
