"""
PAAGERAT UL COI/GCOI loader — ISWL Phase 3 QUIKCOI (U6) / Phase 4 QUIKGCOI (U5).

Business rules:
  * Attained-age scalar: SEQ -> AGE, CNTL=00, VALUE_INFO -> QX0; QX1–QX9 blank.
  * Do NOT use VALUE_FLOAT when VALUE_INFO is present (U5/U6: FLOAT is always 0.0).
  * U6 -> QuikCoi (1658CS, 1679CS); U5 -> QuikGcoi (1679CS only).
  * Segment resolution: PAAGERAT.COVERAGE_ID -> PCOVRSGT -> PCOVR -> crosswalk PLAN.
"""
from __future__ import annotations

import csv
import os

from qla_core import rate_dbf_schema as S
from qla_core import rate_segment_resolution as SR
from qla_core.rate_factor_loader import LoaderConfig, _to_float, load_plan_crosswalk

U6_TYPE_CODE = "U6"
U5_TYPE_CODE = "U5"
U6_SEGMENT_IDS = frozenset({"658 CEN I", "659 CEN II"})
U5_SEGMENT_IDS = frozenset({"659 CEN II"})
ISWL_COI_MPLAN_ALLOWLIST = frozenset({"1658CS", "1679CS"})
ISWL_GCOI_MPLAN_ALLOWLIST = frozenset({"1679CS"})
EXPECTED_U6_SOURCE_ROWS = 800
EXPECTED_U5_SOURCE_ROWS = 200


def iswl_coi_mplan_allowlist(cfg: dict) -> frozenset:
    phase3 = cfg.get("iswl_phase3", {})
    allow = phase3.get("coi_mplan_allowlist")
    if allow:
        return frozenset(str(p).strip() for p in allow)
    return ISWL_COI_MPLAN_ALLOWLIST


def iswl_gcoi_mplan_allowlist(cfg: dict) -> frozenset:
    phase4 = cfg.get("iswl_phase4", {})
    allow = phase4.get("gcoi_mplan_allowlist")
    if allow:
        return frozenset(str(p).strip() for p in allow)
    return ISWL_GCOI_MPLAN_ALLOWLIST


def _rate_from_row(row, col, *, require_value_info: bool) -> tuple[str | None, str | None]:
    """Return (raw_value, source_column) — VALUE_INFO authoritative for U5/U6."""
    vi_idx = col.get("VALUE_INFO")
    vf_idx = col.get("VALUE_FLOAT")
    if vi_idx is not None:
        vi_raw = row[vi_idx].strip()
        if vi_raw:
            return vi_raw, "VALUE_INFO"
        if require_value_info:
            return None, None
    if vf_idx is not None and not require_value_info:
        vf_raw = row[vf_idx].strip()
        if vf_raw:
            return vf_raw, "VALUE_FLOAT"
    return None, None


def _resolve_paagerat_paths(repo_root, cfg) -> list[str] | None:
    pa = cfg.get("paagerat_pr_extract")
    if not pa:
        return None
    pa_path = pa if os.path.isabs(pa) else os.path.join(repo_root, pa)
    psgt = cfg.get("pcovrsgt_csv", "")
    pcovr = cfg.get("pcovr_csv", "")
    xwalk = cfg.get("plan_form_crosswalk", "")
    paths = [
        pa_path,
        psgt if os.path.isabs(psgt) else os.path.join(repo_root, psgt),
        pcovr if os.path.isabs(pcovr) else os.path.join(repo_root, pcovr),
        xwalk if os.path.isabs(xwalk) else os.path.join(repo_root, xwalk),
    ]
    if not all(os.path.isfile(p) for p in paths):
        return None
    return paths


