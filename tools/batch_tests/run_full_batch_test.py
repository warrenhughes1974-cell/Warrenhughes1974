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
os.environ.setdefault("QLA_ENABLE_QUIKBENH_LOAN_EMIT", "1")
os.environ.setdefault("QLA_QUIKBENH_LOAN_WRITE_OUTPUT", "1")
os.environ.setdefault("QLA_ENABLE_QUIKBENH_DIVIDEND_EMIT", "1")
os.environ.setdefault("QLA_QUIKBENH_DIVIDEND_WRITE_OUTPUT", "1")
os.environ.setdefault("QLA_BATCH_INCLUDE_RATE_TABLES", "1")
os.environ.setdefault("QLA_ENABLE_QUIKISRR_EMIT", "1")
os.environ.setdefault("QLA_ENABLE_REINSURANCE_EMIT", "1")
os.environ.setdefault("QLA_REINSURANCE_WRITE_OUTPUT", "1")
# Match run_converter.bat UAT UI — every emit path for training / client package
os.environ["QLA_RUN_MODE"] = "UAT"
os.environ["QLA_BATCH_INCLUDE_CLAIMS_UAT"] = "1"
os.environ["QLA_VALIDATE_CLAIMS_MPOLICY"] = "1"
os.environ["QLA_GENERATE_UAT_CLAIMS_DBF"] = "1"
os.environ["QLA_CLAIMS_ORCHESTRATE"] = "1"
os.environ["QLA_ENABLE_QUIKLOAN_EMIT"] = "1"
os.environ["QLA_QUIKLOAN_WRITE_OUTPUT"] = "1"
os.environ["QLA_ENABLE_QUIKBENH_LOAN_EMIT"] = "1"
os.environ["QLA_QUIKBENH_LOAN_WRITE_OUTPUT"] = "1"
os.environ["QLA_ENABLE_QUIKBENH_DIVIDEND_EMIT"] = "1"
os.environ["QLA_QUIKBENH_DIVIDEND_WRITE_OUTPUT"] = "1"
# Caller may override rates/product isolation (YE policy package keeps latest quikplan/rates).
os.environ.setdefault("QLA_BATCH_INCLUDE_RATE_TABLES", "1")
os.environ.setdefault("QLA_PRODUCT_SETUP_ISOLATED", "0")
os.environ["QLA_ENABLE_QUIKISRR_EMIT"] = "1"
os.environ["QLA_ENABLE_REINSURANCE_EMIT"] = "1"
os.environ["QLA_REINSURANCE_WRITE_OUTPUT"] = "1"
# Never default a current conversion to a prior valuation date. The caller
# must identify the valuation date that matches the source package being run.
_valuation_date = os.environ.get("QLA_VALUATION_DATE", "").strip()
if len(_valuation_date) != 8 or not _valuation_date.isdigit():
    raise SystemExit(
        "QLA_VALUATION_DATE is required as YYYYMMDD and must match the source "
        "package being converted (for example, 20260630 or 20260731)."
    )
os.environ["QLA_VALUATION_DATE"] = _valuation_date
# Headless batch must not pop the Desktop DBF Append Tool GUI
os.environ["QLA_LAUNCH_DBF_APPEND_TOOL"] = "0"

sys.path.insert(0, BASE)
os.chdir(BASE)

messagebox.showinfo = lambda *args, **kwargs: None
messagebox.showerror = lambda *args, **kwargs: None
messagebox.showwarning = lambda *args, **kwargs: None

from app import QLAdminEnterpriseIntegrationSuite  # noqa: E402

root = tk.Tk()
root.withdraw()
app = QLAdminEnterpriseIntegrationSuite(root)

# Select the policy extract that matches the explicitly supplied valuation date.
# Override: QLA_FORCE_PPOLC_EXTRACT=<absolute or Source-relative path>
_force_ppolc = os.environ.get("QLA_FORCE_PPOLC_EXTRACT", "").strip()
_ye_pkg = os.path.join(MIG, "Source", "12312025_Data", "PPOLC_PolicyMaster_Extract_20260102.csv")
if _valuation_date == "20251231":
    src_candidates = [
        _ye_pkg,
        os.path.join(MIG, "Source", "PPOLC_PolicyMaster_Extract_20260102.csv"),
    ]
else:
    src_candidates = [
        os.path.join(MIG, "Source", f"PPOLC_PolicyMaster_Extract_{_valuation_date}.csv"),
    ]
if _force_ppolc:
    _fp = _force_ppolc if os.path.isabs(_force_ppolc) else os.path.join(MIG, "Source", _force_ppolc)
    src_path = _fp
else:
    src_path = next((p for p in src_candidates if os.path.isfile(p)), src_candidates[0])
if not os.path.isfile(src_path):
    raise SystemExit(
        f"No PPOLC policy extract matches QLA_VALUATION_DATE={_valuation_date}: "
        f"{src_path}"
    )
if _valuation_date != "20251231" and f"_{_valuation_date}.csv" not in os.path.basename(src_path):
    raise SystemExit(
        f"Valuation/source mismatch: QLA_VALUATION_DATE={_valuation_date} "
        f"but selected policy extract is {os.path.basename(src_path)}"
    )

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
_include_rates = os.environ.get("QLA_BATCH_INCLUDE_RATE_TABLES", "0").strip().lower() in (
    "1", "true", "yes",
)
_product_isolated = os.environ.get("QLA_PRODUCT_SETUP_ISOLATED", "0").strip().lower() in (
    "1", "true", "yes",
)
if hasattr(app, "rate_include_batch_var"):
    app.rate_include_batch_var.set(_include_rates)
if hasattr(app, "rate_emit_csv_var"):
    app.rate_emit_csv_var.set(True)
if hasattr(app, "product_isolated_var"):
    app.product_isolated_var.set(_product_isolated)

print("=== QLA FULL BATCH TEST START ===", flush=True)
print(f"APP_VERSION={getattr(__import__('app', fromlist=['APP_VERSION']), 'APP_VERSION', '?')}", flush=True)
print(f"RUN_MODE={os.environ.get('QLA_RUN_MODE')}", flush=True)
print(f"INCLUDE_RATES={os.environ.get('QLA_BATCH_INCLUDE_RATE_TABLES')}", flush=True)
print(f"PRODUCT_ISOLATED={os.environ.get('QLA_PRODUCT_SETUP_ISOLATED')}", flush=True)
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
