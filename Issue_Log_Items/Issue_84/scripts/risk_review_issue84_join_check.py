"""Issue #84 Risk peer-review: verify the mismatch finding under different join keys."""
import pandas as pd

OUT = "QLA_Migration/Output/"
clms = pd.read_csv(OUT + "quikclms.csv", dtype=str, keep_default_na=False)
clmp = pd.read_csv(OUT + "quikclmp.csv", dtype=str, keep_default_na=False)
num = lambda s: pd.to_numeric(s, errors="coerce").fillna(0)
clms["MPAID_n"] = num(clms.MPAID)
clmp["MAMOUNT_n"] = num(clmp.MAMOUNT)
clms["pol"] = clms.MPOLICY.str.strip()
clmp["pol"] = clmp.MPOLICY.str.strip()
clms["ph"] = clms.MPHASE.str.strip()
clmp["ph"] = clmp.MPHASE.str.strip()

# Join by policy+phase (claim key)
pay2 = clmp.groupby(["pol", "ph"], as_index=False).agg(psum=("MAMOUNT_n", "sum"), prows=("MAMOUNT_n", "count"))
m2 = clms.merge(pay2, on=["pol", "ph"], how="left")
m2["psum"] = m2.psum.fillna(0)
m2["prows"] = m2.prows.fillna(0).astype(int)
m2["delta"] = (m2.MPAID_n - m2.psum).round(2)
haspay = m2[m2.prows > 0]
mis2 = haspay[haspay.delta.abs() > 0.01]
print("== policy+phase join ==")
print("headers with payees:", len(haspay))
print("mismatch:", len(mis2))
print("match:", len(haspay) - len(mis2))
print("header_zero:", len(haspay[(haspay.MPAID_n.abs() <= 0.01) & (haspay.psum > 0.01)]))
print("mismatch by CLAIMSTAT:", mis2.CLAIMSTAT.str.strip().value_counts().to_dict())

# Are phases unique per policy in each table?
print("\nclms dup pol+ph:", clms.duplicated(["pol", "ph"]).sum())
print("clmp payees per pol+ph max:", clmp.groupby(["pol", "ph"]).size().max())

# vs policy-only join
pay1 = clmp.groupby("pol", as_index=False).agg(psum=("MAMOUNT_n", "sum"))
m1 = clms.merge(pay1, on="pol", how="left")
m1["psum"] = m1.psum.fillna(0)
m1["delta"] = (m1.MPAID_n - m1.psum).round(2)
h1 = m1[m1.psum > 0]
print("\n== policy-only join ==")
print("mismatch:", len(h1[h1.delta.abs() > 0.01]))

# Policy-level rollup: sum of header MPAID vs sum of payees
gh = clms.groupby("pol").agg(hsum=("MPAID_n", "sum"), hn=("MPAID_n", "count"))
gp = clmp.groupby("pol").agg(psum=("MAMOUNT_n", "sum"))
g = gh.join(gp, how="inner")
g["delta"] = (g.hsum - g.psum).round(2)
print("\n== policy-level rollup (sum headers vs sum payees) ==")
print("policies:", len(g))
print("balanced:", int((g.delta.abs() <= 0.01).sum()))
print("unbalanced:", int((g.delta.abs() > 0.01).sum()))
print("unbalanced abs total:", round(g[g.delta.abs() > 0.01].delta.abs().sum(), 2))
mh = g[g.hn > 1]
print("multi-header policies:", len(mh), "balanced:", int((mh.delta.abs() <= 0.01).sum()))
sh = g[g.hn == 1]
print("single-header policies:", len(sh), "balanced:", int((sh.delta.abs() <= 0.01).sum()))

# Sample real mismatches at claim-key level with sizeable dollars
big = mis2[(mis2.psum > 0.01) & (mis2.MPAID_n > 0.01)].copy()
big["absd"] = big.delta.abs()
print("\n== claim-key mismatches with both sides nonzero (top 10 by |delta|) ==")
cols = ["pol", "ph", "CLAIMSTAT", "MPAID_n", "psum", "delta", "prows"]
print(big.sort_values("absd", ascending=False)[cols].head(10).to_string(index=False))

# Screenshot policy under claim-key join
print("\n== 010360289C ==")
print(m2[m2.pol == "010360289C"][cols].to_string(index=False))
print(clmp[clmp.pol == "010360289C"][["pol", "ph", "MCHECKNO", "MAMOUNT", "MPAYNAME"]].to_string(index=False))
