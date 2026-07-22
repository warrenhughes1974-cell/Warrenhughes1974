import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
BASE = Path(__file__).resolve().parents[1]
chg = list(
    csv.DictReader(
        open(
            BASE / "Issue_Log_Items" / "Issue_88" / "evidence" / "issue88_mprem_simulated_changes.csv",
            encoding="utf-8",
        )
    )
)
print("changes by mode", dict(Counter(c["mode"] for c in chg)))

pp = {}
with open(
    BASE / "QLA_Migration" / "Source" / "PPOLC_PolicyMaster_Extract_20260630.csv",
    newline="",
    encoding="latin1",
) as f:
    for r in csv.DictReader(f):
        r = {k.strip().upper(): (v or "").strip() for k, v in r.items()}
        pp[r["POLICY_NUMBER"]] = r

for want in ["1", "12", "3", "6"]:
    print("\nMODE", want)
    n = 0
    match_ann = 0
    checked = 0
    for c in chg:
        if c["mode"] != want:
            continue
        pol = pp.get(c["lp"], {})
        try:
            mp = float(str(pol.get("MODE_PREMIUM", "")).replace(",", "") or 0)
            ap = float(str(pol.get("ANNUAL_PREMIUM", "")).replace(",", "") or 0)
        except ValueError:
            mp = ap = 0
        checked += 1
        if abs(mp - ap) < 0.02:
            match_ann += 1
        if n < 4:
            print(
                f"  {c['qla']} units={c['units']} ph_MODE={c['mode_prem']} "
                f"PPOLC_MODE={pol.get('MODE_PREMIUM')} ANNUAL={pol.get('ANNUAL_PREMIUM')} "
                f"cur={c['current']} prop={c['proposed']}"
            )
        n += 1
    print(f"  total changes mode {want}: {n}; PPOLC MODE_PREM≈ANNUAL among samples checked first pass: see ratio")
    # full ratio for this mode
    m = a = 0
    for c in chg:
        if c["mode"] != want:
            continue
        pol = pp.get(c["lp"], {})
        try:
            mp = float(str(pol.get("MODE_PREMIUM", "")).replace(",", "") or 0)
            ap = float(str(pol.get("ANNUAL_PREMIUM", "")).replace(",", "") or 0)
        except ValueError:
            continue
        m += 1
        if abs(mp - ap) < 0.05 or (ap and abs(mp * 12 - ap) < 0.05) or (ap and abs(mp * (12 / max(float(want), 1)) - ap) < 1):
            # also check mode factor style
            pass
        if abs(mp - ap) < 0.05:
            a += 1
    print(f"  PPOLC MODE_PREMIUM == ANNUAL_PREMIUM: {a}/{m}")
