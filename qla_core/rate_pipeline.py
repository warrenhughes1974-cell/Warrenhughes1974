"""
Shared QLAdmin V5 rate pipeline orchestration.

Single code path used by both the dry run and the guarded emit so transformation,
AGE capping, key generation, and validation are identical regardless of whether DBFs
are written. READ-ONLY with respect to all inputs; produces in-memory structures + a
validation verdict. Emission is the caller's responsibility and is gated separately.
"""
import os
import json
import csv
import collections

from qla_core import rate_dbf_schema as S
from qla_core import rate_factor_loader as L
from qla_core import rate_key_setup as K
from qla_core import rate_member_setup as MB
from qla_core import rate_validation as V
from qla_core import rate_segment_resolution as SR
from qla_core import cv_inheritance_loader as CIL
from qla_core import rate_inheritance_loader as RIL
from qla_core import shared_rate_candidate_loader as SCL
from qla_core import paagerat_pr_loader as PA
from qla_core import paagerat_bp_loader as BP
from qla_core import paagerat_ul_coi_loader as COI
from qla_core import paagerat_db_loader as DB
from qla_core import quikuint_loader as UINT
from qla_core import quikissc_loader as ISSC
from qla_core import pdage_missfill as PDM

KEY_FIELDS = ("PLAN", "GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE")


class PipelineResult:
    def __init__(self):
        self.row_status = collections.Counter()
        self.excluded = collections.defaultdict(lambda: [0, set()])
        self.age_cap = collections.Counter()   # (PLAN,TYPE,ORIG_AGE,EMIT_AGE) -> rows
        self.grids = {}
        self.collisions = []
        self.cap_collisions = []
        self.factor_rows = {}
        self.fmt_issues = []
        self.key_rows = {}
        self.member_rows = {}
        self.member_placeholders = collections.Counter()
        self.default_key_stubs = []  # Issue #77: (plan, key_table) stubs added
        self.gender_companion_keys = []  # Issue #83: (plan, key_table, gender) companions added
        self.deps = []
        self.issues = []
        self.summary = collections.Counter()
        self.authoritative_plans = set()
        self.plan2desc = {}
        self.paagerat_vargp3_plans = frozenset()
        self.paagerat_status = collections.Counter()
        self.paagerat_nf_status = collections.Counter()
        self.paagerat_bp_status = collections.Counter()
        self.paagerat_bp_plans = frozenset()
        self.paagerat_bp_enabled = False
        self.paagerat_bp_mplan_allowlist = []
        self.paagerat_coi_status = collections.Counter()
        self.paagerat_coi_plans = frozenset()
        self.paagerat_coi_enabled = False
        self.paagerat_coi_mplan_allowlist = []
        self.paagerat_gcoi_status = collections.Counter()
        self.paagerat_gcoi_plans = frozenset()
        self.paagerat_gcoi_enabled = False
        self.paagerat_gcoi_mplan_allowlist = []
        self.paagerat_db_status = collections.Counter()
        self.paagerat_db_plans = frozenset()
        self.paagerat_db_enabled = False
        self.paagerat_db_mplan_allowlist = []
        self.quikuint_rows = []
        self.quikuint_status = collections.Counter()
        self.quikuint_enabled = False
        self.quikissc_rows = []
        self.quikissc_status = collections.Counter()
        self.quikissc_enabled = False
        self.cv_inheritance_manifest = []
        self.cv_inheritance_status = collections.Counter()
        self.non_cv_inheritance_manifest = []
        self.non_cv_inheritance_status = collections.Counter()
        self.shared_rate_manifest = []
        self.shared_rate_status = collections.Counter()
        self.pdage_missfill_status = collections.Counter()
        self.pdage_missfill_enabled = False
        self.pdage_merge_summary = {}

    @property
    def blocker_count(self):
        return sum(1 for i in self.issues if i["severity"] == "BLOCKER")

    @property
    def emit_ready(self):
        return self.blocker_count == 0


