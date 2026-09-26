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
from qla_core import paagerat_cv_loader as PUACV
from qla_core import paagerat_np_loader as PANP
from qla_core import quikuint_loader as UINT
from qla_core import quikissc_loader as ISSC
from qla_core import pdage_missfill as PDM
from qla_core import plan_source_paths as PSP
from qla_core import quiktvs_tv0_fill as TV0
from qla_core import quiknps_level_np as NPS
from qla_core import attained_age_grid_fill as AASF
from qla_core import quiktvs_l17_rv as L17RV
from qla_core import psubsseg_substitution_loader as PSUB

KEY_FIELDS = ("PLAN", "GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE")


def _equal_uw_collapse_generations(grid):
    """Return generations whose complete UW factor grids are exactly equal."""
    groups = collections.defaultdict(lambda: collections.defaultdict(dict))
    for key, cells in grid.items():
        plan, age, cntl, gender, uwclass, band, isscntry, issuest, effdate = key
        generation = (plan, effdate)
        base = (age, cntl, gender, band, isscntry, issuest)
        groups[generation][uwclass][base] = cells

    targets = set()
    for (plan, effdate), by_uw in groups.items():
        signatures = {
            uw: tuple(sorted(
                (base, tuple(sorted(
                    (col, str(cell[0]).strip()) for col, cell in cells.items()
                )))
                for base, cells in uw_grid.items()
            ))
            for uw, uw_grid in by_uw.items()
        }
        if (
            len(by_uw) > 1
            and len(set(signatures.values())) == 1
        ):
            targets.add((plan, effdate))
    return targets


def _collapse_equal_uw_grids(grid):
    """Collapse equal UW-class grids to UWCLASS=00, preserving other dimensions."""
    targets = _equal_uw_collapse_generations(grid)
    collapsed = {}
    for key, cells in grid.items():
        plan, age, cntl, gender, uwclass, band, isscntry, issuest, effdate = key
        out_uw = "00" if (plan, effdate) in targets else uwclass
        key = (plan, age, cntl, gender, out_uw, band, isscntry, issuest, effdate)
        if key not in collapsed:
            collapsed[key] = cells
    return collapsed, targets


def _rewrite_collapsed_family_keys(key_rows, collapse_targets, grids=None):
    """Materialize CV/TV collapse after default and companion key enrichment."""
    table_by_family = {"QuikCvs": "QuikPlCv", "QuikTvs": "QuikPlTv"}
    grids = grids or {}
    for factor_table, targets in collapse_targets.items():
        key_table = table_by_family[factor_table]
        protected = set()
        for other_table, other_grid in grids.items():
            if other_table == factor_table or S.KEY_TABLE.get(other_table) != key_table:
                continue
            for key in other_grid:
                plan, age, cntl, gender, uwclass, band, isscntry, issuest, effdate = key
                if (plan, effdate) in targets:
                    protected.add((plan, gender, uwclass, band, isscntry, issuest, effdate))
        rows = key_rows.get(key_table, [])
        rewritten = []
        seen = set()
        for row in rows:
            row = dict(row)
            signature = tuple(row.get(field, "") for field in KEY_FIELDS)
            if (
                (row.get("PLAN", ""), row.get("EFFDATE", "")) in targets
                and signature not in protected
            ):
                row["UWCLASS"] = "00"
            signature = tuple(row.get(field, "") for field in KEY_FIELDS)
            if signature not in seen:
                rewritten.append(row)
                seen.add(signature)
        key_rows[key_table] = rewritten


def collapse_equal_uw_families(grids, return_targets=False):
    """Apply independent CV/TV UW collapse for each effective-date generation."""
    targets = {}
    for table in ("QuikCvs", "QuikTvs"):
        if table in grids:
            grids[table], targets[table] = _collapse_equal_uw_grids(grids[table])
    return (grids, targets) if return_targets else grids


