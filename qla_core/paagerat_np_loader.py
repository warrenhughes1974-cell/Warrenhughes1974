"""
PAAGERAT net-premium (NP) loader — attained-age series expanded onto QuikNps.

Issue #169. LifePRO stores 667 ART's net valuation premium by ATTAINED AGE in
PAAGERAT (SEQ = attained age). PDAGE carries no NP rows for the family at all, and
nothing read the PAAGERAT NP leg — `paagerat_pr_loader` wraps only 'PR' and 'NF'.
So 5667AT emitted no QuikNps rows, MTABNET valued 0, and the plan's reserve came
out $0 against LifePRO's $133,546.48 across 96 valued rows ($132,229.48 on the 95
rows that carry units).

The PSUBSSEG emit plan scoped exactly this as entry E4 ('5667AT' / QuikNps /
19000101 / source '667 ART' PAAGERAT) and its Dependency Gate confirmed the source
present; the entry never reached the delivered scope manifest.

Grid axis
---------
Unlike QuikGps / QuikDbs, QuikNps has no quikplan VARY field that tells QLAdmin to
read a slot axis as attained age -- "NP has no quikplan VARY fields; excluded by
design" (`quikplan_rate_variation_flags`). So this series cannot ride the Issue 140
slot axis. It is expanded onto the issue-age x duration grid QLAdmin actually reads
for net premium:

    QuikNps[issue_age][duration_index] = vector[issue_age + duration_index + 1]

Durations with no source point emit 0.00, per the rate-file import rule (Help p556:
"Rates must begin starting with age 00 and duration 00 and up. If there are no
rates for the lower ages, use 0.00.").

Proof (not assumption)
----------------------
Offset established from LifePRO's own valuation output, using the reference
identity RV_MEAN_RV = net premium x units / 2 (#168 review section 1.3): the
offset above reproduces LifePRO to the cent on 94 of the 95 unit-carrying 667 ART
rows. The 95th is a 1995 issue that reads the '667 ART 95' era segment (vector[53]
= 8.15 vs implied 8.1496). The 96th row (policy 9010886099 seq 2) holds a $1,317.00
reserve against ZERO units, so the per-unit identity cannot reproduce it by
construction -- that row is a separate open question, not an offset problem. See
`Issue_Log_Items/Issue_169/tools/prove_667art_np_expansion.py`.

Scope of this pass
------------------
The base '667 ART' segment resolves through PCOVRSGT -> PCOVR -> crosswalk and emits
on the standard 19000101 generation, covering 94 of the 95 unit-carrying rows LifePRO
reserves.

'667 ART 95' is a PSUBSSEG *substituted* segment: it does not resolve to a plan on
its own (it reports SEGMENT_UNRESOLVED), and its 5667AT relationship is declared only
in the PSUBSSEG scope manifest. Emitting its era generation therefore belongs on the
manifest route, not here — declaring the substitution a second time in this loader
would put coverage-ID substitution under two authorities. Left out deliberately; the
one 1995-issue policy affected (9011136641C) reads the base generation and lands 3.6%
low (7.86 vs LifePRO's 8.15) instead of at zero. Tracked as an issue #169 follow-up.

`coverage_effdate` stays supported for any coverage that does resolve and needs an
era band, but ships empty.
"""
from __future__ import annotations

import csv
import os

from qla_core import rate_dbf_schema as S
from qla_core import rate_segment_resolution as SR
from qla_core.rate_factor_loader import LoaderConfig, _to_float, load_plan_crosswalk

NP_TYPE_CODE = "NP"

# Attained age = issue age + duration index + 1. Verified on 94 of 95 unit-carrying rows.
ATTAINED_AGE_OFFSET = 1

# quikplan 5667AT carries ISSAGE 00..75; its sibling QuikTvs grid spans AGE 0..75.
DEFAULT_ISSUE_AGE_MAX = 75

# Issue #169 scope: only the 667 ART family. Every other coverage carrying PAAGERAT
# NP either already has QuikNps rows from PDAGE (`668 SPWL` -> 1668SP, which is also
# a CEN/ISWL level-NP plan, and `896 DAR` -> A96DAR, which has NP in both extracts)
# or has no resolved QL plan code yet (`667 ART CR`, `646 ART`, `L03 ART`, `SAL OL`).
NP_MPLAN_ALLOWLIST = frozenset({"5667AT"})

