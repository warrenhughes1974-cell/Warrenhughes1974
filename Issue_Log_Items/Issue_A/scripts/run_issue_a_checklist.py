"""Issue A conversion checklist evaluator against current Output (read-only)."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "QLA_Migration" / "Output"
RATES = OUT / "rates"

plan = list(csv.DictReader((OUT / "quikplan.csv").open(encoding="utf-8-sig")))
print(f"quikplan rows: {len(plan)}")

# A1 — single premium DESCR set
sp_codes = {"1668SP", "10L171", "10L172", "1L17SP"}
a1_fail = []
for r in plan:
    if r.get("DESCR", "").strip() not in sp_codes and r.get("PLAN", "").strip() not in sp_codes:
        # also match PLAN code
        if r.get("PLAN", "").strip() not in sp_codes:
            continue
    code = r.get("PLAN", "").strip()
    if code not in sp_codes and r.get("DESCR", "").strip() not in sp_codes:
        continue
for r in plan:
    code = r.get("PLAN", "").strip()
    if code not in sp_codes:
        continue
    payyrs = (r.get("PAYYRS") or "").strip()
    modes = {k: (r.get(k) or "").strip() for k in ("SEMI", "QTRL", "MTHD", "MTHB")}
    bad = []
    if payyrs not in ("1", "1.0", "01"):
        bad.append(f"PAYYRS={payyrs}")
    for k, v in modes.items():
        try:
            if float(v or 0) != 0.0:
                bad.append(f"{k}={v}")
        except ValueError:
            bad.append(f"{k}={v}")
    if bad:
        a1_fail.append(f"{code}: {', '.join(bad)}")
print(f"A1 single-prem: {'PASS' if not a1_fail else 'FAIL'} checked={len(sp_codes)} fails={len(a1_fail)}")
for x in a1_fail[:10]:
    print(" ", x)

# A2 — DEFICIENCY (informational; OPEN awaiting CSO)
defic = Counter((r.get("DEFICIENCY") or r.get("DEFCY") or "").strip() for r in plan)
# column may be named differently
def_cols = [c for c in plan[0] if "DEF" in c.upper()]
print(f"A2 deficiency cols={def_cols} counts={ {c: Counter((r.get(c) or '').strip() for r in plan) for c in def_cols} }")

# A4 — blank PLAN in rates
blank = 0
rate_files = list(RATES.glob("QuikPl*.csv")) + list(RATES.glob("QuikPI*.csv")) if RATES.is_dir() else []
for p in rate_files:
    for r in csv.DictReader(p.open(encoding="utf-8-sig")):
        if not (r.get("PLAN") or "").strip():
            blank += 1
print(f"A4 blank PLAN in QuikPl*/QuikPI*: {'PASS' if blank == 0 else 'FAIL'} blank={blank} files={len(rate_files)}")

# A8a / A8b / A9b annuity + supp PAR
ann = [r for r in plan if r.get("PLAN", "").startswith("A")]
supp = [r for r in plan if r.get("PLAN", "").startswith("9")]
a8a = [r["PLAN"] for r in ann if (r.get("PAR") or "").strip() not in ("0", "0.0", "")]
a8b = [r["PLAN"] for r in ann if (r.get("VARDB") or "").strip() not in ("0", "0.0", "")]
a9b = [r["PLAN"] for r in supp if (r.get("PAR") or "").strip() not in ("0", "0.0", "")]
print(f"A8a annuity PAR=0: {'PASS' if not a8a else 'FAIL'} ann={len(ann)} bad={a8a}")
print(f"A8b annuity VARDB=0: {'PASS' if not a8b else 'FAIL'} bad={a8b}")
print(f"A9b supp9 PAR=0: {'PASS' if not a9b else 'FAIL'} supp={len(supp)} bad={a9b[:10]}")

# A10 QuikUwpo
uwpo = RATES / "QuikUwpo.csv"
if uwpo.is_file():
    uw = list(csv.DictReader(uwpo.open(encoding="utf-8-sig")))
    codes = [(r.get("UWCODE") or r.get("UW") or list(r.values())[0] or "").strip() for r in uw]
    print(f"A10 QuikUwpo: PASS rows={len(uw)} codes={codes}")
else:
    print("A10 QuikUwpo: FAIL missing Output/rates/QuikUwpo.csv")

# A7 VARGP informational
vargp4_with_gp = 0  # can't fully check without rate keys; report VARGP=4 count
print(f"A7 VARGP=4 plans: {sum(1 for r in plan if (r.get('VARGP') or '').strip() == '4')} / {len(plan)} (OPEN item)")
