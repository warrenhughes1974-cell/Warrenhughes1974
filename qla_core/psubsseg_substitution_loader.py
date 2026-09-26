"""
PSUBSSEG coverage-ID substitution rate emit (era-banded EFFDATE generations).

LifePRO redirects a policy's rate segments (CV/RV/NP) by issue-date band via
PSUBS/PSUBSSEG. QLAdmin expresses the same banding natively through the rate-key
EFFDATE dimension (latest EFFDATE <= policy issue date wins), so each scoped band
becomes an additional key generation under the existing plan — strictly additive;
the standard 19000101 generation is never modified here.

Scope manifest (reviewed, committed):
  Issue_Log_Items/PSUBSSEG_Rate_Substitution/psubsseg_substitution_scope.csv
Built by tools/build_psubsseg_scope.py from PSUBSSEG + PCOVRSGT + PPBEN with the
reconciliation value spot-check; every entry names issuing coverage/plan, rate
type, EFFDATE, source segment, and mode.

Modes:
  EXTRACT           stream the merged PDAGE extract, full VALUE1..VALUE10 page
                    expansion (annual Dur = (page-1)*10 + k, the L17 RV fix
                    convention). RV/DV identity durations, NP source-1 (#106),
                    CV native-year identity capped at maturity (2026-08-13 rate
                    identity fix: native labels self-cancel the fnz remap).
  PLAN_COPY:<plan>  post-grid copy of <plan>'s standard-generation grid cells to
                    the entry's EFFDATE (sandwich re-emits proven value-identical
                    by the reconciliation overlap == 1.0).
"""
from __future__ import annotations

import csv
import os
from collections import Counter, defaultdict

from qla_core import rate_dbf_schema as S
from qla_core import rate_factor_loader as L

SOURCE_LABEL = "PSUBSSEG_SUBSTITUTION"
SUPPORTED_TYPES = frozenset({"CV", "RV", "NP", "DV", "DB"})


