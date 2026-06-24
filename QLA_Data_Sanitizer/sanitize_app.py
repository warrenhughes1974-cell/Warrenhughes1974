# =============================================================================
# QLAdmin Data Sanitizer — Standalone Application
# =============================================================================
# Version:     v1.2
# All tool files live in this folder (QLA_Data_Sanitizer/). Does not use app.py.
# =============================================================================

import json
import os
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext, ttk

_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOL_DIR not in sys.path:
    sys.path.insert(0, _TOOL_DIR)

import sanitize_test_data as ST

APP_VERSION = "v1.2"
_REPO_ROOT = os.path.normpath(os.path.join(_TOOL_DIR, ".."))
_LEGACY_SOURCE = os.path.join(_REPO_ROOT, "QLA_Migration", "Source")


def _default_input_dir():
    local = os.path.join(_TOOL_DIR, "Input")
    if os.path.isdir(_LEGACY_SOURCE) and any(
        f.lower().endswith(ext) for f in os.listdir(_LEGACY_SOURCE) for ext in (".csv", ".dbf")
    ):
        return _LEGACY_SOURCE
    os.makedirs(local, exist_ok=True)
    return local


def _default_output_dir():
    out = os.path.join(_TOOL_DIR, "Output")
    os.makedirs(out, exist_ok=True)
    return out


DEFAULT_INPUT = _default_input_dir()
DEFAULT_OUTPUT = _default_output_dir()
DEFAULT_RULES = ST.DEFAULT_RULES_PATH


class ReplaceOptionsDialog(tk.Toplevel):
    """Set a fixed replacement value per sanitize pattern (instead of MASK/FAKE)."""

    def __init__(self, parent, rules_path, enabled, values):
        super().__init__(parent)
        self.title("Replace options")
        self.geometry("720x520")
        self.minsize(600, 400)
        self.result = None
        self._value_vars = {}

        tk.Label(
            self,
            text="Enter a value for each pattern. Non-empty values replace ALL non-blank "
            "cells in matching columns (instead of MASK/FAKE).",
            wraplength=680,
            justify="left",
            font=("Segoe UI", 9),
        ).pack(padx=12, pady=(10, 4), anchor="w")

        self.enabled_var = tk.BooleanVar(value=enabled)
        tk.Checkbutton(
            self,
            text="Enable replace mode",
            variable=self.enabled_var,
            font=("Segoe UI", 9, "bold"),
        ).pack(padx=12, anchor="w")

        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=12, pady=8)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        hdr = tk.Frame(inner)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Pattern", width=28, anchor="w", font=("Segoe UI", 8, "bold")).grid(row=0, column=0)
        tk.Label(hdr, text="Rule", width=8, anchor="w", font=("Segoe UI", 8, "bold")).grid(row=0, column=1)
        tk.Label(hdr, text="Replace with", width=36, anchor="w", font=("Segoe UI", 8, "bold")).grid(row=0, column=2)

        try:
            rules = ST.load_rules(rules_path)
            patterns = ST.list_sanitize_patterns(rules)
        except (OSError, json.JSONDecodeError) as exc:
            tk.Label(inner, text=f"Cannot load rules: {exc}", fg="red").pack()
            patterns = []

        for i, entry in enumerate(patterns, start=1):
            match = entry.get("match", "")
            rule_type = entry.get("type", "")
            row = tk.Frame(inner)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=match, width=28, anchor="w", font=("Consolas", 8)).grid(row=0, column=0, sticky="w")
            tk.Label(row, text=rule_type, width=8, anchor="w", font=("Segoe UI", 8)).grid(row=0, column=1, sticky="w")
            var = tk.StringVar(value=values.get(match, ""))
            self._value_vars[match] = var
            tk.Entry(row, textvariable=var, width=42, bg="#F8FAFC").grid(row=0, column=2, padx=4)

        btns = tk.Frame(self)
        btns.pack(pady=10)
        tk.Button(btns, text="OK", width=10, command=self._ok).pack(side="left", padx=6)
        tk.Button(btns, text="Cancel", width=10, command=self.destroy).pack(side="left", padx=6)
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _ok(self):
        overrides = {}
        if self.enabled_var.get():
            for match, var in self._value_vars.items():
                val = var.get().strip()
                if val:
                    overrides[match] = val
        self.result = (self.enabled_var.get(), overrides)
        self.destroy()


class QLAdminDataSanitizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"QLAdmin Data Sanitizer {APP_VERSION}")
        self.root.geometry("1000x720")
        self.root.minsize(900, 600)

        self.bg_main = "#F1F5F9"
        self.bg_card = "#FFFFFF"
        self.accent = "#0F172A"
        self.btn_run = "#7C3AED"
        self.btn_single = "#2563EB"
        self.text_color = "#334155"
        self.stage_ok = "#059669"
        self.stage_err = "#DC2626"
        self.root.configure(bg=self.bg_main)

        self.is_running = False
        self.start_time = None
        self._last_result = None

        self.input_var = tk.StringVar(value=DEFAULT_INPUT)
        self.output_var = tk.StringVar(value=DEFAULT_OUTPUT)
        self.rules_var = tk.StringVar(value=DEFAULT_RULES if os.path.isfile(DEFAULT_RULES) else "")
        self.patterns_var = tk.StringVar(value="*.csv,*.dbf")
        self.single_in_var = tk.StringVar()
        self.single_out_var = tk.StringVar()
        self.replace_enabled = False
        self.replace_overrides = {}

        self._build_ui()
        self._verify_environment()

    def _verify_environment(self):
        caps = ST.engine_capabilities()
        self.log(f"Engine: {caps.get('engine_version', 'UNKNOWN')} @ {caps.get('script_path', '')}")
        if caps.get("engine_version") != "1.2.0":
            self.log("WARNING: sanitize_test_data.py is outdated (need engine 1.2.0).")
            self._set_status("Outdated engine — copy full QLA_Data_Sanitizer folder", ok=False)
            messagebox.showwarning(
                "Outdated sanitizer engine",
                "This folder's sanitize_test_data.py does not include DBF support.\n\n"
                "Copy the entire QLA_Data_Sanitizer folder from the repo, then run:\n"
                "pip install -r requirements.txt",
            )
            return
        if not caps.get("dbf_support"):
            self.log("WARNING: Python package 'dbf' not installed.")
            self._set_status("Missing dependency: pip install -r requirements.txt", ok=False)
            messagebox.showwarning(
                "Missing dependency",
                "Install DBF support:\n\n"
                f"cd {_TOOL_DIR}\n"
                "pip install -r requirements.txt",
            )
            return
        self.log("DBF support: enabled")

    def _build_ui(self):
        header = tk.Frame(self.root, bg=self.bg_main)
        header.pack(fill="x", pady=(14, 8))
        tk.Label(
            header,
            text=f"QLADMIN DATA SANITIZER {APP_VERSION}",
            font=("Segoe UI", 18, "bold"),
            bg=self.bg_main,
            fg=self.accent,
        ).pack()
        tk.Label(
            header,
            text=f"Tool folder: {_TOOL_DIR}",
            font=("Segoe UI", 9),
            bg=self.bg_main,
            fg=self.text_color,
        ).pack()

        info = tk.LabelFrame(
            self.root,
            text=" What this tool does ",
            bg=self.bg_card,
            fg=self.accent,
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=8,
        )
        info.pack(padx=28, fill="x", pady=4)
        tk.Label(
            info,
            justify="left",
            bg=self.bg_card,
            fg=self.text_color,
            font=("Segoe UI", 9),
            text=(
                "• Default: PRESERVE all columns (policy IDs, amounts, dates, codes, join keys)\n"
                "• Sanitize only PII matched in config/field_masking_rules.json\n"
                "• MASK / FAKE are deterministic; row counts and CSV/DBF structure preserved\n"
                "• DBF: character fields only; dates/logicals/numerics unchanged\n"
                "• Crosswalk files are copied unchanged (see skip_files in rules JSON)\n"
                "• Replace mode: set fixed values per pattern (REPLACE OPTIONS button)"
            ),
        ).pack(anchor="w")

        paths = tk.LabelFrame(
            self.root,
            text=" Paths ",
            bg=self.bg_card,
            fg=self.accent,
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=10,
        )
        paths.pack(padx=28, fill="x", pady=6)

        rows = [
            (self.input_var, "folder", "Input directory (source CSV/DBF):"),
            (self.output_var, "folder", "Output directory (sanitized copy):"),
            (self.rules_var, "file", "Masking rules (JSON):"),
        ]
        for i, (var, mode, label) in enumerate(rows):
            tk.Label(paths, text=label, bg=self.bg_card, fg=self.text_color, font=("Segoe UI", 9, "bold")).grid(
                row=i, column=0, sticky="w", pady=4,
            )
            tk.Entry(paths, textvariable=var, width=88, bg="#F8FAFC").grid(row=i, column=1, padx=10)
            tk.Button(
                paths,
                text="Browse",
                width=9,
                command=lambda v=var, m=mode: self._browse(v, m),
            ).grid(row=i, column=2)

        tk.Label(paths, text="Batch file patterns:", bg=self.bg_card, fg=self.text_color, font=("Segoe UI", 9, "bold")).grid(
            row=3, column=0, sticky="w", pady=4,
        )
        tk.Entry(paths, textvariable=self.patterns_var, width=40, bg="#F8FAFC").grid(row=3, column=1, sticky="w", padx=10)

        single = tk.LabelFrame(
            self.root,
            text=" Single file (optional) ",
            bg=self.bg_card,
            fg=self.accent,
            font=("Segoe UI", 9, "bold"),
            padx=16,
            pady=8,
        )
        single.pack(padx=28, fill="x", pady=4)
        tk.Label(single, text="Input file:", bg=self.bg_card, fg=self.text_color).grid(row=0, column=0, sticky="w")
        tk.Entry(single, textvariable=self.single_in_var, width=70, bg="#F8FAFC").grid(row=0, column=1, padx=8)
        tk.Button(single, text="Browse", command=lambda: self._browse(self.single_in_var, "file")).grid(row=0, column=2)
        tk.Label(single, text="Output file:", bg=self.bg_card, fg=self.text_color).grid(row=1, column=0, sticky="w")
        tk.Entry(single, textvariable=self.single_out_var, width=70, bg="#F8FAFC").grid(row=1, column=1, padx=8)
        tk.Button(single, text="Browse", command=lambda: self._browse(self.single_out_var, "file")).grid(row=1, column=2)

        controls = tk.Frame(self.root, bg=self.bg_main)
        controls.pack(pady=10)
        tk.Button(
            controls,
            text="REPLACE OPTIONS...",
            bg="#64748B",
            fg="white",
            width=18,
            height=2,
            font=("Segoe UI", 9, "bold"),
            command=self._open_replace_dialog,
        ).pack(side="left", padx=8)
        self.lbl_replace = tk.Label(
            controls,
            text="Replace: off",
            bg=self.bg_main,
            fg=self.text_color,
            font=("Segoe UI", 8),
        )
        self.lbl_replace.pack(side="left", padx=4)
        tk.Button(
            controls,
            text="SANITIZE ALL FILES IN FOLDER",
            bg=self.btn_run,
            fg="white",
            width=32,
            height=2,
            font=("Segoe UI", 9, "bold"),
            command=self._start_batch,
        ).pack(side="left", padx=12)
        tk.Button(
            controls,
            text="SANITIZE SINGLE FILE",
            bg=self.btn_single,
            fg="white",
            width=24,
            height=2,
            font=("Segoe UI", 9, "bold"),
            command=self._start_single,
        ).pack(side="left", padx=12)

        self.lbl_timer = tk.Label(self.root, text="Elapsed: 00:00:00", bg=self.bg_main, fg=self.accent, font=("Consolas", 10, "bold"))
        self.lbl_timer.pack()
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=920, mode="determinate")
        self.progress.pack(pady=6)
        self.lbl_status = tk.Label(self.root, text="Ready", bg=self.bg_main, fg=self.text_color, font=("Segoe UI", 10, "bold"))
        self.lbl_status.pack()

        self.console = scrolledtext.ScrolledText(self.root, height=18, bg="#F8FAFC", fg="#1E293B", font=("Consolas", 9))
        self.console.pack(padx=28, pady=10, fill="both", expand=True)
        self.log(f"QLAdmin Data Sanitizer {APP_VERSION} ready.")
        self.log(f"Rules: {self.rules_var.get()}")

    def log(self, msg):
        self.console.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.console.see(tk.END)
        self.root.update_idletasks()

    def _open_replace_dialog(self):
        rules_path = self.rules_var.get().strip() or DEFAULT_RULES
        if not os.path.isfile(rules_path):
            messagebox.showwarning("Rules required", f"Rules file not found:\n{rules_path}")
            return
        dlg = ReplaceOptionsDialog(
            self.root,
            rules_path,
            self.replace_enabled,
            self.replace_overrides,
        )
        self.root.wait_window(dlg)
        if dlg.result is not None:
            self.replace_enabled, self.replace_overrides = dlg.result
            if self.replace_enabled and self.replace_overrides:
                self.lbl_replace.config(
                    text=f"Replace: on ({len(self.replace_overrides)} pattern(s))",
                    fg=self.stage_ok,
                )
                self.log(f"Replace mode ON: {self.replace_overrides}")
            else:
                self.replace_enabled = False
                self.replace_overrides = {}
                self.lbl_replace.config(text="Replace: off", fg=self.text_color)
                self.log("Replace mode OFF")

    def _active_replace_overrides(self):
        if self.replace_enabled and self.replace_overrides:
            return self.replace_overrides
        return None

    def _browse(self, var, mode):
        if mode == "folder":
            path = filedialog.askdirectory()
        else:
            path = filedialog.askopenfilename(
                filetypes=[
                    ("Data files", "*.csv;*.dbf"),
                    ("CSV", "*.csv"),
                    ("DBF", "*.dbf"),
                    ("JSON", "*.json"),
                    ("All", "*.*"),
                ],
            )
        if path:
            var.set(os.path.normpath(path))

    def _set_status(self, text, ok=None):
        color = self.stage_ok if ok is True else self.stage_err if ok is False else self.text_color
        self.lbl_status.config(text=text, fg=color)

    def _start_batch(self):
        if self.is_running:
            messagebox.showwarning("Busy", "A job is already running.")
            return
        self.is_running = True
        self.start_time = time.time()
        threading.Thread(target=self._timer_loop, daemon=True).start()
        threading.Thread(target=self._run_batch_job, daemon=True).start()

    def _start_single(self):
        if self.is_running:
            messagebox.showwarning("Busy", "A job is already running.")
            return
        if not self.single_in_var.get().strip():
            messagebox.showwarning("Input required", "Choose an input CSV or DBF for single-file mode.")
            return
        self.is_running = True
        self.start_time = time.time()
        threading.Thread(target=self._timer_loop, daemon=True).start()
        threading.Thread(target=self._run_single_job, daemon=True).start()

    def _timer_loop(self):
        while self.is_running:
            if self.start_time:
                e = int(time.time() - self.start_time)
                self.lbl_timer.config(text=f"Elapsed: {e // 3600:02d}:{(e % 3600) // 60:02d}:{e % 60:02d}")
            time.sleep(1)

    def _run_batch_job(self):
        try:
            in_dir = self.input_var.get().strip()
            out_dir = self.output_var.get().strip()
            rules_path = self.rules_var.get().strip()
            patterns = [p.strip() for p in self.patterns_var.get().split(",") if p.strip()]

            if not os.path.isdir(in_dir):
                raise FileNotFoundError(f"Input directory not found: {in_dir}")
            if not rules_path or not os.path.isfile(rules_path):
                raise FileNotFoundError(f"Rules file not found: {rules_path}")

            os.makedirs(out_dir, exist_ok=True)
            self.progress["value"] = 5
            self._set_status("Running batch sanitization...")
            self.log(f"BATCH: input={in_dir}")
            self.log(f"BATCH: output={out_dir}")
            self.log(f"BATCH: patterns={patterns}")

            repl = self._active_replace_overrides()
            if repl:
                self.log(f"BATCH: replace_overrides={repl}")
            results, stats = ST.run_batch(in_dir, out_dir, rules_path, patterns, repl)
            self.progress["value"] = 85
            log_path = ST.write_audit_log(out_dir, results, stats, rules_path)
            self.progress["value"] = 100

            sanitized_files = sum(1 for r in results if r["action"] == "SANITIZED")
            skipped = sum(1 for r in results if r["action"] in ("SKIPPED_COPY", "EMPTY_COPY"))
            total_assignments = sum(sum(r.get("sanitized_counts", {}).values()) for r in results)

            self._last_result = {"mode": "batch", "results": results, "stats": stats, "audit": log_path}
            self.log(f"Complete: {len(results)} file(s), {sanitized_files} sanitized, {skipped} copied/skipped")
            self.log(f"Sanitized field assignments: {total_assignments}")
            self.log(f"Mapped PII values: {stats.get('mapped_pii_values', 0)}")
            self.log(f"Audit log: {log_path}")

            for r in results:
                if r.get("sanitized_counts"):
                    self.log(f"  {r['file']}: {dict(r['sanitized_counts'])}")

            self._set_status("Complete — batch sanitization finished", ok=True)
            messagebox.showinfo(
                "Sanitization complete",
                f"Processed {len(results)} file(s).\n\n"
                f"Output: {out_dir}\n"
                f"Audit: {log_path}\n\n"
                f"Mapped PII values: {stats.get('mapped_pii_values', 0)}",
            )
        except Exception as exc:
            self.log(f"ERROR: {exc}")
            self._set_status(f"Failed: {exc}", ok=False)
            messagebox.showerror("Sanitization failed", str(exc))
        finally:
            self.is_running = False
            self.progress["value"] = 0

    def _run_single_job(self):
        try:
            in_path = self.single_in_var.get().strip()
            out_path = self.single_out_var.get().strip()
            rules_path = self.rules_var.get().strip()

            if not os.path.isfile(in_path):
                raise FileNotFoundError(f"Input file not found: {in_path}")
            if not out_path:
                base, ext = os.path.splitext(os.path.basename(in_path))
                out_dir = self.output_var.get().strip() or DEFAULT_OUTPUT
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, f"{base}_sanitized{ext}")
                self.single_out_var.set(out_path)
            else:
                out_base, out_ext = os.path.splitext(out_path)
                in_ext = os.path.splitext(in_path)[1]
                if in_ext and (not out_ext or out_ext.lower() != in_ext.lower()):
                    out_path = out_base + in_ext
                    self.single_out_var.set(out_path)
            if not rules_path or not os.path.isfile(rules_path):
                raise FileNotFoundError(f"Rules file not found: {rules_path}")

            self._set_status("Sanitizing single file...")
            rules = ST.load_rules(rules_path)
            registry = ST.PiiRegistry(rules.get("salt", "qla-enterprise-test-salt-v2"))
            repl = self._active_replace_overrides()
            if repl:
                self.log(f"SINGLE: replace_overrides={repl}")
            result = ST.sanitize_file_structure(in_path, out_path, rules, registry, repl)
            fmt = result.get("format", "")

            self._last_result = {"mode": "single", "result": result, "stats": registry.stats()}
            self.log(f"{result['file']}: action={result['action']} format={fmt} rows={result['rows_in']}")
            if result.get("sanitized_counts"):
                self.log(f"Sanitized columns: {dict(result['sanitized_counts'])}")
            self.log(f"Output: {out_path}")
            self.log(f"Mapped PII values: {registry.stats()['mapped_pii_values']}")

            self._set_status("Complete — single file sanitized", ok=True)
            messagebox.showinfo("Done", f"Wrote:\n{out_path}")
        except Exception as exc:
            self.log(f"ERROR: {exc}")
            self._set_status(f"Failed: {exc}", ok=False)
            messagebox.showerror("Sanitization failed", str(exc))
        finally:
            self.is_running = False


def main():
    os.chdir(_TOOL_DIR)
    root = tk.Tk()
    QLAdminDataSanitizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