def transform_paagerat_ul_scalar(
    paagerat_csv,
    resolver: SR.SegmentResolver,
    config: LoaderConfig,
    *,
    type_code: str,
    target_table: str,
    plan_allowlist: frozenset,
):
    """Stream PAAGERAT attained-age scalar rows for QuikCoi (U6) or QuikGcoi (U5)."""
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

            if plan not in plan_allowlist:
                yield {"status": "EXCLUDED", "type_code": typ, "coverage_id": seg,
                       "plan": plan, "lineno": lineno,
                       "note": f"plan {plan} outside allowlist"}
                continue

            val_raw, val_src = _rate_from_row(row, col, require_value_info=True)
            if val_raw is None:
                yield {"status": "BAD_VALUE", "type_code": typ, "coverage_id": seg,
                       "plan": plan, "note": f"VALUE_INFO required for {type_code}",
                       "lineno": lineno}
                continue

            value = _to_float(val_raw)
            if value is None:
                yield {"status": "BAD_VALUE", "type_code": typ, "coverage_id": seg,
                       "plan": plan, "raw_value": val_raw, "lineno": lineno}
                continue

            sex = row[col["SEX"]].strip()
            band = row[col["BAND"]].strip()
            uw = row[col["UWCLS"]].strip()
            seq = row[col["SEQ"]].strip()

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
                "table": target_table,
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
                "value_source": val_src,
                "lineno": lineno,
                "original_age": original_age,
                "age_capped": age_capped,
            }


def transform_paagerat_u6(paagerat_csv, resolver: SR.SegmentResolver, config: LoaderConfig,
                          plan_allowlist: frozenset | None = None):
    """Stream PAAGERAT TYPE=U6 rows for ISWL current COI (QuikCoi / VARGP=3)."""
    allow = plan_allowlist or ISWL_COI_MPLAN_ALLOWLIST
    return transform_paagerat_ul_scalar(
        paagerat_csv, resolver, config,
        type_code=U6_TYPE_CODE, target_table="QuikCoi", plan_allowlist=allow,
    )


def transform_paagerat_u5(paagerat_csv, resolver: SR.SegmentResolver, config: LoaderConfig,
                          plan_allowlist: frozenset | None = None):
    """Stream PAAGERAT TYPE=U5 rows for ISWL guaranteed COI (QuikGcoi / VARGP=3)."""
    allow = plan_allowlist or ISWL_GCOI_MPLAN_ALLOWLIST
    return transform_paagerat_ul_scalar(
        paagerat_csv, resolver, config,
        type_code=U5_TYPE_CODE, target_table="QuikGcoi", plan_allowlist=allow,
    )


def load_paagerat_coi_plan_set(paagerat_csv, pcovrsgt_csv, pcovr_csv, crosswalk_xlsx,
                               plan_allowlist: frozenset | None = None) -> frozenset:
    allow = plan_allowlist or ISWL_COI_MPLAN_ALLOWLIST
    cov2plan, _ = load_plan_crosswalk(crosswalk_xlsx)
    resolver = SR.SegmentResolver.from_files(pcovrsgt_csv, pcovr_csv, cov2plan)
    config = LoaderConfig()
    plans = set()
    for t in transform_paagerat_u6(paagerat_csv, resolver, config, plan_allowlist=allow):
        if t.get("status") == "IN_SCOPE":
            plans.add(t["plan"])
    return frozenset(plans)


def load_paagerat_coi_plan_set_from_config(repo_root, cfg) -> frozenset:
    if not cfg.get("iswl_phase3", {}).get("quikcoi_enabled", False):
        return frozenset()
    paths = _resolve_paagerat_paths(repo_root, cfg)
    if not paths:
        return frozenset()
    return load_paagerat_coi_plan_set(
        paths[0], paths[1], paths[2], paths[3],
        plan_allowlist=iswl_coi_mplan_allowlist(cfg),
    )


def load_paagerat_gcoi_plan_set(paagerat_csv, pcovrsgt_csv, pcovr_csv, crosswalk_xlsx,
                                plan_allowlist: frozenset | None = None) -> frozenset:
    allow = plan_allowlist or ISWL_GCOI_MPLAN_ALLOWLIST
    cov2plan, _ = load_plan_crosswalk(crosswalk_xlsx)
    resolver = SR.SegmentResolver.from_files(pcovrsgt_csv, pcovr_csv, cov2plan)
    config = LoaderConfig()
    plans = set()
    for t in transform_paagerat_u5(paagerat_csv, resolver, config, plan_allowlist=allow):
        if t.get("status") == "IN_SCOPE":
            plans.add(t["plan"])
    return frozenset(plans)


def load_paagerat_gcoi_plan_set_from_config(repo_root, cfg) -> frozenset:
    if not cfg.get("iswl_phase4", {}).get("quikgcoi_enabled", False):
        return frozenset()
    paths = _resolve_paagerat_paths(repo_root, cfg)
    if not paths:
        return frozenset()
    return load_paagerat_gcoi_plan_set(
        paths[0], paths[1], paths[2], paths[3],
        plan_allowlist=iswl_gcoi_mplan_allowlist(cfg),
    )