def load_scope_manifest(scope_csv, cov2plan):
    """Load + validate the reviewed scope CSV.

    Returns (entries, issues). Any malformed/mismatched row becomes a BLOCKER
    issue dict (fail closed — a drifted manifest must not silently half-emit).
    """
    entries = []
    issues = []
    if not scope_csv or not os.path.isfile(scope_csv):
        issues.append({
            "id": "PSUBSSEG_SCOPE_MISSING", "severity": "BLOCKER",
            "table": "rates",
            "detail": f"psubsseg substitution scope csv not found: {scope_csv}",
        })
        return entries, issues
    with open(scope_csv, newline="", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            cov = (row.get("ISSUING_COVERAGE") or "").strip()
            plan = (row.get("ISSUING_PLAN") or "").strip()
            typ = (row.get("RATE_TYPE") or "").strip()
            effdate = (row.get("EFFDATE") or "").strip()
            seg = (row.get("SOURCE_SEGMENT") or "").strip()
            mode = (row.get("SOURCE_MODE") or "EXTRACT").strip()

            problems = []
            if not cov or not plan or not seg:
                problems.append("blank coverage/plan/segment")
            if typ not in SUPPORTED_TYPES or typ not in S.TYPE_TO_TABLE:
                problems.append(f"unsupported RATE_TYPE {typ!r}")
            if not (len(effdate) == 8 and effdate.isdigit()):
                problems.append(f"bad EFFDATE {effdate!r}")
            if cov2plan.get(cov, plan) != plan:
                problems.append(
                    f"plan mismatch: crosswalk says {cov2plan.get(cov)!r}"
                )
            copy_plan = ""
            if mode.startswith("PLAN_COPY:"):
                copy_plan = mode.split(":", 1)[1].strip()
                if not copy_plan:
                    problems.append("PLAN_COPY without plan")
            elif mode != "EXTRACT":
                problems.append(f"unknown SOURCE_MODE {mode!r}")

            if problems:
                issues.append({
                    "id": "PSUBSSEG_SCOPE_INVALID", "severity": "BLOCKER",
                    "table": S.TYPE_TO_TABLE.get(typ, "rates"),
                    "detail": f"scope line {i} ({cov}/{typ}): " + "; ".join(problems),
                })
                continue
            entries.append({
                "issuing_coverage": cov,
                "issuing_plan": plan,
                "rate_type": typ,
                "target_table": S.TYPE_TO_TABLE[typ],
                "effdate": effdate,
                "source_segment": seg,
                "mode": "PLAN_COPY" if copy_plan else "EXTRACT",
                "copy_plan": copy_plan,
            })
    return entries, issues


def _row_value(row, index):
    val = (row.get(f"VALUE{index}") or "").strip()
    if val:
        return val
    return (row.get(f"VALUE{index}_FLOAT") or "").strip()


def transform_psubsseg_pdage(pdage_path, manifest, config):
    """Stream IN_SCOPE cells for EXTRACT entries from the merged PDAGE extract.

    Single pass; full page expansion. Yields transform dicts compatible with
    rate_factor_loader.build_factor_grid (effdate carries the entry's band).
    """
    targets = defaultdict(list)  # (segment, type) -> [entry, ...]
    for e in manifest:
        if e["mode"] == "EXTRACT":
            targets[(e["source_segment"], e["rate_type"])].append(e)
    if not targets:
        return
    if not pdage_path or not os.path.isfile(pdage_path):
        yield {"status": "PDAGE_MISSING", "type_code": "", "coverage_id": "",
               "lineno": 0, "source": SOURCE_LABEL}
        return

    seen_sources = set()
    filled = defaultdict(set)  # id(entry) -> cell keys
    with open(pdage_path, encoding="utf-8-sig", errors="replace", newline="") as f:
        lineno = 1
        for raw in csv.DictReader(f):
            lineno += 1
            row = {(k or "").strip(): (v or "").strip() for k, v in raw.items()}
            key = (row.get("COVERAGE_ID", ""), row.get("TYPE_CODE", ""))
            if key not in targets:
                continue
            seen_sources.add(key)
            age = row.get("AGE", "")
            sex = row.get("SEX", "")
            band = row.get("BAND", "")
            uw = row.get("UWCLS", "")
            try:
                page = int(row.get("DURATION", ""))
            except ValueError:
                continue
            if page < 1:
                continue
            gender = S.map_sex(sex)
            band2 = S.map_band(band)
            if gender is None or band2 is None:
                for entry in targets[key]:
                    yield {"status": "BAD_VALUE", "type_code": key[1],
                           "coverage_id": entry["issuing_coverage"],
                           "plan": entry["issuing_plan"], "raw_sex": sex,
                           "raw_band": band, "lineno": lineno,
                           "note": "unmapped classification", "source": SOURCE_LABEL}
                continue

            original_age = age
            emitted_age = age.zfill(2)
            age_capped = False
            age_int = int(age) if age.isdigit() else None
            if age_int is not None and age_int > S.MAX_AGE:
                emitted_age = str(S.MAX_AGE).zfill(2)
                age_capped = True

            for vi in range(1, S.N_DURATION_COLS + 1):
                raw_val = _row_value(row, vi)
                if not raw_val or raw_val in (".", "-", "-."):
                    continue
                value = L._to_float(raw_val)
                if value is None:
                    continue
                annual = (page - 1) * S.N_DURATION_COLS + vi
                typ = key[1]
                if typ == "CV":
                    # PDAGE-native CV labels ARE policy years: identity with
                    # maturity truncation (native_first == fnz self-cancel).
                    if age_int is None:
                        continue
                    if annual > L.cv_lifepro_last_duration(age_int):
                        continue
                    ql_dur = annual
                else:
                    try:
                        ql_dur = S.duration_to_ql_for_type(typ, annual)
                    except ValueError:
                        continue
                if ql_dur < 0 or (typ in ("RV", "DV") and ql_dur < 1):
                    continue
                cntl, col = S.duration_to_cntl_col(ql_dur)
                for entry in targets[key]:
                    uwclass = S.map_uwclass(
                        uw, plan=entry["issuing_plan"],
                        coverage_id=entry["source_segment"],
                    )
                    if uwclass is None:
                        continue
                    cell = (entry["target_table"], entry["issuing_plan"],
                            emitted_age, cntl, col, gender, uwclass, band2,
                            entry["effdate"])
                    bucket = filled[id(entry)]
                    if cell in bucket:
                        continue
                    bucket.add(cell)
                    yield {
                        "status": "IN_SCOPE",
                        "coverage_id": entry["issuing_coverage"],
                        "type_code": typ,
                        "table": entry["target_table"],
                        "plan": entry["issuing_plan"],
                        "age": emitted_age,
                        "cntl": cntl,
                        "col": col,
                        "gender": gender,
                        "uwclass": uwclass,
                        "band": band2,
                        "source_band_raw": band,
                        "isscntry": config.isscntry,
                        "issuest": config.issuest,
                        "effdate": entry["effdate"],
                        "source_duration": str(annual),
                        "ql_duration": ql_dur,
                        "value": value,
                        "raw_value": raw_val,
                        "lineno": lineno,
                        "original_age": original_age,
                        "age_capped": age_capped,
                        "source": SOURCE_LABEL,
                        "substitution_from": entry["source_segment"],
                        "pdage_page": page,
                        "pdage_value_index": vi,
                    }

    for key in sorted(set(targets) - seen_sources):
        for entry in targets[key]:
            yield {"status": "SOURCE_SEGMENT_ABSENT", "type_code": key[1],
                   "coverage_id": entry["issuing_coverage"],
                   "plan": entry["issuing_plan"],
                   "substitution_from": key[0], "lineno": 0,
                   "source": SOURCE_LABEL}


def apply_psubsseg_plan_copies(grids, manifest):
    """Post-grid PLAN_COPY application (sandwich re-emits).

    Copies every standard-generation grid key of copy_plan in the target table
    to (issuing_plan, ..., entry EFFDATE). Value-identical by construction.
    Returns stats incl. fail-closed blockers when a copy source is empty.
    """
    stats = {"entries": 0, "keys_copied": 0, "cells_copied": 0, "blockers": []}
    for entry in manifest:
        if entry["mode"] != "PLAN_COPY":
            continue
        stats["entries"] += 1
        table = entry["target_table"]
        grid = grids.get(table)
        src_keys = []
        if grid:
            src_keys = [k for k in grid
                        if k[0] == entry["copy_plan"] and k[8] == S.STANDARD_EFFDATE]
        if not src_keys:
            stats["blockers"].append({
                "id": "PSUBSSEG_PLAN_COPY_EMPTY", "severity": "BLOCKER",
                "table": table,
                "detail": (
                    f"PLAN_COPY source {entry['copy_plan']} has no "
                    f"{S.STANDARD_EFFDATE} keys in {table} "
                    f"(entry {entry['issuing_coverage']}/{entry['rate_type']}"
                    f"@{entry['effdate']})"
                ),
            })
            continue
        for k in src_keys:
            new_key = (entry["issuing_plan"],) + k[1:8] + (entry["effdate"],)
            if new_key in grid:
                continue
            grid[new_key] = dict(grid[k])
            stats["keys_copied"] += 1
            stats["cells_copied"] += len(grid[k])
    return stats


def summarize_status(status_counter: Counter) -> dict:
    return dict(status_counter)
