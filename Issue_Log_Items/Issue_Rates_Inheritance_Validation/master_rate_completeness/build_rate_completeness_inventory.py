"""Build a master source-to-QLAdmin rate completeness inventory.

This is an evidence generator, not a converter. It classifies every grouped rate
source we currently have as loaded, inherited, unmapped, or missing plan mapping.
"""
from __future__ import annotations

import collections
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core import paagerat_bp_loader as BP
from qla_core import paagerat_pr_loader as PA
from qla_core import paagerat_ul_coi_loader as COI
from qla_core import rate_dbf_schema as S
from qla_core import rate_factor_loader as L
from qla_core import rate_pipeline
from qla_core import rate_segment_resolution as SR


OUT_DIR = Path(__file__).resolve().parent
CONFIG = ROOT / "plan_analysis" / "phase_r5_rate_loader" / "rate_loader_config.json"
RATE_TABLE = ROOT / "plan_analysis" / "source_data" / "rates" / "Rate_Table_Extract_20260427.csv"
PAAGERAT = ROOT / "plan_analysis" / "source_data" / "rates" / "PAAGERAT_AttainedAge_Rates_Extract_20260428.csv"
PCOVR = ROOT / "plan_analysis" / "source_data" / "coverage" / "PCOVR.csv"
PCOVRSGT = ROOT / "plan_analysis" / "source_data" / "coverage" / "PCOVRSGT.csv"
CROSSWALK = ROOT / "plan_analysis" / "source_data" / "crosswalk" / "Policy Form Crosswalk 5.22.26.xlsx"


TYPE_MEANING = {
    "CV": "Cash values",
    "DB": "Death benefits",
    "DV": "Dividends",
    "NP": "Net valuation premiums",
    "RV": "Reserve factors",
    "PR": "Gross premiums",
    "NF": "Nonforfeiture factors",
    "NN": "Non-deduction reserve factors",
    "PN": "Non-deduction valuation premiums",
    "BP": "Billable premium",
    "U6": "Current COI",
    "U5": "Guaranteed COI",
    "SL": "Surrender charge schedule candidate",
    "TP": "Tax valuation premium",
    "TX": "Tax reserve factor",
    "UF": "Per-policy monthly expense",
}

PAAGERAT_TABLE_BY_TYPE = {
    "PR": "QuikGps",
    "NF": "QuikNff",
    "BP": "QuikGps",
    "U6": "QuikCoi",
    "U5": "QuikGcoi",
}

SEPARATED_TYPES = {"NN", "PN"}
CONFIRMED_LOAD_TYPES = {"CV", "DB", "DV", "NP", "RV", "PR", "NF"}

KNOWN_SCREENSHOT_SOURCE_GAPS = [
    {
        "area": "L01",
        "lifepro_id": "L01 10Y",
        "type_code": "NP",
        "expected_plan": "5L0110",
        "plain_english_reason": (
            "Client screenshot shows L01 10Y NP under L01 10Y LT, but the delivered "
            "Rate_Table extract has no L01 10Y NP rows."
        ),
    },
    {
        "area": "L10",
        "lifepro_id": "L10 LP9595",
        "type_code": "NP/RV",
        "expected_plan": "",
        "plain_english_reason": (
            "LifePRO setup references L10 LP9595 under L10 LP95, but neither delivered "
            "rate extract contains L10 LP9595 rows."
        ),
    },
]


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def _read_source_counts(path: Path) -> dict[tuple[str, str], dict]:
    groups: dict[tuple[str, str], dict] = {}
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as f:
        for row in csv.DictReader(f):
            cov = (row.get("COVERAGE_ID") or "").strip()
            typ = (row.get("TYPE_CODE") or "").strip()
            if not cov or not typ or set(cov) == {"-"}:
                continue
            key = (cov, typ)
            rec = groups.setdefault(
                key,
                {
                    "source_rows": 0,
                    "ages": set(),
                    "durations": set(),
                    "sexes": set(),
                    "bands": set(),
                    "uwclasses": set(),
                },
            )
            rec["source_rows"] += 1
            rec["ages"].add((row.get("AGE   ") or row.get("SEQ   ") or "").strip())
            rec["durations"].add((row.get("DURATION") or "").strip())
            rec["sexes"].add((row.get("SEX") or "").strip())
            rec["bands"].add((row.get("BAND") or "").strip())
            rec["uwclasses"].add((row.get("UNDERWRITING_CLASS") or row.get("UWCLS") or "").strip())
    return groups


