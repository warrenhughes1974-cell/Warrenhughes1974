"""
Run-logging, staged-progress, and output-hygiene helpers (v57.8).

OPERATIONS / PRESENTATION ONLY. This module never touches conversion data,
schemas, mappings, or business logic. It centralizes:

  * Staged progress plans (honest stage models per run type).
  * RunErrorLog — error-only artifacts under QLA_Migration/Error_Logs/run_<ts>.
  * Output hygiene — keep QLA_Migration/Output CSV-only; relocate (never delete)
    non-CSV diagnostics to Reports / Error_Logs / the rate sandbox DBF folder.

All filesystem side effects are isolated and rollback-safe: error folders are
created lazily (only when something is actually written), and file relocation
never deletes — it moves, and reports anything it cannot safely move.
"""
from __future__ import annotations

import csv
import os
import shutil
import traceback
from datetime import datetime

# ---------------------------------------------------------------------------
# Staged progress plans  ->  list of (stage_number, stage_name, percent)
# ---------------------------------------------------------------------------
STAGE_PLANS = {
    "full_batch": [
        (1, "Initializing run and folders", 5),
        (2, "Loading source extracts", 15),
        (3, "Running product setup / quikplan", 25),
        (4, "Applying rulebooks and crosswalks", 40),
        (5, "Building QLAdmin policy/client/rider outputs", 55),
        (6, "Running claims / payment outputs", 68),
        (7, "Generating rate tables", 80),
        (8, "Running validation and blocker checks", 92),
        (9, "Writing final CSV outputs and summaries", 100),
    ],
    "single_table": [
        (1, "Initializing run and folders", 10),
        (2, "Loading source extracts", 30),
        (3, "Applying rulebooks and crosswalks", 55),
        (4, "Building QLAdmin target table", 80),
        (5, "Writing final CSV output", 100),
    ],
    "product_setup": [
        (1, "Initializing run and folders", 10),
        (2, "Loading source extracts", 30),
        (3, "Converting quikplan and applying CSO assumptions", 55),
        (4, "Running validation and blocker checks", 80),
        (5, "Writing quikplan.csv and summaries", 100),
    ],
    "rate_only": [
        (1, "Initializing run and folders", 10),
        (2, "Loading rate extracts and segmentation", 30),
        (3, "Building factor / key / member tables", 60),
        (4, "Running validation and blocker checks", 85),
        (5, "Writing rate CSV outputs", 100),
    ],
}


def stage_plan(run_type: str):
    return STAGE_PLANS.get(run_type, STAGE_PLANS["full_batch"])


def stage_count(run_type: str) -> int:
    return len(stage_plan(run_type))


