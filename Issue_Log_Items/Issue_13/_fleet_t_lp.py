import os
import pandas as pd
from collections import Counter

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
ppol = pd.read_csv(
    os.path.join(ROOT, "QLA_Migration", "Source", "PPOLC_PolicyMaster_Extract_20260530.csv"),
    encoding="latin1", dtype=str, keep_default_na=False,
)
ppol.columns = [c.strip() for c in ppol.columns]
ST = {
    "ST_PUT_PU": "41", "ST_PUT_RU": "45", "ST_PUT_ET": "44", "ST_PUT_LE": "44",
    "ST_PUT_LP": "54", "ST_PUT_SP": "42", "ST_T_LP": "54", "ST_T_": "?",
}

def mstatus(cc, cr, put):
    put = put.strip().upper()
    cc = cc.strip().upper()
    cr = cr.strip().upper()
    if put in {"PU", "RU", "ET", "LE", "LP", "SP"}:
        k = f"ST_PUT_{put}"
    else:
        k = f"ST_{cc}_{cr}" if cr else f"ST_{cc}_"
    return ST.get(k, "?"), k

tlp = ppol[
    (ppol["CONTRACT_CODE"].str.strip().str.upper() == "T")
    & (ppol["CONTRACT_REASON"].str.strip().str.upper() == "LP")
]
c = Counter()
for _, r in tlp.iterrows():
    ms, k = mstatus(r["CONTRACT_CODE"], r["CONTRACT_REASON"], r.get("PAID_UP_TYPE", ""))
    put = r["PAID_UP_TYPE"].strip() or "(blank)"
    c[(put, ms, k)] += 1

print(f"T+LP fleet: {len(tlp)} policies\n")
for (put, ms, k), n in sorted(c.items(), key=lambda x: -x[1]):
    print(f"  PAID_UP_TYPE={put:8} -> key={k:12} MSTATUS={ms:3}  count={n}")
