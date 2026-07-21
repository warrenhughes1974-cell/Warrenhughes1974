#!/usr/bin/env python3
"""
Stage 2A read-only inventory runner for CFIC_Rates.

Usage (from repo root or any directory):
    python Citizens_Product_Rate_Conversion/tools/inventory/run_stage2a_inventory.py

Never writes to CFIC_Rates.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Allow import of cfic_inventory_core from same directory
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from cfic_inventory_core import (  # noqa: E402
    INVENTORY_COLUMNS,
    build_snapshot,
    compare_snapshots,
    inventory_source,
    record_to_row,
    write_csv,
)

DEFAULT_SOURCE = Path(r"C:\Users\warren\Documents\GitHub\Warrenhughes1974\CFIC_Rates")
DEFAULT_DEST = Path(r"C:\Users\warren\Documents\GitHub\Warrenhughes1974\Citizens_Product_Rate_Conversion")


def git_info(repo_root: Path) -> dict:
    info = {
        "git_repository_root": None,
        "current_branch": None,
        "head_commit": None,
        "cfic_rates_git_status": None,
    }
    try:
        root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout.strip()
        info["git_repository_root"] = root
        info["current_branch"] = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout.strip()
        info["head_commit"] = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "CFIC_Rates"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout.strip()
        info["cfic_rates_git_status"] = "untracked" if status.startswith("??") else status or "clean"
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return info


def disk_free_bytes(path: Path) -> int | None:
    try:
        import shutil
        usage = shutil.disk_usage(path)
        return usage.free
    except OSError:
        return None


def preflight(source: Path, dest: Path) -> dict:
    snap = build_snapshot(source)
    repo_root = source.parent
    gi = git_info(repo_root)
    dest_exists = dest.exists()
    dest_items = list(dest.iterdir()) if dest_exists else []
    return {
        "source_root": str(source),
        "destination_root": str(dest),
        "scan_timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_file_count": snap["file_count"],
        "source_directory_count": snap["directory_count"],
        "total_source_bytes": snap["total_bytes"],
        "file_extension_counts": snap["extension_counts"],
        "largest_25_files": snap["largest_25_files"],
        "source_git_repository_root": gi["git_repository_root"],
        "source_git_branch": gi["current_branch"],
        "source_git_head_commit": gi["head_commit"],
        "source_git_cfic_rates_status": gi["cfic_rates_git_status"],
        "destination_preexisting": dest_exists,
        "destination_preexisting_item_count": len(dest_items) if dest_exists else 0,
        "destination_inside_source": str(dest).startswith(str(source)),
        "source_equals_destination": source.resolve() == dest.resolve(),
        "available_disk_space_bytes": disk_free_bytes(dest.parent),
        "preflight_result": "PASS",
        "preflight_notes": [],
        "file_index": snap["file_index"],
    }


def migration_action_would_copy(action: str) -> bool:
    return action in {
        "COPY", "COPY_AND_RENAME", "COPY_TO_ARCHIVE", "COPY_TO_QUARANTINE",
    }


def generate_reports(
    records: list,
    preflight_data: dict,
    comparison: dict,
    dest: Path,
) -> None:
    rows = [record_to_row(r) for r in records]
    mig_dir = dest / "manifests"
    rep_dir = dest / "reports" / "migration"

    write_csv(mig_dir / "migration_inventory.csv", INVENTORY_COLUMNS, rows)

    # Duplicate report
    dup_rows = []
    for r in records:
        if r.duplicate_group_id:
            dup_rows.append({
                "DUPLICATE_GROUP_ID": r.duplicate_group_id,
                "INVENTORY_ID": r.inventory_id,
                "SOURCE_RELATIVE_PATH": r.relative_path,
                "FILE_SIZE_BYTES": r.size,
                "SOURCE_SHA256": r.sha256,
                "MIGRATION_ACTION": r.migration_action,
            })
    write_csv(rep_dir / "duplicate_file_report.csv",
              ["DUPLICATE_GROUP_ID", "INVENTORY_ID", "SOURCE_RELATIVE_PATH",
               "FILE_SIZE_BYTES", "SOURCE_SHA256", "MIGRATION_ACTION"],
              dup_rows)

    # Case collision report
    case_rows = [record_to_row(r) for r in records if r.case_collision != "NONE"]
    write_csv(rep_dir / "path_collision_report.csv",
              ["INVENTORY_ID", "SOURCE_RELATIVE_PATH", "CASE_COLLISION_STATUS",
               "FILENAME_COLLISION_STATUS", "PROPOSED_DESTINATION_RELATIVE_PATH"],
              [{k: row[k] for k in ["INVENTORY_ID", "SOURCE_RELATIVE_PATH",
                                    "CASE_COLLISION_STATUS", "FILENAME_COLLISION_STATUS",
                                    "PROPOSED_DESTINATION_RELATIVE_PATH"]} for row in case_rows]
              + [{k: row.get(k, "") for k in ["INVENTORY_ID", "SOURCE_RELATIVE_PATH",
                                               "CASE_COLLISION_STATUS", "FILENAME_COLLISION_STATUS",
                                               "PROPOSED_DESTINATION_RELATIVE_PATH"]}
                 for row in [record_to_row(r) for r in records
                             if r.filename_collision == "FILENAME_COLLISION"]])

    # Hardcoded paths
    hc_rows = []
    for r in records:
        if r.hardcoded_path == "Y":
            paths = r.text_scan.get("hardcoded_paths", [])
            hc_rows.append({
                "INVENTORY_ID": r.inventory_id,
                "SOURCE_RELATIVE_PATH": r.relative_path,
                "HARDCODED_PATH_COUNT": len(paths),
                "SAMPLE_PATHS": "; ".join(paths[:5]),
            })
    write_csv(rep_dir / "hardcoded_path_report.csv",
              ["INVENTORY_ID", "SOURCE_RELATIVE_PATH", "HARDCODED_PATH_COUNT", "SAMPLE_PATHS"],
              hc_rows)

    # Sensitive data
    sens_rows = [{
        "INVENTORY_ID": r.inventory_id,
        "SOURCE_RELATIVE_PATH": r.relative_path,
        "SENSITIVE_DATA_INDICATOR": r.sensitive,
        "RISK": r.risk,
        "MIGRATION_ACTION": r.migration_action,
    } for r in records if r.sensitive == "Y"]
    write_csv(rep_dir / "sensitive_data_review.csv",
              ["INVENTORY_ID", "SOURCE_RELATIVE_PATH", "SENSITIVE_DATA_INDICATOR",
               "RISK", "MIGRATION_ACTION"],
              sens_rows)

    # Enterprise dependencies
    ent_rows = []
    for r in records:
        scan = r.text_scan
        if r.qla_core_ref == "Y" or scan.get("qla_migration") or scan.get("cso"):
            ent_rows.append({
                "INVENTORY_ID": r.inventory_id,
                "SOURCE_RELATIVE_PATH": r.relative_path,
                "QLA_CORE_REFERENCE": r.qla_core_ref,
                "QLA_MIGRATION_REFERENCE": "Y" if scan.get("qla_migration") else "N",
                "CSO_REFERENCE": r.cso_ref,
            })
    write_csv(rep_dir / "enterprise_dependency_report.csv",
              ["INVENTORY_ID", "SOURCE_RELATIVE_PATH", "QLA_CORE_REFERENCE",
               "QLA_MIGRATION_REFERENCE", "CSO_REFERENCE"],
              ent_rows)

    # Aggregates for dry-run report
    action_counts = Counter(r.migration_action for r in records)
    category_counts = Counter(r.category for r in records)
    confidence_counts = Counter(r.confidence for r in records)
    ext_counts = Counter((r.extension or "(no ext)").lower() for r in records)

    copy_actions = {a: c for a, c in action_counts.items() if migration_action_would_copy(a)}
    exclude_actions = {a: c for a, c in action_counts.items()
                       if a in ("EXCLUDE_GENERATED", "EXCLUDE_TEMPORARY", "DO_NOT_MIGRATE")}
    review_actions = {a: c for a, c in action_counts.items()
                      if a in ("REVIEW_REQUIRED", "DUPLICATE_REVIEW", "UNKNOWN")}

    would_copy = [r for r in records if migration_action_would_copy(r.migration_action)]
    would_not_copy = [r for r in records if not migration_action_would_copy(r.migration_action)]
    est_copy_bytes = sum(r.size for r in would_copy)

    source_original = [r for r in records if r.proposed_dest.startswith("source/")]
    working_mappings = [r for r in records if r.proposed_dest.startswith("mappings/working")]
    archive_items = [r for r in records if "archive/" in r.proposed_dest
                     or r.migration_action == "COPY_TO_ARCHIVE"]
    quarantine_items = [r for r in records if "quarantine/" in r.proposed_dest
                        or r.migration_action == "COPY_TO_QUARANTINE"]
    exclude_items = [r for r in records
                     if r.migration_action in ("EXCLUDE_GENERATED", "EXCLUDE_TEMPORARY", "DO_NOT_MIGRATE")]

    unknown_auth = [r for r in records if r.authority == "unknown"]
    unknown_purpose = [r for r in records if r.migration_action in ("UNKNOWN", "REVIEW_REQUIRED")]

    largest_copy = sorted(would_copy, key=lambda x: x.size, reverse=True)[:15]

    dry_run_md = f"""# Stage 2A Dry-Run Migration Report

