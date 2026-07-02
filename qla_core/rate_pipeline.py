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
from qla_core import paagerat_pr_loader as PA
from qla_core import paagerat_bp_loader as BP
from qla_core import paagerat_ul_coi_loader as COI
from qla_core import quikuint_loader as UINT
from qla_core import quikissc_loader as ISSC

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
        self.deps = []
        self.issues = []
        self.summary = collections.Counter()
        self.authoritative_plans = set()
        self.plan2desc = {}
        self.paagerat_vargp3_plans = frozenset()
        self.paagerat_status = collections.Counter()
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
        self.quikuint_rows = []
        self.quikuint_status = collections.Counter()
        self.quikuint_enabled = False
        self.quikissc_rows = []
        self.quikissc_status = collections.Counter()
        self.quikissc_enabled = False

    @property
    def blocker_count(self):
        return sum(1 for i in self.issues if i["severity"] == "BLOCKER")

    @property
    def emit_ready(self):
        return self.blocker_count == 0


def load_assumptions(path, cso_path=None):
    # CSO Mortality Crosswalk is authoritative for CV assumptions (MORT/ETIMORT/
    # NFOINT/INTMETHCV) when delivered; otherwise fall back to the static mapping.
    if cso_path and os.path.exists(cso_path):
        from qla_core.cso_mortality_crosswalk import load_cso_mortality_crosswalk
        return K.CSOAssumptionProvider(load_cso_mortality_crosswalk(cso_path))
    if not path or not os.path.exists(path):
        return K.AssumptionProvider()
    with open(path, encoding="utf-8") as f:
        return K.AssumptionProvider.from_rows(list(csv.DictReader(f)))


def _resolve_path(repo_root, rel_or_abs):
    if not rel_or_abs:
        return ""
    return rel_or_abs if os.path.isabs(rel_or_abs) else os.path.join(repo_root, rel_or_abs)


def run(config_path, repo_root):
    cfg = json.load(open(config_path, encoding="utf-8"))
    src = _resolve_path(repo_root, cfg["source_rate_extract"])
    xlsx = _resolve_path(repo_root, cfg["plan_form_crosswalk"])
    config = L.LoaderConfig.from_dict(cfg.get("segmentation_defaults"))
    cso_cfg = cfg.get("cso_mortality_crosswalk",
                      os.path.join("plan_analysis", "source_data", "rates", "CSO_Mortiality_Crosswalk.csv"))
    assumptions = load_assumptions(
        _resolve_path(repo_root, cfg.get("assumption_mapping_csv", "")),
        _resolve_path(repo_root, cso_cfg),
    )

    res = PipelineResult()
    cov2plan, res.plan2desc = L.load_plan_crosswalk(xlsx)
    res.authoritative_plans = set(cov2plan.values())
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

    def stream():
        for t in L.transform_source(src, cov2plan, config):
            _track(t)
            yield t

        pa_path = _resolve_path(repo_root, cfg.get("paagerat_pr_extract", ""))
        psgt_path = _resolve_path(repo_root, cfg.get("pcovrsgt_csv", ""))
        pcovr_path = _resolve_path(repo_root, cfg.get("pcovr_csv", ""))
        if pa_path and os.path.isfile(pa_path) and os.path.isfile(psgt_path) and os.path.isfile(pcovr_path):
            resolver = SR.SegmentResolver.from_files(psgt_path, pcovr_path, cov2plan)
            for t in PA.transform_paagerat_pr(pa_path, resolver, config, plan_exclude=pr_suppress):
                st = t["status"]
                res.paagerat_status[st] += 1
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

    # member / dimension tables (codes derived from validated segmentation tuples)
    res.member_rows, res.member_placeholders = MB.build_member_rows(res.grids, config.effdate)

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
