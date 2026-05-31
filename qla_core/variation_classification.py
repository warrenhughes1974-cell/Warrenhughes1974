"""
Variation Classification Engine — structure-based VARGP / VARDB recommendations.

Analyzes LifePRO rate extracts (Rate_Table, PAAGERAT) and infers QuikPlan variation
codes from grid shape. No product-specific hardcoding; PAAGERAT attained-age is detected
as single age axis without duration.

Read-only with respect to source data. Apply to QuikPlan output only when
AUTO_APPLY_VARIATION_CODES is enabled.
"""
from __future__ import annotations

import csv
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from qla_core import plan_source_paths as PSP
from qla_core import rate_segment_resolution as SR
from qla_core.rate_factor_loader import load_plan_crosswalk

STRUCTURE_NONE = "NONE"
STRUCTURE_LEVEL = "LEVEL"
STRUCTURE_POLICY_YEAR = "POLICY_YEAR_ONLY"
STRUCTURE_ISSUE_DUR = "ISSUE_AGE_DURATION"
STRUCTURE_ATTAINED = "ATTAINED_AGE"
STRUCTURE_MIXED = "MIXED"

VARGP_BY_STRUCTURE = {
    STRUCTURE_LEVEL: "0",
    STRUCTURE_POLICY_YEAR: "1",
    STRUCTURE_ISSUE_DUR: "2",
    STRUCTURE_ATTAINED: "3",
    STRUCTURE_NONE: "4",
    STRUCTURE_MIXED: "4",
}

VARDB_BY_STRUCTURE = {
    STRUCTURE_POLICY_YEAR: "1",
    STRUCTURE_ISSUE_DUR: "2",
    STRUCTURE_ATTAINED: "3",
    STRUCTURE_NONE: "4",
    STRUCTURE_LEVEL: "1",
    STRUCTURE_MIXED: "4",
}

AUDIT_FIELDS = (
    "PLAN", "Source_Table", "Product_Type", "Detected_Structure",
    "Recommended_VARGP", "Recommended_VARDB", "Confidence", "Evidence", "Notes",
)

GP_TYPE_CODES = frozenset({"PR"})
DB_TYPE_CODES = frozenset({"DB"})


@dataclass
class VariationClassificationConfig:
    auto_apply_variation_codes: bool = False
    rate_table_extract: str = ""
    paagerat_extract: str = ""
    pcovrsgt_csv: str = ""
    pcovr_csv: str = ""
    plan_form_crosswalk: str = ""

    @classmethod
    def from_dict(cls, d: dict | None) -> VariationClassificationConfig:
        d = d or {}
        return cls(
            auto_apply_variation_codes=bool(d.get("AUTO_APPLY_VARIATION_CODES", False)),
            rate_table_extract=str(d.get("rate_table_extract", "")),
            paagerat_extract=str(d.get("paagerat_extract", "")),
            pcovrsgt_csv=str(d.get("pcovrsgt_csv", "")),
            pcovr_csv=str(d.get("pcovr_csv", "")),
            plan_form_crosswalk=str(d.get("plan_form_crosswalk", "")),
        )

    @classmethod
    def from_env_and_defaults(cls, repo_root: str) -> VariationClassificationConfig:
        env_apply = os.environ.get("QLA_AUTO_APPLY_VARIATION_CODES", "").strip().lower()
        auto = env_apply in ("1", "true", "yes", "y")
        paths = PSP.paagerat_rate_paths()
        paths["rate_table_extract"] = PSP.rate_table_extract()
        cfg_path = os.path.join(repo_root, "QLA_Migration", "Configs", "variation_classification_config.json")
        if os.path.isfile(cfg_path):
            with open(cfg_path, encoding="utf-8") as f:
                file_cfg = json.load(f)
            cfg = cls.from_dict(file_cfg)
            if env_apply:
                cfg.auto_apply_variation_codes = auto
            return cls._resolve_paths(repo_root, cfg)
        cfg = cls.from_dict({"AUTO_APPLY_VARIATION_CODES": auto, **paths})
        return cls._resolve_paths(repo_root, cfg)

    @staticmethod
    def _resolve_paths(repo_root: str, cfg: VariationClassificationConfig) -> VariationClassificationConfig:
        def rp(p):
            if not p:
                return p
            return p if os.path.isabs(p) else os.path.normpath(os.path.join(repo_root, p))

        cfg.rate_table_extract = rp(cfg.rate_table_extract) or PSP.rate_table_extract()
        cfg.paagerat_extract = rp(cfg.paagerat_extract) or PSP.paagerat_extract()
        cfg.pcovrsgt_csv = rp(cfg.pcovrsgt_csv) or PSP.pcovrsgt_csv()
        cfg.pcovr_csv = rp(cfg.pcovr_csv) or PSP.pcovr_csv()
        cfg.plan_form_crosswalk = rp(cfg.plan_form_crosswalk) or PSP.policy_form_crosswalk()
        return cfg


