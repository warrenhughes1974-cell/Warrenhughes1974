"""Manifest-gated shared/inherited rate loader for confirmed QLAdmin tables.

Consumes the generated master inventory candidate list and emits only rows marked
as candidates. This keeps rate-completeness expansion auditable and avoids a broad
runtime walk of every PCOVRSGT relationship.
"""
from __future__ import annotations

import csv

from qla_core import rate_dbf_schema as S
from qla_core import rate_factor_loader as L

CONFIRMED_TYPES = frozenset({"DB", "DV", "NF", "NP", "PR", "RV"})
RATE_TABLE_STATUS = "Candidate for inherited/shared loader"
PAAGERAT_STATUS = "Candidate for PAAGERAT shared segment loader"
PAAGERAT_TYPES = frozenset({"NF", "PR"})
QLADMIN_BANDS = frozenset({"00", "01", "02", "03"})


def _dedupe_preserve_order(values):
    seen = set()
    out = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _row_sort_key(row):
    try:
        seq = int((row.get("pcovrsgt_seq") or "").strip())
    except ValueError:
        seq = 999999
    return (seq, (row.get("source_segment") or "").strip())


def build_shared_manifest(candidate_csv):
    """Build grouped manifest entries from inherited_shared_rate_candidates.csv."""
    grouped = {}
    with open(candidate_csv, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            source_family = (row.get("source_family") or "").strip()
            status = (row.get("status") or "").strip()
            rate_type = (row.get("type_code") or "").strip()
            issuing_plan = (row.get("issuing_plan") or "").strip()
            issuing_coverage = (row.get("issuing_coverage") or "").strip()
            source_segment = (row.get("source_segment") or "").strip()
            table = S.TYPE_TO_TABLE.get(rate_type)

            if not issuing_plan or not source_segment or rate_type not in CONFIRMED_TYPES or not table:
                continue
            if source_family == "Rate_Table" and status != RATE_TABLE_STATUS:
                continue
            if source_family == "PAAGERAT" and status != PAAGERAT_STATUS:
                continue
            if source_family == "PAAGERAT" and rate_type not in PAAGERAT_TYPES:
                continue
            if rate_type == "CV":
                # CV inheritance remains owned by the Issue #40 loader.
                continue

            key = (source_family, issuing_plan, rate_type, table)
            rec = grouped.setdefault(
                key,
                {
                    "source_family": source_family,
                    "issuing_plan": issuing_plan,
                    "issuing_coverage": issuing_coverage,
                    "rate_type": rate_type,
                    "target_table": table,
                    "candidate_rows": [],
                },
            )
            rec["candidate_rows"].append(row)

    entries = []
    for rec in grouped.values():
        ordered = sorted(rec["candidate_rows"], key=_row_sort_key)
        entries.append({
            "source_family": rec["source_family"],
            "issuing_plan": rec["issuing_plan"],
            "issuing_coverage": rec["issuing_coverage"],
            "rate_type": rec["rate_type"],
            "target_table": rec["target_table"],
            "source_segments": _dedupe_preserve_order(
                (row.get("source_segment") or "").strip() for row in ordered
            ),
        })
    return sorted(entries, key=lambda e: (e["source_family"], e["issuing_plan"], e["rate_type"]))


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


def _transform_rate_table_row(row, lineno, cov, entry, config):
    typ = row[1].strip()
    if typ != entry["rate_type"]:
        return None

    age = row[2].strip()
    sex = row[3].strip()
    band = row[4].strip()
    uw = row[5].strip()
    dur = row[6].strip()
    val = row[7].strip()
    value = L._to_float(val)
    if value is None:
        return {
            "status": "BAD_VALUE", "source": "SHARED_RATE_TABLE",
            "type_code": typ, "coverage_id": cov, "plan": entry["issuing_plan"],
            "raw_value": val, "lineno": lineno,
        }
    try:
        ql_dur = S.source_duration_to_ql(dur)
    except ValueError:
        return {
            "status": "BAD_VALUE", "source": "SHARED_RATE_TABLE",
            "type_code": typ, "coverage_id": cov, "plan": entry["issuing_plan"],
            "raw_duration": dur, "lineno": lineno,
        }
    if ql_dur < 0:
        return None

    gender = S.map_sex(sex)
    uwclass = S.map_uwclass(uw)
    band2 = S.map_band(band)
    if gender is None or uwclass is None or band2 is None or band2 not in QLADMIN_BANDS:
        return {
            "status": "BAD_VALUE", "source": "SHARED_RATE_TABLE",
            "type_code": typ, "coverage_id": cov, "plan": entry["issuing_plan"],
            "note": "segmentation crosswalk", "raw_band": band, "mapped_band": band2, "lineno": lineno,
        }

    original_age = age
    age_capped = False
    if age.isdigit() and int(age) > S.MAX_AGE:
        age = str(S.MAX_AGE)
        age_capped = True
    age2 = age.zfill(2)
    cntl, col = S.duration_to_cntl_col(ql_dur)
    return {
        "status": "IN_SCOPE",
        "source": "SHARED_RATE_TABLE",
        "coverage_id": entry.get("issuing_coverage") or cov,
        "type_code": typ,
        "table": entry["target_table"],
        "plan": entry["issuing_plan"],
        "age": age2,
        "cntl": cntl,
        "col": col,
        "gender": gender,
        "uwclass": uwclass,
        "band": band2,
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
        "inheritance_from": cov,
        "_cell_key": _cell_key(
            entry["issuing_plan"], entry["target_table"], age2, cntl, col,
            gender, uwclass, band2, config,
        ),
    }


def transform_rate_table_shared(source_csv, manifest, config):
    """Stream Rate_Table source segments under issuing PLAN keys."""
    entries = [entry for entry in manifest if entry.get("source_family") == "Rate_Table"]
    if not entries:
        return

    seg_targets = {}
    for ei, entry in enumerate(entries):
        for si, seg in enumerate(entry["source_segments"]):
            seg_targets.setdefault(seg, []).append((ei, si, entry))

    pending = []
    with open(source_csv, encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        for lineno, row in enumerate(reader, 2):
            if len(row) < 8:
                continue
            cov = row[0].strip()
            if cov not in seg_targets:
                continue
            for ei, si, entry in seg_targets[cov]:
                pending.append((ei, si, lineno, cov, row, entry))

    pending.sort(key=lambda x: (x[0], x[1], x[2]))
    filled = {}
    for ei, _si, lineno, cov, row, entry in pending:
        out = _transform_rate_table_row(row, lineno, cov, entry, config)
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


def _transform_paagerat_row(row, col, lineno, seg, entry, config):
    typ = row[col["TYPE_CODE"]].strip()
    if typ != entry["rate_type"]:
        return None

    rec_seq = row[col["RECORD_SEQ"]].strip() if "RECORD_SEQ" in col else "1"
    if rec_seq != "1":
        return {
            "status": "EXCLUDED", "source": "SHARED_PAAGERAT",
            "type_code": typ, "coverage_id": seg, "plan": entry["issuing_plan"],
            "lineno": lineno, "note": f"RECORD_SEQ={rec_seq} (primary table is 1)",
        }

    sex = row[col["SEX"]].strip()
    band = row[col["BAND"]].strip()
    uw = row[col["UWCLS"]].strip()
    seq = row[col["SEQ"]].strip()
    vi = col.get("VALUE_INFO")
    vf = col.get("VALUE_FLOAT")
    val_raw = row[vi].strip() if vi is not None else row[vf].strip()
    value = L._to_float(val_raw)
    if value is None:
        return {
            "status": "BAD_VALUE", "source": "SHARED_PAAGERAT",
            "type_code": typ, "coverage_id": seg, "plan": entry["issuing_plan"],
            "raw_value": val_raw, "lineno": lineno,
        }

    gender = S.map_sex(sex)
    uwclass = S.map_uwclass(uw)
    band2 = S.map_band(band)
    if gender is None or uwclass is None or band2 is None or band2 not in QLADMIN_BANDS:
        return {
            "status": "BAD_VALUE", "source": "SHARED_PAAGERAT",
            "type_code": typ, "coverage_id": seg, "plan": entry["issuing_plan"],
            "note": "segmentation crosswalk", "raw_band": band, "mapped_band": band2, "lineno": lineno,
        }
    if not seq.isdigit():
        return {
            "status": "BAD_VALUE", "source": "SHARED_PAAGERAT",
            "type_code": typ, "coverage_id": seg, "plan": entry["issuing_plan"],
            "raw_age": seq, "lineno": lineno,
        }

    original_age = seq
    age_int = int(seq)
    age_capped = False
    if age_int > S.MAX_AGE:
        age_int = S.MAX_AGE
        age_capped = True
    age2 = str(age_int).zfill(2)
    cntl, col_idx = S.duration_to_cntl_col(0)
    return {
        "status": "IN_SCOPE",
        "source": "SHARED_PAAGERAT",
        "coverage_id": entry.get("issuing_coverage") or seg,
        "type_code": typ,
        "table": entry["target_table"],
        "plan": entry["issuing_plan"],
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
        "inheritance_from": seg,
        "_cell_key": _cell_key(
            entry["issuing_plan"], entry["target_table"], age2, cntl, col_idx,
            gender, uwclass, band2, config,
        ),
    }


def transform_paagerat_shared(paagerat_csv, manifest, config):
    """Stream PAAGERAT source segments under issuing PLAN keys."""
    entries = [entry for entry in manifest if entry.get("source_family") == "PAAGERAT"]
    if not entries:
        return

    seg_targets = {}
    for ei, entry in enumerate(entries):
        for si, seg in enumerate(entry["source_segments"]):
            seg_targets.setdefault(seg, []).append((ei, si, entry))

    pending = []
    with open(paagerat_csv, encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.reader(f)
        header = [name.strip() for name in next(reader)]
        col = {name: i for i, name in enumerate(header)}
        for lineno, row in enumerate(reader, 2):
            seg = row[col["COVERAGE_ID"]].strip()
            if seg not in seg_targets:
                continue
            for ei, si, entry in seg_targets[seg]:
                pending.append((ei, si, lineno, seg, row, entry, col))

    pending.sort(key=lambda x: (x[0], x[1], x[2]))
    filled = {}
    for ei, _si, lineno, seg, row, entry, col in pending:
        out = _transform_paagerat_row(row, col, lineno, seg, entry, config)
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
