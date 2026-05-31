"""
PAAGERAT policy premium (PR) loader — segment-resolved attained-age rates.

Business rules:
  * PAAGERAT.COVERAGE_ID is a segment ID (PCOVRSGT.SEGT_ID), not a policy form.
  * Resolve: PAAGERAT -> PCOVRSGT -> PCOVR -> Policy Form Crosswalk -> PLAN.
  * Only TYPE_CODE = 'PR' rows are in scope for policy gross premium rates.
  * QuikPlan.VARGP = 3 (attained age): SEQ -> QuikGps.AGE, rate in CNTL=00 / GP0.
  * Do NOT unfold into issue-age x duration grids.
"""
import csv
import os

from qla_core import rate_dbf_schema as S
from qla_core import rate_segment_resolution as SR
from qla_core.rate_factor_loader import LoaderConfig, _to_float, load_plan_crosswalk

VARGP_ATTAINED_AGE = "3"


def load_paagerat_vargp3_plan_set(paagerat_csv, pcovrsgt_csv, pcovr_csv, crosswalk_xlsx):
    """Return authoritative PLAN codes with resolved PAAGERAT PR attained-age rates."""
    cov2plan, _ = load_plan_crosswalk(crosswalk_xlsx)
    resolver = SR.SegmentResolver.from_files(pcovrsgt_csv, pcovr_csv, cov2plan)
    config = LoaderConfig()
    plans = set()
    for t in transform_paagerat_pr(paagerat_csv, resolver, config):
        if t.get("status") == "IN_SCOPE":
            plans.add(t["plan"])
    return frozenset(plans)


def load_paagerat_vargp3_plan_set_from_config(repo_root, cfg):
    """Resolve VARGP=3 plan set from rate-loader config dict (optional paths)."""
    pa = cfg.get("paagerat_pr_extract")
    if not pa:
        return frozenset()
    pa_path = pa if os.path.isabs(pa) else os.path.join(repo_root, pa)
    psgt = cfg.get("pcovrsgt_csv", "")
    pcovr = cfg.get("pcovr_csv", "")
    xwalk = cfg.get("plan_form_crosswalk", "")
    psgt_path = psgt if os.path.isabs(psgt) else os.path.join(repo_root, psgt)
    pcovr_path = pcovr if os.path.isabs(pcovr) else os.path.join(repo_root, pcovr)
    xwalk_path = xwalk if os.path.isabs(xwalk) else os.path.join(repo_root, xwalk)
    if not all(os.path.isfile(p) for p in (pa_path, psgt_path, pcovr_path, xwalk_path)):
        return frozenset()
    return load_paagerat_vargp3_plan_set(pa_path, psgt_path, pcovr_path, xwalk_path)


def transform_paagerat_pr(paagerat_csv, resolver: SR.SegmentResolver, config: LoaderConfig):
    """
    Stream PAAGERAT rows filtered to TYPE_CODE='PR', segment-resolved to PLAN.

    Yields dicts with status:
      IN_SCOPE | EXCLUDED | SEGMENT_UNRESOLVED | PLAN_INVALID | BAD_VALUE
    """
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

            if typ != "PR":
                yield {"status": "EXCLUDED", "type_code": typ, "coverage_id": seg,
                       "lineno": lineno, "note": "non-PR PAAGERAT row"}
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

            sex = row[col["SEX"]].strip()
            band = row[col["BAND"]].strip()
            uw = row[col["UWCLS"]].strip()
            seq = row[col["SEQ"]].strip()
            vi = col.get("VALUE_INFO")
            vf = col.get("VALUE_FLOAT")
            val_raw = row[vi].strip() if vi is not None else row[vf].strip()

            value = _to_float(val_raw)
            if value is None:
                yield {"status": "BAD_VALUE", "type_code": typ, "coverage_id": seg,
                       "plan": plan, "raw_value": val_raw, "lineno": lineno}
                continue

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

            # Attained age (VARGP=3): SEQ -> QuikGps.AGE; cap at QLAdmin C2 width
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

            # VARGP=3 attained-age grid: single factor at CNTL=00 / GP0
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
                "table": "QuikGps",
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
                "lineno": lineno,
                "original_age": original_age,
                "age_capped": age_capped,
            }
