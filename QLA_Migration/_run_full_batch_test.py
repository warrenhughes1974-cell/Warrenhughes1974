"""One-shot headless full batch test for QLA_Migration (no GUI interaction)."""
import os
import sys
import tkinter as tk
from tkinter import messagebox

BASE = r"C:\Users\warren\Documents\GitHub\Warrenhughes1974"
MIG = os.path.join(BASE, "QLA_Migration")

os.environ.setdefault("QLA_RUN_MODE", "UAT")
os.environ.setdefault("QLA_BATCH_INCLUDE_CLAIMS_UAT", "1")
os.environ.setdefault("QLA_VALIDATE_CLAIMS_MPOLICY", "1")
os.environ.setdefault("QLA_GENERATE_UAT_CLAIMS_DBF", "1")

sys.path.insert(0, BASE)
os.chdir(BASE)

messagebox.showinfo = lambda *args, **kwargs: None
messagebox.showerror = lambda *args, **kwargs: None
messagebox.showwarning = lambda *args, **kwargs: None

from app import QLAdminEnterpriseIntegrationSuite  # noqa: E402

root = tk.Tk()
root.withdraw()
app = QLAdminEnterpriseIntegrationSuite(root)

paths = {
    "Rule": os.path.join(MIG, "Configs", "Sync_Rulebook_quikplan.csv"),
    "Src": os.path.join(MIG, "Source", "quikplan.csv"),
    "Trans": os.path.join(MIG, "Mapping", "Master_Value_Translation.csv"),
    "CW": os.path.join(MIG, "Mapping", "Master_Crosswalk.csv"),
    "Rel": os.path.join(MIG, "Output", "quikclid.csv"),
    "Out": os.path.join(MIG, "Output"),
}
for key, val in paths.items():
    app.path_vars[key][0].set(val)

print("=== QLA FULL BATCH TEST START ===", flush=True)
print(f"RUN_MODE={os.environ.get('QLA_RUN_MODE')}", flush=True)
print(f"Source={paths['Src']}", flush=True)
print(f"Output={paths['Out']}", flush=True)

try:
    app.process_data(True)
    log_text = app.console.get("1.0", tk.END)
    log_path = os.path.join(MIG, "Output", "_full_batch_test_log.txt")
    with open(log_path, "w", encoding="utf-8") as fh:
        fh.write(log_text)
    print(f"Console log saved: {log_path}", flush=True)
finally:
    root.destroy()

print("=== QLA FULL BATCH TEST DONE ===", flush=True)
