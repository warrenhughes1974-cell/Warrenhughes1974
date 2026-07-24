"""
Manifest-driven inherited non-CV rate emit (first-pass NP/RV/DV/DB).

Reads approved_first_pass_scope.csv and streams Rate_Table rows from source
segments under issuing PLAN codes. CV remains owned by cv_inheritance_loader.
PR/QuikGps and PUA non-CV rows are explicitly excluded.
"""
from __future__ import annotations

import csv
import re

from qla_core import rate_dbf_schema as S
from qla_core import rate_factor_loader as L

APPROVED_TYPES = frozenset({"NP", "RV", "DV", "DB"})
PUA_PLANS = frozenset({"261PUA", "265PUA", "280PUA"})
EXCLUDED_TYPES = frozenset({"CV", "PR"})

_SOURCE_SEG_RE = re.compile(
    r"Source Segment=(.+?);\s*Source Rows Found=",
    re.IGNORECASE,
)


def _parse_source_segments(notes):
    """Extract source segment list from manifest Notes field."""
    if not notes:
        return []
    m = _SOURCE_SEG_RE.search(notes)
    if not m:
        return []
    return [s.strip() for s in m.group(1).split(";") if s.strip()]


def _plan_to_coverages(cov2plan):
    plan2cov = {}
    for cov, plan in cov2plan.items():
        plan2cov.setdefault(plan, []).append(cov)
    return plan2cov