def _count_rate_table_direct_status(cov2plan, config, cv_fnz):
    counts = collections.Counter()
    for rec in L.transform_source(str(RATE_TABLE), cov2plan, config, cv_fnz=cv_fnz):
        cov = rec.get("coverage_id", "")
        typ = rec.get("type_code", "")
        status = rec.get("status", "")
        counts[(cov, typ, status)] += 1
    return counts


def _count_paagerat_statuses(resolver, config, cfg):
    counts = collections.Counter()
    loaders = [
        ("PR", PA.transform_paagerat_pr(str(PAAGERAT), resolver, config)),
        ("NF", PA.transform_paagerat_nf(str(PAAGERAT), resolver, config)),
    ]
    if cfg.get("iswl_phase2", {}).get("quikgps_enabled", False):
        loaders.append((
            "BP",
            BP.transform_paagerat_bp(
                str(PAAGERAT),
                resolver,
                config,
                plan_allowlist=BP.iswl_bp_mplan_allowlist(cfg),
            ),
        ))
    if cfg.get("iswl_phase3", {}).get("quikcoi_enabled", False):
        loaders.append((
            "U6",
            COI.transform_paagerat_u6(
                str(PAAGERAT),
                resolver,
                config,
                plan_allowlist=COI.iswl_coi_mplan_allowlist(cfg),
            ),
        ))
    if cfg.get("iswl_phase4", {}).get("quikgcoi_enabled", False):
        loaders.append((
            "U5",
            COI.transform_paagerat_u5(
                str(PAAGERAT),
                resolver,
                config,
                plan_allowlist=COI.iswl_gcoi_mplan_allowlist(cfg),
            ),
        ))

    for loader_type, stream in loaders:
        for rec in stream:
            cov = rec.get("coverage_id", "")
            typ = rec.get("type_code", loader_type)
            status = rec.get("status", "")
            plan = rec.get("plan", "")
            table = rec.get("table", PAAGERAT_TABLE_BY_TYPE.get(typ, ""))
            counts[(cov, typ, status, plan, table)] += 1
    return counts


def _build_inheritance_index(res):
    idx = collections.defaultdict(list)
    for entry in res.cv_inheritance_manifest:
        src = entry.get("rate_owner_coverage", "")
        idx[(src, "CV")].append({
            "mode": "INHERITED_CV",
            "issuing_plan": entry.get("issuing_plan", ""),
            "issuing_coverage": entry.get("issuing_coverage", ""),
        })
    for entry in res.non_cv_inheritance_manifest:
        for src in entry.get("source_segments", []):
            idx[(src, entry.get("rate_type", ""))].append({
                "mode": "INHERITED_NON_CV",
                "issuing_plan": entry.get("issuing_plan", ""),
                "issuing_coverage": entry.get("issuing_coverage", ""),
            })
    return idx


def _csv_join(values) -> str:
    return "; ".join(str(v) for v in values if str(v).strip())