def load_assumptions(path, cso_path=None, valuation_setup_path=None):
    # CSO Mortality Crosswalk is fallback for CV assumptions when a plan is not on
    # Valuation_Setup (Issue #80). Valuation_Setup wins for its 51 non-PUA plans.
    fallback = K.AssumptionProvider()
    if cso_path and os.path.exists(cso_path):
        from qla_core.cso_mortality_crosswalk import load_cso_mortality_crosswalk
        fallback = K.CSOAssumptionProvider(load_cso_mortality_crosswalk(cso_path))
    elif path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            fallback = K.AssumptionProvider.from_rows(list(csv.DictReader(f)))

    if valuation_setup_path and os.path.exists(valuation_setup_path):
        from qla_core.cso_valuation_setup import (
            CompositeAssumptionProvider,
            ValuationSetupAssumptionProvider,
            load_valuation_setup,
        )
        vs = load_valuation_setup(valuation_setup_path)
        if vs.plans_loaded:
            return CompositeAssumptionProvider(
                ValuationSetupAssumptionProvider(vs), fallback=fallback,
            )
    return fallback


def _resolve_path(repo_root, rel_or_abs):
    if not rel_or_abs:
        return ""
    return rel_or_abs if os.path.isabs(rel_or_abs) else os.path.join(repo_root, rel_or_abs)


