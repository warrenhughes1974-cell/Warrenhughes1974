"""Build the PSUBSSEG substitution emit scope CSV (reviewed manifest for the loader).

Derives era-banded emit entries for CV/RV/NP from PSUBSSEG (0831) + PCOVRSGT defaults
+ PPBEN in-force policies, then filters to entries the current pipeline does not
already cover. PR/premium slots are excluded (deferred; see Planning Report OI-3).

Rules per (coverage, type):
  * Era runs: PSUBSSEG band dates sorted, consecutive same-target bands merged.
  * Covered (skip): run target == PCOVRSGT default segment AND the plan already
    emits rows in that Output table AND the reconciliation value spot-check
    (psubsseg_reconciliation.csv emit_value_overlap) is 1.0 or blank — i.e. the
    standard 19000101 generation demonstrably IS that data.
  * Sandwich rule: once any earlier run is scoped for emit, every later covered
    run must also be emitted at its band date, otherwise QLAdmin's
    latest-EFFDATE<=issue rule would serve the earlier band to that era.
  * EFFDATE: 19000101 when the FIRST run's target equals the default segment
    (whole-history data that simply never emitted); otherwise the run's first
    LifePRO band date verbatim (QLAdmin picks latest EFFDATE <= issue date).
  * SOURCE_MODE: PLAN_COPY:<plan> when the source segment resolves via the plan
    crosswalk to a plan already emitting that table (grid copy, value-identical);
    otherwise EXTRACT (Rate_Table / merged PDAGE page expansion).
  * Deferred (reported, not scoped): source rows absent from Rate_Table and PDAGE
    (e.g. PAAGE/PAAGERAT attained-age segments), and runs with zero in-force
    policies and no sandwich obligation.

Writes: psubsseg_substitution_scope.csv (loader manifest) + scope build report JSON.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)

from qla_core.rate_factor_loader import load_plan_crosswalk  # noqa: E402
from qla_core.plan_source_paths import policy_form_crosswalk  # noqa: E402

ISSUE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SOURCE = os.path.join(ROOT, "QLA_Migration", "Source")

PSUBSSEG_CSV = os.path.join(SOURCE, "PSUBSSEG_SubstituteSegment_Extract_20260831.csv")
PCOVRSGT_CSV = os.path.join(ROOT, "plan_analysis", "source_data", "coverage", "PCOVRSGT.csv")
PPBEN_CSV = os.path.join(SOURCE, "PPBEN_PolicyBenefit_Extract_20260630.csv")
RATE_TABLE_CSV = os.path.join(ROOT, "plan_analysis", "source_data", "rates",
                              "Rate_Table_Extract_20260427.csv")
OUT_SCOPE = os.path.join(ISSUE_DIR, "psubsseg_substitution_scope.csv")
OUT_REPORT = os.path.join(ISSUE_DIR, "evidence", "psubsseg_scope_build_report.json")

SEQ_TO_TYPE = {2: "CV", 12: "RV", 13: "NP"}  # PR (SEQ 1) deferred
TYPE_TO_OUTPUT = {"CV": "QuikCvs.csv", "RV": "QuikTvs.csv", "NP": "QuikNps.csv"}
STANDARD_EFFDATE = "19000101"


def load_rows(path):
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        rd = csv.reader(f)
        hdr = [h.strip() for h in next(rd)]
        for row in rd:
            row = [c.strip() for c in row]
            if row and row[0] and set(row[0]) <= {"-"}:
                continue
            yield dict(zip(hdr, row))


def load_bands():
    """cov -> {date: {type: segt_id}}; sex-specific conflicts collected separately."""
    bands = defaultdict(lambda: defaultdict(dict))
    sex_conflicts = []
    seen = defaultdict(dict)  # (cov, date, typ) -> {sex: seg}
    for x in load_rows(PSUBSSEG_CSV):
        if x.get("TYPE_FLAG") not in ("0", ""):
            continue
        try:
            seq = int(x["SEQ"])
        except ValueError:
            continue
        if seq not in SEQ_TO_TYPE or x["SEGT_FLAG"] != "Y" or not x["SEGT_ID"]:
            continue
        cov, sex, date = x["COVERAGE_ID"], (x.get("SEX_CODE") or "@"), int(x["ISSUE_DATE"])
        typ, seg = SEQ_TO_TYPE[seq], x["SEGT_ID"]
        slot = seen[(cov, date, typ)]
        slot[sex] = seg
        if len({s for s in slot.values()}) > 1:
            sex_conflicts.append({"coverage": cov, "date": date, "type": typ,
                                  "by_sex": dict(slot)})
        bands[cov][date][typ] = seg
    return bands, sex_conflicts


def load_defaults():
    defaults = defaultdict(dict)
    for x in load_rows(PCOVRSGT_CSV):
        if x.get("SEGT_FLAG") != "Y" or not x.get("SEGT_ID"):
            continue
        try:
            seq = int(x["SEQ"])
        except ValueError:
            continue
        if seq in SEQ_TO_TYPE:
            defaults[x["COVERAGE_ID"]][SEQ_TO_TYPE[seq]] = x["SEGT_ID"]
    return defaults


def load_source_presence():
    """(segment, type) -> set of families with rows (Rate_Table / PDAGE, dated merged)."""
    import glob
    avail = defaultdict(set)
    for x in load_rows(RATE_TABLE_CSV):
        avail[(x["COVERAGE_ID"], x["TYPE_CODE"])].add("Rate_Table")
    for fp in glob.glob(os.path.join(SOURCE, "PDAGE_*Extract*.csv")):
        for x in load_rows(fp):
            avail[(x["COVERAGE_ID"], x["TYPE_CODE"])].add("PDAGE")
    return avail


def load_emitted_plan_counts():
    out = {}
    rates_dir = os.path.join(ROOT, "QLA_Migration", "Output", "rates")
    for typ, fn in TYPE_TO_OUTPUT.items():
        counts = defaultdict(int)
        fp = os.path.join(rates_dir, fn)
        if os.path.isfile(fp):
            with open(fp, newline="", encoding="utf-8-sig", errors="replace") as f:
                for row in csv.DictReader(f):
                    plan = (row.get("PLAN") or "").strip()
                    if plan:
                        counts[plan] += 1
        out[typ] = counts
    return out


def load_recon_overlaps():
    """(cov, typ, expected_segment) -> emit_value_overlap string ('' when blank)."""
    path = os.path.join(ISSUE_DIR, "evidence", "psubsseg_reconciliation.csv")
    out = {}
    if not os.path.isfile(path):
        return out
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[(r["coverage_id"], r["rate_type"], r["expected_segment"])] = \
                (r.get("emit_value_overlap") or "").strip()
    return out


def load_policy_issues():
    """cov -> sorted list of (issue_date, active) for in-force benefit rows."""
    out = defaultdict(list)
    for x in load_rows(PPBEN_CSV):
        cov = x.get("PLAN_CODE", "")
        try:
            idt = int(x.get("ISSUE_DATE", ""))
        except ValueError:
            continue
        active = (x.get("STATUS_CODE") or "").startswith("A")
        out[cov].append((idt, active))
    return out


def main():
    os.makedirs(os.path.dirname(OUT_REPORT), exist_ok=True)
    cov2plan, _ = load_plan_crosswalk(policy_form_crosswalk())
    bands, sex_conflicts = load_bands()
    defaults = load_defaults()
    avail = load_source_presence()
    emitted = load_emitted_plan_counts()
    policies = load_policy_issues()
    overlaps = load_recon_overlaps()

    scope_rows = []
    deferred = []
    skipped_covered = []
    for cov in sorted(bands):
        plan = cov2plan.get(cov, "")
        pol = sorted(policies.get(cov, []))
        if not plan or not pol:
            continue
        # per type: era runs
        by_type = defaultdict(list)  # typ -> [(date, seg)]
        for date in sorted(bands[cov]):
            for typ, seg in bands[cov][date].items():
                by_type[typ].append((date, seg))
        for typ, eras in by_type.items():
            default_seg = defaults.get(cov, {}).get(typ, cov)
            # merge consecutive same-target
            runs = []
            for date, seg in eras:
                if runs and runs[-1]["seg"] == seg:
                    runs[-1]["end"] = date
                    continue
                runs.append({"start": date, "end": date, "seg": seg})
            scoped_earlier = False
            for i, run in enumerate(runs):
                nxt = runs[i + 1]["start"] if i + 1 < len(runs) else None
                n = n_act = 0
                for idt, active in pol:
                    if idt >= run["start"] and (nxt is None or idt < nxt):
                        n += 1
                        n_act += int(active)
                ovl = overlaps.get((cov, typ, run["seg"]), "")
                covered = (
                    run["seg"] == default_seg
                    and emitted[typ].get(plan, 0) > 0
                    and ovl in ("", "1.0")
                )
                # PLAN_COPY (self): only when the recon proved the issuing plan's
                # current base generation already carries this run's target values
                # (emit_value_overlap == 1.0). Used by sandwich re-emits.
                if ovl == "1.0" and emitted[typ].get(plan, 0) > 0:
                    source_mode = f"PLAN_COPY:{plan}"
                else:
                    source_mode = "EXTRACT"
                rec = {
                    "ISSUING_COVERAGE": cov,
                    "ISSUING_PLAN": plan,
                    "RATE_TYPE": typ,
                    "EFFDATE": (STANDARD_EFFDATE
                                if (i == 0 and run["seg"] == default_seg)
                                else str(run["start"])),
                    "SOURCE_SEGMENT": run["seg"],
                    "SOURCE_MODE": source_mode,
                    "BAND_START": run["start"],
                    "POLICIES": n,
                    "ACTIVE_POLICIES": n_act,
                    "SOURCE_FAMILIES": ";".join(sorted(avail.get((run["seg"], typ), set()))),
                }
                if covered:
                    if scoped_earlier:
                        # sandwich rule: a covered era after a scoped era must
                        # re-emit at its band date to terminate the earlier band
                        rec["SANDWICH"] = "Y"
                        scope_rows.append(rec)
                    else:
                        skipped_covered.append(rec)
                    continue
                if rec["EFFDATE"] == STANDARD_EFFDATE and emitted[typ].get(plan, 0) > 0:
                    # whole-history replacement of an already-emitted base
                    # generation: material valuation call — report, do not scope
                    # (additive-only loader; base 19000101 rows stay untouched)
                    rec["DEFER_REASON"] = (
                        f"REPLACEMENT_REVIEW: base generation emitted from other "
                        f"segment (overlap={ovl or 'n/a'}) — needs valuation proof"
                    )
                    deferred.append(rec)
                    continue
                if n == 0 and not scoped_earlier:
                    rec["DEFER_REASON"] = "no in-force policies in era"
                    deferred.append(rec)
                    continue
                if source_mode == "EXTRACT" and not avail.get((run["seg"], typ)):
                    rec["DEFER_REASON"] = "no Rate_Table/PDAGE rows (attained-age or absent)"
                    deferred.append(rec)
                    continue
                scope_rows.append(rec)
                scoped_earlier = True

    fieldnames = ["ISSUING_COVERAGE", "ISSUING_PLAN", "RATE_TYPE", "EFFDATE",
                  "SOURCE_SEGMENT", "SOURCE_MODE", "BAND_START", "POLICIES",
                  "ACTIVE_POLICIES", "SOURCE_FAMILIES", "SANDWICH"]
    with open(OUT_SCOPE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in scope_rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})

    report = {
        "psubsseg": os.path.basename(PSUBSSEG_CSV),
        "scope_entries": len(scope_rows),
        "scope_plans": sorted({r["ISSUING_PLAN"] for r in scope_rows}),
        "scope_active_policies": sum(r["ACTIVE_POLICIES"] for r in scope_rows),
        "skipped_covered": len(skipped_covered),
        "deferred": deferred,
        "sex_specific_conflicts": sex_conflicts,
    }
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"scope entries: {len(scope_rows)} -> {OUT_SCOPE}")
    for r in scope_rows:
        print("  {ISSUING_COVERAGE:11s} {ISSUING_PLAN:8s} {RATE_TYPE} EFFDATE={EFFDATE} "
              "<- {SOURCE_SEGMENT:11s} [{SOURCE_MODE}]{sw} pol={POLICIES}/{ACTIVE_POLICIES} "
              "src={SOURCE_FAMILIES}".format(
                  sw=" SANDWICH" if r.get("SANDWICH") else "", **r))
    print(f"skipped covered: {len(skipped_covered)}; deferred: {len(deferred)}; "
          f"sex conflicts: {len(sex_conflicts)}")
    for d in deferred:
        print("  DEFER {ISSUING_COVERAGE:11s} {RATE_TYPE} {SOURCE_SEGMENT:11s} "
              "eff={EFFDATE} pol={POLICIES}/{ACTIVE_POLICIES}: {DEFER_REASON}".format(**d))


if __name__ == "__main__":
    main()