def fmt_elapsed(seconds: float) -> str:
    seconds = int(max(0, seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def run_folder_name(now: datetime | None = None) -> str:
    return "run_" + (now or datetime.now()).strftime("%Y%m%d_%H%M%S")


# ---------------------------------------------------------------------------
# Error log — lazily created, error-only artifacts
# ---------------------------------------------------------------------------
class RunErrorLog:
    """Centralized, timestamped error-only artifact folder.

    The run folder is created lazily on first write so successful, clean runs
    do not litter Error_Logs with empty folders. Call `.folder` after any write
    to surface the path in the UI.
    """

    def __init__(self, error_logs_root: str, now: datetime | None = None):
        self.error_logs_root = error_logs_root
        self._folder = os.path.join(error_logs_root, run_folder_name(now))
        self._created = False
        self.artifacts: list[str] = []

    @property
    def folder(self) -> str:
        return self._folder

    @property
    def created(self) -> bool:
        return self._created

    def _ensure(self) -> str:
        if not self._created:
            os.makedirs(self._folder, exist_ok=True)
            self._created = True
        return self._folder

    def _write_text(self, name: str, text: str) -> str:
        path = os.path.join(self._ensure(), name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        self.artifacts.append(path)
        return path

    def _write_rows(self, name: str, header, rows) -> str:
        path = os.path.join(self._ensure(), name)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(list(header))
            for r in rows:
                if isinstance(r, dict):
                    w.writerow([r.get(h, "") for h in header])
                else:
                    w.writerow(list(r))
        self.artifacts.append(path)
        return path

    def write_exception(self, stage_name: str, exc: BaseException) -> str:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        body = f"Failed stage: {stage_name}\nException: {exc}\n\n{tb}"
        return self._write_text("exception_traceback.txt", body)

    def write_failed_stage(self, stage_name: str, message: str) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self._write_text("failed_stage.txt", f"[{ts}] Failed at stage: {stage_name}\n{message}\n")

    def write_blockers(self, rows) -> str:
        return self._write_rows("blockers.csv", ["ID", "DETAIL"], rows)

    def write_validation_errors(self, rows) -> str:
        return self._write_rows("validation_errors.csv", ["SEVERITY", "CATEGORY", "ENTITY", "DETAIL"], rows)

    def write_warnings(self, rows) -> str:
        return self._write_rows("warnings.csv", ["SEVERITY", "CATEGORY", "ENTITY", "DETAIL"], rows)

    def write_summary(self, run_type: str, status: str, lines) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        body = [f"RUN SUMMARY", f"timestamp: {ts}", f"run_type: {run_type}", f"status: {status}", ""]
        body.extend(str(x) for x in lines)
        return self._write_text("run_error_summary.txt", "\n".join(body) + "\n")


# ---------------------------------------------------------------------------
# Output hygiene — keep Output CSV-only (move, never delete)
# ---------------------------------------------------------------------------
# Non-CSV files whose basename matches these prefixes are treated as error
# artifacts and routed to the Error_Logs run folder; everything else non-CSV
# goes to Reports. *.dbf go to the rate sandbox DBF folder.
_ERROR_NAME_HINTS = ("error", "blocker", "exception", "failed", "validation_issues", "rejected")
_UAT_DBF_DIR_SUFFIX = "_uat_dbf"


def _is_uat_dbf_dir(dir_path: str) -> bool:
    """UAT DBF folders (e.g. quikmemo_uat_dbf, claims_uat_dbf) keep DBF+sidecar together."""
    return os.path.basename(os.path.normpath(dir_path)).lower().endswith(_UAT_DBF_DIR_SUFFIX)


def scan_non_csv(output_dir: str) -> list[str]:
    """Return absolute paths of non-CSV files anywhere under output_dir."""
    found = []
    if not output_dir or not os.path.isdir(output_dir):
        return found
    for root, _dirs, files in os.walk(output_dir):
        if _is_uat_dbf_dir(root):
            continue
        for name in files:
            if not name.lower().endswith(".csv"):
                found.append(os.path.join(root, name))
    return found


def _unique_dest(dest_dir: str, basename: str) -> str:
    dest = os.path.join(dest_dir, basename)
    if not os.path.exists(dest):
        return dest
    stem, ext = os.path.splitext(basename)
    stamp = datetime.now().strftime("%H%M%S")
    return os.path.join(dest_dir, f"{stem}_{stamp}{ext}")


def relocate_non_csv(output_dir, reports_dir, sandbox_dbf_dir, error_log: "RunErrorLog | None" = None):
    """Move non-CSV files out of Output so it stays CSV-only.

    Routing:
      *.dbf                 -> sandbox_dbf_dir (rate sandbox)
      error-named artifacts -> error_log run folder (created lazily)
      everything else       -> reports_dir

    Never deletes. Returns dict with 'moved' (list of (src, dest)) and
    'skipped' (list of (src, reason)) for files that could not be moved.
    """
    result = {"moved": [], "skipped": []}
    for src in scan_non_csv(output_dir):
        base = os.path.basename(src)
        lower = base.lower()
        try:
            if lower.endswith(".dbf"):
                dest_dir = sandbox_dbf_dir
            elif any(h in lower for h in _ERROR_NAME_HINTS) and error_log is not None:
                dest_dir = error_log._ensure()
            else:
                dest_dir = reports_dir
            os.makedirs(dest_dir, exist_ok=True)
            dest = _unique_dest(dest_dir, base)
            shutil.move(src, dest)
            result["moved"].append((src, dest))
        except Exception as exc:  # never delete; just report
            result["skipped"].append((src, str(exc)))
    return result