def run(config_path, repo_root):
    cfg = json.load(open(config_path, encoding="utf-8"))
    base_rt = _resolve_path(repo_root, cfg["source_rate_extract"])
    pdage_cfg = cfg.get("issue42_pdage_missfill") or {}
    pdage_path = _resolve_path(repo_root, pdage_cfg.get("pdage_extract", ""))
    xlsx = _resolve_path(repo_root, cfg["plan_form_crosswalk"])
    config = L.LoaderConfig.from_dict(cfg.get("segmentation_defaults"))
    cov2plan_pre, _ = L.load_plan_crosswalk(xlsx)
    psgt_path_pre = _resolve_path(repo_root, cfg.get("pcovrsgt_csv", ""))
    pcovr_path_pre = _resolve_path(repo_root, cfg.get("pcovr_csv", ""))
    merge_resolver = None
    if os.path.isfile(psgt_path_pre) and os.path.isfile(pcovr_path_pre):
        merge_resolver = SR.SegmentResolver.from_files(psgt_path_pre, pcovr_path_pre, cov2plan_pre)
    src = base_rt
    pdage_merge_summary = {}
    if pdage_cfg.get("enabled", False) and pdage_path and os.path.isfile(pdage_path) and os.path.isfile(base_rt):
        staging_rel = pdage_cfg.get(
            "staging_merged_csv",
            os.path.join("QLA_Migration", "Staging", "rate_table_pdage_missfill_merged.csv"),
        )
        staging_path = _resolve_path(repo_root, staging_rel)
        pdage_merge_summary = PDM.merge_pdage_missfill_to_staging(
            base_rt,
            pdage_path,
            staging_path,
            approved_types=pdage_cfg.get("approved_types"),
            segment_resolver=merge_resolver,
        )
        src = pdage_merge_summary["staging_path"]
    cso_cfg = cfg.get("cso_mortality_crosswalk",
                      os.path.join("plan_analysis", "source_data", "rates", "CSO_Mortiality_Crosswalk.csv"))
    vs_cfg = cfg.get(
        "cso_valuation_setup",
        os.path.join("plan_analysis", "source_data", "rates", "CSO_Valuation_Setup.csv"),
    )
    assumptions = load_assumptions(
        _resolve_path(repo_root, cfg.get("assumption_mapping_csv", "")),
        _resolve_path(repo_root, cso_cfg),
        _resolve_path(repo_root, vs_cfg),
    )

    res = PipelineResult()
    cov2plan, res.plan2desc = L.load_plan_crosswalk(xlsx)
    res.authoritative_plans = set(cov2plan.values())
    cv_fnz = L.load_cv_slice_fnz(src)
    rt_key_index = PDM.rate_table_key_index(base_rt)
    res.paagerat_vargp3_plans = PA.load_paagerat_vargp3_plan_set_from_config(repo_root, cfg)
    res.paagerat_bp_plans = BP.load_paagerat_bp_plan_set_from_config(repo_root, cfg)
    res.paagerat_bp_enabled = bool(cfg.get("iswl_phase2", {}).get("quikgps_enabled", False))
    if res.paagerat_bp_enabled:
        res.paagerat_bp_mplan_allowlist = sorted(BP.iswl_bp_mplan_allowlist(cfg))
    res.paagerat_coi_plans = COI.load_paagerat_coi_plan_set_from_config(repo_root, cfg)
    res.paagerat_coi_enabled = bool(cfg.get("iswl_phase3", {}).get("quikcoi_enabled", False))
    if res.paagerat_coi_enabled:
        res.paagerat_coi_mplan_allowlist = sorted(COI.iswl_coi_mplan_allowlist(cfg))
    res.paagerat_gcoi_plans = COI.load_paagerat_gcoi_plan_set_from_config(repo_root, cfg)
    res.paagerat_gcoi_enabled = bool(cfg.get("iswl_phase4", {}).get("quikgcoi_enabled", False))
    if res.paagerat_gcoi_enabled:
        res.paagerat_gcoi_mplan_allowlist = sorted(COI.iswl_gcoi_mplan_allowlist(cfg))
    res.paagerat_db_plans = DB.load_paagerat_db_plan_set_from_config(repo_root, cfg)
    res.paagerat_db_enabled = bool(cfg.get("wave2_db", {}).get("quikdbs_enabled", False))
    if res.paagerat_db_enabled:
        res.paagerat_db_mplan_allowlist = sorted(DB.wave2_db_mplan_allowlist(cfg))
    res.quikuint_enabled = bool(cfg.get("iswl_phase5", {}).get("quikuint_enabled", False))
    res.quikissc_enabled = bool(cfg.get("iswl_phase6", {}).get("quikissc_enabled", False))
    pr_suppress = PA._iswl_bp_suppress_plans(cfg)

    def _track(t):
        res.row_status[t["status"]] += 1
        if t["status"] == "EXCLUDED":
            res.excluded[t["type_code"]][0] += 1
            res.excluded[t["type_code"]][1].add(t["coverage_id"])
        elif t["status"] == "IN_SCOPE" and t.get("age_capped"):
            res.age_cap[(t["plan"], t["type_code"], t["original_age"], t["age"])] += 1

    psgt_path = _resolve_path(repo_root, cfg.get("pcovrsgt_csv", ""))
    pcovr_path = _resolve_path(repo_root, cfg.get("pcovr_csv", ""))
    segment_resolver = None
    if os.path.isfile(psgt_path) and os.path.isfile(pcovr_path):
        segment_resolver = SR.SegmentResolver.from_files(psgt_path, pcovr_path, cov2plan)

    pdage_approved_types = pdage_cfg.get("approved_types")
    res.pdage_missfill_enabled = bool(pdage_cfg.get("enabled", False))
    res.pdage_merge_summary = pdage_merge_summary

    inh_cfg = cfg.get("issue40_cv_inheritance") or {}
    if inh_cfg.get("enabled", True):
        audit_csv = _resolve_path(
            repo_root,
            inh_cfg.get(
                "fleet_audit_csv",
                os.path.join("Issue_Log_Items", "Issue_40", "Issue_40_Fleet_CV_Inheritance_Audit.csv"),
            ),
        )
        if os.path.isfile(audit_csv) and os.path.isfile(psgt_path):
            res.cv_inheritance_manifest = CIL.build_inheritance_manifest(audit_csv, psgt_path, src)

    ncv_cfg = cfg.get("non_cv_rate_inheritance") or {}
    if ncv_cfg.get("enabled", False):
        manifest_csv = _resolve_path(
            repo_root,
            ncv_cfg.get(
                "manifest_csv",
                os.path.join(
                    "Issue_Log_Items",
                    "Issue_Rates_Inheritance_Validation",
                    "non_cv_inheritance_analysis",
                    "approved_first_pass_scope.csv",
                ),
            ),
        )
        if os.path.isfile(manifest_csv):
            approved_types = ncv_cfg.get("approved_types") or list(RIL.APPROVED_TYPES)
            res.non_cv_inheritance_manifest = RIL.build_inheritance_manifest(
                manifest_csv, source_csv=src, cov2plan=cov2plan, approved_types=approved_types
            )

    shared_cfg = cfg.get("shared_rate_candidates") or {}
    if shared_cfg.get("enabled", False):
        candidate_csv = _resolve_path(
            repo_root,
            shared_cfg.get(
                "candidate_csv",
                os.path.join(
                    "Issue_Log_Items",
                    "Issue_Rates_Inheritance_Validation",
                    "master_rate_completeness",
                    "inherited_shared_rate_candidates.csv",
                ),
            ),
        )
        if os.path.isfile(candidate_csv):
            res.shared_rate_manifest = SCL.build_shared_manifest(candidate_csv)

    def stream():
        for t in L.transform_source(
            src, cov2plan, config, cv_fnz=cv_fnz,
            segment_resolver=segment_resolver, rt_key_index=rt_key_index,
        ):
            _track(t)
            yield t

        for t in CIL.transform_inherited_cv(src, res.cv_inheritance_manifest, config, cv_fnz=cv_fnz):
            st = t["status"]
            res.cv_inheritance_status[st] += 1
            _track(t)
            yield t

        for t in RIL.transform_inherited_rates(src, res.non_cv_inheritance_manifest, config):
            st = t["status"]
            res.non_cv_inheritance_status[st] += 1
            _track(t)
            yield t

        for t in SCL.transform_rate_table_shared(src, res.shared_rate_manifest, config):
            st = t["status"]
            res.shared_rate_status[st] += 1
            _track(t)
            yield t

        pa_path = _resolve_path(repo_root, cfg.get("paagerat_pr_extract", ""))
        if pa_path and os.path.isfile(pa_path) and segment_resolver is not None:
            resolver = segment_resolver
            for t in PA.transform_paagerat_pr(pa_path, resolver, config, plan_exclude=pr_suppress):
                st = t["status"]
                res.paagerat_status[st] += 1
                _track(t)
                yield t
            for t in PA.transform_paagerat_nf(pa_path, resolver, config):
                st = t["status"]
                res.paagerat_nf_status[st] += 1
                _track(t)
                yield t
            if cfg.get("iswl_phase2", {}).get("quikgps_enabled", False):
                bp_allow = BP.iswl_bp_mplan_allowlist(cfg)
                for t in BP.transform_paagerat_bp(pa_path, resolver, config, plan_allowlist=bp_allow):
                    st = t["status"]
                    res.paagerat_bp_status[st] += 1
                    _track(t)
                    yield t
            if cfg.get("iswl_phase3", {}).get("quikcoi_enabled", False):
                coi_allow = COI.iswl_coi_mplan_allowlist(cfg)
                for t in COI.transform_paagerat_u6(pa_path, resolver, config, plan_allowlist=coi_allow):
                    st = t["status"]
                    res.paagerat_coi_status[st] += 1
                    _track(t)
                    yield t
            if cfg.get("iswl_phase4", {}).get("quikgcoi_enabled", False):
                gcoi_allow = COI.iswl_gcoi_mplan_allowlist(cfg)
                for t in COI.transform_paagerat_u5(pa_path, resolver, config, plan_allowlist=gcoi_allow):
                    st = t["status"]
                    res.paagerat_gcoi_status[st] += 1
                    _track(t)
                    yield t
            if cfg.get("wave2_db", {}).get("quikdbs_enabled", False):
                db_allow = DB.wave2_db_mplan_allowlist(cfg)
                for t in DB.transform_paagerat_db(pa_path, resolver, config, plan_allowlist=db_allow):
                    st = t["status"]
                    res.paagerat_db_status[st] += 1
                    _track(t)
                    yield t
            for t in SCL.transform_paagerat_shared(pa_path, res.shared_rate_manifest, config):
                st = t["status"]
                res.shared_rate_status[st] += 1
                _track(t)
                yield t

    res.grids, res.collisions, res.cap_collisions = L.build_factor_grid(stream(), config)

    for table, grid in res.grids.items():
        rows, fi = L.grid_to_factor_rows(table, grid, config)
        res.factor_rows[table] = rows
        res.fmt_issues.extend(fi)

    for table, grid in res.grids.items():
        if table not in S.KEY_TABLE:
            continue
        kt, rows, dep = K.build_key_rows(table, grid, assumptions)
        res.key_rows.setdefault(kt, [])
        existing = {tuple(r[f] for f in KEY_FIELDS) for r in res.key_rows[kt]}
        for r in rows:
            sig = tuple(r[f] for f in KEY_FIELDS)
            if sig not in existing:
                res.key_rows[kt].append(r); existing.add(sig)
        res.deps.extend(dep)

    # Issue #77: default key stub for each GP/DB/CV/TV/DV family missing rates
    rated_plans = K.rated_plans_from_grids(res.grids)
    res.default_key_stubs = K.ensure_default_key_stubs(
        res.key_rows, rated_plans, assumptions=assumptions, effdate=config.effdate,
    )

    # member / dimension tables (codes derived from validated segmentation tuples)
    res.member_rows, res.member_placeholders = MB.build_member_rows(res.grids, config.effdate)
    # Issue #83: F/M companion keys when plan declares both genders (Values=N if no factors)
    res.gender_companion_keys = K.ensure_gender_companion_keys(
        res.key_rows, res.member_rows, assumptions=assumptions,
    )
    # Issue #77: member codes for stub keys (e.g. GENDER=0 / UW=00)
    MB.ensure_members_for_keys(res.member_rows, res.key_rows, effdate=config.effdate)

    res.issues, res.summary = V.validate(res.grids, res.factor_rows, res.fmt_issues,
                                         res.key_rows, res.deps, res.authoritative_plans, config)
    # member-table EFFDATE gate (QuikPlNb must carry the standard generation)
    for row in res.member_rows.get("QuikPlNb", []):
        if row["EFFDATE"] != S.STANDARD_EFFDATE:
            res.issues.append({"id": "V07", "severity": "BLOCKER", "table": "QuikPlNb",
                               "detail": f"QuikPlNb EFFDATE '{row['EFFDATE']}' != {S.STANDARD_EFFDATE}"})
    # collisions are BLOCKER duplicate-cell conditions
    for (table, key, col, prior, line) in res.collisions:
        res.issues.append({"id": "V03", "severity": "BLOCKER", "table": table,
                           "detail": f"duplicate source cell key={key} col={col} lines {prior},{line}"})
    # audited AGE caps (WARNING, never blocking)
    res.issues.extend(V.age_cap_warnings(res.age_cap))
    # cap-induced collisions resolved in favor of genuine data (WARNING, audited)
    cc = collections.Counter()
    for (table, key, col, plan, type_code, dropped, kept) in res.cap_collisions:
        cc[(plan, type_code)] += 1
    for (plan, type_code), n in sorted(cc.items()):
        res.issues.append({
            "id": "AGE_CAP_COLLISION_RESOLVED", "severity": "WARNING",
            "table": V.TYPE_FAMILY.get(type_code, type_code),
            "detail": (f"PLAN {plan} {type_code}: {n} capped cell(s) collided with genuine "
                       f"AGE 99 data; genuine value retained, capped value dropped (audited)"),
            "plan": plan, "type_code": type_code, "row_count": n,
        })
    if res.quikuint_enabled:
        res.quikuint_rows, res.quikuint_status = UINT.load_quikuint_from_config(repo_root, cfg)
        if res.quikuint_status.get("BLOCKER_NO_PDINTTBL"):
            res.issues.append({"id": "V-UINT-PDINT", "severity": "BLOCKER", "table": "QuikUint",
                               "detail": "PDINTTBL extract missing or not configured"})
    if res.quikissc_enabled:
        res.quikissc_rows, res.quikissc_status = ISSC.load_quikissc_from_config(repo_root, cfg)
        if res.quikissc_status.get("BLOCKER_NO_RATE_TABLE"):
            res.issues.append({"id": "V-ISSC-RATE", "severity": "BLOCKER", "table": "QuikIssc",
                               "detail": "Rate_Table extract missing or not configured"})
        if res.quikissc_status.get("BLOCKER_INCOMPLETE_SL"):
            res.issues.append({"id": "V-ISSC-SL", "severity": "BLOCKER", "table": "QuikIssc",
                               "detail": "Rate_Table SL hub schedule incomplete (<14 durations)"})
    return res