**Generated:** {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}  
**Source:** `{preflight_data["source_root"]}`  
**Destination:** `{preflight_data["destination_root"]}`  
**Stage:** 2A — Dry-run only (no files copied)

## Summary

| Metric | Value |
|--------|------:|
| Total source files | {len(records)} |
| Total source directories | {preflight_data["source_directory_count"]} |
| Total source bytes | {preflight_data["total_source_bytes"]:,} |
| Files that would copy (Stage 2B) | {len(would_copy)} |
| Files that would not copy | {len(would_not_copy)} |
| Estimated Stage 2B copy size | {est_copy_bytes:,} bytes ({est_copy_bytes / 1e9:.2f} GB) |
| COPY_APPROVED = YES | **0** (all NO) |
| Source assets copied in Stage 2A | **0** |

## Counts by Extension

| Extension | Count |
|-----------|------:|
"""
    for ext, cnt in sorted(ext_counts.items(), key=lambda x: (-x[1], x[0])):
        dry_run_md += f"| `{ext}` | {cnt} |\n"

    dry_run_md += "\n## Counts by Category\n\n| Category | Count |\n|----------|------:|\n"
    for cat, cnt in sorted(category_counts.items(), key=lambda x: (-x[1], x[0])):
        dry_run_md += f"| {cat} | {cnt} |\n"

    dry_run_md += "\n## Counts by Migration Action\n\n| Action | Count |\n|--------|------:|\n"
    for act, cnt in sorted(action_counts.items(), key=lambda x: (-x[1], x[0])):
        dry_run_md += f"| {act} | {cnt} |\n"

    dry_run_md += "\n## Counts by Classification Confidence\n\n| Confidence | Count |\n|------------|------:|\n"
    for conf, cnt in sorted(confidence_counts.items(), key=lambda x: (-x[1], x[0])):
        dry_run_md += f"| {conf} | {cnt} |\n"

    dry_run_md += f"""
