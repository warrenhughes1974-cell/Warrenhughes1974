"""Headless Single Table conversion — quikplan only (Issue A A1 verify)."""
from __future__ import annotations

import csv
import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

BASE = str(Path(__file__).resolve().parents[3])
MIG = str(Path(BASE) / "QLA_Migration")

os.environ.setdefault("QLA_RUN_MODE", "UAT")

sys.path.insert(0, BASE)
os.chdir(BASE)

messagebox.showinfo = lambda *args, **kwargs: None
messagebox.showerror = lambda *args, **kwargs: None
messagebox.showwarning = lambda *args, **kwargs: None

from app import APP_VERSION, QLAdminEnterpriseIntegrationSuite  # noqa: E402

SP_PLANS = ("1668SP", "10L171", "10L172", "1L17SP")


def check_a1(out_csv: Path) -> None:
    with out_csv.open(newline="", encoding="utf-8-sig") as f:
        rows = {r["PLAN"]: r for r in csv.DictReader(f)}
    print("\n=== Issue A A1 check (quikplan) ===")
    for plan in SP_PLANS:
        r = rows.get(plan)
        if not r:
            print(f"  {plan}: MISSING")
            continue
        ok = (
            str(r.get("PAYYRS", "")).strip() in ("1", "01", "1.0")
            and all(float(r.get(c) or 0) == 0.0 for c in ("SEMI", "QTRL", "MTHD", "MTHB"))
        )
        print(
            f"  {plan}: PAYYRS={r.get('PAYYRS')} "
            f"S/Q/M/B={r.get('SEMI')}/{r.get('QTRL')}/{r.get('MTHD')}/{r.get('MTHB')} "
            f"{'PASS' if ok else 'FAIL'}"
        )


def main() -> int:
    root = tk.Tk()
    root.withdraw()
    app = QLAdminEnterpriseIntegrationSuite(root)
    app.table_var.set("quikplan")
    app.on_table_select()

    print("=== QLA SINGLE TABLE (quikplan) START ===", flush=True)
    print(f"APP_VERSION={APP_VERSION}", flush=True)
    print(f"Rule={app.path_vars['Rule'][0].get()}", flush=True)
    print(f"Source={app.path_vars['Src'][0].get()}", flush=True)
    print(f"Output={app.path_vars['Out'][0].get()}", flush=True)

    try:
        app.process_data(False)
        log_text = app.console.get("1.0", tk.END)
        log_path = Path(MIG) / "Logs" / "_single_quikplan_test_log.txt"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(log_text, encoding="utf-8")
        print(f"Console log saved: {log_path}", flush=True)
    finally:
        root.destroy()

    out_csv = Path(app.path_vars["Out"][0].get()) / "quikplan.csv"
    if out_csv.is_file():
        print(f"Wrote: {out_csv}", flush=True)
        check_a1(out_csv)
    else:
        print(f"ERROR: {out_csv} not found", flush=True)
        return 1

    print("=== QLA SINGLE TABLE (quikplan) DONE ===", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
