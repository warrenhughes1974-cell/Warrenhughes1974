"""
Issue #88 Risk — read-only simulation: blank ANN_PREM_PER_UNIT fallback
  current: MODE_PREMIUM (total)
  proposed: MODE_PREMIUM / NUMBER_OF_UNITS (when units > 0)

Usage:
  python QLA_Migration/_risk_review_issue88_mprem_unit_fallback.py
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SRC = BASE / "QLA_Migration" / "Source"
OUT = BASE / "QLA_Migration" / "Output"
CW = BASE / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
EVID = BASE / "Issue_Log_Items" / "Issue_88" / "evidence"
EVID.mkdir(parents=True, exist_ok=True)

PPBEN = SRC / "PPBEN_PolicyBenefit_Extract_20260630.csv"
PPOLC = SRC / "PPOLC_PolicyMaster_Extract_20260630.csv"
RIDR = OUT / "quikridr.csv"

TRACE = ["010779727C", "010310404C", "010331768C", "010367131C"]


def fnum(v):
    try:
        s = str(v).replace(",", "").strip()
        if s == "" or s.lower() == "nan":
            return None
        return float(s)
    except (TypeError, ValueError):
        return None


def load_csv(path: Path):
    with open(path, newline="", encoding="latin1", errors="replace") as f:
        r = csv.DictReader(f)
        rows = []
        for row in r:
            rows.append({(k or "").strip().upper(): (v or "").strip() for k, v in row.items()})
        return rows


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("Loading ...")
    ppben = load_csv(PPBEN)
    ppolc = {r["POLICY_NUMBER"]: r for r in load_csv(PPOLC)}
    ridr = load_csv(RIDR)
    cw_rows = load_csv(CW) if CW.exists() else []
    # Master_Crosswalk may be headerless
    if not cw_rows or "POLICY_NUMBER" in (list(cw_rows[0].keys())[0] if cw_rows else ""):
        pass
    cw = {}
    with open(CW, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.reader(f):
            if len(row) < 2:
                continue
            lp, ql = row[0].strip(), row[1].strip()
            if lp and ql and lp.lower() != "policy_number":
                cw[lp] = ql

    ridr_ix = {(r["MPOLICY"], str(int(float(r["MPHASE"]))) if fnum(r.get("MPHASE")) is not None else r.get("MPHASE", "")): r for r in ridr}

    stats = Counter()
    by_mode = Counter()
    by_mode_blank = Counter()
    by_units_bucket = Counter()
    changes = []
    zero_unit_blank = 0
    ann_pop_ok = 0
    blank_fallback_change = 0
    blank_fallback_same = 0  # units==1 or mode_prem/units ~= current

    for src in ppben:
        lp = src.get("POLICY_NUMBER", "")
        ql = cw.get(lp)
        if not ql:
            stats["no_crosswalk"] += 1
            continue
        seq = src.get("BENEFIT_SEQ", "")
        try:
            phase = str(int(float(seq)))
        except (TypeError, ValueError):
            phase = seq.lstrip("0") or "0"

        ann = fnum(src.get("ANN_PREM_PER_UNIT"))
        mode_prem = fnum(src.get("MODE_PREMIUM"))
        units = fnum(src.get("NUMBER_OF_UNITS"))
        pol = ppolc.get(lp, {})
        bill_mode = fnum(pol.get("BILLING_MODE"))

        out = ridr_ix.get((ql, phase))
        if not out:
            stats["no_quikridr"] += 1
            continue

        current = fnum(out.get("MPREM"))
        mode_code = bill_mode

        stats["joined"] += 1
        mode_key = str(int(mode_code)) if mode_code is not None else "UNK"
        by_mode[mode_key] += 1

        ann_blank = ann is None or abs(ann) < 1e-12
        if not ann_blank:
            proposed = ann
            stats["ann_populated"] += 1
            # primary path: should already match current within tolerance
            if current is not None and abs(proposed - current) <= 0.01:
                ann_pop_ok += 1
            else:
                stats["ann_pop_mismatch_current"] += 1
        else:
            stats["ann_blank"] += 1
            by_mode_blank[mode_key] += 1
            if units is None or units <= 0:
                zero_unit_blank += 1
                proposed = None  # cannot divide
                stats["blank_zero_units"] += 1
            else:
                if mode_prem is None:
                    proposed = None
                    stats["blank_no_mode_prem"] += 1
                else:
                    proposed = mode_prem / units
                    stats["blank_mode_per_unit"] += 1
                    ub = "1" if abs(units - 1) < 1e-9 else ("1-25" if units <= 25 else ("25-100" if units <= 100 else ">100"))
                    by_units_bucket[ub] += 1

        if proposed is None:
            stats["proposed_null"] += 1
            continue

        cur = current if current is not None else 0.0
        delta = proposed - cur
        if abs(delta) > 0.01:
            stats["would_change"] += 1
            if ann_blank:
                blank_fallback_change += 1
            changes.append(
                {
                    "qla": ql,
                    "lp": lp,
                    "phase": phase,
                    "plan": out.get("MPLAN", src.get("PLAN_CODE", "")),
                    "mode": mode_key,
                    "units": units,
                    "ann": ann,
                    "mode_prem": mode_prem,
                    "current": current,
                    "proposed": round(proposed, 6) if proposed is not None else None,
                    "delta": round(delta, 6),
                    "ann_blank": ann_blank,
                    "reconstruct": round((proposed or 0) * (units or 0), 2) if units else None,
                }
            )
        else:
            stats["unchanged"] += 1
            if ann_blank:
                blank_fallback_same += 1

    # Write changes CSV
    chg_path = EVID / "issue88_mprem_simulated_changes.csv"
    fields = ["qla", "lp", "phase", "plan", "mode", "units", "ann", "mode_prem", "current", "proposed", "delta", "ann_blank", "reconstruct"]
    with open(chg_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in sorted(changes, key=lambda x: -abs(x["delta"] or 0)):
            w.writerow(row)

    # Trace
    print("\n=== TRACE ===")
    for t in TRACE:
        hits = [c for c in changes if c["qla"] == t] + [
            # also show unchanged traces from ppben join
        ]
        # always print from source+output
        for src in ppben:
            ql = cw.get(src.get("POLICY_NUMBER", ""))
            if ql != t:
                continue
            phase = str(int(float(src["BENEFIT_SEQ"]))) if fnum(src.get("BENEFIT_SEQ")) is not None else src.get("BENEFIT_SEQ")
            out = ridr_ix.get((ql, phase), {})
            ann = fnum(src.get("ANN_PREM_PER_UNIT"))
            mp = fnum(src.get("MODE_PREMIUM"))
            u = fnum(src.get("NUMBER_OF_UNITS"))
            cur = fnum(out.get("MPREM"))
            prop = ann if ann not in (None, 0.0) and abs(ann or 0) > 1e-12 else ((mp / u) if mp is not None and u and u > 0 else None)
            print(f"  {ql} ph{phase}: ANN={ann} MODE_PREM={mp} units={u} current_MPREM={cur} proposed={prop}")

    print("\n=== STATS ===")
    for k, v in stats.most_common():
        print(f"  {k}: {v}")
    print("\nMode dist (all joined):", dict(by_mode))
    print("Mode dist (blank ANN):", dict(by_mode_blank))
    print("Blank ANN unit buckets:", dict(by_units_bucket))
    print(f"blank_fallback_change={blank_fallback_change} blank_fallback_same={blank_fallback_same} zero_unit_blank={zero_unit_blank}")
    print(f"changes file: {chg_path} ({len(changes)} rows)")

    # Summary helpers for report
    top = sorted(changes, key=lambda x: -abs(x["delta"] or 0))[:20]
    print("\n=== TOP 20 |delta| ===")
    for c in top:
        print(f"  {c['qla']} ph{c['phase']} units={c['units']} mode={c['mode']} {c['current']} -> {c['proposed']} (d={c['delta']})")

    # Save summary json-like text
    sum_path = EVID / "issue88_risk_sim_summary.txt"
    with open(sum_path, "w", encoding="utf-8") as f:
        f.write(f"stats={dict(stats)}\n")
        f.write(f"by_mode={dict(by_mode)}\n")
        f.write(f"by_mode_blank={dict(by_mode_blank)}\n")
        f.write(f"by_units_bucket={dict(by_units_bucket)}\n")
        f.write(f"changes={len(changes)}\n")
    print("Wrote", sum_path)


if __name__ == "__main__":
    main()