## Proposed Destination Buckets

| Bucket | File count |
|--------|----------:|
| Original source (`source/`) | {len(source_original)} |
| Working mappings (`mappings/working/`) | {len(working_mappings)} |
| Archive | {len(archive_items)} |
| Quarantine | {len(quarantine_items)} |
| Exclusion (generated/temp/do not migrate) | {len(exclude_items)} |
| Review required / unknown purpose | {len(unknown_purpose)} |

## Duplicate Groups

- SHA-256 duplicate groups: **{len(set(r.duplicate_group_id for r in records if r.duplicate_group_id))}**
- See `duplicate_file_report.csv`

## Collision Risks

- Case-collision rows: **{sum(1 for r in records if r.case_collision != "NONE")}**
- Filename-collision rows: **{sum(1 for r in records if r.filename_collision == "FILENAME_COLLISION")}**
- High path-length risk: **{sum(1 for r in records if r.path_length_risk == "HIGH")}**
- See `path_collision_report.csv`

## Sensitive-Data Risks

- Files flagged: **{sum(1 for r in records if r.sensitive == "Y")}**
- See `sensitive_data_review.csv`

## Hardcoded Paths

- Files with absolute path references: **{sum(1 for r in records if r.hardcoded_path == "Y")}**
- See `hardcoded_path_report.csv`

## CSO References

- Files with CSO reference indicators: **{sum(1 for r in records if r.cso_ref == "Y")}**
- Note: Mostly documentation pattern references; not CSO plan mappings.

## qla_core Dependencies

- Files referencing qla_core: **{sum(1 for r in records if r.qla_core_ref == "Y")}**
- See `enterprise_dependency_report.csv`

## QLA_Migration References

- Files referencing QLA_Migration: **{sum(1 for r in records if r.text_scan.get("qla_migration"))}**

## Unknown Authority / Purpose

- Unknown authority: **{len(unknown_auth)}**
- Review-required or unknown action: **{len(unknown_purpose)}**

## Largest Proposed Copy Items