@dataclass
class GridObservation:
    source: str
    structure: str
    row_count: int
    distinct_ages: int
    distinct_durations: int
    distinct_seq: int
    evidence: str


def _is_separator_row(cov: str) -> bool:
    return bool(cov) and set(cov) == {"-"}


def _age_values(raw: str) -> int | None:
    s = (raw or "").strip()
    if not s or not s.isdigit():
        return None
    return int(s)


def classify_grid_shape(
    *,
    row_count: int,
    distinct_ages: set,
    distinct_durations: set,
    distinct_seq: set | None = None,
    source: str,
) -> tuple[str, str]:
    """Return (structure_label, evidence_snippet) from observed dimensions."""
    if row_count == 0:
        return STRUCTURE_NONE, "no rate rows"

    ages = {a for a in distinct_ages if a is not None}
    durs = {d for d in distinct_durations if d is not None}
    seqs = distinct_seq or set()

    if distinct_seq is not None:
        if len(seqs) <= 1 and row_count <= 1:
            return STRUCTURE_LEVEL, f"PAAGERAT single SEQ n={row_count}"
        if len(seqs) >= 2:
            return STRUCTURE_ATTAINED, f"PAAGERAT SEQ axis n={len(seqs)} rows={row_count} no duration"
        return STRUCTURE_ATTAINED, f"PAAGERAT SEQ rows={row_count} no duration"

    # Rate_Table shaped
    age_only_zero = len(ages) <= 1 and (not ages or ages <= {0})
    has_duration = len(durs) >= 2 or (len(durs) == 1 and next(iter(durs), 0) > 0)
    has_issue_ages = len(ages) >= 2 or (len(ages) == 1 and ages - {0})

    if row_count == 1 and age_only_zero and not has_duration:
        return STRUCTURE_LEVEL, f"single cell rows=1"
    if has_duration and age_only_zero:
        return STRUCTURE_POLICY_YEAR, f"AGE=0 duration_values={len(durs)} rows={row_count}"
    if has_issue_ages and has_duration:
        return STRUCTURE_ISSUE_DUR, f"AGE values={len(ages)} DURATION values={len(durs)} rows={row_count}"
    if len(ages) >= 2 and not has_duration:
        return STRUCTURE_ATTAINED, f"AGE axis n={len(ages)} no duration variation"
    if age_only_zero and not has_duration:
        return STRUCTURE_LEVEL, f"constant grid rows={row_count}"
    return STRUCTURE_MIXED, f"ambiguous ages={len(ages)} durs={len(durs)} rows={row_count} source={source}"


def _merge_structures(observations: list[GridObservation]) -> tuple[str, str, str]:
    """Return (merged_structure, confidence, notes)."""
    if not observations:
        return STRUCTURE_NONE, "LOW", "no rate observations"
    structures = {o.structure for o in observations}
    sources = sorted({o.source for o in observations})
    if len(structures) == 1:
        conf = "HIGH" if len(observations) == 1 else "MEDIUM"
        return structures.pop(), conf, ""
    if STRUCTURE_NONE in structures and len(structures) == 2:
        live = structures - {STRUCTURE_NONE}
        return live.pop(), "MEDIUM", "partial rate data"
    return STRUCTURE_MIXED, "LOW", f"mixed structures across sources: {sorted(structures)}"


