"""Issue #169 Development — prove the 667 ART net-premium layout before emitting.

667 ART's net premiums arrive as a 1-D attained-age vector (PAAGERAT SEQ = attained
age). QuikNps is an issue-age x duration grid and, unlike QuikGps/QuikDbs, has no
quikplan VARY field to tell QLAdmin to read a slot axis as attained age
("NP_VARIATION_FIELDS_NOT_CREATED ... excluded by design"). So the vector has to be
expanded: NP[issue_age][duration] = vector[issue_age + duration + offset].

This finds the offset empirically from LifePRO's own valuation output rather than
assuming one. Reference identity established at #168 review section 1.3:

    RV_VALUATION_PREMIUM = net premium x units
    RV_MEAN_RV           = RV_VALUATION_PREMIUM / 2

Read-only.
"""
from __future__ import annotations

import collections
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "docs", "Valuation", "analysis"))

import quikvalf_dbf as QV  # noqa: E402
import valx_layout as VL  # noqa: E402

PAAGERAT = os.path.join(ROOT, "QLA_Migration", "Source",
                        "PAAGERAT_AttainedAge_Rates_Extract_20260831.csv")
PLAN = "5667AT"
COVERAGES = {"667 ART", "667 ART 95"}


def load_np_vectors():
    """(coverage, sex, uwcls) -> {seq_int: value}"""
    vecs: dict[tuple, dict[int, float]] = collections.defaultdict(dict)
    with open(PAAGERAT, encoding="utf-8-sig", errors="replace") as fh:
        hdr = [h.strip() for h in fh.readline().strip().split(",")]
        idx = {n: i for i, n in enumerate(hdr)}
        for line in fh:
            p = line.split(",")
            if len(p) < len(hdr) - 4:
                continue
            if p[idx["TYPE_CODE"]].strip() != "NP":
                continue
            cov = p[idx["COVERAGE_ID"]].strip()
            if cov not in COVERAGES:
                continue
            seq = p[idx["SEQ"]].strip()
            if not seq.isdigit():
                continue
            raw = p[idx.get("VALUE_INFO", idx.get("VALUE_FLOAT"))].strip()
            try:
                val = float(raw)
            except ValueError:
                continue
            key = (cov, p[idx["SEX"]].strip(), p[idx["UWCLS"]].strip())
            vecs[key][int(seq)] = val
    return vecs, hdr


def main() -> int:
    vecs, hdr = load_np_vectors()
    print("PAAGERAT columns:", hdr[:10])
    print()
    print("667 ART net-premium vectors (attained-age SEQ):")
    for key in sorted(vecs):
        seqs = sorted(vecs[key])
        print("   {:<12} sex={!r} uwcls={!r}  {} points, SEQ {}..{}".format(
            key[0], key[1], key[2], len(seqs), seqs[0], seqs[-1]))
    print()

    lifepro = {}
    for rec in VL.read_records():
        pol = str(rec.get("POLICY_NUMBER") or "").strip()
        seq = str(rec.get("BENEFIT_SEQ") or "").strip()
        try:
            seq_i = int(seq)
        except ValueError:
            seq_i = 0
        lifepro[(pol, seq_i)] = rec

    valf = QV.load()
    rows = [r for r in valf.valued if QV.plan_code(r) == PLAN]
    print("{} valued rows for {}".format(len(rows), PLAN))

    sample = None
    cases = []
    for r in rows:
        lp = lifepro.get((QV.lifepro_policy(r), QV.phase_of(r)))
        if not lp:
            continue
        if sample is None:
            sample = lp
        def num(field):
            try:
                return float(lp.get(field) or 0)
            except (TypeError, ValueError):
                return 0.0
        units = num("NUMBER_OF_UNITS")
        mean = num("RV_MEAN_RV")
        if units <= 0 or mean <= 0:
            continue
        cases.append({
            "policy": QV.policy_of(r),
            "age": int(QV.money(r, "MAGE")),
            "dur": int(QV.money(r, "MDUR")),
            "sex": QV.text(r, "MSEX"),
            "units": units,
            "mean": mean,
            "np_implied": mean * 2.0 / units,
        })

    if sample is not None:
        interesting = [k for k in sample
                       if any(t in k.upper() for t in ("UNIT", "PREM", "AGE", "MEAN", "DUR"))]
        print("VALXLIFE fields available:", sorted(interesting))
    print("usable cases (units>0, LifePRO reserve>0):", len(cases))
    print()

    # Which vector/offset reproduces LifePRO's implied net premium?
    print("Offset search — matches within 1 cent of implied net premium:")
    header = "{:<14}{:<6}{:<8}{}".format("COVERAGE", "SEX", "UWCLS", "".join(
        "{:>10}".format("off " + str(o)) for o in range(-3, 4)))
    print(header)
    print("-" * len(header))
    best = None
    for key in sorted(vecs):
        vec = vecs[key]
        counts = []
        for off in range(-3, 4):
            hit = 0
            for c in cases:
                want = vec.get(c["age"] + c["dur"] + off)
                if want is not None and abs(want - c["np_implied"]) <= 0.01:
                    hit += 1
            counts.append(hit)
            if best is None or hit > best[0]:
                best = (hit, key, off)
        print("{:<14}{:<6}{:<8}{}".format(
            key[0], key[1] or "-", key[2] or "-",
            "".join("{:>10}".format(c) for c in counts)))

    print()
    if best and best[0]:
        hits, key, off = best
        print("BEST: {} sex={!r} uwcls={!r} offset {:+d} -> {}/{} cases".format(
            key[0], key[1], key[2], off, hits, len(cases)))
        print()
        print("Worked examples:")
        vec = vecs[key]
        shown = 0
        for c in cases:
            v = vec.get(c["age"] + c["dur"] + off)
            if v is not None and abs(v - c["np_implied"]) <= 0.01 and shown < 6:
                print("   {} age={:<3} dur={:<3} sex={} units={:>7.2f}  LifePRO mean={:>10.2f}"
                      "  implied NP={:>8.4f}  vector[{}]={:>8.4f}".format(
                          c["policy"], c["age"], c["dur"], c["sex"], c["units"],
                          c["mean"], c["np_implied"], c["age"] + c["dur"] + off, v))
                shown += 1
    else:
        print("NO OFFSET REPRODUCES LifePRO. Do not emit — the layout assumption is wrong.")
        print()
        print("Implied net premiums vs the vectors, first 8 cases:")
        for c in cases[:8]:
            print("   {} age={} dur={} attained={} implied NP={:.4f}".format(
                c["policy"], c["age"], c["dur"], c["age"] + c["dur"], c["np_implied"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