class PipelineResult:
    def __init__(self):
        self.row_status = collections.Counter()
        self.excluded = collections.defaultdict(lambda: [0, set()])
        self.age_cap = collections.Counter()   # (PLAN,TYPE,ORIG_AGE,EMIT_AGE) -> rows
        # Issue #140: plans emitted on the attained-age slot axis, carried from the
        # loaders because row shape cannot tell an attained-age key from issue age 0.
        self.attained_age_slot_plans = collections.defaultdict(set)
        self.attained_age_slot_fill = []
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
        self.paagerat_pua_cv_status = collections.Counter()
        self.paagerat_pua_cv_plans = frozenset()
        self.paagerat_pua_cv_enabled = False
        self.paagerat_pua_cv_mplan_allowlist = []
        self.paagerat_np_status = collections.Counter()
        self.paagerat_np_plans = frozenset()
        self.paagerat_np_enabled = False
        self.paagerat_np_mplan_allowlist = []
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
        self.shared_pr_dropped_plans = []
        self.shared_rate_status = collections.Counter()
        # PSUBSSEG coverage-ID substitution (era-banded EFFDATE generations)
        self.psubsseg_enabled = False
        self.psubsseg_manifest = []
        self.psubsseg_scope_issues = []
        self.psubsseg_status = collections.Counter()
        self.psubsseg_plan_copy = {}
        self.pdage_missfill_status = collections.Counter()
        self.pdage_missfill_enabled = False
        self.pdage_merge_summary = {}
        self.quiktvs_tv0_fill = {}
        self.quikdvs_dv0_fill = {}
        self.quiknps_level_np = {}
        self.l17_rv_expansion = {}

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
    # Config often pins Source/Rate_Table_Extract_Txt.txt; when that file is
    # absent (common on a fresh 07/31 cut), use the canonical resolver fallback
    # (Source txt → plan_analysis Rate_Table twin) instead of hard-failing.
    if not base_rt or not os.path.isfile(base_rt):
        resolved_rt = PSP.rate_table_extract()
        if resolved_rt and os.path.isfile(resolved_rt):
            print(
                f"RATE: source_rate_extract missing ({base_rt or cfg.get('source_rate_extract')}); "
                f"using resolver fallback: {resolved_rt}",
                flush=True,
            )
            base_rt = resolved_rt
            cfg["source_rate_extract"] = resolved_rt
    pdage_cfg = cfg.get("issue42_pdage_missfill") or {}

    # Multi-source dated extracts: PAAGE / PAAGERAT / PDAGE — filename YYYYMMDD newest wins
    def _plog(msg):
        print(msg, flush=True)

    paage_path = PSP.paage_extract(log=_plog)
    paagerat_merged = PSP.paagerat_extract(log=_plog)
    pdage_merged = PSP.pdage_extract(log=_plog)
    dated_merge_summaries = PSP.last_merge_summaries()

    # Point config loaders at merged extracts (filename newest wins)
    if paagerat_merged and os.path.isfile(paagerat_merged):
        cfg["paagerat_pr_extract"] = paagerat_merged
    if pdage_merged and os.path.isfile(pdage_merged):
        cfg["pdage_extract"] = pdage_merged
        pdage_cfg = dict(pdage_cfg)
        pdage_cfg["pdage_extract"] = pdage_merged
        cfg["issue42_pdage_missfill"] = pdage_cfg
    if paage_path and os.path.isfile(paage_path):
        cfg["paage_extract"] = paage_path

    # Prefer merged PDAGE over a single hardcoded config path
    pdage_path = pdage_merged or _resolve_path(repo_root, pdage_cfg.get("pdage_extract", ""))
    if not pdage_path:
        pdage_path = _resolve_path(repo_root, cfg.get("pdage_extract", ""))

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
    pdage_merge_summary["dated_extract_merge"] = dated_merge_summaries
    pdage_merge_summary["paage_extract"] = paage_path
    pdage_merge_summary["paagerat_dated_merged"] = paagerat_merged
    pdage_merge_summary["pdage_dated_merged"] = pdage_merged
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
    # Rate identity fix (2026-08-13): CV first-duration truth from PDAGE native
    # pages replaces the cv_lifepro_first_duration() guess. Slices absent from
    # PDAGE fall back to the legacy guess (flagged cv_first_fallback on rows).
    cv_native_first = {}
    if pdage_path and os.path.isfile(pdage_path):
        cv_native_first = L.load_cv_native_first(pdage_path)
    print(f"RATE: CV native-first map from PDAGE: {len(cv_native_first)} slices "
          f"({os.path.basename(pdage_path) if pdage_path else 'no PDAGE — legacy guess'})", flush=True)
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
    res.paagerat_pua_cv_plans = PUACV.load_paagerat_cv_plan_set_from_config(repo_root, cfg)
    res.paagerat_pua_cv_enabled = bool(cfg.get("pua_cv", {}).get("quikcvs_pua_enabled", False))
    if res.paagerat_pua_cv_enabled:
        res.paagerat_pua_cv_mplan_allowlist = sorted(PUACV.pua_cv_mplan_allowlist(cfg))
    # Issue #169: PAAGERAT attained-age NP expanded onto the QuikNps issue-age grid.
    res.paagerat_np_enabled = PANP.np_enabled(cfg)
    if res.paagerat_np_enabled:
        res.paagerat_np_plans = PANP.load_paagerat_np_plan_set_from_config(repo_root, cfg)
        res.paagerat_np_mplan_allowlist = sorted(PANP.np_mplan_allowlist(cfg))
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
        if t["status"] == "IN_SCOPE" and t.get("attained_age_slot"):
            res.attained_age_slot_plans[t["table"]].add(t["plan"])

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
            # Issue #158: plans that own a SEQ 1 premium segment take their QuikGps grid
            # from the PR loader, so their shared PR candidates are dropped here.
            _pa_for_owners = paagerat_merged or _resolve_path(
                repo_root, cfg.get("paagerat_pr_extract", "")
            )
            pr_owner_plans = PA.load_pr_slot_owner_plans(_pa_for_owners, segment_resolver)
            res.shared_rate_manifest = SCL.build_shared_manifest(
                candidate_csv, pr_owner_plans=pr_owner_plans
            )
            res.shared_pr_dropped_plans = list(SCL.SHARED_PR_DROPPED_PLANS)

    # PSUBSSEG coverage-ID substitution: reviewed scope manifest -> additive
    # era-banded EFFDATE generations (CV/RV/NP). See psubsseg_substitution_loader.
    psub_cfg = cfg.get("psubsseg_substitution") or {}
    res.psubsseg_enabled = bool(psub_cfg.get("enabled", False))
    if res.psubsseg_enabled:
        scope_csv = _resolve_path(
            repo_root,
            psub_cfg.get(
                "scope_csv",
                os.path.join(
                    "Issue_Log_Items",
                    "PSUBSSEG_Rate_Substitution",
                    "psubsseg_substitution_scope.csv",
                ),
            ),
        )
        res.psubsseg_manifest, res.psubsseg_scope_issues = PSUB.load_scope_manifest(
            scope_csv, cov2plan
        )

    def stream():
        for t in L.transform_source(
            src, cov2plan, config, cv_fnz=cv_fnz,
            segment_resolver=segment_resolver, rt_key_index=rt_key_index,
            cv_native_first=cv_native_first,
        ):
            _track(t)
            yield t

        for t in CIL.transform_inherited_cv(src, res.cv_inheritance_manifest, config,
                                            cv_fnz=cv_fnz, cv_native_first=cv_native_first):
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

        if res.psubsseg_manifest:
            for t in PSUB.transform_psubsseg_pdage(pdage_path, res.psubsseg_manifest, config):
                res.psubsseg_status[t["status"]] += 1
                _track(t)
                yield t

        pa_path = paagerat_merged or _resolve_path(repo_root, cfg.get("paagerat_pr_extract", ""))
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
            if cfg.get("pua_cv", {}).get("quikcvs_pua_enabled", False):
                pua_allow = PUACV.pua_cv_mplan_allowlist(cfg)
                for t in PUACV.transform_paagerat_pua_cv(pa_path, resolver, config,
                                                         plan_allowlist=pua_allow):
                    st = t["status"]
                    res.paagerat_pua_cv_status[st] += 1
                    _track(t)
                    yield t
            if PANP.np_enabled(cfg):
                for t in PANP.transform_paagerat_np(
                    pa_path, resolver, config,
                    plan_allowlist=PANP.np_mplan_allowlist(cfg),
                    coverage_effdate=PANP.coverage_effdate_map(cfg),
                    age_max=PANP.issue_age_max(cfg),
                ):
                    res.paagerat_np_status[t["status"]] += 1
                    _track(t)
                    yield t
            for t in SCL.transform_paagerat_shared(pa_path, res.shared_rate_manifest, config):
                st = t["status"]
                res.shared_rate_status[st] += 1
                _track(t)
                yield t

    res.grids, res.collisions, res.cap_collisions = L.build_factor_grid(stream(), config)
    quiktvs_grid = res.grids.setdefault("QuikTvs", {})
    res.l17_rv_expansion = L17RV.apply_l17_rv_quiktvs_grid(
        quiktvs_grid,
        repo_root,
        pdage_path,
        config,
    )
    # PSUBSSEG PLAN_COPY entries (sandwich re-emits): clone the copy plan's
    # standard-generation cells to the banded EFFDATE. After L17 RV expansion,
    # before UW collapse so new generations collapse independently.
    if res.psubsseg_manifest:
        res.psubsseg_plan_copy = PSUB.apply_psubsseg_plan_copies(
            res.grids, res.psubsseg_manifest
        )
    # A11: collapse only independently equal CV or TV factor grids. GP/DB/DV
    # and non-UW dimensions remain untouched.
    res.grids, collapse_targets = collapse_equal_uw_families(res.grids, return_targets=True)

    res.quiknps_level_np = NPS.apply_quiknps_level_np_grid(res.grids.get("QuikNps"))

    # Issue #140: attained-age grids must run from CNTL=00 (Help p556).
    res.attained_age_slot_fill = AASF.apply_attained_age_slot_fill(
        res.grids, res.attained_age_slot_plans,
    )

    for table, grid in res.grids.items():
        rows, fi = L.grid_to_factor_rows(table, grid, config)
        res.factor_rows[table] = rows
        res.fmt_issues.extend(fi)

    sp_plans = TV0.load_true_single_premium_plans(repo_root, config=cfg)
    res.quiktvs_tv0_fill = TV0.apply_quiktvs_tv0_blank_fill(
        res.factor_rows, sp_plans, source_decimals=config.source_decimals,
    )
    res.quikdvs_dv0_fill = TV0.apply_quikdvs_dv0_blank_fill(
        res.factor_rows, source_decimals=config.source_decimals,
    )

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
    # A3: extend existing TESTRD-style defaults to the authoritative QuikPlan
    # universe without creating factor values.
    all_plans = rated_plans | {p for p in res.authoritative_plans if p and " " not in p}
    res.default_key_stubs = K.ensure_default_key_stubs(
        res.key_rows, all_plans, assumptions=assumptions, effdate=config.effdate,
    )

    # member / dimension tables (codes derived from validated segmentation tuples)
    res.member_rows, res.member_placeholders = MB.build_member_rows(res.grids, config.effdate)
    # Issue #83: F/M companion keys when plan declares both genders (Values=N if no factors)
    res.gender_companion_keys = K.ensure_gender_companion_keys(
        res.key_rows, res.member_rows, assumptions=assumptions,
    )
    res.gender_companion_keys.extend(
        K.ensure_issue96_sal_gender_companion_keys(res.key_rows, assumptions=assumptions)
    )
    # A11: key materialization must follow all stub/companion enrichment.
    _rewrite_collapsed_family_keys(res.key_rows, collapse_targets, grids=res.grids)
    # Issue #77: member codes for stub keys (e.g. GENDER=0 / UW=00)
    MB.ensure_members_for_keys(res.member_rows, res.key_rows, effdate=config.effdate)

    # PSUBSSEG scope entries legitimize their (PLAN, EFFDATE) era generations for V07
    psubsseg_generations = {
        (e["issuing_plan"], e["effdate"])
        for e in res.psubsseg_manifest
        if e["effdate"] != S.STANDARD_EFFDATE
    }
    res.issues, res.summary = V.validate(res.grids, res.factor_rows, res.fmt_issues,
                                         res.key_rows, res.deps, res.authoritative_plans, config,
                                         allowed_effdate_generations=psubsseg_generations)
    for blocker in res.quiknps_level_np.get("blockers") or []:
        res.issues.append(blocker)
    for blocker in res.l17_rv_expansion.get("blockers") or []:
        res.issues.append(blocker)
    # PSUBSSEG fail-closed gates: manifest drift and empty copy sources block emit
    for issue in res.psubsseg_scope_issues:
        res.issues.append(issue)
    for blocker in (res.psubsseg_plan_copy or {}).get("blockers") or []:
        res.issues.append(blocker)
    if res.psubsseg_enabled and res.psubsseg_status.get("SOURCE_SEGMENT_ABSENT"):
        res.issues.append({
            "id": "PSUBSSEG_SOURCE_ABSENT", "severity": "BLOCKER", "table": "rates",
            "detail": (
                f"{res.psubsseg_status['SOURCE_SEGMENT_ABSENT']} scoped substitution "
                f"source segment(s) missing from merged PDAGE extract"
            ),
        })
    if res.psubsseg_enabled and res.psubsseg_manifest:
        res.issues.append({
            "id": "PSUBSSEG_SUBSTITUTION_EMIT", "severity": "INFO", "table": "rates",
            "detail": (
                f"PSUBSSEG substitution: {len(res.psubsseg_manifest)} scope entries, "
                f"row status {dict(res.psubsseg_status)}, "
                f"plan_copy keys={res.psubsseg_plan_copy.get('keys_copied', 0)} "
                f"cells={res.psubsseg_plan_copy.get('cells_copied', 0)}"
            ),
        })
    if res.l17_rv_expansion.get("applied"):
        prov = res.l17_rv_expansion.get("provenance") or {}
        detail_parts = [
            f"L17 RV page expansion: parent keys={res.l17_rv_expansion.get('keys_injected_parent', 0)}, "
            f"child keys={res.l17_rv_expansion.get('keys_injected_children', 0)}, "
            f"cells={res.l17_rv_expansion.get('cells_injected', 0)}",
            f"source={prov.get('path', '')}",
        ]
        if prov.get("fallback"):
            detail_parts.append(prov.get("warning", "fallback PDAGE used for L17 RV"))
        res.issues.append({
            "id": "L17_RV_PDAGE_EXPAND",
            "severity": "WARNING" if prov.get("fallback") else "INFO",
            "table": "QuikTvs",
            "detail": "; ".join(detail_parts),
        })
    if res.quiknps_level_np.get("rows_flattened") or res.quiknps_level_np.get("rows_already_level"):
        res.issues.append({
            "id": "QUIKNPS_LEVEL_NP",
            "severity": "WARNING",
            "table": "QuikNps",
            "detail": (
                f"Level every year to source DURATION={NPS.SOURCE_DURATION_ISSUE_YEAR} "
                f"(CNTL 00 NP0): {res.quiknps_level_np.get('rows_flattened', 0)} row(s) flattened, "
                f"{res.quiknps_level_np.get('rows_already_level', 0)} already level, "
                f"{res.quiknps_level_np.get('cells_set', 0)} cell(s) set"
            ),
        })
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
    if res.quiktvs_tv0_fill.get("filled") or res.quiktvs_tv0_fill.get("preserved_sp_blank"):
        res.issues.append({
            "id": "QUIKTVS_TV0_BLANK_FILL",
            "severity": "WARNING",
            "table": "QuikTvs",
            "detail": (
                f"TV0 blank fill: {res.quiktvs_tv0_fill.get('filled', 0)} non-SP cell(s) "
                f"set to {TV0.quiktvs_tv0_zero_text(config.source_decimals)!r}; "
                f"{res.quiktvs_tv0_fill.get('preserved_sp_blank', 0)} SP blank(s) preserved "
                f"on plan(s) {', '.join(res.quiktvs_tv0_fill.get('sp_blank_plans') or []) or 'none'}"
            ),
        })
    if res.quikdvs_dv0_fill.get("filled"):
        res.issues.append({
            "id": "QUIKDVS_DV0_BLANK_FILL",
            "severity": "WARNING",
            "table": "QuikDvs",
            "detail": (
                f"DV0 blank fill (DV native identity 2026-08-13): "
                f"{res.quikdvs_dv0_fill.get('filled', 0)} cell(s) set to numeric zero"
            ),
        })
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
    # Issue #140: written here rather than at emit so every runner (rate_emit, the R5
    # loader, the batch finale) leaves quikplan the same attained-age plan set. The
    # membership is a property of the loaders, so it holds for either storage layout.
    AASF.write_manifest(repo_root, res.attained_age_slot_plans)
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
            "grid_mode": "VARGP=3 attained-age (Issue 140 slot axis: AGE=00, slot=SEQ-1)",
        },
        "paagerat_nf": {
            "row_status": dict(res.paagerat_nf_status),
            "grid_mode": "attained-age SEQ->AGE, CNTL=00/NFF0 (no VARNF code; Issue 140 deferred)",
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
            "grid_mode": "VARDB=3 attained-age (Issue 140 slot axis: AGE=00, slot=SEQ)",
        },
        "paagerat_pua_cv": {
            "enabled": res.paagerat_pua_cv_enabled,
            "cv_plan_count": len(res.paagerat_pua_cv_plans),
            "row_status": dict(res.paagerat_pua_cv_status),
            "mplan_allowlist": res.paagerat_pua_cv_mplan_allowlist,
            "grid_mode": "PUA attained-age CV (Issue 140 slot axis: AGE=00, slot=SEQ)",
        },
        "paagerat_np": {
            "enabled": res.paagerat_np_enabled,
            "np_plan_count": len(res.paagerat_np_plans),
            "row_status": dict(res.paagerat_np_status),
            "mplan_allowlist": res.paagerat_np_mplan_allowlist,
            "grid_mode": (
                "Issue #169 attained-age NP expanded to issue-age x duration "
                "(QuikNps[age][idx] = vector[age + idx + 1]); QuikNps has no VARY field"
            ),
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
            # Issue #158: plans that now take QuikGps from their own SEQ 1 segment
            "pr_dropped_plans": sorted(res.shared_pr_dropped_plans),
        },
        "issue42_pdage_missfill": {
            "enabled": res.pdage_missfill_enabled,
            "merge": res.pdage_merge_summary,
            "row_status": dict(res.pdage_missfill_status),
        },
        "psubsseg_substitution": {
            "enabled": res.psubsseg_enabled,
            "scope_entries": len(res.psubsseg_manifest),
            "scope_issues": len(res.psubsseg_scope_issues),
            "row_status": dict(res.psubsseg_status),
            "plan_copy": {k: v for k, v in (res.psubsseg_plan_copy or {}).items()
                          if k != "blockers"},
            "issuing_plans": sorted({e["issuing_plan"] for e in res.psubsseg_manifest}),
        },
        "quiknps_level_np": res.quiknps_level_np,
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
