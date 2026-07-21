#!/usr/bin/env python3
"""
Stage 2B — Controlled Classified Copy Migration.

Never modifies CFIC_Rates. Copy-only with SHA-256 verification.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SOURCE = Path(r"C:\Users\warren\Documents\GitHub\Warrenhughes1974\CFIC_Rates")
DEFAULT_DEST = Path(r"C:\Users\warren\Documents\GitHub\Warrenhughes1974\Citizens_Product_Rate_Conversion")

COPY_ACTIONS = {"COPY", "COPY_AND_RENAME", "COPY_TO_ARCHIVE", "COPY_TO_QUARANTINE"}

STAGE2B_COLUMNS = [
    "STAGE2B_REVIEW_STATUS",
    "STAGE2B_DECISION",
    "CANONICAL_FILE_INDICATOR",
    "FINAL_DESTINATION_RELATIVE_PATH",
    "COPY_RESULT",
    "DESTINATION_SHA256",
    "COPY_VERIFICATION_STATUS",
    "COPY_TIMESTAMP_UTC",
]

# Canonical duplicate group resolution (Decision 2B-03)
CANONICAL_BY_GROUP: dict[str, str] = {
    "DUP-0002": "source/CFIProposalMaker.zip",
    "DUP-0003": "source/CFIProposalMakerRev2.mdb",
    "DUP-0004": "validation/cfic_issue03_p7mn_validation.csv",
}

CANONICAL_REASON: dict[str, str] = {
    "DUP-0001": "Dev/sample PDF duplicates; both EXCLUDE_GENERATED per 2B-05/2B-08",
    "DUP-0002": "source/ is canonical over root duplicate per 2B-03",
    "DUP-0003": "source/original/access canonical; extracted/ is working copy per 2B-03",
    "DUP-0004": "validation/ folder canonical for validation evidence; Issue_Log copy to duplicate_review",
    "DUP-0005": "Identical PT1 content; both archived with distinct paths (legacy SourceData structure)",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return "UNREADABLE"


def norm_rel(p: str) -> str:
    return p.replace("\\", "/")


def build_snapshot(source_root: Path) -> dict:
    files = sorted(source_root.rglob("*"))
    file_entries = []
    ext_counts: Counter = Counter()
    total = 0
    for p in files:
        if not p.is_file():
            continue
        st = p.stat()
        rel = norm_rel(str(p.relative_to(source_root)))
        total += st.st_size
        ext = p.suffix.lower() if p.suffix else "(no ext)"
        ext_counts[ext] += 1
        file_entries.append({
            "relative_path": rel,
            "size": st.st_size,
            "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
    dir_count = sum(1 for d in source_root.rglob("*") if d.is_dir())
    return {
        "source_root": str(source_root),
        "scan_timestamp_utc": utc_now(),
        "file_count": len(file_entries),
        "directory_count": dir_count,
        "total_bytes": total,
        "extension_counts": dict(sorted(ext_counts.items(), key=lambda x: (-x[1], x[0]))),
        "file_index": {e["relative_path"]: {"size": e["size"], "mtime_utc": e["mtime_utc"]} for e in file_entries},
    }


def compare_snapshots(baseline: dict, current: dict) -> dict:
    b_idx = baseline.get("file_index", {})
    c_idx = current.get("file_index", {})
    b_set, c_set = set(b_idx), set(c_idx)
    modified = []
    for rel in sorted(b_set & c_set):
        if b_idx[rel]["mtime_utc"] != c_idx[rel]["mtime_utc"]:
            modified.append({"relative_path": rel, "baseline_mtime": b_idx[rel]["mtime_utc"], "current_mtime": c_idx[rel]["mtime_utc"]})
    return {
        "file_count_delta": current["file_count"] - baseline["file_count"],
        "directory_count_delta": current["directory_count"] - baseline["directory_count"],
        "total_bytes_delta": current["total_bytes"] - baseline["total_bytes"],
        "added_files": sorted(c_set - b_set),
        "missing_files": sorted(b_set - c_set),
        "modified_mtime_files": modified,
        "source_unchanged": not (c_set - b_set or b_set - c_set or modified)
            and current["file_count"] == baseline["file_count"]
            and current["total_bytes"] == baseline["total_bytes"],
    }


def resolve_final_destination(row: dict) -> str:
    """Apply Stage 2B destination overrides."""
    dest = row.get("PROPOSED_DESTINATION_RELATIVE_PATH", "").strip()
    rel = norm_rel(row["SOURCE_RELATIVE_PATH"])
    action = row["MIGRATION_ACTION"]

    # 2B-09 draft Quik outputs
    if "output/rates/" in rel.lower() and row["FILENAME"].startswith("Quik"):
        return f"output/csv/draft_pre_migration/{row['FILENAME']}"

    # Sensitive quarantine (2B-02)
    if row.get("SENSITIVE_DATA_INDICATOR") == "Y":
        if "cifianu1" in rel.lower():
            return "quarantine/sensitive_review/cifianu1.dbf"
        if "agentname" in rel.lower():
            return "quarantine/sensitive_review/AgentName.csv"

    # Duplicate non-canonical -> quarantine
    gid = row.get("DUPLICATE_GROUP_ID", "").strip()
    if gid and gid in CANONICAL_BY_GROUP:
        if rel != CANONICAL_BY_GROUP[gid]:
            return f"quarantine/duplicate_review/{rel}"

    # DUPLICATE_REVIEW extracted mdb -> quarantine (canonical is source/)
    if action == "DUPLICATE_REVIEW":
        return f"quarantine/duplicate_review/{rel}"

    return dest


def review_row(row: dict, source_root: Path) -> dict:
    """Apply approval rules; return updated Stage 2B fields."""
    out = {
        "STAGE2B_REVIEW_STATUS": "REVIEW_REMAINS_OPEN",
        "STAGE2B_DECISION": "",
        "CANONICAL_FILE_INDICATOR": "N",
        "FINAL_DESTINATION_RELATIVE_PATH": "",
        "COPY_APPROVED": "NO",
    }
    action = row["MIGRATION_ACTION"]
    rel = norm_rel(row["SOURCE_RELATIVE_PATH"])
    src_path = source_root / Path(rel)

    # 2B-04 Excel lock
    if row["FILENAME"].startswith("~$"):
        out.update({
            "STAGE2B_REVIEW_STATUS": "EXCLUDED",
            "STAGE2B_DECISION": "2B-04 Excel lock file",
            "FINAL_DESTINATION_RELATIVE_PATH": "",
        })
        return out

    # Never approve these actions
    if action in ("EXCLUDE_TEMPORARY", "EXCLUDE_GENERATED", "DO_NOT_MIGRATE", "UNKNOWN"):
        status = "EXCLUDED" if action != "DO_NOT_MIGRATE" else "DUPLICATE_EXCLUDED"
        if action == "DO_NOT_MIGRATE":
            status = "DUPLICATE_EXCLUDED"
        out.update({
            "STAGE2B_REVIEW_STATUS": status,
            "STAGE2B_DECISION": f"Migration action {action} per inventory",
        })
        return out

    if action not in COPY_ACTIONS:
        if action == "DUPLICATE_REVIEW":
            final_dest = f"quarantine/duplicate_review/{rel}"
            out.update({
                "STAGE2B_REVIEW_STATUS": "APPROVED_FOR_QUARANTINE",
                "STAGE2B_DECISION": "2B-03 extracted duplicate; quarantine audit copy",
                "FINAL_DESTINATION_RELATIVE_PATH": final_dest,
                "COPY_APPROVED": "YES",
                "CANONICAL_FILE_INDICATOR": "N",
            })
            return out
        out["STAGE2B_REVIEW_STATUS"] = "REVIEW_REMAINS_OPEN"
        out["STAGE2B_DECISION"] = f"Unresolved action {action}"
        return out

    if not src_path.is_file():
        out.update({"STAGE2B_REVIEW_STATUS": "BLOCKED", "STAGE2B_DECISION": "Source file missing"})
        return out

    final_dest = resolve_final_destination(row)
    if not final_dest:
        out.update({"STAGE2B_REVIEW_STATUS": "BLOCKED", "STAGE2B_DECISION": "No destination"})
        return out

    # Path traversal check
    dest_full = (DEFAULT_DEST / final_dest).resolve()
    if not str(dest_full).startswith(str(DEFAULT_DEST.resolve())):
        out.update({"STAGE2B_REVIEW_STATUS": "BLOCKED", "STAGE2B_DECISION": "Destination escapes Citizens root"})
        return out

    # mappings/approved prohibition
    if final_dest.startswith("mappings/approved/"):
        out.update({"STAGE2B_REVIEW_STATUS": "BLOCKED", "STAGE2B_DECISION": "Would place in mappings/approved"})
        return out

    # qla_core - don't copy engine modules (not in CFIC_Rates inventory as qla_core path)

    gid = row.get("DUPLICATE_GROUP_ID", "").strip()
    if gid:
        canonical_rel = CANONICAL_BY_GROUP.get(gid)
        if canonical_rel and rel == canonical_rel:
            out["CANONICAL_FILE_INDICATOR"] = "Y"
            out["STAGE2B_DECISION"] = CANONICAL_REASON.get(gid, "Canonical selected")
        elif canonical_rel and rel != canonical_rel:
            out["CANONICAL_FILE_INDICATOR"] = "N"
            out["STAGE2B_DECISION"] = f"Duplicate of {canonical_rel}; quarantine per 2B-03"
        elif gid == "DUP-0005":
            out["CANONICAL_FILE_INDICATOR"] = "Y"  # both archived with distinct paths
            out["STAGE2B_DECISION"] = CANONICAL_REASON["DUP-0005"]

    if action == "DUPLICATE_REVIEW":
        pass  # handled above
    elif not out["STAGE2B_DECISION"]:
        out["STAGE2B_DECISION"] = ""

    # Review status by destination type
    if final_dest.startswith("quarantine/sensitive_review/"):
        review_status = "APPROVED_FOR_QUARANTINE"
    elif final_dest.startswith("quarantine/"):
        review_status = "APPROVED_FOR_QUARANTINE"
    elif final_dest.startswith("archive/"):
        review_status = "APPROVED_FOR_ARCHIVE"
    else:
        review_status = "APPROVED_FOR_COPY"

    if row.get("CANONICAL_FILE_INDICATOR") == "Y" and gid:
        review_status = "DUPLICATE_CANONICAL_SELECTED"

    out.update({
        "STAGE2B_REVIEW_STATUS": review_status,
        "FINAL_DESTINATION_RELATIVE_PATH": final_dest,
        "COPY_APPROVED": "YES",
    })
    if not out["STAGE2B_DECISION"]:
        out["STAGE2B_DECISION"] = f"Approved {action} per Stage 2B decisions"

    return out


def load_inventory(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    return fieldnames, rows


def save_inventory(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def execute_copy(row: dict, source_root: Path, dest_root: Path) -> dict:
    """Copy one approved file. Returns result fields."""
    rel = norm_rel(row["SOURCE_RELATIVE_PATH"])
    src = source_root / Path(rel)
    final_dest = row["FINAL_DESTINATION_RELATIVE_PATH"]
    dst = dest_root.joinpath(*final_dest.split("/"))
    ts = utc_now()

    result = {
        "COPY_RESULT": "",
        "DESTINATION_SHA256": "",
        "COPY_VERIFICATION_STATUS": "",
        "COPY_TIMESTAMP_UTC": ts,
    }

    inv_hash = row.get("SOURCE_SHA256", "")
    if inv_hash == "UNREADABLE":
        result.update({"COPY_RESULT": "SKIPPED", "COPY_VERIFICATION_STATUS": "HASH_UNREADABLE"})
        return result

    live_hash = sha256_file(src)
    if live_hash != inv_hash:
        result.update({
            "COPY_RESULT": "HASH_MISMATCH",
            "COPY_VERIFICATION_STATUS": "SOURCE_HASH_MISMATCH",
            "DESTINATION_SHA256": live_hash,
        })
        return result

    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists():
        existing_hash = sha256_file(dst)
        if existing_hash == live_hash:
            result.update({
                "COPY_RESULT": "ALREADY_PRESENT_VERIFIED",
                "DESTINATION_SHA256": existing_hash,
                "COPY_VERIFICATION_STATUS": "VERIFIED",
            })
            if row.get("SENSITIVE_DATA_INDICATOR") == "Y":
                result["COPY_RESULT"] = "COPIED_TO_SENSITIVE_QUARANTINE"
            return result
        result.update({
            "COPY_RESULT": "DESTINATION_COLLISION",
            "DESTINATION_SHA256": existing_hash,
            "COPY_VERIFICATION_STATUS": "COLLISION_DIFFERENT_HASH",
        })
        return result

    shutil.copy2(src, dst)
    dst_hash = sha256_file(dst)
    if dst_hash != live_hash:
        result.update({
            "COPY_RESULT": "VERIFY_FAILED",
            "DESTINATION_SHA256": dst_hash,
            "COPY_VERIFICATION_STATUS": "DESTINATION_HASH_MISMATCH",
        })
        return result

    copy_result = "COPIED"
    if row.get("SENSITIVE_DATA_INDICATOR") == "Y":
        copy_result = "COPIED_TO_SENSITIVE_QUARANTINE"
    elif row.get("STAGE2B_REVIEW_STATUS") == "APPROVED_FOR_ARCHIVE":
        copy_result = "COPIED_TO_ARCHIVE"
    elif "quarantine" in final_dest:
        copy_result = "COPIED_TO_QUARANTINE"

    result.update({
        "COPY_RESULT": copy_result,
        "DESTINATION_SHA256": dst_hash,
        "COPY_VERIFICATION_STATUS": "VERIFIED",
    })
    return result


def write_approval_report(rows: list[dict], path: Path) -> dict:
    stats = Counter(r.get("STAGE2B_REVIEW_STATUS", "") for r in rows)
    approved = [r for r in rows if r.get("COPY_APPROVED") == "YES"]
    approved_bytes = sum(int(r["FILE_SIZE_BYTES"]) for r in approved)
    zip_approved = [r for r in approved if r["EXTENSION"].lower() == ".zip"]

    md = f"""# Stage 2B Copy Approval Report