def _scan_rate_table(path: str, cov2plan: dict, type_codes: frozenset) -> dict[str, list[GridObservation]]:
    """plan -> list of observations for GP or DB family."""
    buckets: dict[str, dict] = defaultdict(lambda: {
        "rows": 0, "ages": set(), "durs": set(), "source": "Rate_Table",
    })
    if not path or not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        hdr = [c.strip() for c in next(rd)]
        idx = {n: i for i, n in enumerate(hdr)}
        ti = idx.get("TYPE_CODE", 1)
        ai = idx.get("AGE", 2)
        di = idx.get("DURATION", idx.get("DURATION ", 6))
        for row in rd:
            if len(row) <= max(ti, ai, di):
                continue
            cov = row[0].strip()
            typ = row[ti].strip()
            if _is_separator_row(cov) or typ not in type_codes:
                continue
            plan = cov2plan.get(cov)
            if not plan or " " in plan:
                continue
            b = buckets[plan]
            b["rows"] += 1
            a = _age_values(row[ai].strip())
            if a is not None:
                b["ages"].add(a)
            d = _age_values(row[di].strip())
            if d is not None:
                b["durs"].add(d)

    out: dict[str, list[GridObservation]] = defaultdict(list)
    for plan, b in buckets.items():
        struct, ev = classify_grid_shape(
            row_count=b["rows"],
            distinct_ages=b["ages"],
            distinct_durations=b["durs"],
            source="Rate_Table",
        )
        out[plan].append(GridObservation(
            source="Rate_Table", structure=struct, row_count=b["rows"],
            distinct_ages=len(b["ages"]), distinct_durations=len(b["durs"]),
            distinct_seq=0, evidence=ev,
        ))
    return out


def _scan_paagerat(
    path: str,
    resolver: SR.SegmentResolver,
    type_codes: frozenset,
) -> dict[str, list[GridObservation]]:
    buckets: dict[str, dict] = defaultdict(lambda: {
        "rows": 0, "seqs": set(), "source": "PAAGERAT",
    })
    if not path or not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        hdr = [c.strip() for c in next(rd)]
        idx = {n: i for i, n in enumerate(hdr)}
        for row in rd:
            seg = row[idx["COVERAGE_ID"]].strip()
            typ = row[idx["TYPE_CODE"]].strip()
            if _is_separator_row(seg) or typ not in type_codes:
                continue
            if "RECORD_SEQ" in idx and row[idx["RECORD_SEQ"]].strip() != "1":
                continue
            resolved = resolver.resolve(seg, source="paagerat")
            if not resolved or " " in resolved.plan:
                continue
            plan = resolved.plan
            b = buckets[plan]
            b["rows"] += 1
            seq = row[idx["SEQ"]].strip()
            if seq.isdigit():
                b["seqs"].add(int(seq))

    out: dict[str, list[GridObservation]] = defaultdict(list)
    for plan, b in buckets.items():
        struct, ev = classify_grid_shape(
            row_count=b["rows"],
            distinct_ages=set(),
            distinct_durations=set(),
            distinct_seq=b["seqs"],
            source="PAAGERAT",
        )
        out[plan].append(GridObservation(
            source="PAAGERAT", structure=struct, row_count=b["rows"],
            distinct_ages=0, distinct_durations=0,
            distinct_seq=len(b["seqs"]), evidence=ev,
        ))
    return out


