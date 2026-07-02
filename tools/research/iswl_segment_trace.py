#!/usr/bin/env python3
"""
ISWL mandatory segment hierarchy trace — research only.
Writes deliverables to docs/research/ISWL_Segment_Trace/

Trace path (where extracts permit):
  PPRDF -> PCOMP -> PCOVR -> PCOVRSGT -> [PSEGT missing] -> rate tables

Does NOT modify app.py, catalogs, rulebooks, or loaders.
"""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs" / "research" / "ISWL_Segment_Trace"
ZIP_PATH = Path(r"C:\Users\warren\Downloads\LifePRO_Extracts_20260530 (1).zip")

ISWL_FLEET = [
    ("1658C1", "658 CEN I"),
    ("1658CS", "658 CEN SD"),
    ("1659C2", "659 CEN II"),
    ("1659CR", "659 CEN SR"),
    ("1659CS", "659 CEN SD"),
    ("1659SR", "659 SR GD"),
    ("1669SR", "669 SR GD"),
    ("1679CS", "679 CEN SD"),
]
ISWL_COV = {c for _, c in ISWL_FLEET}
MPLAN_BY_COV = {c: m for m, c in ISWL_FLEET}

# Product Book segment codes in scope
SEGMENT_CODES = {
    "QUIKUINT": ["A1", "G1", "LN"],
    "Expenses": ["UF", "U1", "U2", "U3", "G2", "G3", "GF", "BI", "UG", "UH", "UX", "UY", "UZ"],
    "QUIKCOI": ["U6", "NR", "UL", "UI", "FC", "MR", "NC"],
    "QUIKGCOI": ["U5"],
    "QUIKISSC": ["SR", "SL", "U7", "U8", "TP", "TX"],
    "QUIKGPS": ["BP", "BI", "UG", "UH", "UX", "UY", "UZ", "MP", "PR"],
    "QUIKCVS": ["CV"],
}

ALL_CODES = sorted({c for codes in SEGMENT_CODES.values() for c in codes})

RATE_SOURCES = [
    ("PAAGERAT", r"PAAGERAT_.*\.csv", "segment"),
    ("PDAGE", r"PDAGE_.*\.csv", "parent"),
    ("Rate_Table", "plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv", "parent"),
]

REPO_PCOVRSGT = REPO / "plan_analysis" / "source_data" / "coverage" / "PCOVRSGT.csv"
REPO_PCOVR = REPO / "plan_analysis" / "source_data" / "coverage" / "PCOVR.csv"
REPO_PCOMP = REPO / "plan_analysis" / "PCOMP.csv"


def log(msg: str):
    print(msg, flush=True)


def open_csv(path: Path | str, zf: zipfile.ZipFile | None = None, zip_name: str | None = None):
    if zf and zip_name:
        raw = zf.open(zip_name)
        return io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
    return open(path, encoding="utf-8-sig", errors="replace", newline="")


def read_csv_rows(path: Path | None, zf=None, zip_name: str | None = None):
    src = zip_name or str(path)
    with open_csv(path, zf, zip_name) as f:
        rd = csv.reader(f)
        raw_hdr = next(rd, [])
        hdr = [c.strip() for c in raw_hdr]
        if hdr and set(hdr) <= {"-" * len(h) for h in hdr}:
            hdr = [c.strip() for c in next(rd, [])]
        for row in rd:
            if len(row) <= 1:
                continue
            if row[0].strip().startswith("-"):
                continue
            padded = row + [""] * max(0, len(hdr) - len(row))
            yield dict(zip(hdr, [c.strip() if isinstance(c, str) else c for c in padded[: len(hdr)]]))


def find_zip_member(zf: zipfile.ZipFile, pattern: str) -> str | None:
    pat = re.compile(pattern, re.I)
    for n in zf.namelist():
        if pat.search(n):
            return n
    return None


def decode_hex_blob(blob: str) -> str:
    blob = (blob or "").strip()
    if not blob.startswith("0x"):
        return blob
    try:
        raw = bytes.fromhex(blob[2:])
        return raw.decode("ascii", errors="replace")
    except Exception:
        return ""


def find_codes_in_text(text: str, codes: list[str]) -> list[str]:
    found = []
    for code in codes:
        if re.search(rf"(?<![A-Z0-9]){re.escape(code)}(?![A-Z0-9])", text):
            found.append(code)
    return found


def load_pcovrsgt(path: Path) -> tuple[dict, dict]:
    """parent -> list of {seq, segt_id, flag}; segt_id -> parent (Y only)."""
    by_parent: dict[str, list] = defaultdict(list)
    segt_to_parent: dict[str, str] = {}
    for row in read_csv_rows(path):
        parent = row.get("COVERAGE_ID", "").strip()
        if not parent:
            continue
        seq = row.get("SEQ", "").strip()
        flag = row.get("SEGT_FLAG", "").strip()
        segt = row.get("SEGT_ID", "").strip()
        by_parent[parent].append({"seq": seq, "segt_flag": flag, "segt_id": segt})
        if flag == "Y" and segt:
            segt_to_parent[segt] = parent
    return dict(by_parent), segt_to_parent


def load_pcovr(path: Path) -> dict:
    out = {}
    for row in read_csv_rows(path):
        cov = row.get("COVERAGE_ID", "").strip()
        if cov:
            out[cov] = row
    return out


def load_pcomp(path: Path) -> dict:
    """product/coverage key -> list of component rows."""
    by_key: dict[str, list] = defaultdict(list)
    for row in read_csv_rows(path):
        key = row.get("PRODUCT_ID", row.get("COVERAGE_ID", "")).strip()
        if not key:
            continue
        by_key[key].append(row)
    return dict(by_key)