# Era-banded generations for coverages that resolve to a plan on their own. Empty by
# design: '667 ART 95' is a PSUBSSEG substituted segment and is not declared here (see
# module docstring). Config key `paagerat_np.coverage_effdate` can add entries.
COVERAGE_EFFDATE: dict[str, str] = {}

ZERO_RAW = "0.00"
SYNTHETIC_LINENO = 0


def np_mplan_allowlist(cfg: dict) -> frozenset:
    block = cfg.get("paagerat_np", {})
    allow = block.get("np_mplan_allowlist")
    if allow:
        return frozenset(str(p).strip() for p in allow)
    return NP_MPLAN_ALLOWLIST


def coverage_effdate_map(cfg: dict) -> dict:
    block = cfg.get("paagerat_np", {})
    raw = block.get("coverage_effdate")
    if raw:
        return {str(k).strip(): str(v).strip() for k, v in raw.items()}
    return dict(COVERAGE_EFFDATE)


def issue_age_max(cfg: dict) -> int:
    block = cfg.get("paagerat_np", {})
    try:
        return int(block.get("issue_age_max", DEFAULT_ISSUE_AGE_MAX))
    except (TypeError, ValueError):
        return DEFAULT_ISSUE_AGE_MAX


def np_enabled(cfg: dict) -> bool:
    return bool(cfg.get("paagerat_np", {}).get("quiknps_attained_age_enabled", False))


def load_np_vectors(paagerat_csv, resolver: SR.SegmentResolver, plan_allowlist: frozenset,
                    coverage_effdate: dict | None = None):
    """Attained-age net-premium vectors, segment-resolved to PLAN.

    Returns (vectors, statuses):
      vectors  {(plan, effdate, gender, uwclass, band): {attained_age: (value, raw, lineno)}}
      statuses list of non-IN_SCOPE audit dicts (same vocabulary as the PR loader)
    """
    coverage_effdate = coverage_effdate or {}
    vectors: dict[tuple, dict[int, tuple]] = {}
    statuses = []

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
            if typ != NP_TYPE_CODE:
                continue

            rec_seq = row[col["RECORD_SEQ"]].strip() if "RECORD_SEQ" in col else "1"
            if rec_seq != "1":
                statuses.append({"status": "EXCLUDED", "type_code": typ, "coverage_id": seg,
                                 "lineno": lineno,
                                 "note": f"RECORD_SEQ={rec_seq} (primary table is 1)"})
                continue

            resolved = resolver.resolve(seg, source="paagerat")
            if not resolved:
                statuses.append({"status": "SEGMENT_UNRESOLVED", "type_code": typ,
                                 "coverage_id": seg, "lineno": lineno})
                continue

            plan = resolved.plan
            if not plan or " " in plan:
                statuses.append({"status": "PLAN_INVALID", "type_code": typ, "coverage_id": seg,
                                 "plan": plan, "lineno": lineno})
                continue
            if plan not in plan_allowlist:
                statuses.append({"status": "EXCLUDED", "type_code": typ, "coverage_id": seg,
                                 "plan": plan, "lineno": lineno,
                                 "note": f"plan {plan} outside NP allowlist"})
                continue

            seq = row[col["SEQ"]].strip()
            if not seq.isdigit():
                statuses.append({"status": "BAD_VALUE", "type_code": typ, "coverage_id": seg,
                                 "plan": plan, "raw_age": seq, "lineno": lineno,
                                 "note": "non-numeric SEQ (attained age)"})
                continue

            vi = col.get("VALUE_INFO")
            vf = col.get("VALUE_FLOAT")
            raw_value = row[vi].strip() if vi is not None else row[vf].strip()
            value = _to_float(raw_value)
            if value is None:
                statuses.append({"status": "BAD_VALUE", "type_code": typ, "coverage_id": seg,
                                 "plan": plan, "raw_value": raw_value, "lineno": lineno})
                continue

            gender = S.map_sex(row[col["SEX"]].strip())
            uwclass = S.map_uwclass(row[col["UWCLS"]].strip(), plan=plan, coverage_id=seg)
            band_raw = row[col["BAND"]].strip()
            band = S.map_band(band_raw) if band_raw in S.BAND_MAP else None
            if gender is None or uwclass is None or band is None:
                statuses.append({"status": "BAD_VALUE", "type_code": typ, "coverage_id": seg,
                                 "plan": plan, "lineno": lineno,
                                 "note": "segmentation crosswalk"})
                continue

            effdate = coverage_effdate.get(seg, S.STANDARD_EFFDATE)
            key = (plan, effdate, gender, uwclass, band, band_raw, seg)
            vectors.setdefault(key, {})[int(seq)] = (value, raw_value, lineno)

    return vectors, statuses


