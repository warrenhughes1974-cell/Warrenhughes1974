"""Issue #48 Risk — read-only PLAN+TYPE ownership / collision simulation.

No production code changes. Quantifies:
  1) Path wiring row delta (expect 0 — identical Rate_Table bytes)
  2) PLAN+TYPE pairs owned by PAAGERAT (after segment resolve)
  3) PLAN+TYPE pairs owned by Rate_Table (direct crosswalk)
  4) Overlap = collision / suppress candidates under A1
"""
from __future__ import annotations

import csv
import hashlib
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qla_core import rate_factor_loader as L  # noqa: E402
from qla_core import rate_segment_resolution as SR  # noqa: E402
from qla_core import rate_dbf_schema as S  # noqa: E402

RT = ROOT / "QLA_Migration" / "Source" / "Rate_Table_Extract_Txt.txt"
RT_TWIN = ROOT / "plan_analysis" / "source_data" / "rates" / "Rate_Table_Extract_20260427.csv"
PAA = ROOT / "QLA_Migration" / "Source" / "PAAGERAT_AttainedAge_Rates_Extract_20260630.csv"
PSGT = ROOT / "QLA_Migration" / "Source" / "PCOVRSGT_CoverageSegment_Extract_20260630.csv"
PCOVR = ROOT / "QLA_Migration" / "Source" / "PCOVR_Coverage_Extract_20260630.csv"
XWALK = ROOT / "plan_analysis" / "source_data" / "crosswalk" / "Policy Form Crosswalk 5.22.26.xlsx"
EVID = Path(__file__).resolve().parent / "evidence"

SHARED = frozenset({"PR", "NP", "CV", "RV", "NF", "DB"})
ISWL_BP = frozenset({"1658CS", "1659CS", "1669SR", "1679CS"})


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_rate_table(path: Path, cov2plan: dict) -> dict:
    """Return {(plan, type): {rows, coverages}} for shared TYPE_TO_TABLE types."""
    out = defaultdict(lambda: {"rows": 0, "coverages": set(), "unmapped_rows": 0})
    with path.open(encoding="utf-8", errors="replace") as f:
        f.readline()
        f.readline()
        for line in f:
            p = [x.strip() for x in line.split(",")]
            if len(p) < 2:
                continue
            cov, tc = p[0], p[1]
            if tc not in SHARED or tc not in S.TYPE_TO_TABLE:
                continue
            plan = cov2plan.get(cov)
            if not plan:
                out[("__UNMAPPED__", tc)]["unmapped_rows"] += 1
                out[("__UNMAPPED__", tc)]["coverages"].add(cov)
                continue
            rec = out[(plan, tc)]
            rec["rows"] += 1
            rec["coverages"].add(cov)
    return out


def scan_paagerat(path: Path, resolver: SR.SegmentResolver) -> dict:
    """Return {(plan, type): {rows, segments, unresolved}} for shared types."""
    out = defaultdict(
        lambda: {"rows": 0, "segments": set(), "unresolved_rows": 0, "unresolved_segs": set()}
    )
    with path.open(encoding="utf-8", errors="replace", newline="") as f:
        rd = csv.reader(f)
        hdr = [c.strip() for c in next(rd)]
        # skip separator if present
        first = next(rd, None)
        if first and first[0].startswith("-"):
            pass
        else:
            # process first data row
            if first:
                _consume_paa_row(first, hdr, resolver, out)
        for row in rd:
            _consume_paa_row(row, hdr, resolver, out)
    return out


def _consume_paa_row(row, hdr, resolver, out):
    if len(row) < 2:
        return
    col = {n: i for i, n in enumerate(hdr)}
    try:
        cov = row[col["COVERAGE_ID"]].strip()
        tc = row[col["TYPE_CODE"]].strip()
    except (KeyError, IndexError):
        cov, tc = row[0].strip(), row[1].strip()
    if tc not in SHARED:
        return
    resolved = resolver.resolve(cov, source="paagerat")
    if not resolved or not getattr(resolved, "plan", None):
        out[("__UNRESOLVED__", tc)]["unresolved_rows"] += 1
        out[("__UNRESOLVED__", tc)]["unresolved_segs"].add(cov)
        return
    plan = str(resolved.plan).strip()
    rec = out[(plan, tc)]
    rec["rows"] += 1
    rec["segments"].add(cov)