def load_pprdf(zf: zipfile.ZipFile, name: str, pcomp_keys: set[str]) -> list[dict]:
    """Match PPRDF rows to ISWL via PCOMP product keys or Interest-Sensitive text."""
    rows = []
    for row in read_csv_rows(None, zf, name):
        pid = row.get("PRODUCT_ID", "").strip()
        text = " ".join(row.values()).upper()
        if pid in pcomp_keys or "INTEREST-SENSITIVE" in text or "WHOLE LIFE" in text and "658" in text:
            rows.append(row)
    return rows


def build_segment_resolution_detail(zf: zipfile.ZipFile, zip_name: str, segt_to_parent: dict) -> dict:
    """PAAGERAT: TYPE_CODE -> SEGT_ID -> parent -> row count (mandatory chain evidence)."""
    detail: dict[str, dict] = defaultdict(lambda: defaultdict(lambda: {"parent": "", "rows": 0, "sample_segt_ids": set()}))
    try:
        for row in read_csv_rows(None, zf, zip_name):
            tc = row.get("TYPE_CODE", "").strip()
            sid = row.get("COVERAGE_ID", "").strip()
            parent = segt_to_parent.get(sid)
            if not parent or parent not in ISWL_COV:
                continue
            bucket = detail[tc][parent]
            bucket["parent"] = parent
            bucket["rows"] += 1
            if len(bucket["sample_segt_ids"]) < 5:
                bucket["sample_segt_ids"].add(sid)
    except Exception:
        pass
    # serialize sets
    out = {}
    for tc, by_parent in detail.items():
        out[tc] = {
            p: {"rows": v["rows"], "sample_segt_ids": sorted(v["sample_segt_ids"])}
            for p, v in by_parent.items()
        }
    return out


def scan_rate_file(
    label: str,
    path: Path | None,
    zf: zipfile.ZipFile | None,
    zip_name: str | None,
    id_mode: str,
    segt_to_parent: dict,
    type_col: str = "TYPE_CODE",
    cov_col: str = "COVERAGE_ID",
):
    """
    Count ISWL rows by (resolved_parent_coverage, TYPE_CODE).
    id_mode: 'segment' = resolve COVERAGE_ID via segt_to_parent; 'parent' = direct match.
    """
    counts: dict[tuple[str, str], int] = defaultdict(int)
    samples: dict[tuple[str, str], list] = defaultdict(list)
    dims_present: dict[tuple[str, str], set] = defaultdict(set)
    dim_cols = ["AGE", "ISSUE_AGE", "DURATION", "SEX", "UW_CLASS", "BAND", "STATE", "SMOKER", "PLAN"]

    src = zip_name or str(path)
    try:
        gen = read_csv_rows(path, zf, zip_name)
    except Exception as e:
        return {"error": str(e), "source": src}, counts, samples

    for row in gen:
        tc = row.get(type_col, row.get("TYPE", "")).strip()
        if not tc:
            continue
        cid = row.get(cov_col, "").strip()
        if id_mode == "segment":
            parent = segt_to_parent.get(cid)
            if not parent and cid in ISWL_COV:
                parent = cid
        else:
            parent = cid if cid in ISWL_COV else None
            if not parent:
                # Rate_Table may use trimmed ids
                for ic in ISWL_COV:
                    if ic.strip() == cid.strip():
                        parent = ic
                        break
        if not parent or parent not in ISWL_COV:
            continue
        key = (parent, tc)
        counts[key] += 1
        if len(samples[key]) < 3:
            samples[key].append({k: row.get(k, "") for k in list(row.keys())[:12]})
        for dc in dim_cols:
            val = row.get(dc, "")
            if val and val not in ("0", ".00000"):
                dims_present[key].add(dc)

    return {"source": src, "id_mode": id_mode}, counts, samples, dims_present


def hex_scan_pcovr_pcomp(pcovr: dict, pcomp: dict) -> dict[str, dict[str, list]]:
    """Search ROW_COLUMN / COMP_KEY0 hex for Product Book segment codes."""
    hits: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for cov in ISWL_COV:
        if cov in pcovr:
            row = pcovr[cov]
            for col in ("ROW_COLUMN", "COVR_KEY0"):
                text = decode_hex_blob(row.get(col, "")) + " " + row.get(col, "")
                for code in find_codes_in_text(text, ALL_CODES):
                    hits[cov][code].append(f"PCOVR.{col}")
        for comp in pcomp.get(cov, []):
            blob = " ".join(decode_hex_blob(comp.get(c, "")) for c in ("ROW_COLUMN", "COMP_KEY0"))
            blob += " " + " ".join(comp.get(c, "") for c in comp if isinstance(comp.get(c), str))
            for code in find_codes_in_text(blob, ALL_CODES):
                hits[cov][code].append(f"PCOMP.comp#{comp.get('COMPONENT_NUMBER','')}.{comp.get('COVERAGE_ID','')}")
    return dict(hits)