def _rate_table_rows(groups, cov2plan, direct_counts, inheritance_idx, pipeline_tables):
    rows = []
    for (cov, typ), rec in sorted(groups.items()):
        table = S.TYPE_TO_TABLE.get(typ, "")
        plan = cov2plan.get(cov, "")
        direct_in_scope = direct_counts.get((cov, typ, "IN_SCOPE"), 0)
        direct_excluded = direct_counts.get((cov, typ, "EXCLUDED"), 0)
        direct_unresolved = direct_counts.get((cov, typ, "PLAN_UNRESOLVED"), 0)
        direct_bad = direct_counts.get((cov, typ, "BAD_VALUE"), 0)
        inherited = inheritance_idx.get((cov, typ), [])
        inherited_plans = sorted({x["issuing_plan"] for x in inherited})

        if typ in SEPARATED_TYPES:
            status = "Separated - no confirmed QLAdmin load target"
            reason = (
                "Rows exist in LifePRO source, but this rate type is not included in the "
                "actionable load gap count until QLAdmin confirms a target table."
            )
        elif direct_in_scope:
            status = "Loaded directly"
            reason = "Rows map to a confirmed QLAdmin table and policy-form crosswalk plan."
        elif inherited_plans:
            status = "Loaded by inheritance/shared segment"
            reason = "Rows are used as source rates for issuing plans through the approved inherited-rate loaders."
        elif not table:
            status = "Present in source but not yet mapped"
            reason = "This LifePRO rate type does not yet have a confirmed QLAdmin destination in the converter."
        elif not plan:
            status = "Present in source but missing crosswalk"
            reason = "Rows exist, but the LifePRO coverage ID has no policy-form crosswalk plan."
        elif direct_bad:
            status = "Present in source but has bad values"
            reason = "Rows reached the loader but failed value, duration, or segmentation checks."
        elif direct_excluded or direct_unresolved:
            status = "Present in source but not emitted"
            reason = "Rows were excluded or unresolved by the current direct loader."
        else:
            status = "Needs review"
            reason = "No direct or inherited emit evidence found."

        output_keys = len(pipeline_tables.get(table, {})) if table else 0
        rows.append({
            "source_file": _rel(RATE_TABLE),
            "lifepro_id": cov,
            "type_code": typ,
            "meaning": TYPE_MEANING.get(typ, ""),
            "source_rows": rec["source_rows"],
            "distinct_ages": len(rec["ages"] - {""}),
            "distinct_durations": len(rec["durations"] - {""}),
            "distinct_sexes": len(rec["sexes"] - {""}),
            "distinct_bands": len(rec["bands"] - {""}),
            "distinct_uwclasses": len(rec["uwclasses"] - {""}),
            "qladmin_table": table,
            "direct_plan": plan,
            "direct_in_scope_rows": direct_in_scope,
            "direct_bad_rows": direct_bad,
            "pipeline_table_distinct_keys": output_keys,
            "inherited_issuing_plans": _csv_join(inherited_plans),
            "status": status,
            "plain_english_reason": reason,
        })
    return rows


def _paagerat_rows(groups, pa_counts, pipeline_tables):
    rows = []
    for (cov, typ), rec in sorted(groups.items()):
        table = PAAGERAT_TABLE_BY_TYPE.get(typ, "")
        relevant = [(k, v) for k, v in pa_counts.items() if k[0] == cov and k[1] == typ]
        in_scope = sum(v for k, v in relevant if k[2] == "IN_SCOPE")
        bad = sum(v for k, v in relevant if k[2] == "BAD_VALUE")
        loaded_plans = sorted({k[3] for k, v in relevant if k[2] == "IN_SCOPE" and k[3]})

        if in_scope:
            status = "Loaded directly from PAAGERAT segment resolution"
            reason = "Rows resolve through PCOVRSGT/PCOVR/crosswalk and load to the confirmed QLAdmin table."
        elif not table:
            status = "Present in source but not yet mapped"
            reason = "This PAAGERAT rate type does not yet have a confirmed QLAdmin destination or enabled loader."
        elif bad:
            status = "Present in source but has bad values"
            reason = "Rows reached the loader but failed value, age, or segmentation checks."
        else:
            status = "Present in source but not emitted"
            reason = "Rows exist, but current segment resolution or loader gating did not emit them."

        rows.append({
            "source_file": _rel(PAAGERAT),
            "lifepro_id": cov,
            "type_code": typ,
            "meaning": TYPE_MEANING.get(typ, ""),
            "source_rows": rec["source_rows"],
            "distinct_ages": len(rec["ages"] - {""}),
            "distinct_durations": 0,
            "distinct_sexes": len(rec["sexes"] - {""}),
            "distinct_bands": len(rec["bands"] - {""}),
            "distinct_uwclasses": len(rec["uwclasses"] - {""}),
            "qladmin_table": table,
            "direct_plan": _csv_join(loaded_plans),
            "direct_in_scope_rows": in_scope,
            "direct_bad_rows": bad,
            "pipeline_table_distinct_keys": len(pipeline_tables.get(table, {})) if table else 0,
            "inherited_issuing_plans": "",
            "status": status,
            "plain_english_reason": reason,
        })
    return rows


def _write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _write_known_source_gaps(path: Path):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(KNOWN_SCREENSHOT_SOURCE_GAPS[0].keys()))
        w.writeheader()
        w.writerows(KNOWN_SCREENSHOT_SOURCE_GAPS)