def _issuing_has_direct_rows(source_csv, issuing_plan, rate_type, plan2cov):
    """True when issuing coverage already has direct Rate_Table rows for type."""
    covs = plan2cov.get(issuing_plan, [])
    if not covs:
        return False
    cov_set = set(covs)
    with open(source_csv, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        next(rd, None)
        for r in rd:
            if len(r) < 8:
                continue
            if r[0].strip() in cov_set and r[1].strip() == rate_type:
                return True
    return False


def build_inheritance_manifest(manifest_csv, source_csv=None, cov2plan=None, approved_types=None):
    """
    Build approved non-CV inheritance manifest entries from scope CSV.

    Each entry:
      issuing_plan, issuing_coverage, rate_type, target_table,
      source_segments, source_plan, source_plans
    """
    types = frozenset(approved_types or APPROVED_TYPES)
    plan2cov = _plan_to_coverages(cov2plan or {})
    entries = []
    with open(manifest_csv, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("Include In First Pass") or "").strip().upper() != "YES":
                continue
            issuing_plan = (row.get("Issuing Plan") or "").strip()
            rate_type = (row.get("Rate Type") or "").strip()
            if not issuing_plan or not rate_type:
                continue
            if issuing_plan in PUA_PLANS or rate_type in EXCLUDED_TYPES:
                continue
            if rate_type not in types:
                continue
            table = S.TYPE_TO_TABLE.get(rate_type)
            if table is None:
                continue
            source_segments = _parse_source_segments(row.get("Notes", ""))
            if not source_segments:
                continue
            if source_csv and cov2plan and _issuing_has_direct_rows(
                source_csv, issuing_plan, rate_type, plan2cov
            ):
                continue
            source_plans = [
                p.strip() for p in (row.get("Source/Inherited Plan") or "").split(";") if p.strip()
            ]
            issuing_cov = (plan2cov.get(issuing_plan) or [None])[0]
            entries.append({
                "issuing_plan": issuing_plan,
                "issuing_coverage": issuing_cov,
                "rate_type": rate_type,
                "target_table": table,
                "source_segments": source_segments,
                "source_plan": source_plans[0] if source_plans else "",
                "source_plans": source_plans,
            })
    return entries


def _cell_key(plan, table, age2, cntl, col, gender, uwclass, band, config):
    return (
        plan,
        table,
        age2,
        cntl,
        col,
        gender,
        uwclass,
        band,
        config.isscntry,
        config.issuest,
        config.effdate,
    )


def _transform_row(r, lineno, cov, entry, config):
    """Transform one source row for a manifest entry; returns status dict or None."""
    typ = r[1].strip()
    if typ != entry["rate_type"]:
        return None
    table = entry["target_table"]
    issuing_plan = entry["issuing_plan"]
    age = r[2].strip()
    sex = r[3].strip()
    band = r[4].strip()
    uw = r[5].strip()
    dur = r[6].strip()
    val = r[7].strip()

    value = L._to_float(val)
    if value is None:
        return {
            "status": "BAD_VALUE", "type_code": typ, "coverage_id": cov,
            "plan": issuing_plan, "raw_value": val, "lineno": lineno,
            "inheritance_from": cov, "source_plan": entry.get("source_plan", ""),
            "issuing_coverage": entry.get("issuing_coverage"),
        }
    try:
        int(dur)
    except ValueError:
        return {
            "status": "BAD_VALUE", "type_code": typ, "coverage_id": cov,
            "plan": issuing_plan, "raw_duration": dur, "lineno": lineno,
            "inheritance_from": cov, "source_plan": entry.get("source_plan", ""),
            "issuing_coverage": entry.get("issuing_coverage"),
        }

    gender = S.map_sex(sex)
    uwclass = S.map_uwclass(uw)
    band2 = S.map_band(band)
    original_age = age
    emitted_age_int = age.zfill(2)
    age_capped = False
    if age.isdigit() and int(age) > S.MAX_AGE:
        emitted_age_int = str(S.MAX_AGE).zfill(2)
        age_capped = True
    age2 = emitted_age_int

    try:
        # Issue #106: RV identity Dur; other inherited non-CV stay source-1
        ql_dur = S.duration_to_ql_for_type(typ, dur)
    except ValueError:
        return {
            "status": "BAD_VALUE", "type_code": typ, "coverage_id": cov,
            "plan": issuing_plan, "raw_duration": dur, "lineno": lineno,
            "inheritance_from": cov, "source_plan": entry.get("source_plan", ""),
            "issuing_coverage": entry.get("issuing_coverage"),
        }
    if ql_dur < 0:
        return None

    cntl, col = S.duration_to_cntl_col(ql_dur)
    return {
        "status": "IN_SCOPE",
        "coverage_id": entry.get("issuing_coverage") or cov,
        "type_code": typ,
        "table": table,
        "plan": issuing_plan,
        "age": age2,
        "cntl": cntl,
        "col": col,
        "gender": gender,
        "uwclass": uwclass,
        "band": band2,
        "source_band_raw": band,
        "isscntry": config.isscntry,
        "issuest": config.issuest,
        "effdate": config.effdate,
        "source_duration": dur,
        "ql_duration": ql_dur,
        "value": value,
        "raw_value": val,
        "lineno": lineno,
        "original_age": original_age,
        "age_capped": age_capped,
        "source": "INHERITED_RATE",
        "inheritance_from": cov,
        "source_plan": entry.get("source_plan", ""),
        "_cell_key": _cell_key(
            issuing_plan, table, age2, cntl, col, gender, uwclass, band2, config
        ),
    }


def transform_inherited_rates(source_csv, manifest, config):
    """
    Stream inherited non-CV rows: source segment Coverage -> issuing PLAN keys.

    Multi-segment manifest entries merge with manifest segment order first-wins
    so overlapping owner segments do not create duplicate grid cells.
    """
    if not manifest:
        return

    seg_targets = {}
    for ei, entry in enumerate(manifest):
        for si, seg in enumerate(entry["source_segments"]):
            seg_targets.setdefault(seg, []).append((ei, si, entry))

    pending = []
    with open(source_csv, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        next(rd, None)
        lineno = 1
        for r in rd:
            lineno += 1
            if len(r) < 8:
                continue
            cov = r[0].strip()
            if cov not in seg_targets:
                continue
            for ei, si, entry in seg_targets[cov]:
                pending.append((ei, si, lineno, cov, r, entry))

    pending.sort(key=lambda x: (x[0], x[1], x[2]))

    filled = {}
    for ei, _si, lineno, cov, r, entry in pending:
        out = _transform_row(r, lineno, cov, entry, config)
        if out is None:
            continue
        if out["status"] != "IN_SCOPE":
            yield out
            continue
        ck = out.pop("_cell_key")
        if ck in filled.setdefault(ei, set()):
            continue
        filled[ei].add(ck)
        yield out


def merged_source_rows(source_csv, entry, config):
    """
    Return source rows that survive segment-order first-wins merge for an entry.
    Used by validators for parity checks.
    """
    segments = entry["source_segments"]
    rate_type = entry["rate_type"]
    seg_set = set(segments)
    seg_order = {s: i for i, s in enumerate(segments)}
    pending = []
    with open(source_csv, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        next(rd, None)
        lineno = 0
        for r in rd:
            lineno += 1
            if len(r) < 8:
                continue
            cov = r[0].strip()
            if cov not in seg_set or r[1].strip() != rate_type:
                continue
            pending.append((seg_order[cov], lineno, cov, r))

    pending.sort(key=lambda x: (x[0], x[1]))
    filled = set()
    rows = []
    for _so, _ln, cov, r in pending:
        out = _transform_row(r, _ln, cov, entry, config)
        if out is None or out["status"] != "IN_SCOPE":
            continue
        ck = out["_cell_key"]
        if ck in filled:
            continue
        filled.add(ck)
        rows.append((
            cov,
            r[3].strip(),
            int(r[2].strip()) if r[2].strip().isdigit() else r[2].strip(),
            S.map_uwclass(r[5].strip()),
            S.map_band(r[4].strip()),
            int(r[6].strip()),
            out["ql_duration"],
            out["value"],
        ))
    return rows