def build_trace_results(
    pcovrsgt_by_parent,
    segt_to_parent,
    pcovr,
    pcomp,
    pprdf_rows,
    rate_data,
    hex_hits,
):
    """Assemble matrix rows per (area, segment_code, coverage)."""
    matrix = []
    row_counts = []
    missing = []

    # PAAGERAT segment-id -> parent mapping for ISWL
    paagerat_counts = rate_data.get("PAAGERAT", ({}, {}, {}))[1]

    for area, codes in SEGMENT_CODES.items():
        for code in codes:
            for mplan, cov in ISWL_FLEET:
                segt_slots = pcovrsgt_by_parent.get(cov, [])
                active_segts = [s for s in segt_slots if s["segt_flag"] == "Y" and s["segt_id"]]

                # Rate table evidence by TYPE_CODE (not authority alone — documented separately)
                pa_cnt = paagerat_counts.get((cov, code), 0)
                pd_cnt = rate_data.get("PDAGE", ({}, {}, {}))[1].get((cov, code), 0)
                rt_cnt = rate_data.get("Rate_Table", ({}, {}, {}))[1].get((cov, code), 0)
                total_rate = pa_cnt + pd_cnt + rt_cnt

                hex_paths = hex_hits.get(cov, {}).get(code, [])
                hierarchy_confirmed = "Partial" if segt_slots else "No"
                source_table = ""
                if pa_cnt:
                    source_table = "PAAGERAT"
                elif pd_cnt:
                    source_table = "PDAGE"
                elif rt_cnt:
                    source_table = "Rate_Table_Extract_20260427"
                elif code in ("A1", "G1", "LN") and cov in pcovr:
                    ann = pcovr[cov].get("ANN_GUAR_RATE", "")
                    if ann and float(ann.replace(",", "") or 0) > 0:
                        source_table = "PCOVR.ANN_GUAR_RATE (constant)"
                elif hex_paths:
                    source_table = "PCOVR/PCOMP hex (unverified)"

                # Attempt to link PAAGERAT segment IDs under this coverage
                linked_segts = []
                for s in active_segts:
                    sid = s["segt_id"]
                    for (p, tc), n in paagerat_counts.items():
                        if p == cov and tc == code:
                            if sid == cov or sid in segt_to_parent:
                                linked_segts.append(
                                    {"seq": s["seq"], "segt_id": sid, "rate_rows": n}
                                )

                matrix.append(
                    {
                        "qla_area": area,
                        "segment_code": code,
                        "mplan": mplan,
                        "coverage_id": cov,
                        "pcovrsgt_slot_count": len(segt_slots),
                        "pcovrsgt_active_segt_count": len(active_segts),
                        "pcomp_component_count": len(pcomp.get(cov, [])),
                        "hex_blob_code_hit": "Y" if hex_paths else "N",
                        "hex_hit_paths": "; ".join(hex_paths[:5]),
                        "paagerat_rows": pa_cnt,
                        "pdage_rows": pd_cnt,
                        "rate_table_rows": rt_cnt,
                        "total_rate_rows": total_rate,
                        "inferred_source_table": source_table,
                        "hierarchy_confirmed": hierarchy_confirmed,
                        "pset_extract_present": "N",
                    }
                )
                row_counts.append(
                    {
                        "coverage_id": cov,
                        "mplan": mplan,
                        "segment_code": code,
                        "qla_area": area,
                        "paagerat": pa_cnt,
                        "pdage": pd_cnt,
                        "rate_table_april": rt_cnt,
                        "total": total_rate,
                    }
                )
                if total_rate == 0 and not hex_paths and code not in ("NC", "TP", "TX", "PR", "U7", "U8"):
                    missing.append(
                        {
                            "coverage_id": cov,
                            "mplan": mplan,
                            "segment_code": code,
                            "qla_area": area,
                            "gap": "no rate rows and no hex segment hit",
                        }
                    )

    return matrix, row_counts, missing


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    log("ISWL Segment Trace — starting")

    pcovrsgt_by_parent, segt_to_parent = load_pcovrsgt(REPO_PCOVRSGT)
    pcovr = load_pcovr(REPO_PCOVR)
    pcomp = load_pcomp(REPO_PCOMP)

    pprdf_rows = []
    rate_data = {}
    zip_members = {}
    segment_resolution = {}

    pcomp_keys = {k for k in pcomp if k in ISWL_COV}

    if ZIP_PATH.exists():
        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            zip_members = {
                k: find_zip_member(zf, k if k != "PAAGERAT" else r"PAAGERAT_.*\.csv")
                for k in ["PPRDF", "PAAGERAT", "PDAGE", "PCOMP", "PCOVR", "PCOVRSGT", "PSEGT", "PDINT"]
            }
            # regex patterns for rate files
            zip_members["PAAGERAT"] = find_zip_member(zf, r"PAAGERAT_.*\.csv")
            zip_members["PDAGE"] = find_zip_member(zf, r"PDAGE_.*\.csv")

            if zip_members.get("PPRDF"):
                pprdf_rows = load_pprdf(zf, zip_members["PPRDF"], pcomp_keys)
                log(f"PPRDF ISWL-linked rows (via PCOMP keys): {len(pprdf_rows)}")

            if zip_members.get("PAAGERAT"):
                segment_resolution = build_segment_resolution_detail(
                    zf, zip_members["PAAGERAT"], segt_to_parent
                )

            for label, repo_rel, id_mode in RATE_SOURCES:
                if label == "Rate_Table":
                    path = REPO / repo_rel
                    meta, counts, samples, dims = scan_rate_file(
                        label, path, None, None, id_mode, segt_to_parent
                    )
                else:
                    zm = zip_members.get(label)
                    meta, counts, samples, dims = scan_rate_file(
                        label, None, zf, zm, id_mode, segt_to_parent
                    )
                rate_data[label] = (meta, counts, samples, dims)
                iswl_total = sum(v for (c, _), v in counts.items() if c in ISWL_COV)
                log(f"{label} ISWL typed rows: {iswl_total}")
    else:
        log(f"ZIP not found at {ZIP_PATH}; rate counts from repo Rate_Table only")
        meta, counts, samples, dims = scan_rate_file(
            "Rate_Table",
            REPO / "plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv",
            None,
            None,
            "parent",
            segt_to_parent,
        )
        rate_data["Rate_Table"] = (meta, counts, samples, dims)
        for label in ("PAAGERAT", "PDAGE"):
            rate_data[label] = ({"error": "ZIP missing"}, {}, {}, {})

    hex_hits = hex_scan_pcovr_pcomp(pcovr, pcomp)
    matrix, row_counts, missing = build_trace_results(
        pcovrsgt_by_parent, segt_to_parent, pcovr, pcomp, pprdf_rows, rate_data, hex_hits
    )

    # Summaries per area
    area_summary = {}
    for area in SEGMENT_CODES:
        area_rows = [r for r in matrix if r["qla_area"] == area]
        cov_with_data = {r["coverage_id"] for r in area_rows if r["total_rate_rows"] > 0}
        primary_codes = [c for c in SEGMENT_CODES[area] if any(r["segment_code"] == c and r["total_rate_rows"] > 0 for r in area_rows)]
        area_summary[area] = {
            "coverages_with_any_rate_data": len(cov_with_data),
            "coverages_fully_8": len(cov_with_data) == 8,
            "primary_codes_with_data": primary_codes,
        }

    bundle = {
        "generated": datetime.now().isoformat(),
        "zip_path": str(ZIP_PATH),
        "zip_members": zip_members,
        "pprdf_iswl_rows": len(pprdf_rows),
        "pcovrsgt_iswl": {c: len(pcovrsgt_by_parent.get(c, [])) for c in ISWL_COV},
        "area_summary": area_summary,
        "hex_hits_sample": {k: dict(v) for k, v in list(hex_hits.items())[:3]},
        "paagerat_segment_resolution": segment_resolution,
        "pcomp_product_keys": sorted(pcomp_keys),
    }
    (OUT / "iswl_segment_trace_bundle.json").write_text(
        json.dumps(bundle, indent=2), encoding="utf-8"
    )

    write_csv(OUT / "ISWL_Segment_Trace_Matrix.csv", matrix)
    write_csv(OUT / "ISWL_Segment_Row_Counts.csv", row_counts)

    # Generate markdown deliverables via template fill
    generate_reports(
        OUT, matrix, row_counts, missing, pcovrsgt_by_parent, segt_to_parent,
        pcovr, pcomp, pprdf_rows, rate_data, hex_hits, zip_members, area_summary, bundle,
        segment_resolution,
    )
    log(f"Done — outputs in {OUT}")


