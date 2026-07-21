"""
Citizens CFIC_Rates read-only inventory scanner.

Safety guarantees:
- Never writes to the source tree
- Never opens source files in write mode
- Never executes source scripts
- Never extracts ZIPs or opens MDB/DBF for repair
- Deterministic classification for unchanged source trees
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Text extensions scanned for path/reference indicators (read-only, size-capped)
TEXT_SCAN_EXTENSIONS = {
    ".py", ".md", ".txt", ".csv", ".json", ".yaml", ".yml", ".bat", ".ps1",
    ".cpy", ".PT1", ".pt1",
}
TEXT_SCAN_MAX_BYTES = 512_000

SENSITIVE_PATTERNS = [
    (re.compile(r"agentname", re.I), "agent_name_file"),
    (re.compile(r"cifianu1", re.I), "annuity_transaction_dbf"),
    (re.compile(r"ssn|social.?security", re.I), "possible_pii_keyword"),
]

ABSOLUTE_PATH_PATTERN = re.compile(
    r"[A-Za-z]:\\[^\s\"'<>|*?]+|/Users/[^\s\"'<>|*?]+|/home/[^\s\"'<>|*?]+"
)
CFIC_RATES_REF = re.compile(r"CFIC_Rates", re.I)
CITIZENS_REF = re.compile(r"Citizens|CFIC", re.I)
CSO_REF = re.compile(r"\bCSO\b|cso_|CSO-style|CSO style", re.I)
QLA_CORE_REF = re.compile(r"qla_core", re.I)
QLA_MIGRATION_REF = re.compile(r"QLA_Migration", re.I)

INVENTORY_COLUMNS = [
    "INVENTORY_ID", "SOURCE_FULL_PATH", "SOURCE_RELATIVE_PATH", "FILENAME",
    "EXTENSION", "FILE_SIZE_BYTES", "LAST_MODIFIED_UTC", "SOURCE_SHA256",
    "CATEGORY", "PROBABLE_PURPOSE", "PROBABLE_SOURCE_AUTHORITY",
    "ORIGINAL_OR_GENERATED", "CURRENT_OR_HISTORICAL", "APPROVAL_STATUS",
    "PROPOSED_DESTINATION_RELATIVE_PATH", "MIGRATION_ACTION",
    "CLASSIFICATION_CONFIDENCE", "CLASSIFICATION_BASIS",
    "DUPLICATE_GROUP_ID", "CASE_COLLISION_STATUS", "FILENAME_COLLISION_STATUS",
    "PATH_LENGTH_RISK", "HARDCODED_PATH_INDICATOR", "CSO_REFERENCE_INDICATOR",
    "QLA_CORE_REFERENCE_INDICATOR", "SENSITIVE_DATA_INDICATOR", "DEPENDS_ON",
    "RISK", "COPY_APPROVED", "NOTES",
]


@dataclass
class FileRecord:
    inventory_id: str
    full_path: Path
    relative_path: str
    filename: str
    extension: str
    size: int
    mtime_utc: str
    sha256: str
    category: str = ""
    purpose: str = ""
    authority: str = ""
    original_or_generated: str = ""
    current_or_historical: str = ""
    approval_status: str = "unknown"
    proposed_dest: str = ""
    migration_action: str = "UNKNOWN"
    confidence: str = "UNKNOWN"
    basis: str = ""
    duplicate_group_id: str = ""
    case_collision: str = "NONE"
    filename_collision: str = "NONE"
    path_length_risk: str = "LOW"
    hardcoded_path: str = "N"
    cso_ref: str = "N"
    qla_core_ref: str = "N"
    sensitive: str = "N"
    depends_on: str = ""
    risk: str = ""
    notes: str = ""
    text_scan: dict[str, Any] = field(default_factory=dict)


def utc_from_timestamp(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
    except (OSError, PermissionError):
        return "UNREADABLE"
    return h.hexdigest()


def scan_text_references(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "hardcoded_paths": [],
        "cfic_rates": False,
        "citizens": False,
        "cso": False,
        "qla_core": False,
        "qla_migration": False,
    }
    ext = path.suffix.lower()
    if ext not in {e.lower() for e in TEXT_SCAN_EXTENSIONS} and ext != "":
        return result
    try:
        if path.stat().st_size > TEXT_SCAN_MAX_BYTES:
            data = path.read_bytes()[:TEXT_SCAN_MAX_BYTES]
            text = data.decode("utf-8", errors="replace")
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return result

    paths = ABSOLUTE_PATH_PATTERN.findall(text)
    if paths:
        result["hardcoded_paths"] = list(dict.fromkeys(paths))[:20]

    result["cfic_rates"] = bool(CFIC_RATES_REF.search(text))
    result["citizens"] = bool(CITIZENS_REF.search(text))
    result["cso"] = bool(CSO_REF.search(text))
    result["qla_core"] = bool(QLA_CORE_REF.search(text))
    result["qla_migration"] = bool(QLA_MIGRATION_REF.search(text))
    return result


def norm_rel(path_str: str) -> str:
    return path_str.replace("\\", "/")


def classify(rel: str, filename: str, ext: str, size: int) -> tuple:
    """Return classification tuple for a source file."""
    r = norm_rel(rel).lower()
    fn = filename.lower()
    e = ext.lower() if ext else "(no ext)"

    # Temporary
    if "__pycache__" in r or e == ".pyc":
        return (
            "Temporary files", "Python bytecode cache", "derived", "generated",
            "historical", "unknown", "", "EXCLUDE_TEMPORARY", "HIGH",
            "path contains __pycache__ or .pyc extension", "",
        )
    if fn.startswith("~$"):
        return (
            "Temporary files", "Excel lock file", "derived", "generated",
            "current", "unknown", "", "EXCLUDE_TEMPORARY", "HIGH",
            "Excel lock filename prefix ~$", "Exclude from migration",
        )

    # Sensitive quarantine
    if "cifianu1" in fn:
        return (
            "Database extracts", "Annuity payment transactions DBF", "client",
            "original", "current", "unknown",
            "quarantine/sensitive_review/cifianu1.dbf",
            "COPY_TO_QUARANTINE", "MEDIUM",
            "annuity DBF scope unconfirmed for life rates",
            "Review before any conversion use",
        )
    if fn == "agentname.csv":
        return (
            "CSV files", "Agent name reference extract", "client", "original",
            "current", "unknown",
            "quarantine/sensitive_review/AgentName.csv",
            "COPY_TO_QUARANTINE", "HIGH",
            "filename AgentName.csv", "Possible PII",
        )

    # Duplicate review - root zip
    if r == "cfiproposalmaker.zip":
        return (
            "Archive files", "Duplicate of source/CFIProposalMaker.zip",
            "client", "original", "current", "unknown", "",
            "DO_NOT_MIGRATE", "HIGH",
            "duplicate of source/CFIProposalMaker.zip",
            "Keep canonical copy in source/original/access/",
        )
    if r == "extracted/cfiproposalmakerrev2.mdb":
        return (
            "Database extracts", "Duplicate MDB copy", "client", "original",
            "current", "unknown", "",
            "DUPLICATE_REVIEW", "HIGH",
            "duplicate of source/CFIProposalMakerRev2.mdb", "",
        )
    if r == "cfic_cash_values/multiplecashvaluefiles.zip":
        return (
            "Archive files", "Bundled cash-value ZIPs", "client", "original",
            "current", "unknown",
            "quarantine/duplicate_review/MultipleCashValueFiles.zip",
            "COPY_TO_QUARANTINE", "MEDIUM",
            "may overlap per-family *_CV.zip archives", "Audit overlap",
        )

    # Dev/sample/OCR generated
    if "_dev_p7mn" in r or "_sample_plp" in r or "_sample_pdfs" in r:
        return (
            "Temporary files", "Development or sample artifact", "derived",
            "generated", "historical", "unknown",
            "archive/legacy_cfic_rates/dev_samples/" + norm_rel(rel),
            "EXCLUDE_GENERATED", "HIGH",
            "dev or sample path segment", "",
        )
    if "docs/_ocr_extract" in r:
        return (
            "Generated output", "OCR text/image extract", "derived", "generated",
            "historical", "unknown",
            "archive/legacy_cfic_rates/ocr_extract/" + Path(rel).name,
            "COPY_TO_ARCHIVE", "HIGH",
            "OCR output not authoritative", "",
        )

    # Legacy SourceData
    if r.startswith("sourcedata_11-18-2024/"):
        return (
            "Archive files", "Legacy Citizens source dump Nov 2024", "client",
            "original", "historical", "unknown",
            "archive/legacy_cfic_rates/SourceData_11-18-2024/" + rel.split("/", 1)[-1],
            "COPY_TO_ARCHIVE", "MEDIUM",
            "legacy dump authority unconfirmed", "Quarantine review",
        )

    # Canonical DBF sources
    if r in ("docs/cifi0007.dbf",):
        return (
            "Database extracts", "Primary Reserve DBF (~369K rows)", "client",
            "original", "current", "unknown",
            "source/original/dbf/cifi0007.DBF", "COPY", "HIGH",
            "authoritative reserve source in legacy discovery", "",
        )
    if r == "docs/cifi0004.dbf":
        return (
            "Database extracts", "Plans master DBF", "client", "original",
            "current", "unknown",
            "source/original/dbf/cifi0004.dbf", "COPY", "HIGH",
            "plans table source", "",
        )

    # Access source
    if r.startswith("source/"):
        dest = "source/original/access/" + Path(rel).name
        return (
            "Source data files", "Canonical Access Proposal Maker archive",
            "client", "original", "current", "unknown", dest, "COPY", "HIGH",
            "source/ folder designated canonical", "",
        )

    # Excel mappings (working)
    if fn == "citizens_plan_crosswak.xlsx":
        return (
            "Crosswalks", "CFIC plan to QLPlan crosswalk (working)", "client",
            "original", "current", "working",
            "mappings/working/plans/Citizens_Plan_Crosswalk.xlsx",
            "COPY_AND_RENAME", "HIGH",
            "root crosswalk xlsx", "Rename typo Crosswak->Crosswalk",
        )
    if fn == "citizens_plan_rate_requirements_catalog.xlsx":
        return (
            "Mapping files", "Plan rate requirements catalog", "client",
            "original", "current", "working",
            "mappings/working/rate_types/Citizens_Plan_Rate_Requirements_Catalog.xlsx",
            "COPY", "HIGH", "requirements catalog", "",
        )

    # Cash value ZIPs
    if r.startswith("cfic_cash_values/") and e == ".zip" and "_cv.zip" in fn:
        return (
            "Rate files", "Cash-value green-sheet PDF archive", "client",
            "original", "current", "unknown",
            "source/original/cash_values/" + filename, "COPY", "HIGH",
            "per-family CV zip", "Large file; LFS or external store",
        )

    # Docs PDFs (rate sheets)
    if r.startswith("docs/") and e == ".pdf":
        return (
            "PDFs", "Product or rate sheet PDF", "client", "original",
            "current", "unknown",
            "source/product_documents/rate_sheets/" + filename, "COPY", "HIGH",
            "docs pdf not in ocr_extract", "",
        )

    # Access extracted CSVs
    if r.startswith("extracted/") and e == ".csv":
        return (
            "CSV files", "Access MDB table export", "client", "original",
            "current", "unknown",
            "source/extracts/access/" + filename, "COPY", "HIGH",
            "Access extract csv", "",
        )

    # Staging generated
    if r.startswith("extracted_reserve/"):
        return (
            "Generated output", "Reserve DBF per-plan staging grid", "derived",
            "generated", "current", "working",
            "staging/normalized_rates/reserve/" + "/".join(Path(rel).parts[1:]),
            "COPY", "MEDIUM",
            "generated from cifi0007.DBF", "Not source authority",
        )
    if r.startswith("extracted_plans/"):
        return (
            "Generated output", "Plans DBF staging export", "derived",
            "generated", "current", "working",
            "staging/normalized_plans/" + "/".join(Path(rel).parts[1:]),
            "COPY", "MEDIUM", "generated from cifi0004.dbf", "",
        )
    if r.startswith("extracted_pdf_rates/"):
        return (
            "Generated output", "PDF gross premium pilot staging", "derived",
            "generated", "current", "working",
            "staging/normalized_rates/pdf_gross/" + "/".join(Path(rel).parts[1:]),
            "COPY", "MEDIUM", "Issue 02 pilot staging", "",
        )
    if r.startswith("extracted_green_sheets/"):
        return (
            "Generated output", "Green-sheet OCR pilot staging", "derived",
            "generated", "historical", "working",
            "archive/legacy_cfic_rates/green_sheet_pilot/" + "/".join(Path(rel).parts[1:]),
            "COPY_TO_ARCHIVE", "HIGH", "OCR pilot FAIL", "",
        )

    # Output Quik tables
    if ("output/rates/" in r or "output/rates/" in r) and fn.startswith("quik"):
        return (
            "Generated output", "QLAdmin draft rate load CSV", "derived",
            "generated", "current", "working",
            "output/csv/draft_reserve_wave/" + filename,
            "COPY", "MEDIUM",
            "draft Quik output not client-approved", "OBQ blockers",
        )
    if (r.startswith("output/") or r.startswith("output/")) and fn == "readme.md":
        return (
            "Documentation", "Output folder README", "derived", "generated",
            "current", "unknown",
            "docs/runbooks/legacy_output_readme.md",
            "COPY_AND_RENAME", "MEDIUM", "output readme", "",
        )

    # Reports and validation
    if r.startswith("reports/"):
        return (
            "Validation reports", "Conversion run report", "derived",
            "generated", "current", "unknown",
            "reports/audit/" + filename, "COPY", "HIGH",
            "reports folder", "",
        )
    if r.startswith("validation/") or r.startswith("validation/"):
        return (
            "Validation reports", "Validation evidence CSV", "derived",
            "generated", "current", "unknown",
            "validation/rate_validation/" + filename, "COPY", "HIGH",
            "validation evidence", "",
        )

    # Tracking / discovery
    if r.startswith("tracking/"):
        if e == ".py":
            dest = "tools/reporting/" + filename
            cat = "Scripts"
        else:
            dest = "discovery/rates/" + filename
            cat = "CSV files"
        return (
            cat, "Rate load tracker material", "derived", "mixed", "current",
            "working", dest, "COPY", "HIGH", "tracking folder", "",
        )

    # Issue log
    if r.startswith("issue_log/"):
        parts = Path(rel)
        if e == ".py":
            dest = "archive/legacy_cfic_rates/issues/" + "/".join(parts.parts[1:])
            cat = "Scripts"
            action = "COPY"
        elif "business_inputs" in r:
            dest = "mappings/working/business_inputs/" + parts.name
            cat = "Mapping files"
            action = "COPY"
        elif "evidence" in r:
            dest = "validation/rate_validation/legacy_evidence/" + "/".join(parts.parts[2:])
            cat = "Validation reports"
            action = "COPY"
        else:
            dest = "issues/closed/legacy_" + "/".join(parts.parts[1:])
            cat = "Documentation"
            action = "COPY"
        return (
            cat, "CFIC issue framework artifact", "derived", "mixed", "current",
            "working", dest, action, "HIGH", "issue_log path", "",
        )

    # Scripts
    if r == "cfic_paths.py":
        return (
            "Configuration files", "Legacy path configuration module", "derived",
            "generated", "current", "working",
            "conversion/orchestration/legacy_cfic_paths.py",
            "COPY_AND_RENAME", "HIGH",
            "root path module", "Retarget in Development gate",
        )
    if r.startswith("scripts/"):
        return (
            "Scripts", "Legacy packaging orchestration script", "derived",
            "generated", "current", "working",
            "conversion/orchestration/" + filename, "COPY", "HIGH",
            "scripts folder", "Engine dependency documented only",
        )
    if r.startswith("docs/") and e == ".md":
        return (
            "Documentation", "Discovery or platform documentation", "derived",
            "mixed", "current", "unknown",
            "docs/source_layout/" + filename, "COPY", "HIGH",
            "docs markdown", "",
        )
    if r.startswith("docs/") and e == ".csv":
        return (
            "CSV files", "Plan/rate inventory CSV", "derived", "generated",
            "current", "working",
            "discovery/plans/" + filename, "COPY", "HIGH",
            "docs inventory csv", "",
        )
    if r.startswith("docs/") and e == ".py":
        return (
            "Scripts", "Inventory builder script", "derived", "generated",
            "current", "working",
            "tools/inventory/legacy_" + filename, "COPY_AND_RENAME", "HIGH",
            "docs python utility", "",
        )

    # Root documentation
    if r in ("readme.md", "run_guide.md"):
        dest = "docs/runbooks/" + ("README_legacy.md" if fn == "readme.md" else "RUN_GUIDE_legacy.md")
        return (
            "Documentation", "Legacy project documentation", "derived", "mixed",
            "current", "unknown", dest, "COPY_AND_RENAME", "HIGH",
            "root md file", "",
        )

    # Empty mapping folder - nothing usually
    if r.startswith("mapping/"):
        return (
            "Unknown or unclassified files", "Empty mapping placeholder", "unknown",
            "unknown", "historical", "unknown", "", "DO_NOT_MIGRATE", "LOW",
            "empty placeholder", "",
        )

    # Default by extension
    ext_defaults = {
        ".zip": ("Archive files", "Archive bundle", "client", "original", "current",
                 "unknown", "archive/legacy_cfic_rates/" + filename, "REVIEW_REQUIRED", "LOW"),
        ".dbf": ("Database extracts", "FoxPro DBF", "client", "original", "current",
                 "unknown", "source/original/dbf/" + filename, "REVIEW_REQUIRED", "MEDIUM"),
        ".mdb": ("Database extracts", "Access database", "client", "original", "current",
                 "unknown", "source/original/access/" + filename, "COPY", "MEDIUM"),
        ".pdf": ("PDFs", "PDF document", "client", "original", "current",
                 "unknown", "source/product_documents/" + filename, "REVIEW_REQUIRED", "LOW"),
        ".csv": ("CSV files", "CSV data file", "mixed", "mixed", "current",
                 "unknown", "discovery/source_analysis/" + filename, "REVIEW_REQUIRED", "LOW"),
        ".py": ("Python files", "Python script", "derived", "generated", "current",
                "working", "archive/legacy_cfic_rates/scripts/" + filename, "REVIEW_REQUIRED", "LOW"),
        ".json": ("Configuration files", "JSON metadata", "derived", "generated", "current",
                  "unknown", "reports/audit/" + filename, "COPY", "MEDIUM"),
        ".txt": ("Text files", "Text log or extract", "mixed", "mixed", "current",
                 "unknown", "discovery/source_analysis/" + filename, "REVIEW_REQUIRED", "LOW"),
        ".png": ("Temporary files", "Image render artifact", "derived", "generated",
                 "historical", "unknown", "", "EXCLUDE_GENERATED", "MEDIUM"),
        ".pt1": ("Rate files", "Legacy print rate file", "client", "original", "historical",
                 "unknown", "archive/legacy_cfic_rates/" + filename, "COPY_TO_ARCHIVE", "MEDIUM"),
        ".cpy": ("Text files", "Legacy copybook", "client", "original", "historical",
                 "unknown", "archive/legacy_cfic_rates/copybooks/" + filename, "COPY_TO_ARCHIVE", "MEDIUM"),
        ".dat": ("Source data files", "Legacy data file", "client", "original", "historical",
                 "unknown", "archive/legacy_cfic_rates/" + filename, "COPY_TO_ARCHIVE", "LOW"),
    }
    if e in ext_defaults:
        cat, purp, auth, orig, cur, appr, dest, act, conf = ext_defaults[e]
        return (cat, purp, auth, orig, cur, appr, dest, act, conf, f"extension default {e}", "")

    return (
        "Unknown or unclassified files", "Unclassified file", "unknown", "unknown",
        "unknown", "unknown",
        "quarantine/unknown/" + filename,
        "REVIEW_REQUIRED", "LOW", "no classification rule matched", "",
    )


def collect_source_files(source_root: Path) -> list[Path]:
    files: list[Path] = []
    for p in sorted(source_root.rglob("*")):
        if p.is_file():
            files.append(p)
    return files


def build_snapshot(source_root: Path) -> dict[str, Any]:
    files = collect_source_files(source_root)
    ext_counts: dict[str, int] = defaultdict(int)
    total_bytes = 0
    file_entries = []
    for p in files:
        st = p.stat()
        total_bytes += st.st_size
        ext = p.suffix.lower() if p.suffix else "(no ext)"
        ext_counts[ext] += 1
        file_entries.append({
            "relative_path": norm_rel(str(p.relative_to(source_root))),
            "size": st.st_size,
            "mtime_utc": utc_from_timestamp(st.st_mtime),
        })

    dir_count = sum(1 for d in source_root.rglob("*") if d.is_dir())
    largest = sorted(file_entries, key=lambda x: x["size"], reverse=True)[:25]

    return {
        "source_root": str(source_root),
        "scan_timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "file_count": len(files),
        "directory_count": dir_count,
        "total_bytes": total_bytes,
        "extension_counts": dict(sorted(ext_counts.items(), key=lambda x: (-x[1], x[0]))),
        "largest_25_files": largest,
        "file_index": {
            e["relative_path"]: {"size": e["size"], "mtime_utc": e["mtime_utc"]}
            for e in file_entries
        },
    }


def compare_snapshots(preflight: dict, post: dict) -> dict[str, Any]:
    pre_idx = preflight.get("file_index", {})
    post_idx = post.get("file_index", {})
    pre_set = set(pre_idx)
    post_set = set(post_idx)

    added = sorted(post_set - pre_set)
    missing = sorted(pre_set - post_set)
    modified = []
    for rel in sorted(pre_set & post_set):
        if pre_idx[rel]["mtime_utc"] != post_idx[rel]["mtime_utc"]:
            modified.append({
                "relative_path": rel,
                "preflight_mtime": pre_idx[rel]["mtime_utc"],
                "post_mtime": post_idx[rel]["mtime_utc"],
            })

    return {
        "file_count_delta": post["file_count"] - preflight["file_count"],
        "directory_count_delta": post["directory_count"] - preflight["directory_count"],
        "total_bytes_delta": post["total_bytes"] - preflight["total_bytes"],
        "added_files": added,
        "missing_files": missing,
        "modified_mtime_files": modified,
        "source_unchanged": (
            not added and not missing and not modified
            and post["file_count"] == preflight["file_count"]
            and post["total_bytes"] == preflight["total_bytes"]
        ),
    }


def inventory_source(
    source_root: Path,
    dest_project: Path,
) -> tuple[list[FileRecord], dict[str, Any]]:
    files = collect_source_files(source_root)
    records: list[FileRecord] = []

    # Pre-pass: case-insensitive path map
    case_map: dict[str, list[str]] = defaultdict(list)
    filename_map: dict[str, list[str]] = defaultdict(list)
    for p in files:
        rel = norm_rel(str(p.relative_to(source_root)))
        case_map[rel.lower()].append(rel)
        filename_map[p.name.lower()].append(rel)

    hash_map: dict[str, list[str]] = defaultdict(list)

    for idx, p in enumerate(files, start=1):
        rel = norm_rel(str(p.relative_to(source_root)))
        st = p.stat()
        ext = p.suffix if p.suffix else ""
        digest = sha256_file(p)
        unreadable = digest == "UNREADABLE"

        inv_id = f"CIT-INV-{idx:05d}"
        rec = FileRecord(
            inventory_id=inv_id,
            full_path=p,
            relative_path=rel,
            filename=p.name,
            extension=ext,
            size=st.st_size,
            mtime_utc=utc_from_timestamp(st.st_mtime),
            sha256=digest,
        )
        if unreadable:
            rec.notes = "SHA-256 unreadable (locked or permission denied)"
        hash_map[digest].append(rel)

        # Classify
        cls = classify(rel, p.name, ext, st.st_size)
        (rec.category, rec.purpose, rec.authority, rec.original_or_generated,
         rec.current_or_historical, rec.approval_status, rec.proposed_dest,
         rec.migration_action, rec.confidence, rec.basis, cls_notes) = cls
        if cls_notes:
            rec.notes = (rec.notes + "; " + cls_notes).strip("; ") if rec.notes else cls_notes

        # Case collision
        if len(case_map[rel.lower()]) > 1:
            rec.case_collision = "CASE_COLLISION"
            rec.risk = (rec.risk + "; case-insensitive path duplicate").strip("; ")

        # Filename collision (different paths, same name)
        same_name = filename_map[p.name.lower()]
        if len(same_name) > 1:
            rec.filename_collision = "FILENAME_COLLISION"

        # Path length risk for proposed destination
        if rec.proposed_dest:
            full_dest = dest_project / rec.proposed_dest
            dest_len = len(str(full_dest))
            if dest_len > 240:
                rec.path_length_risk = "HIGH"
            elif dest_len > 200:
                rec.path_length_risk = "MEDIUM"

        # Text scan
        scan = scan_text_references(p)
        rec.text_scan = scan
        if scan.get("hardcoded_paths"):
            rec.hardcoded_path = "Y"
        if scan.get("cso"):
            rec.cso_ref = "Y"
        if scan.get("qla_core"):
            rec.qla_core_ref = "Y"

        # Sensitive
        for pat, label in SENSITIVE_PATTERNS:
            if pat.search(rel) or pat.search(p.name):
                rec.sensitive = "Y"
                rec.risk = (rec.risk + f"; {label}").strip("; ")

        records.append(rec)

    # Duplicate groups by hash
    dup_id = 0
    for digest, paths in hash_map.items():
        if digest == "UNREADABLE":
            continue
        if len(paths) > 1:
            dup_id += 1
            gid = f"DUP-{dup_id:04d}"
            for rec in records:
                if rec.sha256 == digest:
                    rec.duplicate_group_id = gid
                    if rec.migration_action not in ("DO_NOT_MIGRATE", "EXCLUDE_TEMPORARY", "EXCLUDE_GENERATED"):
                        if not rec.notes:
                            rec.notes = f"SHA-256 duplicate group {gid}"

    meta = {
        "source_root": str(source_root),
        "file_count": len(records),
        "hash_duplicate_groups": dup_id,
    }
    return records, meta


def record_to_row(rec: FileRecord) -> dict[str, str]:
    return {
        "INVENTORY_ID": rec.inventory_id,
        "SOURCE_FULL_PATH": str(rec.full_path),
        "SOURCE_RELATIVE_PATH": rec.relative_path,
        "FILENAME": rec.filename,
        "EXTENSION": rec.extension,
        "FILE_SIZE_BYTES": str(rec.size),
        "LAST_MODIFIED_UTC": rec.mtime_utc,
        "SOURCE_SHA256": rec.sha256,
        "CATEGORY": rec.category,
        "PROBABLE_PURPOSE": rec.purpose,
        "PROBABLE_SOURCE_AUTHORITY": rec.authority,
        "ORIGINAL_OR_GENERATED": rec.original_or_generated,
        "CURRENT_OR_HISTORICAL": rec.current_or_historical,
        "APPROVAL_STATUS": rec.approval_status,
        "PROPOSED_DESTINATION_RELATIVE_PATH": rec.proposed_dest,
        "MIGRATION_ACTION": rec.migration_action,
        "CLASSIFICATION_CONFIDENCE": rec.confidence,
        "CLASSIFICATION_BASIS": rec.basis,
        "DUPLICATE_GROUP_ID": rec.duplicate_group_id,
        "CASE_COLLISION_STATUS": rec.case_collision,
        "FILENAME_COLLISION_STATUS": rec.filename_collision,
        "PATH_LENGTH_RISK": rec.path_length_risk,
        "HARDCODED_PATH_INDICATOR": rec.hardcoded_path,
        "CSO_REFERENCE_INDICATOR": rec.cso_ref,
        "QLA_CORE_REFERENCE_INDICATOR": rec.qla_core_ref,
        "SENSITIVE_DATA_INDICATOR": rec.sensitive,
        "DEPENDS_ON": rec.depends_on,
        "RISK": rec.risk,
        "COPY_APPROVED": "NO",
        "NOTES": rec.notes,
    }


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
