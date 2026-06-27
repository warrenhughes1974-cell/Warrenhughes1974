"""Targeted headless validation for Issue #21 fixes (21B / 21C / 21H).

Runs single-table conversions for quikmstr then quikridr (in that order, so the
policy-fee and banking caches built during quikmstr persist for quikridr), then
prints the relevant fields for the Issue-21 example policies.

No GUI interaction; regenerates only Output/quikmstr.csv and Output/quikridr.csv.
Run:  python _validate_issue21.py
"""
import os
import sys
import csv
import tkinter as tk
from tkinter import messagebox

BASE = str(Path(__file__).resolve().parents[2])
MIG = os.path.join(BASE, "QLA_Migration")

# Keep this light: no claims orchestration for a core-table validation.
os.environ["QLA_RUN_MODE"] = "UAT"
os.environ["QLA_BATCH_INCLUDE_CLAIMS_UAT"] = "0"
os.environ["QLA_VALIDATE_CLAIMS_MPOLICY"] = "0"
os.environ["QLA_GENERATE_UAT_CLAIMS_DBF"] = "0"
os.environ["QLA_CLAIMS_ORCHESTRATE"] = "0"

sys.path.insert(0, BASE)
os.chdir(BASE)
messagebox.showinfo = lambda *a, **k: None
messagebox.showerror = lambda *a, **k: None
messagebox.showwarning = lambda *a, **k: None

# Load the REPO-ROOT engine (the file run_converter.bat actually executes).
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("qla_root_app", os.path.join(BASE, "app.py"))
_mod = importlib.util.module_from_spec(_spec)
sys.modules["qla_root_app"] = _mod
_spec.loader.exec_module(_mod)
QLAdminEnterpriseIntegrationSuite = _mod.QLAdminEnterpriseIntegrationSuite
print("LOADED ENGINE:", _mod.__file__, flush=True)

root = tk.Tk()
root.withdraw()
app = QLAdminEnterpriseIntegrationSuite(root)

app.path_vars["Trans"][0].set(os.path.join(MIG, "Mapping", "Master_Value_Translation.csv"))
app.path_vars["CW"][0].set(os.path.join(MIG, "Mapping", "Master_Crosswalk.csv"))
app.path_vars["Rel"][0].set(os.path.join(MIG, "Output", "quikclid.csv"))
app.path_vars["Out"][0].set(os.path.join(MIG, "Output"))


def run_single(table, rulebook, source):
    app.table_var.set(table)
    app.path_vars["Rule"][0].set(os.path.join(MIG, "Configs", rulebook))
    app.path_vars["Src"][0].set(os.path.join(MIG, "Source", source))
    print(f"\n=== RUN {table} (src={source}) ===", flush=True)
    app.process_data(False)
    log = app.console.get("1.0", tk.END)
    for line in log.splitlines():
        if any(k in line for k in ["ABA routing lookup", "Policy Fee Cache", "PPACH Banking Cache",
                                   "full-ABA", "Could not load", "MANNLFEE", "POLICY FEE"]):
            print("   LOG:", line.strip(), flush=True)


try:
    run_single("quikmstr", "Sync_Rulebook_quikmstr.csv", "quikmstr.csv")
    run_single("quikridr", "Sync_Rulebook_quikridr.csv", "PPBEN.csv")
finally:
    root.destroy()

print("\n=== VALIDATION READOUT ===", flush=True)
OUT = os.path.join(MIG, "Output")


def show(table, cols, match):
    path = os.path.join(OUT, table)
    if not os.path.isfile(path):
        print(f"  MISSING: {path}")
        return
    with open(path, encoding="latin1", newline="") as fh:
        r = csv.DictReader(fh)
        n = 0
        for row in r:
            if match(row):
                print("  " + " | ".join(f"{c}={row.get(c)!r}" for c in cols))
                n += 1
        print(f"  ({n} matched rows in {table})")


print("[21B Bill Day + 21H Banking] quikmstr — example policies:")
show("quikmstr.csv", ["MPOLICY", "MBILLDAY", "MBANKNO"],
     lambda r: (r.get("MPOLICY") or "").strip() in ("010713704C", "010391876C", "010818663C", "010765930C", "010718309C"))

print("[21C Policy Fee] quikridr — base rows (MPHASE 1) for example policies:")
show("quikridr.csv", ["MPOLICY", "MPHASE", "MANNLFEE"],
     lambda r: (r.get("MPOLICY") or "").strip() in ("010713704C", "010391876C") and (r.get("MPHASE") or "").strip() in ("1", "01"))

# Aggregate health
with open(os.path.join(OUT, "quikmstr.csv"), encoding="latin1", newline="") as fh:
    rows = list(csv.DictReader(fh))
nine = sum(1 for r in rows if (r.get("MBANKNO") or "").split("/")[0].isdigit() and len((r.get("MBANKNO") or "").split("/")[0]) == 9)
banked = sum(1 for r in rows if (r.get("MBANKNO") or "").strip())
print(f"\nquikmstr: {banked} rows with MBANKNO; {nine} with 9-digit ABA")
with open(os.path.join(OUT, "quikridr.csv"), encoding="latin1", newline="") as fh:
    rr = list(csv.DictReader(fh))
fee = sum(1 for r in rr if (r.get("MANNLFEE") or "").strip() not in ("", "0", "0.00"))
base = sum(1 for r in rr if (r.get("MPHASE") or "").strip() in ("1", "01"))
print(f"quikridr: {len(rr)} rows; base(MPHASE1)={base}; MANNLFEE populated={fee}")
print("=== DONE ===", flush=True)
