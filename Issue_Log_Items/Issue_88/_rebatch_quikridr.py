"""Headless quikridr-only rebatch for Issue #88 (no commit)."""
import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

BASE = str(Path(__file__).resolve().parents[2])
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
from qla_core.issue21_open_item_decisions import resolve_ppben_path  # noqa: E402
from qla_core.lifepro_source_resolver import resolve_table_source  # noqa: E402

root = tk.Tk()
root.withdraw()
app = QLAdminEnterpriseIntegrationSuite(root)

src_dir = os.path.join(MIG, "Source")
out_dir = os.path.join(MIG, "Output")
cfg_dir = os.path.join(MIG, "Configs")
map_dir = os.path.join(MIG, "Mapping")

ppben = resolve_ppben_path(src_dir)
if not ppben:
    ppben, _ = resolve_table_source(src_dir, "quikridr")

app.path_vars["Trans"][0].set(os.path.join(map_dir, "Master_Value_Translation.csv"))
app.path_vars["CW"][0].set(os.path.join(map_dir, "Master_Crosswalk.csv"))
app.path_vars["Rel"][0].set(os.path.join(out_dir, "quikclid.csv"))
app.path_vars["Out"][0].set(out_dir)
app.path_vars["Src"][0].set(ppben)
app.path_vars["Rule"][0].set(os.path.join(cfg_dir, "Sync_Rulebook_quikridr.csv"))
app.table_var.set("quikridr")

print("=== ISSUE #88 QUIKRIDR REBATCH START ===", flush=True)
print(f"APP_VERSION={APP_VERSION}", flush=True)
print(f"PPBEN={ppben}", flush=True)

app.process_data(False)
log_text = app.console.get("1.0", tk.END)
log_path = os.path.join(MIG, "Logs", "_issue88_quikridr_rebatch_log.txt")
os.makedirs(os.path.dirname(log_path), exist_ok=True)
with open(log_path, "w", encoding="utf-8") as fh:
    fh.write(log_text)
print(f"Console log saved: {log_path}", flush=True)
print("=== ISSUE #88 QUIKRIDR REBATCH DONE ===", flush=True)
root.destroy()
