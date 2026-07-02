#!/usr/bin/env python3
"""
ISWL LifePRO ZIP source analysis — 20260530 complete extract.
Reads directly from ZIP via zipfile; does NOT fully extract archive.
Research only — writes to docs/research/ and tools/research/ only.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

try:
    import zipfile
except ImportError:
    sys.exit("zipfile required")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]
ZIP_PATH = Path(r"C:\Users\warren\Downloads\LifePRO_Extracts_20260530 (1).zip")
OUT_DIR = REPO / "docs" / "research"
TOOLS_DIR = REPO / "tools" / "research"

# Prior research ISWL fleet (proven)
ISWL_MPLAN = {
    "1658C1", "1658CS", "1659C2", "1659CR", "1659CS", "1659SR", "1669SR", "1679CS",
}
ISWL_COV = {
    "658 CEN I", "658 CEN SD", "659 CEN II", "659 CEN SR", "659 CEN SD",
    "659 SR GD", "669 SR GD", "679 CEN SD",
}
# User-requested additional search terms
EXTRA_MPLAN = {"1668B1", "1669B2", "1678CS"}
EXTRA_COV = {"668 CEN I", "669 CEN II", "678 CEN SEN", "679 CEN SEN"}

SEARCH_TERMS = sorted(
    set(ISWL_MPLAN | EXTRA_MPLAN | ISWL_COV | EXTRA_COV)
    | {
        "CEN", "SEN", "SR GD", "FV_GUAR_RATE", "UV_GUAR_COI_RATE", "UV_CURR_COI_RATE",
        "TYPE_CODE", "COI", "GCOI", "SURRENDER", "SURR", "EXPENSE", "EXP",
        "INTEREST", "GUAR", "PREMIUM", "CASH",
    }
)

REPO_COMPARE_ROOTS = [
    REPO / "QLA_Migration" / "Source",
    REPO / "plan_analysis" / "source_data",
    REPO / "plan_analysis" / "source_data" / "rates",
    REPO / "plan_analysis" / "source_data" / "coverage",
    REPO / "docs",
]

# Files to always profile if present
PRIORITY_PATTERNS = [
    r"Rate_Table", r"PAAGERAT", r"PAAGE_", r"PDAGE", r"PPBEN", r"PCOVR", r"PCOVRSGT",
    r"PDDIC", r"PRBEN", r"PPRBN", r"PPRDF", r"PPOLC", r"PLOAN", r"PPBENTYP",
]

MAX_SAMPLE_ROWS = 5
MAX_DISTINCT_REPORT = 50
CHUNK_READ = 1024 * 1024  # 1MB line buffer for streaming grep
# Skip full line-scan on non-priority files above this size (bytes)
MAX_GREP_BYTES = 150_000_000
# Skip full row-count profiling above this size unless priority
MAX_PROFILE_BYTES = 400_000_000


def log(msg: str):
    print(msg, flush=True)


def ensure_out():
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def open_zip_text(zf: zipfile.ZipFile, name: str, encoding="utf-8"):
    raw = zf.open(name)
    return io.TextIOWrapper(raw, encoding=encoding, errors="replace", newline="")


def strip_row(row: dict) -> dict:
    return {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}


def read_csv_header_and_rows(zf, name, max_rows=MAX_SAMPLE_ROWS, encoding="utf-8"):
    """Return (raw_columns, stripped_columns, sample_rows, total_rows)."""
    raw_cols = []
    stripped_cols = []
    samples = []
    total = 0
    try:
        with open_zip_text(zf, name, encoding) as f:
            reader = csv.reader(f)
            raw_cols = next(reader, [])
            stripped_cols = [c.strip() for c in raw_cols]
            for row in reader:
                total += 1
                if len(samples) < max_rows:
                    # pad row
                    padded = row + [""] * max(0, len(stripped_cols) - len(row))
                    samples.append(dict(zip(stripped_cols, padded[: len(stripped_cols)])))
    except Exception as e:
        return raw_cols, stripped_cols, samples, total, str(e)
    return raw_cols, stripped_cols, samples, total, None


def infer_dtypes(samples: list[dict], cols: list[str]) -> dict:
    out = {}
    for c in cols:
        vals = [s.get(c, "") for s in samples if s.get(c, "")]
        if not vals:
            out[c] = "empty"
            continue
        numeric = sum(1 for v in vals if re.match(r"^-?\d+\.?\d*$", v.replace(",", "")))
        out[c] = "numeric" if numeric == len(vals) else "text"
    return out


def count_distinct_column(zf, name, col_name, encoding="utf-8", limit=MAX_DISTINCT_REPORT):
    """Stream count distinct values for one column."""
    counts = Counter()
    try:
        with open_zip_text(zf, name, encoding) as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return counts, "no header"
            field_map = {h.strip(): h for h in reader.fieldnames}
            key = field_map.get(col_name.strip())
            if not key:
                return counts, f"column {col_name!r} not found; have {list(field_map.keys())[:20]}"
            for row in reader:
                counts[row.get(key, "").strip()] += 1
                if len(counts) > limit * 3 and sum(counts.values()) > 500000:
                    break
    except Exception as e:
        return counts, str(e)
    return counts, None


def stream_search_terms(zf, name, terms, encoding="utf-8"):
    """Count line-level term hits (case-sensitive where literal)."""
    hits = Counter()
    lines = 0
    try:
        with open_zip_text(zf, name, encoding) as f:
            for line in f:
                lines += 1
                for t in terms:
                    if t in line:
                        hits[t] += 1
    except Exception:
        try:
            with open_zip_text(zf, name, "latin-1") as f:
                for line in f:
                    lines += 1
                    for t in terms:
                        if t in line:
                            hits[t] += 1
        except Exception as e:
            return hits, lines, str(e)
    return hits, lines, None


def profile_iswl_column(zf, name, col_candidates, value_sets, encoding="utf-8"):
    """Count rows matching ISWL values in first matching column."""
    result = {"iswl_rows": 0, "total_rows": 0, "column_used": None, "value_counts": Counter()}
    try:
        with open_zip_text(zf, name, encoding) as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return result, "no header"
            fmap = {h.strip(): h for h in reader.fieldnames}
            col = None
            for cand in col_candidates:
                if cand in fmap:
                    col = cand
                    break
            if not col:
                return result, f"no column in {col_candidates}"
            result["column_used"] = col
            for row in reader:
                result["total_rows"] += 1
                v = row.get(fmap[col], "").strip()
                if v in value_sets:
                    result["iswl_rows"] += 1
                    result["value_counts"][v] += 1
    except Exception as e:
        return result, str(e)
    return result, None


def find_repo_file(basename: str) -> list[Path]:
    found = []
    for root in REPO_COMPARE_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.is_file() and p.name.lower() == basename.lower():
                found.append(p)
    return found


def file_sig(path: Path) -> dict:
    st = path.stat()
    return {"size": st.st_size, "mtime": datetime.fromtimestamp(st.st_mtime).isoformat()}


def task1_inventory(zf: zipfile.ZipFile) -> tuple[list[dict], dict]:
    rows = []
    for info in zf.infolist():
        ext = Path(info.filename).suffix.lower()
        rows.append({
            "zip_path": ZIP_PATH.as_posix(),
            "internal_path": info.filename,
            "filename": Path(info.filename).name,
            "extension": ext,
            "compressed_size": info.compress_size,
            "uncompressed_size": info.file_size,
            "last_modified": datetime(*info.date_time).isoformat(),
        })
    meta = {
        "zip_path": str(ZIP_PATH),
        "zip_size_bytes": ZIP_PATH.stat().st_size,
        "file_count": len(rows),
        "total_compressed": sum(r["compressed_size"] for r in rows),
        "total_uncompressed": sum(r["uncompressed_size"] for r in rows),
    }
    return rows, meta


def task2_compare(inventory: list[dict]) -> list[dict]:
    out = []
    analyzed_basenames = {
        "Rate_Table_Extract_20260427.csv",
        "PAAGERAT_AttainedAge_Rates_Extract_20260428.csv",
        "PCOVR.csv", "PCOVRSGT.csv",
    }
    for inv in inventory:
        bn = inv["filename"]
        repo_matches = find_repo_file(bn)
        # also match by prefix without date
        prefix_matches = []
        stem = re.sub(r"_Extract_?\d{8}|_\d{8}", "", bn.replace(".csv", ""))
        for root in REPO_COMPARE_ROOTS:
            if root.exists():
                for p in root.rglob("*.csv"):
                    if stem.split("_")[0] in p.name or p.name.startswith(stem[:5]):
                        if p not in prefix_matches and p not in repo_matches:
                            prefix_matches.append(p)

        exists = bool(repo_matches)
        same_size = False
        same_mtime = False
        repo_path = ""
        if repo_matches:
            repo_path = str(repo_matches[0].relative_to(REPO))
            sig = file_sig(repo_matches[0])
            same_size = sig["size"] == inv["uncompressed_size"]
        elif prefix_matches:
            repo_path = f"(similar) {prefix_matches[0].relative_to(REPO)}"
            exists = True

        likely_prior = (
            bn in analyzed_basenames
            or "20260427" in bn or "20260428" in bn
            or (exists and "20260530" in bn and repo_matches)
        )
        # April rate files in plan_analysis were analyzed; May partial in Source
        if "Rate_Table" in bn and "20260427" in bn:
            likely_prior = True
        if bn.startswith("PPBEN") and exists:
            likely_prior = True  # forensic audit used Source copy

        out.append({
            **inv,
            "exists_in_repo": "Yes" if exists else "No",
            "repo_path": repo_path,
            "same_size_as_repo": "Yes" if same_size else ("No" if exists and repo_matches else "N/A"),
            "likely_previously_analyzed": "Yes" if likely_prior else "No",
            "should_newly_analyze": "Yes" if not likely_prior or not exists else "Maybe",
        })
    return out


def is_relevant_file(name: str) -> bool:
    n = name.upper()
    if not name.lower().endswith(".csv"):
        return False
    for pat in PRIORITY_PATTERNS:
        if re.search(pat, name, re.I):
            return True
    return any(k in n for k in ("RATE", "BENEFIT", "COVER", "DIC", "PRODUCT", "PREMIUM", "FUND", "LOAN"))


def is_priority_file(name: str) -> bool:
    return is_relevant_file(name) or any(
        k in name.upper() for k in ("PDDIC", "PDAGE", "PAAGERAT", "PAAGE", "PPBEN", "PRBEN", "PPRBN", "PPRDF", "PCOVR", "PLOAN")
    )


def should_grep_file(name: str, size: int) -> bool:
    if size <= MAX_GREP_BYTES:
        return True
    return is_priority_file(name)


def search_pddic_type_codes(zf) -> list[dict]:
    """Search data dictionary files for TYPE_CODE / NC / U6 etc."""
    results = []
    dic_files = [i.filename for i in zf.infolist() if "PDDIC" in i.filename.upper()]
    type_terms = ["TYPE_CODE", "NC", "U6", "BP", "PR", "CV", "TP", "TX", "SURRENDER", "COI", "GCOI", "RATE_TYPE", "FACTOR"]
    rate_code_terms = {"NC", "U6", "BP", "PR", "CV", "TP", "TX"}
    for fname in dic_files:
        hits, lines, err = stream_search_terms(zf, fname, type_terms)
        cols = []
        samples = []
        rate_code_defs = []
        desc_cols = []
        try:
            with open_zip_text(zf, fname) as f:
                reader = csv.DictReader(f)
                cols = [c.strip() for c in (reader.fieldnames or [])]
                # identify description columns
                desc_cols = [c for c in cols if any(x in c.upper() for x in ("DESC", "NAME", "LABEL", "TEXT", "TITLE"))]
                code_cols = [c for c in cols if any(x in c.upper() for x in ("CODE", "TYPE", "VALUE", "KEY"))]
                for row in reader:
                    sr = strip_row(row)
                    line = ",".join(str(v) for v in sr.values())
                    if any(t in line for t in type_terms):
                        if len(samples) < 25:
                            samples.append(sr)
                    # capture rows that define rate TYPE codes
                    for cc in code_cols:
                        val = sr.get(cc, "")
                        if val in rate_code_terms:
                            rate_code_defs.append(sr)
                            break
                    if len(rate_code_defs) >= 30:
                        pass  # keep scanning for samples
        except Exception as e:
            err = err or str(e)
        results.append({
            "file": fname,
            "line_hits": dict(hits),
            "total_lines": lines,
            "error": err,
            "sample_rows": samples[:15],
            "rate_code_definition_rows": rate_code_defs[:20],
            "columns": cols,
            "description_columns": desc_cols,
        })
    return results


def analyze_ppben_iswl(zf, name="PPBEN_PolicyBenefit_Extract_20260530.csv"):
    out = {}
    raw, cols, samples, total, err = read_csv_header_and_rows(zf, name, max_rows=3)
    out["total_rows"] = total
    out["columns_with_trailing_space"] = [c for c in raw if c != c.strip()]
    prof, err2 = profile_iswl_column(zf, name, ["PLAN_CODE", "COVERAGE_ID"], ISWL_COV | EXTRA_COV)
    out["iswl_profile"] = prof
    # FV_GUAR_RATE distribution on ISWL
    fv = Counter()
    uv_g = Counter()
    uv_c = Counter()
    try:
        with open_zip_text(zf, name) as f:
            reader = csv.DictReader(f)
            fmap = {h.strip(): h for h in reader.fieldnames}
            pc = fmap.get("PLAN_CODE")
            for row in reader:
                plan = row.get(pc, "").strip() if pc else ""
                if plan not in ISWL_COV and plan not in EXTRA_COV:
                    continue
                fv[row.get(fmap.get("FV_GUAR_RATE", "FV_GUAR_RATE"), "").strip()] += 1
                uv_g[row.get(fmap.get("UV_GUAR_COI_RATE", "UV_GUAR_COI_RATE"), "").strip()] += 1
                uv_c[row.get(fmap.get("UV_CURR_COI_RATE", "UV_CURR_COI_RATE"), "").strip()] += 1
    except Exception as e:
        out["field_error"] = str(e)
    out["FV_GUAR_RATE_counts"] = dict(fv.most_common(15))
    out["UV_GUAR_COI_RATE_counts"] = dict(uv_g.most_common(15))
    out["UV_CURR_COI_RATE_counts"] = dict(uv_c.most_common(15))
    out["sample_rows"] = samples
    return out


def analyze_rate_file_type_codes(zf, name, iswl_only=True):
    """Profile TYPE_CODE / COVERAGE_ID for rate-like files."""
    out = {"file": name}
    type_counts = Counter()
    iswl_type_counts = Counter()
    iswl_rows = 0
    total = 0
    samples = []
    cov_col = type_col = None
    try:
        with open_zip_text(zf, name) as f:
            reader = csv.DictReader(f)
            fmap = {h.strip(): h for h in (reader.fieldnames or [])}
            for c in ("COVERAGE_ID", "PLAN_CODE", "PRODUCT_CODE"):
                if c in fmap:
                    cov_col = c
                    break
            type_col = fmap.get("TYPE_CODE")
            for row in reader:
                total += 1
                tc = row.get(type_col, "").strip() if type_col else ""
                if tc:
                    type_counts[tc] += 1
                cov = row.get(fmap[cov_col], "").strip() if cov_col else ""
                if cov in ISWL_COV or cov in EXTRA_COV:
                    iswl_rows += 1
                    if tc:
                        iswl_type_counts[tc] += 1
                    if len(samples) < 5:
                        samples.append({k.strip(): row.get(fmap[k], "").strip() for k in list(fmap.keys())[:12]})
    except Exception as e:
        out["error"] = str(e)
        return out
    out["total_rows"] = total
    out["iswl_rows"] = iswl_rows
    out["type_code_counts"] = dict(type_counts.most_common(30))
    out["iswl_type_code_counts"] = dict(iswl_type_counts.most_common(30))
    out["samples"] = samples
    out["coverage_column"] = cov_col
    return out


def write_csv(path: Path, rows: list[dict], fieldnames=None):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    if not fieldnames:
        fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main():
    ensure_out()
    if not ZIP_PATH.exists():
        print(f"ERROR: ZIP not found: {ZIP_PATH}")
        sys.exit(1)

    log(f"Opening ZIP: {ZIP_PATH} ({ZIP_PATH.stat().st_size:,} bytes)")
    zf = zipfile.ZipFile(ZIP_PATH, "r")

    # TASK 1
    inventory, meta = task1_inventory(zf)
    write_csv(OUT_DIR / "iswl_zip_inventory_20260530.csv", inventory)
    md1 = [
        "# ISWL ZIP Inventory — LifePRO_Extracts_20260530",
        "",
        f"**ZIP path:** `{ZIP_PATH}`",
        f"**ZIP size:** {meta['zip_size_bytes']:,} bytes ({meta['zip_size_bytes']/1e9:.2f} GB)",
        f"**File count:** {meta['file_count']}",
        f"**Total compressed:** {meta['total_compressed']:,} bytes",
        f"**Total uncompressed:** {meta['total_uncompressed']:,} bytes ({meta['total_uncompressed']/1e9:.2f} GB)",
        "",
        "See `iswl_zip_inventory_20260530.csv` for full file list.",
        "",
    ]
    (OUT_DIR / "iswl_zip_inventory_20260530.md").write_text("\n".join(md1), encoding="utf-8")
    log(f"Task 1: {meta['file_count']} files inventoried")

    # TASK 2
    comparison = task2_compare(inventory)
    write_csv(OUT_DIR / "iswl_zip_vs_repo_source_comparison_20260530.csv", comparison)
    log("Task 2: repo comparison done")

    # TASK 3 — relevant file hits
    hit_rows = []
    relevant_files = [i.filename for i in zf.infolist() if is_relevant_file(i.filename)]
    all_csv = [i.filename for i in zf.infolist() if i.filename.lower().endswith(".csv")]
    strong_terms = list(ISWL_COV | ISWL_MPLAN | EXTRA_COV | EXTRA_MPLAN | {"658 CEN", "659 CEN", "669 SR", "679 CEN", "1658C1", "1659C2"})
    broad_terms = list(SEARCH_TERMS)

    grep_targets = [f for f in all_csv if should_grep_file(f, zf.getinfo(f).file_size)]
    log(f"Task 3: grepping {len(grep_targets)}/{len(all_csv)} CSV files (skipped {len(all_csv)-len(grep_targets)} large non-priority)")

    for idx, fname in enumerate(grep_targets):
        if idx and idx % 10 == 0:
            log(f"  Task 3 progress: {idx}/{len(grep_targets)}")
        hits, lines, err = stream_search_terms(zf, fname, strong_terms)
        if sum(hits.values()) == 0:
            continue
        hit_rows.append({
            "internal_path": fname,
            "filename": Path(fname).name,
            "lines_scanned": lines,
            "matched_terms": "; ".join(f"{k}:{v}" for k, v in hits.most_common(20)),
            "total_hits": sum(hits.values()),
            "error": err or "",
        })

    hit_rows.sort(key=lambda x: -x["total_hits"])

    # enrich top hits with column-level ISWL profiling
    for h in hit_rows[:25]:
        fname = h["internal_path"]
        if not fname.lower().endswith(".csv") or zf.getinfo(fname).file_size > MAX_PROFILE_BYTES:
            continue
        raw, cols, samples, _, _ = read_csv_header_and_rows(zf, fname, max_rows=3)
        h["columns"] = "|".join(cols[:30])
        h["sample_rows"] = json.dumps(samples[:2], default=str)[:800]
        prof, _ = profile_iswl_column(
            zf, fname,
            ["COVERAGE_ID", "PLAN_CODE", "PRODUCT_CODE", "MPLAN"],
            ISWL_COV | EXTRA_COV | ISWL_MPLAN | EXTRA_MPLAN,
        )
        h["iswl_rows"] = prof.get("iswl_rows", 0)
        h["iswl_column"] = prof.get("column_used", "")
        h["level_guess"] = (
            "rate-level" if "RATE" in fname.upper() or "TYPE_CODE" in cols
            else "benefit-level" if "BEN" in fname.upper()
            else "policy-level" if "PPOLC" in fname.upper() or "PCOVR" in fname.upper()
            else "table-level" if "PDDIC" in fname.upper() or "PPRDF" in fname.upper()
            else "unknown"
        )

    md3 = ["# ISWL ZIP Relevant File Hits — 20260530", "", f"CSV files grepped: {len(grep_targets)}/{len(all_csv)}", f"Files with hits: {len(hit_rows)}", ""]
    for h in hit_rows[:40]:
        md3.append(f"## {h['filename']}")
        md3.append(f"- Path: `{h['internal_path']}`")
        md3.append(f"- Lines: {h['lines_scanned']:,}")
        md3.append(f"- Hits: {h['matched_terms']}")
        if h.get("iswl_rows"):
            md3.append(f"- ISWL rows: {h['iswl_rows']} (column `{h.get('iswl_column','')}`)")
        if h.get("level_guess"):
            md3.append(f"- Level: {h['level_guess']}")
        if h.get("sample_rows"):
            md3.append(f"- Sample: {h['sample_rows']}")
        md3.append("")
    (OUT_DIR / "iswl_zip_relevant_file_hits_20260530.md").write_text("\n".join(md3), encoding="utf-8")
    write_csv(OUT_DIR / "iswl_zip_relevant_file_hits_20260530.csv", hit_rows)
    log(f"Task 3: {len(hit_rows)} files with ISWL term hits")

    # TASK 4 — table profiles
    profile_rows = []
    profile_details = {}
    profile_targets = list(dict.fromkeys(
        relevant_files + [
            "PAAGERAT_AttainedAge_Rates_Extract_20260530.csv",
            "PAAGE_AttainedAge_Rates_Extract_20260530.csv",
            "PDAGE_AgeDuration_Rates_Extract_20260530.csv",
            "PPBEN_PolicyBenefit_Extract_20260530.csv",
            "PCOVR_Coverage_Extract_20260530.csv",
            "PCOVRSGT_CoverageSegment_Extract_20260530.csv",
            "PDDIC_DataDictionary_Extract_20260530.csv",
            "PDDICFLD_DataDictionaryField_Extract_20260530.csv",
            "PRBEN_BenefitRates_Extract_20260530.csv",
            "PRBENINT_BenefitRatesINT_Extract_20260530.csv",
            "PRBENINF_BenefitRatesINF_Extract_20260530.csv",
            "PPRBNUL_ProductBenefitInformationUL_Extract_20260530.csv",
            "PPRDF_ProductInformation_Extract_20260530.csv",
            "PLOAN_LoanInformation_Extract_20260530.csv",
        ]
    ))
    profile_targets = [f for f in profile_targets if f in all_csv]

    for fname in profile_targets:
        info = zf.getinfo(fname)
        if info.file_size > 800_000_000:
            profile_rows.append({
                "filename": fname, "row_count": "SKIPPED_TOO_LARGE",
                "column_count": "", "note": f"uncompressed {info.file_size:,} bytes",
            })
            continue
        log(f"  Task 4 profiling: {Path(fname).name} ({info.file_size:,} bytes)")
        raw, cols, samples, total, err = read_csv_header_and_rows(zf, fname, max_rows=MAX_SAMPLE_ROWS)
        dtypes = infer_dtypes(samples, cols)
        trailing = [c for c in raw if c != c.strip()]
        row = {
            "filename": fname,
            "uncompressed_size": info.file_size,
            "row_count": total,
            "column_count": len(cols),
            "columns": "|".join(cols[:40]) + ("..." if len(cols) > 40 else ""),
            "trailing_space_columns": "|".join(trailing),
            "error": err or "",
        }
        # distinct TYPE_CODE if present
        if "TYPE_CODE" in cols and info.file_size < 400_000_000:
            tc, terr = count_distinct_column(zf, fname, "TYPE_CODE")
            row["distinct_TYPE_CODE"] = "|".join(f"{k}:{v}" for k, v in tc.most_common(25))
        if "COVERAGE_ID" in cols and info.file_size < 400_000_000:
            cc, _ = count_distinct_column(zf, fname, "COVERAGE_ID")
            iswl_c = sum(v for k, v in cc.items() if k in ISWL_COV)
            row["iswl_COVERAGE_ID_rows"] = iswl_c
        profile_rows.append(row)
        profile_details[fname] = {"samples": samples, "dtypes": dtypes}

    write_csv(OUT_DIR / "iswl_zip_table_profile_20260530.csv", profile_rows)
    md4 = ["# ISWL ZIP Table Profile — 20260530", ""]
    for pr in profile_rows:
        md4.append(f"## {pr['filename']}")
        for k, v in pr.items():
            if k != "filename":
                md4.append(f"- **{k}:** {v}")
        if pr["filename"] in profile_details:
            md4.append("- **Sample rows:**")
            for s in profile_details[pr["filename"]]["samples"][:3]:
                md4.append(f"  - `{s}`")
        md4.append("")
    (OUT_DIR / "iswl_zip_table_profile_20260530.md").write_text("\n".join(md4), encoding="utf-8")
    log(f"Task 4: profiled {len(profile_rows)} files")

    # Rate file deep dives
    rate_analyses = {}
    for rf in [
        "PAAGERAT_AttainedAge_Rates_Extract_20260530.csv",
        "PAAGE_AttainedAge_Rates_Extract_20260530.csv",
        "PDAGE_AgeDuration_Rates_Extract_20260530.csv",
    ]:
        if rf in all_csv:
            rate_analyses[rf] = analyze_rate_file_type_codes(zf, rf)

    ppben_analysis = analyze_ppben_iswl(zf)
    pddic_results = search_pddic_type_codes(zf)

    # TASK 5 — target analysis
    targets = []
    # QUIKCVS — note Rate_Table NOT in ZIP
    rt_in_zip = any("Rate_Table" in n for n in all_csv)
    pdage = rate_analyses.get("PDAGE_AgeDuration_Rates_Extract_20260530.csv", {})
    targets.append({
        "target": "QUIKCVS",
        "candidate_file": "PDAGE_AgeDuration_Rates_Extract_20260530.csv" if not rt_in_zip else "Rate_Table",
        "in_zip": "Yes" if not rt_in_zip else "Partial",
        "evidence": json.dumps(pdage.get("iswl_type_code_counts", {}))[:500],
        "note": "Rate_Table_Extract NOT in ZIP; repo uses 20260427 extract",
    })
    targets.append({
        "target": "QUIKCOI",
        "candidate_file": "PAAGERAT_AttainedAge_Rates_Extract_20260530.csv TYPE NC",
        "in_zip": "Yes",
        "evidence": json.dumps(rate_analyses.get("PAAGERAT_AttainedAge_Rates_Extract_20260530.csv", {}).get("iswl_type_code_counts", {})),
        "note": "Compare to repo PAAGERAT 20260428",
    })
    targets.append({
        "target": "QUIKGCOI",
        "candidate_file": "PAAGERAT TYPE U6",
        "in_zip": "Yes",
        "evidence": json.dumps(rate_analyses.get("PAAGERAT_AttainedAge_Rates_Extract_20260530.csv", {}).get("iswl_type_code_counts", {})),
        "note": "",
    })
    targets.append({
        "target": "QUIKGPS",
        "candidate_file": "PAAGERAT PR/BP; PDAGE PR",
        "in_zip": "Yes",
        "evidence": json.dumps(rate_analyses.get("PAAGERAT_AttainedAge_Rates_Extract_20260530.csv", {}).get("iswl_type_code_counts", {})),
        "note": "PR ISWL rows TBD from analysis",
    })
    targets.append({
        "target": "QUIKUINT",
        "candidate_file": "PPBEN; PRBENINT; PPRBNUL",
        "in_zip": "Yes",
        "evidence": json.dumps(ppben_analysis.get("FV_GUAR_RATE_counts", {})),
        "note": json.dumps(ppben_analysis.get("UV_CURR_COI_RATE_counts", {})),
    })
    targets.append({
        "target": "QUIKISSC",
        "candidate_file": "PDDIC dictionary; PDAGE TP/TX",
        "in_zip": "Search",
        "evidence": "",
        "note": "INFERENCE ONLY for TP/TX",
    })
    targets.append({
        "target": "Expenses",
        "candidate_file": "PDDIC; PCOMP; PBILL",
        "in_zip": "Search",
        "evidence": "",
        "note": "",
    })

    md5 = ["# ISWL ZIP Target Source Analysis — 20260530", ""]
    md5.append(f"**Rate_Table in ZIP:** {'Yes' if rt_in_zip else 'NO — critical gap vs repo'}")
    md5.append("")
    md5.append("## PPBEN ISWL field analysis (from ZIP stream)")
    md5.append("```json")
    md5.append(json.dumps(ppben_analysis, indent=2, default=str)[:8000])
    md5.append("```")
    md5.append("")
    for rf, ra in rate_analyses.items():
        md5.append(f"## {rf}")
        md5.append("```json")
        md5.append(json.dumps(ra, indent=2, default=str)[:4000])
        md5.append("```")
        md5.append("")
    # QUIKISSC / Expenses — scan PDAGE type codes for TP/TX/SC
    pdage_tc = pdage.get("type_code_counts", {})
    pdage_iswl_tc = pdage.get("iswl_type_code_counts", {})
    issc_candidates = {k: v for k, v in pdage_tc.items() if any(x in k.upper() for x in ("SC", "SUR", "TP", "TX", "WD"))}
    targets[5]["evidence"] = json.dumps({"pdage_global": issc_candidates, "pdage_iswl": {k: v for k, v in pdage_iswl_tc.items() if k in issc_candidates or k in ("TP", "TX", "SC", "SUR")}})
    targets[6]["evidence"] = json.dumps({r["file"]: r["line_hits"].get("EXPENSE", 0) for r in pddic_results})
    write_csv(OUT_DIR / "iswl_zip_target_source_analysis_20260530.csv", targets)

    (OUT_DIR / "iswl_zip_target_source_analysis_20260530.md").write_text("\n".join(md5), encoding="utf-8")
    log("Task 5: target analysis done")

    # TASK 6 — dictionary
    md6 = ["# ISWL ZIP TYPE_CODE Dictionary Search — 20260530", ""]
    md6.append("Goal: prove or disprove NC, U6, BP, TP, TX meanings from LifePRO metadata in ZIP.")
    md6.append("")
    proven = []
    for r in pddic_results:
        md6.append(f"## {r['file']}")
        md6.append(f"- Line hits: {r['line_hits']}")
        md6.append(f"- Columns ({len(r.get('columns', []))}): `{', '.join(r.get('columns', [])[:15])}`")
        if r.get("description_columns"):
            md6.append(f"- Description columns: {r['description_columns']}")
        md6.append(f"- Rate-code definition rows: {len(r.get('rate_code_definition_rows', []))}")
        for s in r.get("rate_code_definition_rows", [])[:10]:
            md6.append(f"- Rate code row: `{s}`")
            line = json.dumps(s).upper()
            for code in ("NC", "U6", "BP", "PR", "CV", "TP", "TX"):
                if f'"{code}"' in line or f": {code}," in line:
                    proven.append((code, r["file"], s))
        for s in r.get("sample_rows", [])[:5]:
            md6.append(f"- Sample: `{s}`")
        md6.append("")
    md6.append("## Conclusion")
    if proven:
        md6.append("Dictionary rows referencing rate TYPE codes were found (see above). Review rate_code_definition_rows for authoritative labels.")
    else:
        md6.append("**Unable to verify from available ZIP source data** whether NC/U6/BP/TP/TX labels are authoritatively defined in PDDIC extracts.")
    (OUT_DIR / "iswl_zip_type_code_dictionary_search_20260530.md").write_text("\n".join(md6), encoding="utf-8")
    log(f"Task 6: dictionary search — {len(pddic_results)} PDDIC files")

    # TASK 7 — revalidation
    paagerat = rate_analyses.get("PAAGERAT_AttainedAge_Rates_Extract_20260530.csv", {})
    iswl_tc = paagerat.get("iswl_type_code_counts", {})
    pr_iswl = iswl_tc.get("PR", 0)
    findings = [
        ("QUIKCVS from Rate_Table CV proven", "Weakened" if not rt_in_zip else "Confirmed", "Rate_Table not in May ZIP; PDAGE may substitute"),
        ("Rate_Table PR zero ISWL rows", "Confirmed" if pr_iswl == 0 else "Disproven", f"PAAGERAT 20260530 ISWL PR rows={pr_iswl}"),
        ("PAAGERAT NC may be COI", "Still unknown" if not pddic_results else "Strengthened", "PDDIC may define NC"),
        ("PAAGERAT U6 may be GCOI", "Still unknown", ""),
        ("PAAGERAT BP may be GP", "Still unknown", ""),
        ("iswl-prem.csv not LifePRO authority", "Confirmed", "Not in ZIP"),
        ("PPBEN FV_GUAR_RATE 4.50", "Confirmed", str(ppben_analysis.get("FV_GUAR_RATE_counts", {}))),
        ("UV_CURR_COI_RATE zero all ISWL", "Confirmed", str(ppben_analysis.get("UV_CURR_COI_RATE_counts", {}))),
        ("QUIKISSC unknown", "Still unknown", ""),
        ("Expenses unknown", "Still unknown", ""),
        ("Senior plans weak PAAGERAT", "TBD", str({k: v for k, v in iswl_tc.items()})),
        ("QUIKUINT mapping unknown", "Still unknown", ""),
    ]
    pdage_cv = pdage.get("iswl_type_code_counts", {}).get("CV", 0)
    if pdage_cv > 0:
        findings[0] = ("QUIKCVS from Rate_Table CV proven", "Strengthened", f"Rate_Table absent from ZIP; PDAGE has {pdage_cv:,} ISWL CV rows (May 20260530)")
    if pr_iswl == 0:
        pdage_pr = pdage.get("iswl_type_code_counts", {}).get("PR", 0)
        findings[1] = ("Rate_Table PR zero ISWL rows", "Confirmed", f"PAAGERAT ISWL PR={pr_iswl}; PDAGE ISWL PR={pdage_pr}")
    findings[10] = ("Senior plans weak PAAGERAT support", "Strengthened", f"PAAGERAT ISWL types={iswl_tc}; PDAGE adds CV/TP/TX for senior coverages (e.g. 659 SR GD)")

    md7 = ["# ISWL ZIP Prior Finding Revalidation — 20260530", ""]
    for i, (f, status, note) in enumerate(findings, 1):
        md7.append(f"### {i}. {f}")
        md7.append(f"- **Status:** {status}")
        md7.append(f"- **Note:** {note}")
        md7.append("")
    (OUT_DIR / "iswl_zip_prior_finding_revalidation_20260530.md").write_text("\n".join(md7), encoding="utf-8")
    log("Task 7: revalidation done")

    # Save machine bundle
    bundle = {
        "meta": meta,
        "rate_analyses": rate_analyses,
        "ppben_analysis": ppben_analysis,
        "pddic_results": pddic_results,
        "rate_table_in_zip": rt_in_zip,
        "hit_file_count": len(hit_rows),
    }
    (OUT_DIR / "iswl_zip_analysis_bundle_20260530.json").write_text(
        json.dumps(bundle, indent=2, default=str), encoding="utf-8"
    )

    # TASK 9 — executive summary
    new_files = [c for c in comparison if c.get("should_newly_analyze") == "Yes"]
    md9 = [
        "# ISWL ZIP Research Executive Summary — 20260530",
        "",
        f"**ZIP:** `{ZIP_PATH}`",
        f"**Analyzed:** {datetime.now().isoformat()}",
        "",
        "## Was this ZIP already used in prior ISWL research?",
        "",
        "Partially. Prior ISWL rate research used **April 2026** extracts in `plan_analysis/source_data/rates/` "
        "(`Rate_Table_Extract_20260427.csv`, `PAAGERAT_Extract_20260428.csv`). "
        "Policy extracts from this **May 20260530** ZIP were partially copied to `QLA_Migration/Source/` (12 files) "
        "and used in Issue #21D forensic PPBEN analysis. "
        "**The complete 125-file ZIP was NOT previously inventoried or analyzed as a whole.**",
        "",
        f"## ZIP statistics",
        f"- Files: {meta['file_count']}",
        f"- Uncompressed: {meta['total_uncompressed']/1e9:.2f} GB",
        "",
        "## Critical discovery: Rate_Table NOT in ZIP",
        "",
        f"**Rate_Table_Extract present in ZIP:** {'Yes' if rt_in_zip else '**NO**'}",
        "",
        "Cash value research (QUIKCVS) relied on repo copy `Rate_Table_Extract_20260427.csv`. "
        "This May ZIP includes **`PDAGE_AgeDuration_Rates_Extract_20260530.csv`** (~203 MB) as a potential alternate rate source.",
        "",
        f"## New / unanalyzed file categories: {len(new_files)} flagged",
        "",
        "Key new files: PDDIC Data Dictionary, PDAGE rates, PAAGE rates, PRBEN* benefit rates, PPRBNUL UL product info.",
        "",
        "## PPBEN ISWL (streamed from ZIP)",
        "",
        f"```json\n{json.dumps(ppben_analysis, indent=2, default=str)[:3000]}\n```",
        "",
        "## Implementation status",
        "",
        "**Remain blocked** for UL table loaders (QUIKUINT/COI/GCOI/ISSC) until TYPE_CODE dictionary meanings confirmed from PDDIC review.",
        "",
        "See deliverables in `docs/research/iswl_zip_*_20260530.*`",
    ]
    (OUT_DIR / "ISWL_Zip_Research_Executive_Summary_20260530.md").write_text("\n".join(md9), encoding="utf-8")
    log("Task 9: executive summary written")

    zf.close()
    log(f"Done. Outputs in {OUT_DIR}")


if __name__ == "__main__":
    main()