def transform_paagerat_np(paagerat_csv, resolver: SR.SegmentResolver, config: LoaderConfig,
                          plan_allowlist: frozenset | None = None,
                          coverage_effdate: dict | None = None,
                          age_max: int | None = None):
    """Yield QuikNps cells expanded from PAAGERAT attained-age NP vectors.

    Statuses match the PR loader's vocabulary:
      IN_SCOPE | EXCLUDED | SEGMENT_UNRESOLVED | PLAN_INVALID | BAD_VALUE
    """
    allow = plan_allowlist if plan_allowlist is not None else NP_MPLAN_ALLOWLIST
    cov_eff = coverage_effdate if coverage_effdate is not None else dict(COVERAGE_EFFDATE)
    top_age = DEFAULT_ISSUE_AGE_MAX if age_max is None else age_max

    vectors, statuses = load_np_vectors(paagerat_csv, resolver, allow, cov_eff)
    for st in statuses:
        yield st

    for key, vec in sorted(vectors.items(), key=lambda kv: str(kv[0])):
        plan, effdate, gender, uwclass, band, band_raw, coverage_id = key
        if not vec:
            continue
        top_attained = max(vec)
        for age in range(0, top_age + 1):
            age2 = str(age).zfill(2)
            highest_idx = top_attained - age - ATTAINED_AGE_OFFSET
            if highest_idx < 0:
                continue
            for idx in range(0, highest_idx + 1):
                attained = age + idx + ATTAINED_AGE_OFFSET
                entry = vec.get(attained)
                if entry is None:
                    # Help p556: a grid runs from duration 00; unrated slots are 0.00.
                    value, raw_value, src_lineno = 0.0, ZERO_RAW, SYNTHETIC_LINENO
                else:
                    value, raw_value, src_lineno = entry
                cntl, col_idx = S.duration_to_cntl_col(idx)
                yield {
                    "status": "IN_SCOPE",
                    "source": "PAAGERAT",
                    "coverage_id": coverage_id,
                    "parent_coverage_id": coverage_id,
                    "segment_tier": 0,
                    "type_code": NP_TYPE_CODE,
                    "table": S.TYPE_TO_TABLE[NP_TYPE_CODE],
                    "plan": plan,
                    "age": age2,
                    "cntl": cntl,
                    "col": col_idx,
                    "gender": gender,
                    "uwclass": uwclass,
                    "band": band,
                    "source_band_raw": band_raw,
                    "isscntry": config.isscntry,
                    "issuest": config.issuest,
                    "effdate": effdate,
                    "source_duration": "1",
                    "ql_duration": idx,
                    "attained_age_slot": False,
                    "attained_age_seq": str(attained),
                    "value": value,
                    "raw_value": raw_value,
                    "lineno": src_lineno,
                    "original_age": age2,
                    "age_capped": False,
                }


def load_paagerat_np_plan_set_from_config(repo_root, cfg) -> frozenset:
    """PLAN codes that will receive an expanded attained-age QuikNps grid."""
    if not np_enabled(cfg):
        return frozenset()
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
    cov2plan, _ = load_plan_crosswalk(xwalk_path)
    resolver = SR.SegmentResolver.from_files(psgt_path, pcovr_path, cov2plan)
    vectors, _ = load_np_vectors(
        pa_path, resolver, np_mplan_allowlist(cfg), coverage_effdate_map(cfg),
    )
    return frozenset(key[0] for key in vectors)