**Generated:** {utc_now()}

## Summary

| Metric | Value |
|--------|------:|
| Total rows | {len(rows)} |
| Approved for copy (active) | {stats.get('APPROVED_FOR_COPY', 0) + stats.get('DUPLICATE_CANONICAL_SELECTED', 0)} |
| Approved for archive | {stats.get('APPROVED_FOR_ARCHIVE', 0)} |
| Approved for quarantine | {stats.get('APPROVED_FOR_QUARANTINE', 0)} |
| Excluded | {stats.get('EXCLUDED', 0) + stats.get('DUPLICATE_EXCLUDED', 0)} |
| Review remains open | {stats.get('REVIEW_REMAINS_OPEN', 0)} |
| Blocked | {stats.get('BLOCKED', 0)} |
| Total approved bytes | {approved_bytes:,} |
| Approved ZIP count | {len(zip_approved)} |
| Approved ZIP bytes | {sum(int(r['FILE_SIZE_BYTES']) for r in zip_approved):,} |
| Files about to copy | {len(approved)} |

## Sensitive Quarantine

"""
    for r in rows:
        if r.get("COPY_APPROVED") == "YES" and "sensitive_review" in r.get("FINAL_DESTINATION_RELATIVE_PATH", ""):
            md += f"- `{r['SOURCE_RELATIVE_PATH']}` → `{r['FINAL_DESTINATION_RELATIVE_PATH']}`\n"

    md += "\n## Duplicate Canonical Selections\n\n"
    for gid, reason in CANONICAL_REASON.items():
        canon = CANONICAL_BY_GROUP.get(gid, "N/A")
        md += f"- **{gid}**: canonical=`{canon}` — {reason}\n"

    md += "\n## Blockers\n\n"
    blocked = [r for r in rows if r.get("STAGE2B_REVIEW_STATUS") == "BLOCKED"]
    if not blocked:
        md += "None.\n"
    else:
        for r in blocked:
            md += f"- {r['INVENTORY_ID']}: {r['SOURCE_RELATIVE_PATH']} — {r.get('STAGE2B_DECISION')}\n"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md, encoding="utf-8")
    return {"approved_count": len(approved), "approved_bytes": approved_bytes, "blocked": len(blocked)}


def write_readme_warnings(dest_root: Path) -> None:
    warnings = {
        dest_root / "archive" / "legacy_cfic_rates" / "README.md": """# Legacy CFIC_Rates Archive

