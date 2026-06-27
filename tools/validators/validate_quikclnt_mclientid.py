"""Rebuild quikclnt and validate MCLIENTID / Primary Insured linkage."""
import os
import sys
import tkinter as tk
from tkinter import messagebox

BASE = str(Path(__file__).resolve().parents[2])
MIG = os.path.join(BASE, "QLA_Migration")

os.environ.setdefault("QLA_RUN_MODE", "UAT")
sys.path.insert(0, BASE)
os.chdir(BASE)

messagebox.showinfo = lambda *a, **k: None
messagebox.showerror = lambda *a, **k: None
messagebox.showwarning = lambda *a, **k: None

from app import QLAdminEnterpriseIntegrationSuite  # noqa: E402

root = tk.Tk()
root.withdraw()
app = QLAdminEnterpriseIntegrationSuite(root)

app.path_vars["Rule"][0].set(os.path.join(MIG, "Configs", "Sync_Rulebook_quikclnt.csv"))
app.path_vars["Src"][0].set(
    os.path.join(MIG, "Source", "RelationshipNameAddress_Extract_20260403.csv")
)
app.path_vars["Trans"][0].set(os.path.join(MIG, "Mapping", "Master_Value_Translation.csv"))
app.path_vars["CW"][0].set(os.path.join(MIG, "Mapping", "Master_Crosswalk.csv"))
app.path_vars["Rel"][0].set(os.path.join(MIG, "Output", "quikclid.csv"))
app.path_vars["Out"][0].set(os.path.join(MIG, "Output"))
app.table_var.set("quikclnt")

print("=== QUIKCLNT REBUILD START ===", flush=True)
app.process_data(False)
print("=== QUIKCLNT REBUILD DONE ===", flush=True)

import pandas as pd  # noqa: E402

out = os.path.join(MIG, "Output", "quikclnt.csv")
clnt = pd.read_csv(out, dtype=str, encoding="latin1")
clnt.columns = [c.strip().upper() for c in clnt.columns]
ids = clnt["MCLIENTID"].astype(str).str.strip()
nonblank = ids[(ids != "") & (ids.str.lower() != "nan")]
print(f"quikclnt rows: {len(clnt)}")
print(f"unique non-blank MCLIENTID: {nonblank.nunique()}")

for fld in ["MADDR1", "MDOB", "MSEX", "MZIP"]:
    col = clnt[fld].astype(str).str.strip()
    blank = ((col == "") | (col.str.lower() == "nan")).sum()
    print(f"quikclnt blank {fld}: {blank}/{len(clnt)} ({100 * blank / len(clnt):.1f}%)")
    if blank > len(clnt) * 0.01:
        print(f"FAIL: more than 1% blank {fld}")
        sys.exit(1)

policy = "010335095C"
prim = "590355"
hit = clnt[clnt["MCLIENTID"].astype(str).str.strip() == prim]
if len(hit):
    r = hit.iloc[0]
    name = f"{r.get('MFNAME', '').strip()} {r.get('MLNAME', '').strip()}"
    print(f"OK  policy {policy} primary {prim}: {name}")
    for fld, label in [
        ("MADDR1", "address"), ("MDOB", "DOB"), ("MSEX", "sex"), ("MZIP", "zip"), ("MTAXID", "taxid"),
    ]:
        val = str(r.get(fld, "")).strip()
        if not val or val.lower() == "nan":
            print(f"FAIL {policy} missing {label} ({fld})")
            sys.exit(1)
        print(f"    {label}: {val}")
else:
    print(f"FAIL policy {policy} primary {prim}: not found in quikclnt")
    sys.exit(1)

# legacy spot-check from prior MCLIENTID validation
policy2 = "010445575C"
prim2 = "588835"
hit2 = clnt[clnt["MCLIENTID"].astype(str).str.strip() == prim2]
if len(hit2):
    r2 = hit2.iloc[0]
    print(f"OK  policy {policy2} primary {prim2}: {r2.get('MFNAME','').strip()} {r2.get('MLNAME','').strip()}")
else:
    print(f"WARN policy {policy2} primary {prim2}: not found")

clid = pd.read_csv(os.path.join(MIG, "Output", "quikclid.csv"), dtype=str, encoding="latin1")
clid.columns = [c.strip().upper() for c in clid.columns]
clid_ids = set(clid["MCLIENTID"].astype(str).str.strip())
clnt_ids = set(nonblank)
missing = clid_ids - clnt_ids
print(f"quikclid IDs missing from quikclnt: {len(missing)} of {len(clid_ids)}")
if len(missing) > 500:
    print("FAIL: large quikclid/quikclnt gap")
    sys.exit(1)
if missing:
    print(f"sample missing (edge cases): {list(sorted(missing))[:5]}")

m = pd.read_csv(os.path.join(MIG, "Output", "quikmstr.csv"), dtype=str, encoding="latin1")
m.columns = [c.strip().upper() for c in m.columns]
prim_ids = m["MPRIMID"].astype(str).str.strip()
prim_ids = prim_ids[(prim_ids != "") & (prim_ids.str.lower() != "nan")]
missing_prim = sum(1 for p in prim_ids if p not in clnt_ids)
pct = 100.0 * (len(prim_ids) - missing_prim) / max(len(prim_ids), 1)
print(f"quikmstr MPRIMID not in quikclnt: {missing_prim} of {len(prim_ids)} ({pct:.2f}% linked)")
if pct < 99.5:
    sys.exit(1)

print("VALIDATION PASSED")
root.destroy()
