"""Merge dated LifePRO rate extracts — filename YYYYMMDD newest wins.

Families: PAAGE, PAAGERAT, PDAGE under QLA_Migration/Source/.
Duplicate natural keys: later filename date overwrites earlier.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import os
import re
from typing import Callable, Iterable

_DATE_RE = re.compile(r"_(\d{8})\.csv$", re.I)

# Natural keys for per-family row identity (columns stripped/upper).
FAMILY_KEYS: dict[str, tuple[str, ...]] = {
    "PAAGE": ("COVERAGE_ID", "TYPE_CODE", "SEX", "BAND", "UWCLS", "RECORD_SEQ"),
    "PAAGERAT": (
        "COVERAGE_ID",
        "TYPE_CODE",
        "SEX",
        "BAND",
        "UWCLS",
        "RECORD_SEQ",
        "SEQ",
    ),
    "PDAGE": (
        "COVERAGE_ID",
        "TYPE_CODE",
        "AGE",
        "SEX",
        "BAND",
        "UWCLS",
        "DURATION",
    ),
}

FAMILY_GLOBS: dict[str, str] = {
    "PAAGE": "PAAGE_AttainedAge_Rates_Extract_*.csv",
    "PAAGERAT": "PAAGERAT_AttainedAge_Rates_Extract_*.csv",
    "PDAGE": "PDAGE_AgeDuration_Rates_Extract_*.csv",
}


def filename_extract_date(path: str) -> str | None:
    """Return YYYYMMDD from filename, or None if absent."""
    m = _DATE_RE.search(os.path.basename(path))
    return m.group(1) if m else None


def discover_dated_extracts(source_dir: str, family: str) -> list[tuple[str, str]]:
    """Return (YYYYMMDD, path) sorted ascending by filename date.

    Only files with a parseable _YYYYMMDD.csv suffix are included.
    """
    fam = family.upper().strip()
    pattern = FAMILY_GLOBS.get(fam)
    if not pattern:
        raise ValueError(f"Unknown rate extract family: {family!r}")
    out: list[tuple[str, str]] = []
    for path in glob.glob(os.path.join(source_dir, pattern)):
        if not os.path.isfile(path):
            continue
        dt = filename_extract_date(path)
        if not dt:
            continue
        out.append((dt, os.path.normpath(path)))
    out.sort(key=lambda x: (x[0], x[1]))
    return out


def _is_separator_row(values: Iterable[str]) -> bool:
    vals = [str(v or "").strip() for v in values]
    if not any(vals):
        return True
    # LifePRO dashed header/separator lines
    non_empty = [v for v in vals if v]
    if non_empty and all(set(v) <= {"-"} for v in non_empty):
        return True
    return False


def _row_key(row: dict[str, str], key_cols: tuple[str, ...]) -> tuple[str, ...] | None:
    parts = []
    for c in key_cols:
        v = (row.get(c) or "").strip()
        parts.append(v)
    if not parts[0] or set(parts[0]) <= {"-"}:
        return None
    if all(not p or set(p) <= {"-"} for p in parts):
        return None
    return tuple(parts)


def _sig_payload(files: list[tuple[str, str]]) -> str:
    h = hashlib.sha256()
    for dt, path in files:
        st = os.stat(path)
        h.update(f"{dt}|{path}|{st.st_size}|{int(st.st_mtime)}".encode("utf-8", errors="replace"))
    return h.hexdigest()


def merge_dated_extracts(
    files: list[tuple[str, str]],
    key_cols: tuple[str, ...],
    staging_path: str,
    encoding: str = "latin1",
) -> dict:
    """Merge dated extracts; filename newest wins. Write staging CSV.

    Processes newest→oldest so only keys (not full rows) stay in memory:
    first writer for a key wins (= newest file). Older-only keys are appended.
    ``files`` must be sorted ascending by YYYYMMDD.
    """
    os.makedirs(os.path.dirname(staging_path) or ".", exist_ok=True)
    sig_path = staging_path + ".sig"
    sig = _sig_payload(files) if files else ""
    if (
        files
        and os.path.isfile(staging_path)
        and os.path.isfile(sig_path)
        and open(sig_path, encoding="utf-8").read().strip() == sig
    ):
        return {
            "staging_path": staging_path,
            "files": [p for _, p in files],
            "dates": [d for d, _ in files],
            "cached": True,
            "rows": None,
            "overlays": None,
        }

    header: list[str] = []
    for _dt, path in files:
        with open(path, encoding=encoding, errors="replace", newline="") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames:
                continue
            for c in reader.fieldnames:
                cu = str(c or "").strip().upper()
                if cu and cu not in header:
                    header.append(cu)
    if not header:
        header = list(key_cols)

    seen: set[tuple[str, ...]] = set()
    written = 0
    skipped_older = 0
    scanned = 0

    # Newest first: first write for a key wins (= newest filename date)
    ordered = list(reversed(files))

    with open(staging_path, "w", encoding="utf-8", newline="") as out_fh:
        writer = csv.DictWriter(
            out_fh,
            fieldnames=header,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for _dt, path in ordered:
            with open(path, encoding=encoding, errors="replace", newline="") as fh:
                reader = csv.DictReader(fh)
                for raw in reader:
                    scanned += 1
                    row = {
                        str(k or "").strip().upper(): str(v or "").strip()
                        for k, v in raw.items()
                    }
                    if _is_separator_row(row.values()):
                        continue
                    key = _row_key(row, key_cols)
                    if key is None:
                        continue
                    if key in seen:
                        skipped_older += 1
                        continue
                    seen.add(key)
                    writer.writerow({c: row.get(c, "") for c in header})
                    written += 1

    with open(sig_path, "w", encoding="utf-8") as fh:
        fh.write(sig)

    return {
        "staging_path": staging_path,
        "files": [p for _, p in files],
        "dates": [d for d, _ in files],
        "cached": False,
        "rows": written,
        "overlays": skipped_older,
        "scanned": scanned,
        "newest_date": files[-1][0] if files else "",
        "oldest_date": files[0][0] if files else "",
    }


def ensure_merged_family(
    source_dir: str,
    staging_dir: str,
    family: str,
    extra_paths: list[str] | None = None,
    log: Callable[[str], None] | None = None,
) -> tuple[str, dict]:
    """Discover + merge one family; return (path_to_use, summary).

    If no dated Source files exist, falls back to first existing extra_paths entry.
    """
    fam = family.upper().strip()
    key_cols = FAMILY_KEYS[fam]
    files = discover_dated_extracts(source_dir, fam)

    # Optional legacy fallbacks (no date or older packages) — only if no Source hits
    if not files and extra_paths:
        for p in extra_paths:
            if p and os.path.isfile(p):
                dt = filename_extract_date(p) or "00000000"
                files.append((dt, os.path.normpath(p)))
        files.sort(key=lambda x: (x[0], x[1]))

    if not files:
        summary = {
            "staging_path": "",
            "files": [],
            "dates": [],
            "cached": False,
            "rows": 0,
            "overlays": 0,
            "error": "no_files",
        }
        if log:
            log(f"dated_extract_merge {fam}: no files found under {source_dir}")
        return "", summary

    if len(files) == 1:
        path = files[0][1]
        summary = {
            "staging_path": path,
            "files": [path],
            "dates": [files[0][0]],
            "cached": False,
            "rows": None,
            "overlays": 0,
            "single_file": True,
            "newest_date": files[0][0],
        }
        if log:
            log(f"dated_extract_merge {fam}: single file {os.path.basename(path)}")
        return path, summary

    staging_path = os.path.join(staging_dir, f"{fam.lower()}_dated_merged.csv")
    summary = merge_dated_extracts(files, key_cols, staging_path)
    if log:
        log(
            f"dated_extract_merge {fam}: files={len(files)} "
            f"dates={summary.get('oldest_date')}..{summary.get('newest_date')} "
            f"rows={summary.get('rows')} overlays={summary.get('overlays')} "
            f"cached={summary.get('cached')} -> {staging_path}"
        )
    return staging_path, summary