def _build_shared_candidate_rows(rt_groups, pa_groups, cov2plan, res):
    active_slots = []
    with PCOVRSGT.open(encoding="utf-8-sig", errors="replace", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("SEGT_FLAG") or "").strip() != "Y":
                continue
            issuing_cov = (row.get("COVERAGE_ID") or "").strip()
            source_segment = (row.get("SEGT_ID   ") or "").strip()
            seq = (row.get("SEQ   ") or "").strip()
            if issuing_cov and source_segment and issuing_cov != source_segment:
                active_slots.append((issuing_cov, seq, source_segment))

    rows = []
    for issuing_cov, seq, source_segment in active_slots:
        issuing_plan = cov2plan.get(issuing_cov, "")
        for typ in sorted(CONFIRMED_LOAD_TYPES):
            if (issuing_cov, typ) in rt_groups:
                continue
            source_rows = rt_groups.get((source_segment, typ), {}).get("source_rows", 0)
            if not source_rows:
                continue
            table = S.TYPE_TO_TABLE.get(typ, "")
            pipeline_keys = sum(1 for key in res.grids.get(table, {}) if key[0] == issuing_plan) if table else 0
            if pipeline_keys:
                status = "Already loaded or covered by current inheritance/direct resolution"
            elif issuing_plan:
                status = "Candidate for inherited/shared loader"
            else:
                status = "Candidate but issuing coverage missing crosswalk"
            rows.append({
                "source_family": "Rate_Table",
                "issuing_coverage": issuing_cov,
                "issuing_plan": issuing_plan,
                "pcovrsgt_seq": seq,
                "source_segment": source_segment,
                "type_code": typ,
                "meaning": TYPE_MEANING.get(typ, ""),
                "qladmin_table": table,
                "source_segment_rows": source_rows,
                "current_issuing_plan_keys": pipeline_keys,
                "status": status,
            })

    for issuing_cov, seq, source_segment in active_slots:
        issuing_plan = cov2plan.get(issuing_cov, "")
        for typ in ("PR", "NF"):
            source_rows = pa_groups.get((source_segment, typ), {}).get("source_rows", 0)
            if not source_rows:
                continue
            table = PAAGERAT_TABLE_BY_TYPE.get(typ, "")
            pipeline_keys = sum(1 for key in res.grids.get(table, {}) if key[0] == issuing_plan) if table else 0
            if pipeline_keys:
                status = "Already loaded through PAAGERAT segment resolution"
            elif issuing_plan:
                status = "Candidate for PAAGERAT shared segment loader"
            else:
                status = "Candidate but issuing coverage missing crosswalk"
            rows.append({
                "source_family": "PAAGERAT",
                "issuing_coverage": issuing_cov,
                "issuing_plan": issuing_plan,
                "pcovrsgt_seq": seq,
                "source_segment": source_segment,
                "type_code": typ,
                "meaning": TYPE_MEANING.get(typ, ""),
                "qladmin_table": table,
                "source_segment_rows": source_rows,
                "current_issuing_plan_keys": pipeline_keys,
                "status": status,
            })

    rows.sort(key=lambda r: (r["status"], r["issuing_plan"], r["type_code"], r["source_segment"]))
    return rows


