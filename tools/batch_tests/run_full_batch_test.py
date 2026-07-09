"""One-shot headless full batch test for QLA_Migration (no GUI interaction)."""
from pathlib import Path
import os
import sys
import tkinter as tk
from tkinter import messagebox

BASE = str(Path(__file__).resolve().parents[2])
MIG = str(Path(BASE) / "QLA_Migration")

os.environ.setdefault("QLA_RUN_MODE", "UAT")
os.environ.setdefault("QLA_BATCH_INCLUDE_CLAIMS_UAT", "1")
os.environ.setdefault("QLA_VALIDATE_CLAIMS_MPOLICY", "1")
os.environ.setdefault("QLA_GENERATE_UAT_CLAIMS_DBF", "1")
os.environ.setdefault("QLA_CLAIMS_ORCHESTRATE", "1")
os.environ.setdefault("QLA_ENABLE_QUIKLOAN_EMIT", "1")
os.environ.setdefault("QLA_QUIKLOAN_WRITE_OUTPUT", "1")
os.environ.setdefault("QLA_BATCH_INCLUDE_RATE_TABLES", "1")
os.environ.setdefault("QLA_ENABLE_QUIKISRR_EMIT", "1")
os.environ.setdefault("QLA_ENABLE_REINSURANCE_EMIT", "1")
os.environ.setdefault("QLA_REINSURANCE_WRITE_OUTPUT", "1")

sys.path.insert(0, BASE)
os.chdir(BASE)

messagebox.showinfo = lambda *args, **kwargs: None
messagebox.showerror = lambda *args, **kwargs: None
messagebox.showwarning = lambda *args, **kwargs: None

from app import QLAdminEnterpriseIntegrationSuite  # noqa: E402

root = tk.Tk()
root.withdraw()
app = QLAdminEnterpriseIntegrationSuite(root)

# Prefer dated PolicyMaster extract; fall back to any PPOLC*.csv in Source.
src_candidates = [
    os.path.join(MIG, "Source", "PPOLC_PolicyMaster_Extract_20260630.csv"),
    os.path.join(MIG, "Source", "PPOLC_PolicyMaster_Extract_20260530.csv"),
]
src_path = next((p for p in src_candidates if os.path.isfile(p)), src_candidates[0])
if not os.path.isfile(src_path):
    for name in sorted(os.listdir(os.path.join(MIG, "Source"))):
        if name.upper().startswith("PPOLC") and name.lower().endswith(".csv"):
            src_path = os.path.join(MIG, "Source", name)
            break

paths = {
    "Rule": os.path.join(MIG, "Configs", "Sync_Rulebook_quikplan.csv"),
    "Src": src_path,
    "Trans": os.path.join(MIG, "Mapping", "Master_Value_Translation.csv"),
    "CW": os.path.join(MIG, "Mapping", "Master_Crosswalk.csv"),
    "Rel": os.path.join(MIG, "Output", "quikclid.csv"),
    "Out": os.path.join(MIG, "Output"),
}
for key, val in paths.items():
    app.path_vars[key][0].set(val)

# Mirror UAT launcher: include rates in full batch when env flag is set.
if hasattr(app, "rate_include_batch_var"):
    app.rate_include_batch_var.set(
        os.environ.get("QLA_BATCH_INCLUDE_RATE_TABLES", "0").strip().lower() in ("1", "true", "yes")
    )
if hasattr(app, "rate_emit_csv_var"):
    app.rate_emit_csv_var.set(True)

print("=== QLA FULL BATCH TEST START ===", flush=True)
print(f"APP_VERSION={getattr(__import__('app', fromlist=['APP_VERSION']), 'APP_VERSION', '?')}", flush=True)
print(f"RUN_MODE={os.environ.get('QLA_RUN_MODE')}", flush=True)
print(f"INCLUDE_RATES={os.environ.get('QLA_BATCH_INCLUDE_RATE_TABLES')}", flush=True)
print(f"Source={paths['Src']}", flush=True)
print(f"Output={paths['Out']}", flush=True)

try:
    app.process_data(True)
    log_text = app.console.get("1.0", tk.END)
    log_path = os.path.join(MIG, "Logs", "_full_batch_test_log.txt")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as fh:
        fh.write(log_text)
    print(f"Console log saved: {log_path}", flush=True)
finally:
    root.destroy()

print("=== QLA FULL BATCH TEST DONE ===", flush=True)
