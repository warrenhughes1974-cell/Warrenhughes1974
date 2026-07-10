"""Headless quikmstr + quikridr rebatch for Issue #49 (correct per-table source/rulebook)."""
from pathlib import Path
import os
import sys
import tkinter as tk
from tkinter import messagebox

BASE = str(Path(__file__).resolve().parents[2])
MIG = str(Path(BASE) / "QLA_Migration")

os.environ.setdefault("QLA_RUN_MODE", "UAT")
os.environ["QLA_BATCH_INCLUDE_CLAIMS_UAT"] = "0"
os.environ["QLA_BATCH_INCLUDE_RATE_TABLES"] = "0"
os.environ["QLA_ENABLE_QUIKISRR_EMIT"] = "0"
os.environ["QLA_ENABLE_REINSURANCE_EMIT"] = "0"

sys.path.insert(0, BASE)
os.chdir(BASE)

messagebox.showinfo = lambda *args, **kwargs: None
messagebox.showerror = lambda *args, **kwargs: None
messagebox.showwarning = lambda *args, **kwargs: None

from app import QLAdminEnterpriseIntegrationSuite, APP_VERSION  # noqa: E402
from qla_core.lifepro_source_resolver import resolve_table_source  # noqa: E402
from qla_core.issue21_open_item_decisions import resolve_ppben_path  # noqa: E402

root = tk.Tk()
root.withdraw()
app = QLAdminEnterpriseIntegrationSuite(root)

src_dir = os.path.join(MIG, "Source")
out_dir = os.path.join(MIG, "Output")
cfg_dir = os.path.join(MIG, "Configs")
map_dir = os.path.join(MIG, "Mapping")

ppolc_path, ppolc_label = resolve_table_source(src_dir, "quikmstr")
ppben = resolve_ppben_path(src_dir)
if not ppben:
    ppben_path, _ = resolve_table_source(src_dir, "quikridr")
    ppben = ppben_path
ppolc = ppolc_path

common = {
    "Trans": os.path.join(map_dir, "Master_Value_Translation.csv"),
    "CW": os.path.join(map_dir, "Master_Crosswalk.csv"),
    "Rel": os.path.join(out_dir, "quikclid.csv"),
    "Out": out_dir,
}
for key, val in common.items():
    app.path_vars[key][0].set(val)

jobs = [
    ("quikmstr", ppolc, os.path.join(cfg_dir, "Sync_Rulebook_quikmstr.csv")),
    ("quikridr", ppben, os.path.join(cfg_dir, "Sync_Rulebook_quikridr.csv")),
]

print("=== ISSUE #49 QUIKMSTR+QUIKRIDR REBATCH START ===", flush=True)
print(f"APP_VERSION={APP_VERSION}", flush=True)
print(f"PPOLC={ppolc} ({ppolc_label})", flush=True)
print(f"PPBEN={ppben}", flush=True)

try:
    for table, src, rule in jobs:
        if not src or not os.path.isfile(src):
            raise FileNotFoundError(f"Missing source for {table}: {src}")
        if not os.path.isfile(rule):
            raise FileNotFoundError(f"Missing rulebook for {table}: {rule}")
        app.path_vars["Src"][0].set(src)
        app.path_vars["Rule"][0].set(rule)
        app.table_var.set(table)
        print(f"--- converting {table} ---", flush=True)
        print(f"  Src={src}", flush=True)
        print(f"  Rule={rule}", flush=True)
        app.process_data(False)
    log_text = app.console.get("1.0", tk.END)
    log_path = os.path.join(MIG, "Logs", "_issue49_quikmstr_quikridr_rebatch_log.txt")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as fh:
        fh.write(log_text)
    print(f"Console log saved: {log_path}", flush=True)
finally:
    root.destroy()

print("=== ISSUE #49 REBATCH DONE ===", flush=True)