def classify_all_plans(cfg: VariationClassificationConfig) -> list[dict]:
    """Analyze all plans in crosswalk; return audit rows."""
    if not os.path.isfile(cfg.plan_form_crosswalk):
        return []
    cov2plan, plan2desc = load_plan_crosswalk(cfg.plan_form_crosswalk)
    all_plans = sorted({p for p in cov2plan.values() if p and " " not in p})

    resolver = None
    if os.path.isfile(cfg.pcovrsgt_csv) and os.path.isfile(cfg.pcovr_csv):
        resolver = SR.SegmentResolver.from_files(cfg.pcovrsgt_csv, cfg.pcovr_csv, cov2plan)

    gp_rt = _scan_rate_table(cfg.rate_table_extract, cov2plan, GP_TYPE_CODES)
    gp_pa = _scan_paagerat(cfg.paagerat_extract, resolver, GP_TYPE_CODES) if resolver else {}
    db_rt = _scan_rate_table(cfg.rate_table_extract, cov2plan, DB_TYPE_CODES)
    db_pa = _scan_paagerat(cfg.paagerat_extract, resolver, DB_TYPE_CODES) if resolver else {}

    rows = []
    for plan in all_plans:
        gp_obs = gp_rt.get(plan, []) + gp_pa.get(plan, [])
        db_obs = db_rt.get(plan, []) + db_pa.get(plan, [])

        gp_struct, gp_conf, gp_notes = _merge_structures(gp_obs)
        db_struct, db_conf, db_notes = _merge_structures(db_obs)

        sources = sorted({o.source for o in gp_obs + db_obs})
        source_table = "+".join(sources) if sources else "NONE"

        conf_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        confidence = min(gp_conf, db_conf, key=lambda c: conf_rank.get(c, 0))

        notes = "; ".join(x for x in (gp_notes, db_notes) if x)
        if gp_struct == STRUCTURE_MIXED:
            notes = (notes + "; " if notes else "") + "ambiguous GP structure"
        if db_struct == STRUCTURE_MIXED:
            notes = (notes + "; " if notes else "") + "ambiguous DB structure"
        if not gp_obs:
            notes = (notes + "; " if notes else "") + "no GP/PR rate data"
        if not db_obs:
            notes = (notes + "; " if notes else "") + "no DB rate data"

        evidence_parts = []
        for o in gp_obs:
            evidence_parts.append(f"GP[{o.source}]:{o.structure}({o.evidence})")
        for o in db_obs:
            evidence_parts.append(f"DB[{o.source}]:{o.structure}({o.evidence})")
        evidence = " | ".join(evidence_parts) if evidence_parts else "no matching rate rows"

        detected = f"GP={gp_struct}|DB={db_struct}"
        rows.append({
            "PLAN": plan,
            "Source_Table": source_table,
            "Product_Type": plan2desc.get(plan, ""),
            "Detected_Structure": detected,
            "Recommended_VARGP": VARGP_BY_STRUCTURE.get(gp_struct, "4"),
            "Recommended_VARDB": VARDB_BY_STRUCTURE.get(db_struct, "4"),
            "Confidence": confidence,
            "Evidence": evidence,
            "Notes": notes.strip("; "),
        })
    return rows


def recommendations_by_plan(audit_rows: list[dict]) -> dict[str, dict]:
    return {r["PLAN"]: r for r in audit_rows}


def write_variation_audit_csv(rows: list[dict], path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=AUDIT_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def build_summary_report(rows: list[dict]) -> dict:
    vargp = Counter(r["Recommended_VARGP"] for r in rows)
    vardb = Counter(r["Recommended_VARDB"] for r in rows)
    conf = Counter(r["Confidence"] for r in rows)
    ambiguous = [r["PLAN"] for r in rows if "MIXED" in r["Detected_Structure"]]
    low_conf = [r["PLAN"] for r in rows if r["Confidence"] == "LOW"]
    no_gp = [r["PLAN"] for r in rows if r["Recommended_VARGP"] == "4"]
    no_db = [r["PLAN"] for r in rows if r["Recommended_VARDB"] == "4"]
    return {
        "total_plans_analyzed": len(rows),
        "vargp_counts": {k: vargp.get(k, 0) for k in "01234"},
        "vardb_counts": {k: vardb.get(k, 0) for k in "1234"},
        "confidence_counts": dict(conf),
        "ambiguous_plans": ambiguous,
        "low_confidence_plans": low_conf,
        "missing_gp_data_plans": no_gp,
        "missing_db_data_plans": no_db,
    }


def run_classification(cfg: VariationClassificationConfig, audit_output_path: str) -> tuple[list[dict], dict]:
    rows = classify_all_plans(cfg)
    write_variation_audit_csv(rows, audit_output_path)
    summary = build_summary_report(rows)
    summary_path = audit_output_path.replace(".csv", "_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return rows, summary