def main():
    EVID.mkdir(parents=True, exist_ok=True)
    cov2plan, _ = L.load_plan_crosswalk(str(XWALK))
    resolver = SR.SegmentResolver.from_files(str(PSGT), str(PCOVR), cov2plan)

    rt_md5 = md5(RT)
    twin_md5 = md5(RT_TWIN)
    path_delta_rows = 0 if rt_md5 == twin_md5 else -1

    print("MD5 RT", rt_md5)
    print("MD5 twin", twin_md5)
    print("path_wiring_row_delta", path_delta_rows)

    print("Scanning Rate_Table...")
    rt = scan_rate_table(RT, cov2plan)
    print("Scanning PAAGERAT...")
    paa = scan_paagerat(PAA, resolver)

    rt_keys = {k for k in rt if not str(k[0]).startswith("__")}
    paa_keys = {k for k in paa if not str(k[0]).startswith("__")}
    both = sorted(rt_keys & paa_keys)
    only_rt = sorted(rt_keys - paa_keys)
    only_paa = sorted(paa_keys - rt_keys)

    print(f"RT PLAN+TYPE={len(rt_keys)} PAA={len(paa_keys)} both={len(both)} only_RT={len(only_rt)} only_PAA={len(only_paa)}")

    by_tc = Counter()
    for plan, tc in both:
        by_tc[tc] += 1
    print("overlap by TYPE:", dict(by_tc))

    # ISWL BP suppress intersection
    iswl_hits = [(p, t) for p, t in both if p in ISWL_BP]
    print("ISWL BP plan overlaps:", iswl_hits)

    # Write collision candidates
    coll_path = EVID / "issue48_risk_collision_candidates.csv"
    with coll_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "plan",
                "type_code",
                "target_table",
                "rt_rows",
                "paa_rows",
                "rt_coverages",
                "paa_segments",
                "iswl_bp_plan",
                "proposed_action",
            ],
        )
        w.writeheader()
        for plan, tc in both:
            w.writerow(
                {
                    "plan": plan,
                    "type_code": tc,
                    "target_table": S.TYPE_TO_TABLE.get(tc, ""),
                    "rt_rows": rt[(plan, tc)]["rows"],
                    "paa_rows": paa[(plan, tc)]["rows"],
                    "rt_coverages": "|".join(sorted(rt[(plan, tc)]["coverages"])),
                    "paa_segments": "|".join(sorted(paa[(plan, tc)]["segments"])),
                    "iswl_bp_plan": "Y" if plan in ISWL_BP else "N",
                    "proposed_action": "SUPPRESS_RATE_TABLE_KEEP_PAAGERAT",
                }
            )

    # Secondary-used candidates (only RT)
    sec_path = EVID / "issue48_risk_secondary_candidates.csv"
    with sec_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["plan", "type_code", "target_table", "rt_rows", "rt_coverages", "proposed_action"],
        )
        w.writeheader()
        for plan, tc in only_rt:
            w.writerow(
                {
                    "plan": plan,
                    "type_code": tc,
                    "target_table": S.TYPE_TO_TABLE.get(tc, ""),
                    "rt_rows": rt[(plan, tc)]["rows"],
                    "rt_coverages": "|".join(sorted(rt[(plan, tc)]["coverages"])),
                    "proposed_action": "EMIT_RATE_TABLE_TAG_SECONDARY",
                }
            )

    # Summary
    rt_rows_both = sum(rt[k]["rows"] for k in both)
    paa_rows_both = sum(paa[k]["rows"] for k in both)
    rt_rows_only = sum(rt[k]["rows"] for k in only_rt)
    summary = {
        "path_wiring_md5_match": rt_md5 == twin_md5,
        "path_wiring_row_delta": path_delta_rows,
        "rt_plan_type_keys": len(rt_keys),
        "paa_plan_type_keys": len(paa_keys),
        "collision_plan_type_keys": len(both),
        "collision_by_type": dict(by_tc),
        "rt_rows_on_collision_keys": rt_rows_both,
        "paa_rows_on_collision_keys": paa_rows_both,
        "secondary_only_plan_type_keys": len(only_rt),
        "secondary_only_rt_rows": rt_rows_only,
        "paa_only_plan_type_keys": len(only_paa),
        "iswl_bp_collision_keys": len(iswl_hits),
        "unmapped_rt_pr_note": "see secondary CSV for DISCHO/L01",
    }
    sum_path = EVID / "issue48_risk_impact_summary.csv"
    with sum_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["metric", "value"])
        w.writeheader()
        for k, v in summary.items():
            w.writerow({"metric": k, "value": v})

    print("Wrote", coll_path)
    print("Wrote", sec_path)
    print("Wrote", sum_path)
    print("SUMMARY", summary)
    if both[:20]:
        print("Sample collisions:")
        for k in both[:20]:
            print(" ", k, "RT", rt[k]["rows"], "PAA", paa[k]["rows"])


if __name__ == "__main__":
    main()