def _write_summary(path: Path, inventory_rows: list[dict], res):
    by_status = collections.Counter(r["status"] for r in inventory_rows)
    by_type = collections.Counter()
    loaded_rows = 0
    gap_rows = 0
    separated_rows = 0
    for r in inventory_rows:
        source_rows = int(r["source_rows"])
        by_type[(r["type_code"], r["status"])] += source_rows
        if r["status"].startswith("Separated"):
            separated_rows += source_rows
        elif r["status"].startswith("Loaded"):
            loaded_rows += source_rows
        else:
            gap_rows += source_rows

    total_source_rows = loaded_rows + gap_rows + separated_rows
    actionable_total = loaded_rows + gap_rows
    lines = [
        "# Master Rate Completeness Summary",
        "",
        "Generated from delivered source extracts and current in-memory rate pipeline.",
        "",
        "## High-Level Counts",
        "",
        f"- Source grouped rows reviewed: {len(inventory_rows):,}",
        f"- Delivered source rate rows reviewed: {total_source_rows:,}",
        f"- Actionable source rows reviewed, excluding NN/PN: {actionable_total:,}",
        f"- Source rows in loaded actionable groups: {loaded_rows:,}",
        f"- Source rows in actionable gap/review groups: {gap_rows:,}",
        f"- NN/PN source rows separated from actionable load list: {separated_rows:,}",
        f"- Current pipeline blockers: {res.blocker_count}",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(by_status.items()):
        rows_for_status = sum(int(r["source_rows"]) for r in inventory_rows if r["status"] == status)
        lines.append(f"- {status}: {count:,} groups / {rows_for_status:,} source rows")

    lines.extend(["", "## Rate Type Disposition", ""])
    for (typ, status), rows_count in sorted(by_type.items()):
        lines.append(f"- {typ or '(blank)'} / {status}: {rows_count:,} source rows")

    lines.extend([
        "",
        "## Known Screenshot-Only Source Gaps",
        "",
    ])
    for gap in KNOWN_SCREENSHOT_SOURCE_GAPS:
        lines.append(
            f"- {gap['lifepro_id']} {gap['type_code']}: {gap['plain_english_reason']}"
        )

    lines.extend([
        "",
        "## Suggested Next Moves",
        "",
        "1. Resolve the largest mapped-but-not-loaded or unmapped source groups in the inventory CSV.",
        "2. Add inherited/shared segment rules for confirmed QLAdmin destinations beyond the first-pass manifest, starting with PR and NF.",
        "3. Ask CSO for missing extract rows where screenshots show rates but the delivered extracts do not contain them.",
        "4. Keep NN and PN separated from the actionable load list until their QLAdmin destination is confirmed.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    import json

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cov2plan, _ = L.load_plan_crosswalk(str(CROSSWALK))
    config = L.LoaderConfig.from_dict(cfg.get("segmentation_defaults"))

    print("Running rate pipeline...")
    res = rate_pipeline.run(str(CONFIG), str(ROOT))
    print("Loading direct source status...")
    cv_fnz = L.load_cv_slice_fnz(str(RATE_TABLE))
    direct_counts = _count_rate_table_direct_status(cov2plan, config, cv_fnz)

    print("Loading PAAGERAT status...")
    resolver = SR.SegmentResolver.from_files(str(PCOVRSGT), str(PCOVR), cov2plan)
    pa_counts = _count_paagerat_statuses(resolver, config, cfg)

    print("Building inventory rows...")
    inheritance_idx = _build_inheritance_index(res)
    rt_groups = _read_source_counts(RATE_TABLE)
    pa_groups = _read_source_counts(PAAGERAT)
    rows = []
    rows.extend(_rate_table_rows(rt_groups, cov2plan, direct_counts, inheritance_idx, res.grids))
    rows.extend(_paagerat_rows(pa_groups, pa_counts, res.grids))

    inventory = OUT_DIR / "master_rate_completeness_inventory.csv"
    summary = OUT_DIR / "master_rate_completeness_summary.md"
    source_gaps = OUT_DIR / "known_screenshot_source_gaps.csv"
    type_summary = OUT_DIR / "rate_type_status_summary.csv"
    shared_candidates = OUT_DIR / "inherited_shared_rate_candidates.csv"

    _write_csv(inventory, rows)
    _write_known_source_gaps(source_gaps)
    _write_csv(shared_candidates, _build_shared_candidate_rows(rt_groups, pa_groups, cov2plan, res))

    type_rows = []
    rollup = collections.Counter()
    for r in rows:
        rollup[(r["source_file"], r["type_code"], r["meaning"], r["qladmin_table"], r["status"])] += int(r["source_rows"])
    for (source_file, typ, meaning, table, status), source_rows in sorted(rollup.items()):
        type_rows.append({
            "source_file": source_file,
            "type_code": typ,
            "meaning": meaning,
            "qladmin_table": table,
            "status": status,
            "source_rows": source_rows,
        })
    _write_csv(type_summary, type_rows)
    _write_summary(summary, rows, res)

    print(f"Wrote {inventory}")
    print(f"Wrote {type_summary}")
    print(f"Wrote {source_gaps}")
    print(f"Wrote {shared_candidates}")
    print(f"Wrote {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
