"""
Issue #40 — PCOVRSGT-aware inherited CV rate emit for QuikCvs.

Emits Rate_Table CV rows from rate-owner coverages under issuing plan codes when
the issuing coverage has no direct CV table but inherits CV-bearing segments.
"""
from __future__ import annotations

import csv

from qla_core import rate_dbf_schema as S
from qla_core import rate_factor_loader as L


def _cv_coverage_ids(source_csv):
    counts = {}
    with open(source_csv, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        next(rd, None)
        for r in rd:
            if len(r) < 8 or r[1].strip() != "CV":
                continue
            cov = r[0].strip()
            if cov and set(cov) == {"-"}:
                continue
            counts[cov] = counts.get(cov, 0) + 1
    return {cov for cov, n in counts.items() if n}


def _load_active_segt_ids(pcovrsgt_csv):
    """Return {issuing_coverage: [SEGT_ID, ...]} for active PCOVRSGT slots."""
    slots = {}
    with open(pcovrsgt_csv, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        hdr = [c.strip() for c in next(rd)]
        ci = hdr.index("COVERAGE_ID")
        si = hdr.index("SEGT_ID")
        sf = hdr.index("SEGT_FLAG")
        for row in rd:
            if len(row) <= max(ci, si, sf):
                continue
            if row[sf].strip() != "Y":
                continue
            cov = row[ci].strip()
            segt = row[si].strip()
            if cov and segt:
                slots.setdefault(cov, []).append(segt)
    return slots


def _select_rate_owner(issuing_cov, candidates, active_segts):
    if len(candidates) == 1:
        return candidates[0]
    scores = {c: sum(1 for s in active_segts if s == c) for c in candidates}
    return max(candidates, key=lambda c: (scores.get(c, 0), -candidates.index(c)))


def build_inheritance_manifest(audit_csv, pcovrsgt_csv, source_csv):
    """
    Build approved Issue #40 inheritance manifest entries.

    Each entry:
      issuing_coverage, issuing_plan, rate_owner_coverage, candidate_owners
    """
    cv_covs = _cv_coverage_ids(source_csv)
    active = _load_active_segt_ids(pcovrsgt_csv)
    entries = []
    with open(audit_csv, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("bucket") != "MISSING_INHERITED_CV":
                continue
            issuing_cov = row["lifepro_coverage"].strip()
            issuing_plan = row["ql_plan"].strip()
            if issuing_cov in cv_covs:
                continue
            candidates = [c.strip() for c in row["rate_owner_coverage"].split(";") if c.strip()]
            candidates = [c for c in candidates if c in cv_covs]
            if not candidates:
                continue
            owner = _select_rate_owner(issuing_cov, candidates, active.get(issuing_cov, []))
            entries.append({
                "issuing_coverage": issuing_cov,
                "issuing_plan": issuing_plan,
                "rate_owner_coverage": owner,
                "candidate_owners": candidates,
            })
    return entries


def transform_inherited_cv(source_csv, manifest, config, cv_fnz=None):
    """
    Stream inherited CV rows: rate_owner Coverage -> issuing PLAN QuikCvs keys.
    """
    if not manifest:
        return
    owner_to_entries = {}
    for entry in manifest:
        owner_to_entries.setdefault(entry["rate_owner_coverage"], []).append(entry)

    with open(source_csv, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        next(rd, None)
        lineno = 1
        for r in rd:
            lineno += 1
            if len(r) < 8:
                continue
            cov = r[0].strip()
            if cov not in owner_to_entries:
                continue
            typ = r[1].strip()
            if typ != "CV":
                continue
            age = r[2].strip()
            sex = r[3].strip()
            band = r[4].strip()
            uw = r[5].strip()
            dur = r[6].strip()
            val = r[7].strip()

            value = L._to_float(val)
            if value is None:
                for entry in owner_to_entries[cov]:
                    yield {
                        "status": "BAD_VALUE", "type_code": typ, "coverage_id": cov,
                        "plan": entry["issuing_plan"], "raw_value": val, "lineno": lineno,
                        "inheritance_from": cov, "issuing_coverage": entry["issuing_coverage"],
                    }
                continue
            try:
                source_d = int(dur)
            except ValueError:
                for entry in owner_to_entries[cov]:
                    yield {
                        "status": "BAD_VALUE", "type_code": typ, "coverage_id": cov,
                        "plan": entry["issuing_plan"], "raw_duration": dur, "lineno": lineno,
                        "inheritance_from": cov, "issuing_coverage": entry["issuing_coverage"],
                    }
                continue

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

            fnz_key = (cov, sex, int(original_age if original_age.isdigit() else age))
            fnz = cv_fnz.get(fnz_key) if cv_fnz is not None else None
            if fnz is not None and age.isdigit():
                ql_dur = L.cv_remap_ql_duration(source_d, sex, fnz_key[2], fnz)
                if ql_dur is None:
                    for entry in owner_to_entries[cov]:
                        yield {
                            "status": "EXCLUDED", "type_code": typ, "coverage_id": cov,
                            "lineno": lineno, "note": "CV_TRUNCATED_PAST_MATURITY",
                            "inheritance_from": cov, "issuing_coverage": entry["issuing_coverage"],
                            "plan": entry["issuing_plan"],
                        }
                    continue
            else:
                try:
                    ql_dur = S.source_duration_to_ql(dur)
                except ValueError:
                    for entry in owner_to_entries[cov]:
                        yield {
                            "status": "BAD_VALUE", "type_code": typ, "coverage_id": cov,
                            "plan": entry["issuing_plan"], "raw_duration": dur, "lineno": lineno,
                            "inheritance_from": cov, "issuing_coverage": entry["issuing_coverage"],
                        }
                    continue
            if ql_dur < 0:
                continue

            cntl, col = S.duration_to_cntl_col(ql_dur)
            for entry in owner_to_entries[cov]:
                yield {
                    "status": "IN_SCOPE",
                    "coverage_id": entry["issuing_coverage"],
                    "type_code": typ,
                    "table": "QuikCvs",
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
                    "source": "INHERITED_CV",
                    "inheritance_from": cov,
                }