def build_summary(res, phase, source, extra=None):
    tables = set(S.TYPE_TO_TABLE.values()) | set(res.factor_rows.keys())
    by_family = {S.FAMILY[t]: {"factor_rows": len(res.factor_rows.get(t, [])),
                               "distinct_keys": len(res.grids.get(t, {})),
                               "distinct_plans": len({k[0] for k in res.grids.get(t, {})})}
                 for t in tables if t in S.FAMILY}
    sev = collections.Counter(i["severity"] for i in res.issues)
    by_id = collections.Counter(i["id"] for i in res.issues)
    age_cap_rows = sum(res.age_cap.values())
    summary = {
        "phase": phase,
        "source": source,
        "row_status": dict(res.row_status),
        "excluded_type_codes": {k: {"rows": v[0], "distinct_coverage_ids": len(v[1])}
                                for k, v in sorted(res.excluded.items())},
        "factor_rows_by_family": by_family,
        "key_tables": {kt: len(rows) for kt, rows in res.key_rows.items()},
        "member_tables": {mt: len(rows) for mt, rows in res.member_rows.items()},
        "member_placeholders_deferred": dict(res.member_placeholders),
        "age_capping": {"groups": len(res.age_cap), "rows_capped": age_cap_rows,
                        "cap_induced_collisions_resolved": len(res.cap_collisions),
                        "rule": ("AGE>99 -> 99 (QLAdmin AGE is C2); audited, non-blocking. "
                                 "Capped cells colliding with genuine AGE 99 data yield to the "
                                 "genuine value (retained), capped value dropped + audited.")},
        "validation": {"total_issues": len(res.issues), "by_severity": dict(sev),
                       "by_id": dict(by_id), "blocker_count": res.blocker_count},
        "format_observations": {
            "does_not_fit": sum(1 for x in res.fmt_issues if x["issue"] == "DOES_NOT_FIT"),
            "precision_reduced": sum(1 for x in res.fmt_issues if x["issue"] == "PRECISION_REDUCED"),
        },
        "assumption_dependencies_deferred": len(res.deps),
        "emit_ready": res.emit_ready,
        "paagerat_pr": {
            "vargp3_plan_count": len(res.paagerat_vargp3_plans),
            "row_status": dict(res.paagerat_status),
            "grid_mode": "VARGP=3 attained-age (SEQ->AGE, CNTL=00/GP0)",
        },
        "paagerat_nf": {
            "row_status": dict(res.paagerat_nf_status),
            "grid_mode": "VARGP=3 attained-age (SEQ->AGE, CNTL=00/NFF0)",
        },
        "paagerat_bp": {
            "enabled": res.paagerat_bp_enabled,
            "bp_plan_count": len(res.paagerat_bp_plans),
            "row_status": dict(res.paagerat_bp_status),
            "mplan_allowlist": res.paagerat_bp_mplan_allowlist,
        },
        "paagerat_coi": {
            "enabled": res.paagerat_coi_enabled,
            "coi_plan_count": len(res.paagerat_coi_plans),
            "row_status": dict(res.paagerat_coi_status),
            "mplan_allowlist": res.paagerat_coi_mplan_allowlist,
        },
        "paagerat_gcoi": {
            "enabled": res.paagerat_gcoi_enabled,
            "gcoi_plan_count": len(res.paagerat_gcoi_plans),
            "row_status": dict(res.paagerat_gcoi_status),
            "mplan_allowlist": res.paagerat_gcoi_mplan_allowlist,
        },
        "paagerat_db": {
            "enabled": res.paagerat_db_enabled,
            "db_plan_count": len(res.paagerat_db_plans),
            "row_status": dict(res.paagerat_db_status),
            "mplan_allowlist": res.paagerat_db_mplan_allowlist,
            "grid_mode": "VARDB=3 attained-age (SEQ->AGE, CNTL=00/DB0)",
        },
        "quikuint": {
            "enabled": res.quikuint_enabled,
            "row_count": len(res.quikuint_rows),
            "status": dict(res.quikuint_status),
            "distinct_mplans": len({r["MPLAN"] for r in res.quikuint_rows}),
        },
        "quikissc": {
            "enabled": res.quikissc_enabled,
            "row_count": len(res.quikissc_rows),
            "status": dict(res.quikissc_status),
            "distinct_plans": len({r["PLAN"] for r in res.quikissc_rows}),
        },
        "issue40_cv_inheritance": {
            "manifest_entries": len(res.cv_inheritance_manifest),
            "row_status": dict(res.cv_inheritance_status),
            "issuing_plans": sorted({e["issuing_plan"] for e in res.cv_inheritance_manifest}),
        },
        "non_cv_rate_inheritance": {
            "manifest_entries": len(res.non_cv_inheritance_manifest),
            "row_status": dict(res.non_cv_inheritance_status),
            "issuing_plans": sorted({e["issuing_plan"] for e in res.non_cv_inheritance_manifest}),
            "rate_types": sorted({e["rate_type"] for e in res.non_cv_inheritance_manifest}),
        },
        "shared_rate_candidates": {
            "manifest_entries": len(res.shared_rate_manifest),
            "row_status": dict(res.shared_rate_status),
            "issuing_plans": sorted({e["issuing_plan"] for e in res.shared_rate_manifest}),
            "rate_types": sorted({e["rate_type"] for e in res.shared_rate_manifest}),
        },
        "issue42_pdage_missfill": {
            "enabled": res.pdage_missfill_enabled,
            "merge": res.pdage_merge_summary,
            "row_status": dict(res.pdage_missfill_status),
        },
    }
    if extra:
        summary.update(extra)
    return summary


def write_issue_reports(res, out_dir):
    with open(os.path.join(out_dir, "dryrun_validation_issues.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["VALIDATION_ID", "SEVERITY", "TABLE", "DETAIL"])
        for i in res.issues:
            w.writerow([i["id"], i["severity"], i["table"], i["detail"]])
    with open(os.path.join(out_dir, "age_cap_audit.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["PLAN", "TYPE_CODE", "ORIGINAL_AGE", "EMITTED_AGE", "ROW_COUNT"])
        for (plan, type_code, orig, emit), count in sorted(res.age_cap.items()):
            w.writerow([plan, type_code, orig, emit, count])
    with open(os.path.join(out_dir, "age_cap_collision_audit.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["TABLE", "PLAN", "TYPE_CODE", "KEY", "COLUMN", "DROPPED_CAPPED_VALUE", "RETAINED_GENUINE_VALUE"])
        for (table, key, col, plan, type_code, dropped, kept) in res.cap_collisions:
            w.writerow([table, plan, type_code, "|".join(key), col, dropped, kept])
