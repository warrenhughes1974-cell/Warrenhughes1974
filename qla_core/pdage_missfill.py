"""
Issue #42 — PDAGE age/duration miss-fill into Rate_Table-shaped emit.

Streams PDAGE rows only when (COVERAGE_ID, TYPE_CODE) is absent from the
authoritative Rate_Table extract. Segment-only coverage IDs resolve to issuing
PLAN codes via PCOVRSGT (same chain as PAAGERAT segment resolution).
"""
from __future__ import annotations

import csv
from collections import defaultdict

from qla_core import rate_dbf_schema as S
from qla_core import rate_factor_loader as L

RATE_TABLE_HEADER = (
    "COVERAGE_ID",
    "TYPE_CODE",
    "AGE",
    "SEX",
    "BAND",
    "UNDERWRITING_CLASS",
    "DURATION",
    "VALUE",
)


def rate_table_key_index(rate_table_path: str) -> set[tuple[str, str]]:
    """Return set of (COVERAGE_ID, TYPE_CODE) present in Rate_Table."""
    keys: set[tuple[str, str]] = set()
    with open(rate_table_path, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        next(rd, None)
        for r in rd:
            if len(r) < 8:
                continue
            cov = r[0].strip()
            if not cov or set(cov) == {"-"}:
                continue
            keys.add((cov, r[1].strip()))
    return keys


def _norm_pdage_row(raw: dict) -> dict:
    return {(k or "").strip(): (v or "").strip() for k, v in raw.items()}


def _pdage_row_mappable(row: dict) -> bool:
    """True when PDAGE classification fields map to QLAdmin segmentation."""
    sex = row.get("SEX", "")
    band = row.get("BAND", "")
    uw = row.get("UWCLS", "")
    if S.map_sex(sex) is None:
        return False
    if S.map_uwclass(uw) is None:
        return False
    if S.map_band(band) is None:
        return False
    return True


def _pdage_to_rate_table_row(row: dict) -> list[str] | None:
    cov = row.get("COVERAGE_ID", "")
    typ = row.get("TYPE_CODE", "")
    if not cov or not typ:
        return None
    if not _pdage_row_mappable(row):
        return None
    val = row.get("VALUE1", "")
    if not val:
        val = row.get("VALUE1_FLOAT", "")
    if not val or val in (".", "-", "-."):
        return None
    return [
        cov,
        typ,
        row.get("AGE", ""),
        row.get("SEX", ""),
        row.get("BAND", ""),
        row.get("UWCLS", ""),
        row.get("DURATION", ""),
        val,
    ]


def _resolve_plan(cov: str, cov2plan: dict, segment_resolver) -> tuple[str | None, str]:
    plan = cov2plan.get(cov)
    if plan:
        return plan, "DIRECT"
    if segment_resolver is None:
        return None, ""
    res = segment_resolver.resolve(cov, source="rate_table")
    if res and res.plan:
        return res.plan, res.resolution_path
    return None, ""


def _transform_rate_table_row(
    r: list[str],
    lineno: int,
    cov2plan: dict,
    config: L.LoaderConfig,
    segment_resolver,
    cv_fnz,
    *,
    source_label: str = "PDAGE_MISSFILL",
):
    """Transform one Rate_Table-shaped row; mirrors transform_source row logic."""
    cov = r[0].strip()
    typ = r[1].strip()
    age = r[2].strip()
    sex = r[3].strip()
    band = r[4].strip()
    uw = r[5].strip()
    dur = r[6].strip()
    val = r[7].strip()

    if typ in S.EXCLUDED_TYPE_CODES:
        yield {
            "status": "EXCLUDED",
            "type_code": typ,
            "coverage_id": cov,
            "lineno": lineno,
            "source": source_label,
        }
        return

    table = S.TYPE_TO_TABLE.get(typ)
    if table is None:
        yield {
            "status": "EXCLUDED",
            "type_code": typ,
            "coverage_id": cov,
            "lineno": lineno,
            "note": "unmapped TYPE_CODE",
            "source": source_label,
        }
        return

    plan, resolution = _resolve_plan(cov, cov2plan, segment_resolver)
    if not plan:
        yield {
            "status": "PLAN_UNRESOLVED",
            "type_code": typ,
            "coverage_id": cov,
            "lineno": lineno,
            "source": source_label,
        }
        return
    if " " in plan or not plan:
        yield {
            "status": "PLAN_INVALID",
            "type_code": typ,
            "coverage_id": cov,
            "plan": plan,
            "lineno": lineno,
            "source": source_label,
        }
        return

    value = L._to_float(val)
    if value is None:
        yield {
            "status": "BAD_VALUE",
            "type_code": typ,
            "coverage_id": cov,
            "plan": plan,
            "raw_value": val,
            "lineno": lineno,
            "source": source_label,
        }
        return
    try:
        source_d = int(dur)
    except ValueError:
        yield {
            "status": "BAD_VALUE",
            "type_code": typ,
            "coverage_id": cov,
            "plan": plan,
            "raw_duration": dur,
            "lineno": lineno,
            "source": source_label,
        }
        return

    gender = S.map_sex(sex)
    uwclass = S.map_uwclass(uw)
    band2 = S.map_band(band)
    if gender is None or uwclass is None or band2 is None:
        yield {
            "status": "BAD_VALUE",
            "type_code": typ,
            "coverage_id": cov,
            "plan": plan,
            "raw_sex": sex,
            "raw_band": band,
            "raw_uw": uw,
            "lineno": lineno,
            "source": source_label,
            "note": "unmapped classification",
        }
        return

    original_age = age
    emitted_age_int = age.zfill(2)
    age_capped = False
    if age.isdigit() and int(age) > S.MAX_AGE:
        emitted_age_int = str(S.MAX_AGE).zfill(2)
        age_capped = True
    age2 = emitted_age_int

    if table == "QuikCvs" and cv_fnz is not None and age.isdigit():
        fnz_key = (cov, sex, int(original_age if original_age.isdigit() else age))
        fnz = cv_fnz.get(fnz_key)
        if fnz is not None:
            ql_dur = L.cv_remap_ql_duration(source_d, sex, fnz_key[2], fnz)
            if ql_dur is None:
                yield {
                    "status": "EXCLUDED",
                    "type_code": typ,
                    "coverage_id": cov,
                    "lineno": lineno,
                    "note": "CV_TRUNCATED_PAST_MATURITY",
                    "source": source_label,
                }
                return
        else:
            ql_dur = S.source_duration_to_ql(dur)
    else:
        try:
            ql_dur = S.source_duration_to_ql(dur)
        except ValueError:
            yield {
                "status": "BAD_VALUE",
                "type_code": typ,
                "coverage_id": cov,
                "plan": plan,
                "raw_duration": dur,
                "lineno": lineno,
                "source": source_label,
            }
            return
    if ql_dur < 0:
        yield {
            "status": "BAD_VALUE",
            "type_code": typ,
            "coverage_id": cov,
            "plan": plan,
            "raw_duration": dur,
            "lineno": lineno,
            "source": source_label,
        }
        return

    cntl, col = S.duration_to_cntl_col(ql_dur)
    yield {
        "status": "IN_SCOPE",
        "coverage_id": cov,
        "type_code": typ,
        "table": table,
        "plan": plan,
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
        "source": source_label,
        "segment_resolution": resolution,
    }


def transform_pdage_missfill(
    pdage_path: str,
    rate_table_path: str,
    cov2plan: dict,
    config: L.LoaderConfig,
    segment_resolver=None,
    cv_fnz=None,
    approved_types=None,
):
    """
    Stream transformed rows from PDAGE for keys missing in Rate_Table.

    approved_types: optional TYPE_CODE allow-list (default: mapped factor types).
    """
    if not pdage_path or not rate_table_path:
        return
    rt_keys = rate_table_key_index(rate_table_path)
    allowed = frozenset(approved_types) if approved_types else None
    stats = defaultdict(int)

    with open(pdage_path, encoding="utf-8-sig", errors="replace", newline="") as f:
        lineno = 1
        for raw in csv.DictReader(f):
            lineno += 1
            row = _norm_pdage_row(raw)
            cov = row.get("COVERAGE_ID", "")
            typ = row.get("TYPE_CODE", "")
            if not cov or set(cov) == {"-"}:
                continue
            if (cov, typ) in rt_keys:
                stats["skipped_rt_present"] += 1
                continue
            if allowed is not None and typ not in allowed:
                stats["skipped_type"] += 1
                continue
            if typ in S.EXCLUDED_TYPE_CODES or typ not in S.TYPE_TO_TABLE:
                stats["skipped_type"] += 1
                continue
            rt_row = _pdage_to_rate_table_row(row)
            if rt_row is None:
                stats["skipped_bad_value"] += 1
                continue
            stats["rows_considered"] += 1
            for out in _transform_rate_table_row(
                rt_row,
                lineno,
                cov2plan,
                config,
                segment_resolver,
                cv_fnz,
            ):
                stats[f"status_{out['status']}"] += 1
                yield out

    stats["rt_key_count"] = len(rt_keys)


def merge_pdage_missfill_to_staging(
    rate_table_path: str,
    pdage_path: str,
    staging_path: str,
    approved_types=None,
    segment_resolver=None,
) -> dict:
    """
    Copy Rate_Table then append PDAGE rows for (cov,type) keys absent from RT.

    Returns summary counts. Reuses existing staging file when inputs are unchanged.
    """
    import hashlib
    import os
    import shutil

    rt_keys = rate_table_key_index(rate_table_path)
    allowed = frozenset(approved_types) if approved_types else None

    def _file_sig(*paths):
        parts = []
        for p in paths:
            st = os.stat(p)
            parts.append(f"{p}|{st.st_size}|{int(st.st_mtime)}")
        return hashlib.md5("|".join(parts).encode()).hexdigest()

    sig = _file_sig(rate_table_path, pdage_path)
    sig_path = staging_path + ".sig"
    if os.path.isfile(staging_path) and os.path.isfile(sig_path):
        with open(sig_path, encoding="utf-8") as f:
            if f.read().strip() == sig:
                return {"staging_path": staging_path, "reused": True}

    os.makedirs(os.path.dirname(staging_path) or ".", exist_ok=True)
    appended = 0
    skipped = 0
    shutil.copyfile(rate_table_path, staging_path)
    with open(staging_path, "a", encoding="utf-8", newline="") as out:
        w = csv.writer(out)
        with open(pdage_path, encoding="utf-8-sig", errors="replace", newline="") as f:
            for raw in csv.DictReader(f):
                row = _norm_pdage_row(raw)
                cov = row.get("COVERAGE_ID", "")
                typ = row.get("TYPE_CODE", "")
                if not cov or set(cov) == {"-"}:
                    continue
                if (cov, typ) in rt_keys:
                    skipped += 1
                    continue
                if segment_resolver is not None:
                    parent = segment_resolver.parent_coverage(cov)
                    if parent and (parent, typ) in rt_keys:
                        skipped += 1
                        continue
                if allowed is not None and typ not in allowed:
                    skipped += 1
                    continue
                if typ in S.EXCLUDED_TYPE_CODES or typ not in S.TYPE_TO_TABLE:
                    skipped += 1
                    continue
                rt_row = _pdage_to_rate_table_row(row)
                if rt_row is None:
                    skipped += 1
                    continue
                w.writerow(rt_row)
                appended += 1
    with open(sig_path, "w", encoding="utf-8") as f:
        f.write(sig)
    return {
        "staging_path": staging_path,
        "reused": False,
        "appended_rows": appended,
        "skipped_rows": skipped,
        "rate_table_keys": len(rt_keys),
    }


def missfill_summary(pdage_path: str, rate_table_path: str) -> dict:
    """Read-only inventory of PDAGE keys that would miss-fill."""
    rt_keys = rate_table_key_index(rate_table_path)
    by_key: dict[tuple[str, str], int] = defaultdict(int)
    with open(pdage_path, encoding="utf-8-sig", errors="replace", newline="") as f:
        for raw in csv.DictReader(f):
            row = _norm_pdage_row(raw)
            cov = row.get("COVERAGE_ID", "")
            typ = row.get("TYPE_CODE", "")
            if not cov or (cov, typ) in rt_keys:
                continue
            if _pdage_to_rate_table_row(row) is None:
                continue
            by_key[(cov, typ)] += 1
    return {
        "rate_table_keys": len(rt_keys),
        "missfill_keys": len(by_key),
        "missfill_rows": sum(by_key.values()),
        "keys": sorted(f"{c}|{t}|{n}" for (c, t), n in by_key.items()),
    }