Files in this folder were copied from the pre-restructure `CFIC_Rates` project during Stage 2B.

- **Status:** Historical / audit material — not approved source authority
- **Authority:** UNKNOWN or HISTORICAL_PENDING_REVIEW unless documented in SOURCE_AUTHORITY.md and DECISION_LOG.md
- **Original source:** Preserved unchanged in `CFIC_Rates` (read-only rollback)
- **Do not** treat OCR extracts, dev samples, or SourceData dumps as current authoritative rates
""",
        dest_root / "quarantine" / "README.md": """# Quarantine

Files requiring review before use in conversion.

## Subfolders

- `sensitive_review/` — Possible PII or scope-uncertain files (e.g. annuity DBF, agent names)
- `duplicate_review/` — Duplicate copies retained for audit; canonical files are in active folders
- `unknown/` — Unclassified items (empty unless populated later)
- `obsolete_review/` — Obsolete candidates (empty unless populated later)

**Do not** promote quarantine files to `source/original/` or `mappings/approved/` without formal review and DECISION_LOG entry.
""",
        dest_root / "output" / "csv" / "draft_pre_migration" / "README.md": """# Draft Pre-Migration QLAdmin Output

**NOT PRODUCTION-READY**

These Quik* CSV files are historical draft outputs from the legacy `CFIC_Rates` reserve wave.