| Size (bytes) | Relative path | Action |
|-------------:|---------------|--------|
"""
    for r in largest_copy:
        dry_run_md += f"| {r.size:,} | `{r.relative_path}` | {r.migration_action} |\n"

    dry_run_md += f"""
## Migration Blockers (Stage 2B)

1. `COPY_APPROVED = NO` on all {len(records)} inventory rows
2. Duplicate groups require review before copy
3. Quarantine items ({len(quarantine_items)}) require authority decision
4. Working mappings not approved for `mappings/approved/`
5. Enterprise Engine path not retargeted (`qla_core` dependency)
6. OBQ business gates from legacy issues remain open

## Open Decisions

- 308 vs 301 plan count reconciliation
- Source authority for legacy SourceData dump
- `cifianu1.dbf` scope
- Cash-value ZIP storage (Git LFS vs external)
- OCR/green-sheet path: archive-only vs continued investment

## Stage 2B Copy Projection

| Action group | Count |
|--------------|------:|
| Would COPY (all copy actions) | {len(would_copy)} |
| Would EXCLUDE / DO_NOT_MIGRATE | {sum(action_counts.get(a, 0) for a in ("EXCLUDE_GENERATED", "EXCLUDE_TEMPORARY", "DO_NOT_MIGRATE"))} |
| Would REVIEW / DUPLICATE_REVIEW / UNKNOWN | {sum(action_counts.get(a, 0) for a in ("REVIEW_REQUIRED", "DUPLICATE_REVIEW", "UNKNOWN"))} |

## Confirmations

- [x] `COPY_APPROVED` is **NO** for every row in `migration_inventory.csv`
- [x] No source assets were copied during Stage 2A
- [x] CFIC_Rates was read only

## Source Integrity (Post-Scan)

- Source unchanged: **{comparison.get("source_unchanged", False)}**
- Files added during Stage 2A: {len(comparison.get("added_files", []))}
- Files missing after Stage 2A: {len(comparison.get("missing_files", []))}
- mtime changes: {len(comparison.get("modified_mtime_files", []))}
"""
    (rep_dir / "Stage2A_Dry_Run_Migration_Report.md").write_text(dry_run_md, encoding="utf-8")


def main() -> int:
    source = DEFAULT_SOURCE
    dest = DEFAULT_DEST

    if not source.is_dir():
        print(f"ERROR: Source not found: {source}", file=sys.stderr)
        return 1

    if dest.resolve() == source.resolve():
        print("ERROR: Source and destination are the same", file=sys.stderr)
        return 1

    if str(dest).startswith(str(source)):
        print("ERROR: Destination inside source", file=sys.stderr)
        return 1

    print("Building preflight snapshot...")
    pre = preflight(source, dest)
    preflight_path = dest / "manifests" / "preflight_source_snapshot.json"
    preflight_path.parent.mkdir(parents=True, exist_ok=True)
    # Write preflight without full file_index in saved JSON (large) - keep summary + index
    pre_save = {k: v for k, v in pre.items()}
    preflight_path.write_text(json.dumps(pre_save, indent=2), encoding="utf-8")

    print(f"Inventorying {source} ({pre['source_file_count']} files)...")
    records, _meta = inventory_source(source, dest)

    print("Writing migration inventory and reports...")
    comparison_placeholder = {"source_unchanged": None}
    generate_reports(records, pre, comparison_placeholder, dest)

    print("Building post-run snapshot...")
    post_snap = build_snapshot(source)
    post_path = dest / "manifests" / "post_stage2a_source_snapshot.json"
    comparison = compare_snapshots(
        {
            "file_index": pre["file_index"],
            "file_count": pre["source_file_count"],
            "directory_count": pre["source_directory_count"],
            "total_bytes": pre["total_source_bytes"],
        },
        post_snap,
    )
    post_save = {
        **{k: post_snap[k] for k in (
            "source_root", "scan_timestamp_utc", "file_count",
            "directory_count", "total_bytes", "extension_counts",
        )},
        "comparison_to_preflight": comparison,
        "stage2a_source_integrity": "PASS" if comparison["source_unchanged"] else "FAIL",
        "file_index": post_snap["file_index"],
    }
    post_path.write_text(json.dumps(post_save, indent=2), encoding="utf-8")

    # Regenerate dry-run report with comparison
    generate_reports(records, pre, comparison, dest)

    print(f"Inventory complete: {len(records)} files")
    print(f"Source integrity: {post_save['stage2a_source_integrity']}")
    return 0 if comparison["source_unchanged"] else 2


if __name__ == "__main__":
    sys.exit(main())
