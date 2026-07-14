"""Headless quikmstr rebatch for Issue #57 (MNFOPT rulebook + translation)."""
import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

BASE = str(Path(__file__).resolve().parents[3])
MIG = str(Path(BASE) / "QLA_Migration")

sys.path.insert(0, BASE)
os.chdir(BASE)

os.environ.setdefault("QLA_RUN_MODE", "UAT")
os.environ["QLA_BATCH_INCLUDE_CLAIMS_UAT"] = "0"
os.environ["QLA_BATCH_INCLUDE_RATE_TABLES"] = "0"
os.environ["QLA_ENABLE_QUIKISRR_EMIT"] = "0"
os.environ["QLA_ENABLE_REINSURANCE_EMIT"] = "0"
messagebox.showinfo = lambda *args, **kwargs: None
messagebox.showerror = lambda *args, **kwargs: None
messagebox.showwarning = lambda *args, **kwargs: None

from app import QLAdminEnterpriseIntegrationSuite, APP_VERSION  # noqa: E402
from qla_core.lifepro_source_resolver import resolve_table_source  # noqa: E402

root = tk.Tk()
root.withdraw()
app = QLAdminEnterpriseIntegrationSuite(root)

src_dir = os.path.join(MIG, "Source")
out_dir = os.path.join(MIG, "Output")
cfg_dir = os.path.join(MIG, "Configs")
map_dir = os.path.join(MIG, "Mapping")

ppolc_path, ppolc_label = resolve_table_source(src_dir, "quikmstr")

for key, val in {
    "Trans": os.path.join(map_dir, "Master_Value_Translation.csv"),
    "CW": os.path.join(map_dir, "Master_Crosswalk.csv"),
    "Rel": os.path.join(out_dir, "quikclid.csv"),
    "Out": out_dir,
    "Src": ppolc_path,
    "Rule": os.path.join(cfg_dir, "Sync_Rulebook_quikmstr.csv"),
}.items():
    app.path_vars[key][0].set(val)

app.table_var.set("quikmstr")

print("=== ISSUE #57 QUIKMSTR REBATCH START ===", flush=True)
print(f"APP_VERSION={APP_VERSION}", flush=True)
print(f"PPOLC={ppolc_path} ({ppolc_label})", flush=True)

try:
    app.process_data(False)
    log_path = os.path.join(MIG, "Logs", "_issue57_quikmstr_rebatch_log.txt")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as fh:
        fh.write(app.console.get("1.0", tk.END))
    print(f"Console log saved: {log_path}", flush=True)
    print("=== ISSUE #57 QUIKMSTR REBATCH COMPLETE ===", flush=True)
except Exception as exc:
    print(f"FAIL: {exc}", flush=True)
    raise
