#!/usr/bin/env python3
"""Issue #36 G5 supplemental evidence (read-only)."""
from __future__ import annotations

import os
import re

import pandas as pd

OUT = os.path.join("QLA_Migration", "Output")
m = pd.read_csv(os.path.join(OUT, "quikmstr.csv"), dtype=str, encoding="latin1").fillna("")
r = pd.read_csv(os.path.join(OUT, "quikridr.csv"), dtype=str, encoding="latin1").fillna("")
qp = pd.read_csv(os.path.join(OUT, "quikplan.csv"), dtype=str, encoding="latin1").fillna("")

print("ROWCOUNTS", "mstr", len(m), "ridr", len(r), "plan", len(qp))
w = m["MPOLICY"].astype(str).str.len()
print("MPOLICY width min/max/ne10", int(w.min()), int(w.max()), int((w != 10).sum()))
print("MMODEPREM blank", int((m["MMODEPREM"].str.strip() == "").sum()))
print("MPREM blank", int((r["MPREM"].str.strip() == "").sum()), "of", len(r))

samples = [
    "010560185C",
    "010396186C",
    "010459011C",
    "010442216C",
    "010473868C",
    "010449334C",
    "010488273C",
]
p1 = r[r["MPHASE"].isin(["1", "01"])][["MPOLICY", "MPLAN"]].drop_duplicates("MPOLICY")
x = m.merge(p1, on="MPOLICY", how="left")
print("--- client PAC samples ---")
for pol in samples:
    row = x[x["MPOLICY"].str.strip() == pol]
    if row.empty:
        print(pol, "MISSING")
        continue
    row = row.iloc[0]
    print(
        pol,
        "plan",
        row["MPLAN"],
        "mode",
        row["MMODE"],
        "bill",
        row["MBILLFRM"],
        "S",
        row["MSEMI"],
        "Q",
        row["MQTRL"],
        "D",
        row["MMTHD"],
        "B",
        row["MMTHB"],
        "prem",
        row["MMODEPREM"],
    )

row = x[x["MPOLICY"].str.strip() == "010148856C"].iloc[0]
fr = qp[qp["PLAN"] == row["MPLAN"]].iloc[0]
print(
    "010148856C vs plan match",
    row["MSEMI"] == fr["SEMI"],
    row["MQTRL"] == fr["QTRL"],
    row["MMTHD"] == fr["MTHD"],
    row["MMTHB"] == fr["MTHB"],
)

# All PAC Q/S list
pac = x[
    (x["MPLAN"].isin(["170858", "17085M"]))
    & (x["MBILLFRM"].astype(str).str.strip().isin(["2", "PAC"]))
]
mode = pac["MMODE"].astype(str).str.replace(r"\.0$", "", regex=True).str.lstrip("0")
q = pac[mode == "3"]
s = pac[mode == "6"]
print("PAC Q policies:")
print(q[["MPOLICY", "MPLAN", "MMODE", "MQTRL", "MSEMI"]].to_string(index=False))
print("PAC S policies:")
print(s[["MPOLICY", "MPLAN", "MMODE", "MSEMI", "MQTRL"]].to_string(index=False))

for p in ["app.py", os.path.join("QLA_Migration", "app.py")]:
    text = open(p, encoding="utf-8", errors="replace").read()
    mver = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', text)
    print(p, mver.group(1) if mver else "?")