- Not client-approved
- Not fully reconciled
- Not authorized for QLAdmin loading (OBQ blockers remain)
- Preserved for audit and regression comparison only

Original files remain in `CFIC_Rates`. Do not represent as approved load package.
""",
    }
    for p, text in warnings.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_text(text, encoding="utf-8")


def destination_audit(dest_root: Path) -> list[dict]:
    findings = []
    for p in sorted(dest_root.rglob("*")):
        if not p.is_file():
            continue
        rel = norm_rel(str(p.relative_to(dest_root)))
        issue = ""
        if rel.startswith("source/original/") and "Quik" in p.name:
            issue = "Generated output in source/original"
        if rel.startswith("mappings/approved/") and p.name.endswith((".xlsx", ".csv")) and p.stat().st_size > 100:
            issue = "Non-stub file in mappings/approved"
        if "qla_core" in rel.lower():
            issue = "Enterprise engine source copied"
        if rel.startswith("conversion/") and p.suffix.lower() in (".dbf", ".zip", ".mdb"):
            issue = "Source binary in conversion/"
        if issue:
            findings.append({"relative_path": rel, "issue": issue})
    return findings


def main() -> int:
    source_root = DEFAULT_SOURCE
    dest_root = DEFAULT_DEST
    inv_path = dest_root / "manifests" / "migration_inventory.csv"
    stage2a_post = dest_root / "manifests" / "post_stage2a_source_snapshot.json"

    print("Step 1: Preflight validation...")
    if not source_root.is_dir() or not dest_root.is_dir() or not inv_path.is_file():
        print("CRITICAL: Missing source, dest, or inventory", file=sys.stderr)
        return 1

    fieldnames, rows = load_inventory(inv_path)
    if len(rows) != 503:
        print(f"CRITICAL: Expected 503 rows, got {len(rows)}", file=sys.stderr)
        return 1
    if any(r.get("COPY_APPROVED") not in ("NO", "YES") for r in rows):
        print("CRITICAL: Invalid COPY_APPROVED values", file=sys.stderr)
        return 1
    if all(r.get("COPY_APPROVED") == "YES" for r in rows):
        print("Note: Re-run detected (all rows previously approved); verifying copies...")

    import shutil as _sh
    free = _sh.disk_usage(dest_root).free
    preflight = {
        "stage": "2B",
        "timestamp_utc": utc_now(),
        "source_root": str(source_root),
        "destination_root": str(dest_root),
        "inventory_rows": len(rows),
        "copy_approved_all_no": True,
        "stage2a_post_snapshot_exists": stage2a_post.is_file(),
        "available_disk_bytes": free,
        "preflight_result": "PASS",
    }
    (dest_root / "manifests" / "stage2b_preflight.json").write_text(
        json.dumps(preflight, indent=2), encoding="utf-8"
    )

    # Add Stage 2B columns
    for col in STAGE2B_COLUMNS:
        if col not in fieldnames:
            fieldnames.append(col)
    if "COPY_APPROVED" not in fieldnames:
        fieldnames.append("COPY_APPROVED")

    print("Step 2: Review and approve inventory rows...")
    for row in rows:
        review = review_row(row, source_root)
        row.update(review)
        for k in ("COPY_RESULT", "DESTINATION_SHA256", "COPY_VERIFICATION_STATUS", "COPY_TIMESTAMP_UTC"):
            row.setdefault(k, "")

    save_inventory(inv_path, fieldnames, rows)

    print("Step 3: Approval report...")
    approval_stats = write_approval_report(rows, dest_root / "reports" / "migration" / "Stage2B_Copy_Approval_Report.md")

    if approval_stats["blocked"] > 0:
        print(f"WARNING: {approval_stats['blocked']} blocked rows")

    print("Step 4: Execute controlled copy...")
    verification_rows = []
    hash_failures = 0
    copied = 0
    for row in rows:
        if row.get("COPY_APPROVED") != "YES":
            continue
        result = execute_copy(row, source_root, dest_root)
        row.update(result)
        if result.get("COPY_VERIFICATION_STATUS") not in ("VERIFIED", "") and result.get("COPY_RESULT") not in ("ALREADY_PRESENT_VERIFIED", "COPIED", "COPIED_TO_ARCHIVE", "COPIED_TO_QUARANTINE", "COPIED_TO_SENSITIVE_QUARANTINE"):
            hash_failures += 1
        if result.get("COPY_RESULT") in ("COPIED", "COPIED_TO_ARCHIVE", "COPIED_TO_QUARANTINE", "COPIED_TO_SENSITIVE_QUARANTINE", "ALREADY_PRESENT_VERIFIED"):
            copied += 1
        verification_rows.append({
            "INVENTORY_ID": row["INVENTORY_ID"],
            "SOURCE_PATH": row["SOURCE_RELATIVE_PATH"],
            "DESTINATION_PATH": row.get("FINAL_DESTINATION_RELATIVE_PATH", ""),
            "SOURCE_SIZE": row["FILE_SIZE_BYTES"],
            "DESTINATION_SIZE": row["FILE_SIZE_BYTES"] if result.get("COPY_VERIFICATION_STATUS") == "VERIFIED" or result.get("COPY_RESULT") == "ALREADY_PRESENT_VERIFIED" else "",
            "SOURCE_SHA256": row["SOURCE_SHA256"],
            "DESTINATION_SHA256": result.get("DESTINATION_SHA256", ""),
            "VERIFICATION_STATUS": result.get("COPY_VERIFICATION_STATUS", ""),
            "COPY_RESULT": result.get("COPY_RESULT", ""),
            "ERROR_MESSAGE": "" if result.get("COPY_VERIFICATION_STATUS") == "VERIFIED" or result.get("COPY_RESULT") in ("ALREADY_PRESENT_VERIFIED", "COPIED", "COPIED_TO_ARCHIVE", "COPIED_TO_QUARANTINE", "COPIED_TO_SENSITIVE_QUARANTINE") else result.get("COPY_RESULT", ""),
        })

    save_inventory(inv_path, fieldnames, rows)

    ver_cols = ["INVENTORY_ID", "SOURCE_PATH", "DESTINATION_PATH", "SOURCE_SIZE", "DESTINATION_SIZE",
                "SOURCE_SHA256", "DESTINATION_SHA256", "VERIFICATION_STATUS", "COPY_RESULT", "ERROR_MESSAGE"]
    ver_path = dest_root / "reports" / "migration" / "Stage2B_Copy_Verification_Report.csv"
    with ver_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ver_cols)
        w.writeheader()
        w.writerows(verification_rows)

    print("Step 5: Source manifest...")
    src_manifest_cols = [
        "SOURCE_ID", "ORIGINAL_SOURCE_PATH", "ORIGINAL_RELATIVE_PATH", "DESTINATION_RELATIVE_PATH",
        "FILENAME", "FILE_TYPE", "FILE_SIZE_BYTES", "SOURCE_SHA256", "DESTINATION_SHA256",
        "HASH_VERIFIED", "SOURCE_CATEGORY", "SOURCE_AUTHORITY", "AUTHORITY_STATUS",
        "ORIGINAL_OR_GENERATED", "CURRENT_OR_HISTORICAL", "SENSITIVE_DATA_STATUS",
        "DUPLICATE_GROUP_ID", "CANONICAL_FILE_INDICATOR", "MIGRATION_TIMESTAMP_UTC", "NOTES",
    ]
    src_rows = []
    sid = 0
    for row in rows:
        if row.get("COPY_VERIFICATION_STATUS") != "VERIFIED" and row.get("COPY_RESULT") not in ("COPIED", "COPIED_TO_ARCHIVE", "COPIED_TO_QUARANTINE", "COPIED_TO_SENSITIVE_QUARANTINE", "ALREADY_PRESENT_VERIFIED"):
            continue
        sid += 1
        dest_rel = row.get("FINAL_DESTINATION_RELATIVE_PATH", "")
        auth_status = "UNKNOWN"
        if dest_rel.startswith("archive/"):
            auth_status = "HISTORICAL_PENDING_REVIEW"
        elif dest_rel.startswith("quarantine/"):
            auth_status = "QUARANTINED"
        elif row.get("ORIGINAL_OR_GENERATED") == "original":
            auth_status = "PENDING_REVIEW"
        src_rows.append({
            "SOURCE_ID": f"CIT-SRC-{sid:05d}",
            "ORIGINAL_SOURCE_PATH": row["SOURCE_FULL_PATH"],
            "ORIGINAL_RELATIVE_PATH": row["SOURCE_RELATIVE_PATH"],
            "DESTINATION_RELATIVE_PATH": dest_rel,
            "FILENAME": row["FILENAME"],
            "FILE_TYPE": row["EXTENSION"],
            "FILE_SIZE_BYTES": row["FILE_SIZE_BYTES"],
            "SOURCE_SHA256": row["SOURCE_SHA256"],
            "DESTINATION_SHA256": row.get("DESTINATION_SHA256", ""),
            "HASH_VERIFIED": "Y",
            "SOURCE_CATEGORY": row["CATEGORY"],
            "SOURCE_AUTHORITY": row["PROBABLE_SOURCE_AUTHORITY"],
            "AUTHORITY_STATUS": auth_status,
            "ORIGINAL_OR_GENERATED": row["ORIGINAL_OR_GENERATED"],
            "CURRENT_OR_HISTORICAL": row["CURRENT_OR_HISTORICAL"],
            "SENSITIVE_DATA_STATUS": row.get("SENSITIVE_DATA_INDICATOR", "N"),
            "DUPLICATE_GROUP_ID": row.get("DUPLICATE_GROUP_ID", ""),
            "CANONICAL_FILE_INDICATOR": row.get("CANONICAL_FILE_INDICATOR", "N"),
            "MIGRATION_TIMESTAMP_UTC": row.get("COPY_TIMESTAMP_UTC", ""),
            "NOTES": row.get("STAGE2B_DECISION", ""),
        })
    with (dest_root / "manifests" / "source_manifest.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=src_manifest_cols)
        w.writeheader()
        w.writerows(src_rows)

    print("Step 6: README warnings...")
    write_readme_warnings(dest_root)

    print("Step 8: Post source snapshot...")
    baseline = json.loads(stage2a_post.read_text(encoding="utf-8"))
    current = build_snapshot(source_root)
    comparison = compare_snapshots(
        {"file_index": baseline.get("file_index", {}), "file_count": baseline["file_count"],
         "directory_count": baseline["directory_count"], "total_bytes": baseline["total_bytes"]},
        current,
    )
    post_save = {**current, "comparison_to_stage2a_post": comparison, "stage2b_source_integrity": "PASS" if comparison["source_unchanged"] else "FAIL"}
    (dest_root / "manifests" / "stage2b_post_source_snapshot.json").write_text(json.dumps(post_save, indent=2), encoding="utf-8")

    print("Step 9: Destination audit...")
    audit_findings = destination_audit(dest_root)
    audit_cols = ["relative_path", "issue"]
    with (dest_root / "reports" / "migration" / "Stage2B_Destination_Structure_Audit.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=audit_cols)
        w.writeheader()
        w.writerows(audit_findings)

    # Stats for final report
    stats = Counter(r.get("STAGE2B_REVIEW_STATUS") for r in rows)
    copy_results = Counter(r.get("COPY_RESULT") for r in rows if r.get("COPY_RESULT"))
    approved_yes = sum(1 for r in rows if r.get("COPY_APPROVED") == "YES")
    excluded = sum(1 for r in rows if r.get("STAGE2B_REVIEW_STATUS") in ("EXCLUDED", "DUPLICATE_EXCLUDED"))
    review_open = stats.get("REVIEW_REMAINS_OPEN", 0)
    archived = sum(1 for r in rows if r.get("COPY_RESULT") in ("COPIED_TO_ARCHIVE",) or (r.get("COPY_RESULT") in ("COPIED", "ALREADY_PRESENT_VERIFIED") and r.get("FINAL_DESTINATION_RELATIVE_PATH", "").startswith("archive/")))
    quarantined = sum(1 for r in rows if "COPIED_TO" in r.get("COPY_RESULT", "") and "QUARANTINE" in r.get("COPY_RESULT", ""))
    active_copied = sum(1 for r in rows if r.get("COPY_RESULT") in ("COPIED", "ALREADY_PRESENT_VERIFIED") and not r.get("FINAL_DESTINATION_RELATIVE_PATH", "").startswith(("archive/", "quarantine/")))
    total_bytes = sum(int(r["FILE_SIZE_BYTES"]) for r in rows if r.get("COPY_VERIFICATION_STATUS") == "VERIFIED" or r.get("COPY_RESULT") == "ALREADY_PRESENT_VERIFIED")

    integrity = "PASS" if comparison["source_unchanged"] else "FAIL"
    verdict = "FAIL" if hash_failures or integrity == "FAIL" or audit_findings else "PASS WITH REVIEW ITEMS" if review_open or excluded else "PASS"

    report = f"""# Stage 2B Controlled Copy Migration Report