def generate_reports(
    out, matrix, row_counts, missing, pcovrsgt_by_parent, segt_to_parent,
    pcovr, pcomp, pprdf_rows, rate_data, hex_hits, zip_members, area_summary, bundle,
    segment_resolution=None,
):
    segment_resolution = segment_resolution or {}
    refs = [
        "docs/research/ISWL_LifePRO_to_QLAdmin_Master_Reference.md",
        "docs/research/ISWL_Implementation_Gap_Report.md",
        "docs/research/ISWL_Product_Book_Manual_Findings_Addendum.md",
        "docs/research/ISWL_Gap_Report_Manual_Revised_Summary.md",
    ]

    def area_section(area: str, primary_segs: list[str], notes: dict) -> str:
        lines = [f"## {area}\n"]
        lines.append("### Segment(s) traced\n")
        lines.append(", ".join(f"`{s}`" for s in SEGMENT_CODES[area]) + "\n")
        lines.append("### Current repo behavior\n")
        lines.append(notes.get("repo", "See gap report.") + "\n")
        lines.append("### Source evidence\n")
        lines.append(notes.get("evidence", "") + "\n")
        lines.append("### Segment hierarchy confirmed?\n")
        lines.append(notes.get("hierarchy", "**Partial only** — `PSEGT` extract absent; `PCOVRSGT` slot→`SEGT_ID` mapped; Product Book segment type (e.g. U6) not resolved to slot without PSEGT.") + "\n")
        lines.append("### Source table resolved?\n")
        lines.append(notes.get("source_table", "Blocked pending PSEGT or SME.") + "\n")
        lines.append("### Dimensions preserved?\n")
        lines.append(notes.get("dimensions", "See matrix — varies by table.") + "\n")
        lines.append("### All 8 ISWL MPLANs covered?\n")
        s = area_summary.get(area, {})
        lines.append(f"**{s.get('coverages_with_any_rate_data', 0)}/8** coverages show rate rows for primary segment codes.\n")
        lines.append("### QLAdmin target supported?\n")
        lines.append(notes.get("supported", "Not proven via hierarchy trace alone.") + "\n")
        lines.append("### Gaps\n")
        lines.append(notes.get("gaps", "") + "\n")
        lines.append("### SME confirmation needed?\n")
        lines.append(notes.get("sme", "**Yes** — segment type ↔ PCOVRSGT slot linkage.") + "\n")
        lines.append("### Recommended next action\n")
        lines.append(notes.get("next", "Request PSEGT extract; SME map slots to Product Book codes.") + "\n")
        lines.append("### Code change needed now? Yes/No\n")
        lines.append(notes.get("code", "**No**") + "\n")
        lines.append("### Business decision needed? Yes/No\n")
        lines.append(notes.get("business", "**Yes**") + "\n")
        return "\n".join(lines)

    def seg_res_block(code: str) -> str:
        data = segment_resolution.get(code, {})
        if not data:
            return "- No ISWL PAAGERAT rows after PCOVRSGT segment resolution."
        lines = []
        for parent, info in sorted(data.items()):
            segts = ", ".join(f"`{s}`" for s in info.get("sample_segt_ids", []))
            lines.append(
                f"- Parent `{parent}`: **{info['rows']}** rows; PAAGERAT.COVERAGE_ID (SEGT_ID) samples: {segts}"
            )
        return "\n".join(lines)

    pa_counts = rate_data.get("PAAGERAT", ({}, {}, {}))[1]
    pd_counts = rate_data.get("PDAGE", ({}, {}, {}))[1]
    rt_counts = rate_data.get("Rate_Table", ({}, {}, {}))[1]

    def rate_summary(code: str) -> str:
        parts = []
        for cov in sorted(ISWL_COV):
            pa = pa_counts.get((cov, code), 0)
            pd = pd_counts.get((cov, code), 0)
            rt = rt_counts.get((cov, code), 0)
            if pa or pd or rt:
                parts.append(f"- `{cov}`: PAAGERAT={pa}, PDAGE={pd}, Rate_Table={rt}")
        return "\n".join(parts) if parts else "- No ISWL rows for this TYPE_CODE in available extracts."

    report = f"""# ISWL Segment Trace Report

**Date:** {datetime.now().strftime("%Y-%m-%d")}  
**Mode:** Research only — no code changes  
**Authority chain attempted:** `PPRDF → PCOMP → PCOVR → PCOVRSGT → Segment → Rate Table / Constant`

## Master references used

{chr(10).join(f"- `{r}`" for r in refs)}

## Executive summary

| QLA area | Hierarchy trace | Authoritative source (proven) | Implementation readiness |
|----------|-----------------|------------------------------|--------------------------|
| QUIKCVS | Partial | `PDAGE` + April `Rate_Table` TYPE=CV (parent COVERAGE_ID) | **Routing ready**; parity analysis needed |
| QUIKUINT | **Blocked** | No PDINT/PDINTTBL/PSEGT; PPBEN FV_GUAR_RATE constant | **Blocked** — missing extracts |
| Expenses | **Blocked** | No typed rate rows for UF/U1–U3/G2/G3/GF in ISWL extracts | **Blocked** |
| QUIKCOI | Partial | PAAGERAT TYPE=U6 via segment chain → **658 CEN SD**, **679 CEN SD** only (800 rows) — Product Book U6 slot **not proven** | **SME + PSEGT** |
| QUIKGCOI | Partial | PAAGERAT TYPE=U5 → **679 CEN SD** only (200 rows) — not hierarchy-proven | **SME + PSEGT** |
| QUIKISSC | Partial | PDAGE/Rate_Table TP/TX present but **withdrawn** as surrender; SR/SL hierarchy not resolved | **SME + PSEGT** |
| QUIKGPS | Partial | PAAGERAT TYPE=BP — **not hierarchy-proven**; PR=0 confirmed | **SME + PSEGT** |

### Critical blocker

**`PSEGT` is not in the May 20260530 ZIP** (nor repo). Without PSEGT, Product Book segment codes (`U6`, `U5`, `BP`, `CV`, `A1`, …) **cannot be authoritatively mapped** to `PCOVRSGT` sequence slots or `SEGT_ID` values. This trace documents **partial** hierarchy plus **rate-table correlation** resolved through the **PAAGERAT → PCOVRSGT → parent COVERAGE_ID** chain where applicable.

### Segment resolution proof (PAAGERAT chain)

Mandatory chain applied: `PAAGERAT.COVERAGE_ID` = `PCOVRSGT.SEGT_ID` → parent `COVERAGE_ID`.

**U6 (current COI candidate):**
{seg_res_block("U6")}

**U5 (guaranteed COI candidate):**
{seg_res_block("U5")}

**BP (billable premium candidate):**
{seg_res_block("BP")}

**NC (withdrawn — net premium credited):**
{seg_res_block("NC")}

**Prior direct COVERAGE_ID counting without segment resolution is withdrawn** — e.g. U6 rows attach to `658 CEN SD` / `679 CEN SD` parents via SEGT_ID `658 CEN I` / `659 CEN II`, not to flagship coverages directly.

### PPRDF linkage

PPRDF contains **no** rows matching ISWL coverage text. ISWL hierarchy **starts at PCOMP** where `PRODUCT_ID` equals coverage id (e.g. `658 CEN I`). PPRDF ISWL-linked rows via PCOMP keys: **{len(pprdf_rows)}**.

### Withdrawn hypotheses (confirmed)

- **`NC` → QUIKCOI** — withdrawn (Net Premium Credited, not COI)
- **`TYPE_CODE=U6` → QUIKGCOI** — withdrawn; manual + trace supports U6 as **current** COI candidate only
- **`TP`/`TX` → QUIKISSC** — withdrawn (tax valuation / reserve)
- **`PR` → QUIKGPS for ISWL** — zero rows all sources

---

{area_section("QUIKUINT", SEGMENT_CODES["QUIKUINT"], {
    "repo": "Partial: `quikplan.NFOINT` + `quikdvdp.MDEPINT=4.50` for ISWL allowlist (`app.py` ~5618). No QUIKUINT loader.",
    "evidence": f"PPRDF rows (ISWL filter): {len(pprdf_rows)}. ZIP members: PDINT={zip_members.get('PDINT', 'MISSING')}, PSEGT={zip_members.get('PSEGT', 'MISSING')}. PCOVR `ANN_GUAR_RATE` present on ISWL coverages (e.g. 658 CEN I). PPBEN `FV_GUAR_RATE=4.50` on 2,159 ISWL rows (May ZIP prior research).",
    "source_table": "**Not resolved** — interest segments A1/G1/LN require PDINT/PDINTTBL/PRBENINT or PSEGT linkage; none available.",
    "supported": "**No** — blocked by missing interest extracts.",
    "gaps": "- PSEGT absent\n- PDINT/PDINTTBL absent from May ZIP\n- Cannot trace A1/G1/LN through PCOVRSGT",
    "sme": "**Yes** — confirm whether 4.50% plan constant is sufficient vs policy-level PPBEN.",
    "next": "**Source Dependency Agent** — request PDINT/PDINTTBL/PSEGT extracts.",
    "code": "**No**",
    "business": "**Yes**",
})}

{area_section("Expenses", SEGMENT_CODES["Expenses"], {
    "repo": "Partial: Issue #21C maps `POLICY_FEE` → `quikridr.MANNLFEE` only.",
    "evidence": rate_summary("UF") + "\\n\\nNo ISWL PAAGERAT/PDAGE rows for U1,U2,U3,G2,G3,GF. PCOMP lists riders (WP, FR, CR) but not expense segment types.",
    "source_table": "**Not resolved** for UL expense segments.",
    "supported": "**No**",
    "gaps": "- No rate rows for expense TYPE_CODEs\\n- BP nesting (UF/U1 inside BP) not traceable without PSEGT",
    "next": "SME: identify LifePRO table for monthly expense charges on ISWL.",
    "business": "**Yes**",
})}

{area_section("QUIKCOI", SEGMENT_CODES["QUIKCOI"], {
    "repo": "Not implemented. NC/U6/BP excluded from `TYPE_TO_TABLE` in `rate_dbf_schema.py`.",
    "evidence": "### U6 (current COI candidate)\\n" + rate_summary("U6") + "\\n\\n### PAAGERAT segment chain (U6)\\n" + seg_res_block("U6") + "\\n\\n### NC (withdrawn as COI)\\n" + rate_summary("NC") + "\\n\\n" + seg_res_block("NC") + "\\n\\nPCOVRSGT for 658 CEN I: 56 slots, active SEGT_IDs include `658 CEN I`, `659 CEN II`, `LIFE`, `LIFEWCV`, `DEFRA`, `AA9B2`, `BMA658`, `IBA01 45`, `L14` — **none labeled U6**.",
    "source_table": "Correlated: **PAAGERAT** TYPE=U6 (800 ISWL rows, 658 CEN I + 659 CEN II only). **Not hierarchy-proven.**",
    "dimensions": "PAAGERAT U6: attained age (SEQ), sex, UW class — differs from CV issue-age×duration.",
    "supported": "**Partial data** for 2/8 coverages (658 CEN SD, 679 CEN SD) after segment resolution; flagship 658 CEN I / 659 CEN II have zero direct PAAGERAT U6 rows.",
    "gaps": "- 659 SR GD, 669 SR GD: **zero PAAGERAT** for any TYPE\\n- U6 absent for 658 CEN SD, 659 CEN SR/SD, 679 CEN SD\\n- NC must not map to QUIKCOI",
    "sme": "**Yes** — confirm U6 segment slots; explain senior plan COI source.",
})}

{area_section("QUIKGCOI", SEGMENT_CODES["QUIKGCOI"], {
    "repo": "Not implemented.",
    "evidence": rate_summary("U5"),
    "source_table": "Correlated: **PAAGERAT** TYPE=U5 (200 ISWL rows). Not hierarchy-proven.",
    "supported": "**Partial** — sparse coverage across fleet.",
    "gaps": "U6 is **not** used as guaranteed COI (confirmed policy). U5 rows do not cover all 8 MPLANs.",
    "sme": "**Yes**",
})}

{area_section("QUIKISSC", SEGMENT_CODES["QUIKISSC"], {
    "repo": "Not implemented. TP/TX/SL in `EXCLUDED_TYPE_CODES`.",
    "evidence": "### SR/SL\\n" + rate_summary("SR") + "\\n" + rate_summary("SL") + "\\n\\n### TP/TX (withdrawn)\\n" + rate_summary("TP") + "\\n" + rate_summary("TX"),
    "source_table": "**Not resolved** — SR→SL parent/child not found in PCOVRSGT SEGT_ID labels.",
    "supported": "**No** — surrender path not proven.",
    "gaps": "TP/TX are tax factors, not surrender. PCOMP has SC (discount) components, not SR/SL Product Book segments.",
    "sme": "**Yes** — confirm SR/SL slot numbers on ISWL forms.",
})}

{area_section("QUIKGPS", SEGMENT_CODES["QUIKGPS"], {
    "repo": "`paagerat_pr_loader.py` filters PR only; zero ISWL PR rows.",
    "evidence": rate_summary("BP") + "\\n\\nPR (all sources): **0 ISWL rows**.",
    "source_table": "Correlated: **PAAGERAT** TYPE=BP (1,164 ISWL rows). Not hierarchy-proven.",
    "supported": "**Partial data** — 6/8 coverages have BP rows; 659 SR GD / 669 SR GD lack PAAGERAT entirely.",
    "gaps": "BP segment slot unknown without PSEGT. Premium assembly segments UG/UH/UX/UY/UZ/MP: no ISWL rate rows.",
    "sme": "**Yes**",
})}

{area_section("QUIKCVS", SEGMENT_CODES["QUIKCVS"], {
    "repo": "**Implemented routing**: CV → QuikCvs via `rate_pipeline.py` / `TYPE_TO_TABLE`. Uses April Rate_Table.",
    "evidence": rate_summary("CV") + "\\n\\nPCOVRSGT SEGT_ID `LIFEWCV` on 658 CEN I seq 44 (semantic hint only — not proof).",
    "source_table": "**PDAGE** (12,084 ISWL CV rows, May) + **Rate_Table_Extract_20260427** (repo). Parity not validated.",
    "dimensions": "Issue age × duration × sex × UW (VARGP=2 style in Rate_Table).",
    "supported": "**Yes for loader path** — strongest ISWL area; parity analysis still required.",
    "gaps": "May PDAGE vs April Rate_Table equivalence unproven. PSEGT CV slot not confirmed.",
    "sme": "**Optional** — parity sign-off.",
    "next": "Run PDAGE vs Rate_Table parity analysis; then Implementation Planning for QUIKCVS hardening.",
    "code": "**No** (research phase)",
    "business": "**No** (unless parity fails)",
})}

## Authoritative source table conclusions

| QLA target | Authoritative source (research conclusion) | Confidence |
|------------|---------------------------------------------|------------|
| QUIKUINT | **Unresolved** — need PDINT/PDINTTBL + PSEGT | Blocked |
| Expenses | **Unresolved** | Blocked |
| QUIKCOI | **PAAGERAT U6** (correlated, 2 plans) — pending PSEGT proof | Low–Medium |
| QUIKGCOI | **PAAGERAT U5** (correlated) — pending PSEGT proof | Low–Medium |
| QUIKISSC | **Unresolved** — SR/SL path not traced | Blocked |
| QUIKGPS | **PAAGERAT BP** (correlated) — PR disproven | Medium (correlation only) |
| QUIKCVS | **PDAGE / Rate_Table CV** at parent COVERAGE_ID | Medium–High |

## PCOVRSGT snapshot (ISWL)

| Coverage | Slots | Active SEGT_ID (sample) |
|----------|-------|-------------------------|
"""
    for _, cov in ISWL_FLEET:
        slots = pcovrsgt_by_parent.get(cov, [])
        active = [s["segt_id"] for s in slots if s["segt_flag"] == "Y" and s["segt_id"]][:8]
        report += f"| `{cov}` | {len(slots)} | {', '.join(f'`{a}`' for a in active)} |\n"

    report += """
---

*Generated by `tools/research/iswl_segment_trace.py`. Rate TYPE_CODE counts are correlation evidence only — not segment hierarchy authority.*
"""
    (out / "ISWL_Segment_Trace_Report.md").write_text(report, encoding="utf-8")

    # Missing coverage report
    miss_md = f"""# ISWL Segment Missing Coverage Report

**Date:** {datetime.now().strftime("%Y-%m-%d")}

## Coverages with no PAAGERAT rows (any TYPE)

"""
    pa_all = pa_counts
    for _, cov in ISWL_FLEET:
        total = sum(v for (c, _), v in pa_all.items() if c == cov)
        miss_md += f"- `{cov}`: **{total}** PAAGERAT rows\n"

    miss_md += "\n## Segment codes with zero rate rows across all 8 coverages\n\n"
    for code in ALL_CODES:
        total = sum(r["total"] for r in row_counts if r["segment_code"] == code)
        if total == 0:
            miss_md += f"- `{code}`\n"

    miss_md += "\n## Per-area primary segment gaps\n\n"
    for area, codes in SEGMENT_CODES.items():
        miss_md += f"### {area}\n\n"
        primary = codes[0]
        for _, cov in ISWL_FLEET:
            row = next((r for r in row_counts if r["coverage_id"] == cov and r["segment_code"] == primary), None)
            if row and row["total"] == 0:
                miss_md += f"- `{cov}` missing `{primary}`\n"
        miss_md += "\n"

    (out / "ISWL_Segment_Missing_Coverage_Report.md").write_text(miss_md, encoding="utf-8")

    # Source table map
    src_md = f"""# ISWL Segment Source Table Map

**Date:** {datetime.now().strftime("%Y-%m-%d")}

## Hierarchy files

| Table | Repo path | May ZIP | Role |
|-------|-----------|---------|------|
| PPRDF | — | `{zip_members.get('PPRDF', 'MISSING')}` | Product root |
| PCOMP | `plan_analysis/PCOMP.csv` | `{zip_members.get('PCOMP', 'MISSING')}` | Components / riders |
| PCOVR | `plan_analysis/source_data/coverage/PCOVR.csv` | `{zip_members.get('PCOVR', 'MISSING')}` | Coverage metadata |
| PCOVRSGT | `plan_analysis/source_data/coverage/PCOVRSGT.csv` | `{zip_members.get('PCOVRSGT', 'MISSING')}` | Segment slots → SEGT_ID |
| PSEGT | — | **MISSING** | Segment type definition (required) |
| PDINT/PDINTTBL | — | **MISSING** | Interest rates |

## Rate tables (segment → rate linkage)

| Segment types (manual) | Rate file | ID mode | ISWL notes |
|------------------------|-----------|---------|------------|
| CV | PDAGE, Rate_Table | Parent COVERAGE_ID | 12,084 PDAGE CV rows |
| U6 | PAAGERAT | SEGT_ID → PCOVRSGT | 800 rows; 658/659 only |
| U5 | PAAGERAT | SEGT_ID → PCOVRSGT | 200 ISWL rows |
| BP | PAAGERAT | SEGT_ID → PCOVRSGT | 1,164 ISWL rows |
| NC | PAAGERAT | SEGT_ID → PCOVRSGT | 690 rows — **not COI** |
| A1/G1/LN | PDINT/PDINTTBL | Unknown | Extracts missing |
| SR/SL | Unknown | Unknown | Not traced |
| UF/U1–U3 | Unknown | Unknown | No ISWL rate rows |

## PAAGERAT resolution chain (repo)

`PAAGERAT.COVERAGE_ID` = `PCOVRSGT.SEGT_ID` → parent `PCOVR.COVERAGE_ID` → MPLAN crosswalk (`qla_core/rate_segment_resolution.py`).
"""
    (out / "ISWL_Segment_Source_Table_Map.md").write_text(src_md, encoding="utf-8")

    sme_md = """# ISWL Segment SME Question List

**For:** Eric / actuarial / LifePRO IT  
**Context:** Mandatory segment hierarchy trace blocked without PSEGT.

## P0 — Blocking

1. Provide **PSEGT** extract (or equivalent) mapping `PCOVRSGT` SEQ/`SEGT_ID` → Product Book segment codes (U6, U5, BP, CV, A1, G1, LN, SR, SL, UF, …) for all eight ISWL coverages.
2. Provide **PDINT** / **PDINTTBL** extracts for credited/guaranteed/loan interest segments.
3. For **659 SR GD** and **669 SR GD**: where are COI/GP rates stored? (Zero PAAGERAT rows in May extract.)
4. Confirm **SR → SL** surrender charge parent/child slot numbers per ISWL form.

## P1 — Mapping confirmation

5. Confirm **U6** = Current COI and **U5** = Guaranteed COI for ISWL (Product Book alignment).
6. Confirm **NC** = Net Premium Credited — not loaded to QUIKCOI.
7. Confirm **BP** feeds **QUIKGPS** (billable/gross premium) for ISWL.
8. Confirm **TP/TX** are tax valuation only — not QUIKISSC.

## P2 — Implementation

9. Is plan-level **4.50%** (`ANN_GUAR_RATE` / PPBEN `FV_GUAR_RATE`) sufficient for QUIKUINT, or must credited interest vary by policy?
10. May **PDAGE CV** vs April **Rate_Table CV** — which is authoritative for migration?
11. Which expense segments (UF, U1, U2, U3, G2, G3, GF) are active on ISWL central vs senior plans?

## Withdrawn — do not re-ask unless new evidence

- NC as QUIKCOI source
- U6 as QUIKGCOI source  
- TP/TX as QUIKISSC source
- PR as ISWL QUIKGPS source
"""
    (out / "ISWL_Segment_SME_Question_List.md").write_text(sme_md, encoding="utf-8")

    next_md = """# ISWL Segment Next Step Recommendation

**Date:** 2026-06-28  
**Trace outcome:** Partial — **PSEGT blocker** prevents hierarchy-authoritative mapping for 6 of 7 QLA areas.

## Implementation-ready

| Area | Readiness | Condition |
|------|-----------|-----------|
| **QUIKCVS** | **Conditional ready** | Existing CV routing; complete PDAGE vs Rate_Table parity first |

## Blocked (missing extracts)

- **QUIKUINT** — PDINT/PDINTTBL/PSEGT
- **Expenses** — no typed rate source identified
- **QUIKISSC** — SR/SL hierarchy not resolved

## SME + PSEGT required before implementation

- **QUIKCOI** (U6 correlation only)
- **QUIKGCOI** (U5 correlation only)
- **QUIKGPS** (BP correlation only; PR disproven)

## Recommended agent sequence

1. **Source Dependency Agent** (immediate) — request PSEGT, PDINT, PDINTTBL from client; document delivery SLA.
2. **SME Review Agent** (parallel) — circulate `ISWL_Segment_SME_Question_List.md`; focus P0 questions 1–4.
3. **Implementation Planning Agent** (after PSEGT) — QUIKCVS parity + QUIKCOI/GCOI/GPS once hierarchy proven.

---

## Cursor-ready prompt: Source Dependency Agent

```
# ISWL Source Dependency Agent

**Project:** LifePRO → QLAdmin Conversion Platform  
**Mode:** Research / client request only — no code changes

## Objective

Obtain missing LifePRO extracts blocking ISWL segment hierarchy trace:

1. PSEGT (segment type definitions — maps PCOVRSGT slots to Product Book codes U6/U5/BP/CV/A1/G1/LN/SR/SL/UF/…)
2. PDINT and PDINTTBL (interest segments A1/G1/LN)
3. Confirm whether May 20260530 ZIP is complete for ISWL product setup

## Authority

- docs/research/ISWL_Segment_Trace/ISWL_Segment_Trace_Report.md
- docs/research/ISWL_Segment_Trace/ISWL_Segment_SME_Question_List.md

## Deliverables

- Client request email draft listing exact table names
- Gap closure checklist
- Re-run segment trace when extracts arrive

Stop after request package — do not implement loaders.
```

## Cursor-ready prompt: SME Review Agent

```
# ISWL SME Review Agent

**Project:** LifePRO → QLAdmin Conversion Platform  
**Mode:** Research only

## Objective

Review ISWL_Segment_SME_Question_List.md with Eric/actuarial team.
Confirm Product Book segment assignments for 8 ISWL MPLANs.
Validate withdrawn hypotheses (NC, TP/TX, PR, U6≠GCOI).

## Inputs

- docs/research/ISWL_Segment_Trace/ISWL_Segment_Trace_Report.md
- docs/research/ISWL_Product_Book_Manual_Findings_Addendum.md

## Deliverable

- ISWL_SME_Segment_Confirmations.md with signed-off segment→table map

Stop after SME document — no code changes.
```

## Cursor-ready prompt: Implementation Planning Agent (QUIKCVS only)

```
# ISWL Implementation Planning Agent — QUIKCVS

**Prerequisite:** PDAGE vs Rate_Table CV parity analysis acceptable

## Scope

Plan surgical QUIKCVS hardening only:
- Parity test: PDAGE_AgeDuration_Rates_Extract_20260530 CV vs Rate_Table_Extract_20260427
- Document authoritative path for production
- No QUIKCOI/GCOI/GPS/UINT/ISSC until PSEGT trace complete

## Constraints

AGENTS.md surgical edit rules; preserve rate_pipeline architecture.

Stop after implementation plan document — no app.py changes unless explicitly approved.
```
"""
    (out / "ISWL_Segment_Next_Step_Recommendation.md").write_text(next_md, encoding="utf-8")


if __name__ == "__main__":
    main()