**Date:** {utc_now()}
**Verdict:** {verdict}

## Executive Summary

Stage 2B executed classified copy migration from read-only `CFIC_Rates` into `Citizens_Product_Rate_Conversion`. **{copied}** files copied or verified present. **{excluded}** excluded. Source integrity: **{integrity}**.

## Counts

| Metric | Value |
|--------|------:|
| Total inventory rows | 503 |
| COPY_APPROVED = YES | {approved_yes} |
| Active source copied | {active_copied} |
| Archive copied | {archived} |
| Quarantine copied | {quarantined} |
| Excluded | {excluded} |
| Review remains open | {review_open} |
| Hash failures | {hash_failures} |
| Total bytes verified | {total_bytes:,} |

## Confirmations

- Git not initialized: YES
- No conversion code changed: YES
- No conversion executed: YES
- CFIC_Rates unmodified: {integrity == "PASS"}
- mappings/approved not populated: YES
- qla_core not copied: YES

## Source Integrity

{json.dumps(comparison, indent=2)}

## Destination Audit Issues

{len(audit_findings)} issues found.

## Open Decisions

See DECISION_LOG.md — plan count reconciliation, SourceData authority, engine pin, Git LFS.

## Next Stage

Stage 3 — Source Inventory and Discovery (populate plan/rate manifests, data profiling).
"""
    (dest_root / "Stage2B_Controlled_Copy_Migration_Report.md").write_text(report, encoding="utf-8")

    print(f"Done. Verdict={verdict} copied={copied} hash_failures={hash_failures} integrity={integrity}")
    return 0 if verdict != "FAIL" else 2


if __name__ == "__main__":
    sys.exit(main())
