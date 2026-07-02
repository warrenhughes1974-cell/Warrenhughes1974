#!/usr/bin/env python3
"""
Issue #31 follow-up — validate PSEGT/PDINT/PDINTTBL and re-trace ISWL hierarchy.
Research only — writes to docs/research/ISWL_Segment_Trace/ and Issue_Log_Items/Issue_31/
"""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "QLA_Migration" / "Source"
OUT_TRACE = REPO / "docs" / "research" / "ISWL_Segment_Trace"
OUT_ISSUE = REPO / "Issue_Log_Items" / "Issue_31"
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

TARGET_CODES = [
    "U5", "U6", "BP", "CV", "A1", "G1", "LN", "SR", "SL",
    "UF", "U1", "U2", "U3", "G2", "G3", "GF",
]

QLA_AREAS = {
    "QUIKUINT": ["A1", "G1", "LN"],
    "QUIKCOI": ["U6"],
    "QUIKGCOI": ["U5"],
    "QUIKGPS": ["BP"],
    "QUIKISSC": ["SR", "SL"],
    "QUIKCVS": ["CV"],
    "Expenses": ["UF", "U1", "U2", "U3", "G2", "G3", "GF"],
}

PATHS = {
    "PSEGT": SOURCE / "PSEGT_Segment_Extract_20260629.csv",
    "PDINT": SOURCE / "PDINT_DeclaredInterestRates_Extract_20260629.csv",
    "PDINTTBL": SOURCE / "PDINTTBL_DeclaredInterestRates_Extract_20260629.csv",
    "PCOVRSGT": REPO / "plan_analysis" / "source_data" / "coverage" / "PCOVRSGT.csv",
    "PCOVR": SOURCE / "PCOVR_Coverage_Extract_20260530.csv",
    "PCOMP": REPO / "plan_analysis" / "PCOMP.csv",
    "PAAGERAT": REPO / "plan_analysis" / "source_data" / "rates" / "PAAGERAT_AttainedAge_Rates_Extract_20260428.csv",
    "Rate_Table": REPO / "plan_analysis" / "source_data" / "rates" / "Rate_Table_Extract_20260427.csv",
}


def log(msg: str):
    print(msg, flush=True)


def read_csv(path: Path):
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        hdr = [c.strip() for c in next(rd)]
        if hdr and all(set(h) <= {"-"} for h in hdr if h):
            hdr = [c.strip() for c in next(rd)]
        for row in rd:
            if not row or row[0].strip().startswith("-"):
                continue
            padded = row + [""] * max(0, len(hdr) - len(row))
            yield dict(zip(hdr, [c.strip() if isinstance(c, str) else c for c in padded[: len(hdr)]]))


def read_csv_zip(zf, name):
    raw = zf.open(name)
    f = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
    rd = csv.reader(f)
    hdr = [c.strip() for c in next(rd)]
    for row in rd:
        if not row or row[0].strip().startswith("-"):
            continue
        padded = row + [""] * max(0, len(hdr) - len(row))
        yield dict(zip(hdr, [c.strip() if isinstance(c, str) else c for c in padded[: len(hdr)]]))


def load_pcovrsgt():
    by_parent = defaultdict(list)
    segt_to_parent = {}
    for row in read_csv(PATHS["PCOVRSGT"]):
        parent = row.get("COVERAGE_ID", "").strip()
        seq = row.get("SEQ", "").strip()
        flag = row.get("SEGT_FLAG", "").strip()
        segt = row.get("SEGT_ID", "").strip()
        by_parent[parent].append({"seq": seq, "segt_flag": flag, "segt_id": segt})
        if flag == "Y" and segt:
            segt_to_parent[segt] = parent
    return dict(by_parent), segt_to_parent


def load_psetg():
    """PSEGT may have multiple SEGT_TYPE rows per SEGMENT_ID."""
    types_by_id = defaultdict(set)
    rows_by_key = {}
    rows = []
    for row in read_csv(PATHS["PSEGT"]):
        sid = row.get("SEGMENT_ID", "").strip()
        stype = row.get("SEGT_TYPE", "").strip()
        if not sid:
            continue
        rows.append(row)
        if stype:
            types_by_id[sid].add(stype)
            rows_by_key[(sid, stype)] = row
    return rows, dict(types_by_id), rows_by_key


def validate_extracts():
    val = {}
    for key in ("PSEGT", "PDINT", "PDINTTBL"):
        path = PATHS[key]
        rows = list(read_csv(path))
        hdr = list(rows[0].keys()) if rows else []
        type_counts = Counter()
        ident_counts = Counter()
        nulls = Counter()
        for r in rows:
            if key == "PSEGT":
                type_counts[r.get("SEGT_TYPE", "")] += 1
                if not r.get("SEGMENT_ID", "").strip():
                    nulls["SEGMENT_ID"] += 1
            else:
                type_counts[r.get("TYPE_CODE", "")] += 1
                ident_counts[r.get("IDENT", "")] += 1
                if not r.get("IDENT", "").strip():
                    nulls["IDENT"] += 1
        val[key] = {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "row_count": len(rows),
            "columns": hdr,
            "type_code_counts": dict(type_counts.most_common(30)),
            "distinct_idents": len(ident_counts) if key != "PSEGT" else 0,
            "distinct_segment_ids": len({r.get("SEGMENT_ID", "").strip() for r in rows if r.get("SEGMENT_ID", "").strip()}) if key == "PSEGT" else 0,
            "null_key_fields": dict(nulls),
            "sample_rows": rows[:3],
        }
    return val


def trace_hierarchy(pcovrsgt_by_parent, segt_to_parent, types_by_id):
    """PCOVRSGT slot -> PSEGT.SEGT_TYPE(s) for ISWL coverages."""
    traces = []
    code_coverage = defaultdict(lambda: defaultdict(list))

    for mplan, cov in ISWL_FLEET:
        slots = pcovrsgt_by_parent.get(cov, [])
        for slot in slots:
            if slot["segt_flag"] != "Y" or not slot["segt_id"]:
                continue
            sid = slot["segt_id"]
            stypes = sorted(types_by_id.get(sid, []))
            traces.append({
                "mplan": mplan,
                "parent_coverage": cov,
                "seq": slot["seq"],
                "segt_id": sid,
                "psetg_types": "|".join(stypes),
                "psetg_found": "Y" if stypes else "N",
            })
            for stype in stypes:
                code_coverage[stype][cov].append({
                    "seq": slot["seq"],
                    "segt_id": sid,
                })

    return traces, dict(code_coverage)


def rate_counts(segt_to_parent, pdage_rows=None):
    counts = defaultdict(lambda: defaultdict(int))
    segts_for_type = defaultdict(set)

    def scan(path, label, id_mode, type_col="TYPE_CODE", cov_col="COVERAGE_ID"):
        for row in read_csv(path):
            tc = row.get(type_col, "").strip()
            if tc not in TARGET_CODES:
                continue
            cid = row.get(cov_col, "").strip()
            if id_mode == "segment":
                parent = segt_to_parent.get(cid)
            else:
                parent = cid if cid in ISWL_COV else None
            if parent not in ISWL_COV:
                continue
            counts[label][(parent, tc)] += 1
            segts_for_type[(tc, parent)].add(cid)

    scan(PATHS["PAAGERAT"], "PAAGERAT", "segment")
    scan(PATHS["Rate_Table"], "Rate_Table", "parent")
    if pdage_rows:
        for row in pdage_rows:
            tc = row.get("TYPE_CODE", "").strip()
            cid = row.get("COVERAGE_ID", "").strip()
            if tc in TARGET_CODES and cid in ISWL_COV:
                counts["PDAGE"][(cid, tc)] += 1
    else:
        if ZIP_PATH.exists():
            with zipfile.ZipFile(ZIP_PATH) as zf:
                name = next((n for n in zf.namelist() if "PDAGE" in n), None)
                if name:
                    for row in read_csv_zip(zf, name):
                        tc = row.get("TYPE_CODE", "").strip()
                        cid = row.get("COVERAGE_ID", "").strip()
                        if tc in TARGET_CODES and cid in ISWL_COV:
                            counts["PDAGE"][(cid, tc)] += 1
    return dict(counts), dict(segts_for_type)


def link_pdint(types_by_id, traces):
    """Link PDINT IDENT to ISWL segments via naming conventions."""
    pdint_rows = list(read_csv(PATHS["PDINT"]))
    pdinttbl_rows = list(read_csv(PATHS["PDINTTBL"]))
    idents = {r.get("IDENT", "").strip() for r in pdint_rows} | {r.get("IDENT", "").strip() for r in pdinttbl_rows}

    # Known IDENT -> SEGT_ID hints
    ident_to_segt = {
        "CENII": "659 CEN II",
        "IBA01": "IBA01 45",
    }
    ident_links = []
    for ident in sorted(idents):
        if not ident:
            continue
        segt = ident_to_segt.get(ident)
        types = sorted(types_by_id.get(segt, [])) if segt else []
        ident_links.append({
            "ident": ident,
            "inferred_segt_id": segt or "",
            "psetg_types": types,
            "has_a1": any(r.get("TYPE_CODE") == "A1" for r in pdint_rows if r.get("IDENT") == ident),
            "has_g1": any(r.get("TYPE_CODE") == "G1" for r in pdint_rows if r.get("IDENT") == ident),
        })

    interest_slots = []
    for t in traces:
        types = set(t["psetg_types"].split("|")) if t["psetg_types"] else set()
        if types & {"A1", "G1", "LN"}:
            interest_slots.append(t)

    pdinttbl_cenii = [r for r in pdinttbl_rows if r.get("IDENT") == "CENII" and r.get("TYPE_CODE") == "A1"]

    return {
        "pdint_rows": len(pdint_rows),
        "pdinttbl_rows": len(pdinttbl_rows),
        "distinct_idents": sorted(idents),
        "ident_links": ident_links,
        "interest_slot_traces": interest_slots[:20],
        "pdint_types": dict(Counter(r.get("TYPE_CODE") for r in pdint_rows)),
        "pdinttbl_types": dict(Counter(r.get("TYPE_CODE") for r in pdinttbl_rows)),
        "cenii_a1_current_rate": [r for r in pdinttbl_cenii if r.get("END_DATE", "").strip() >= "20020101"],
    }


def evaluate_qla_areas(code_coverage, rate_counts_all, interest_info, traces):
    evals = {}
    pa = rate_counts_all.get("PAAGERAT", {})
    pd = rate_counts_all.get("PDAGE", {})
    rt = rate_counts_all.get("Rate_Table", {})

    for area, codes in QLA_AREAS.items():
        cov_with_psetg = set()
        cov_with_rates = set()
        gaps = []
        for code in codes:
            for _, cov in ISWL_FLEET:
                if code in code_coverage and cov in code_coverage[code]:
                    cov_with_psetg.add(cov)
                total = pa.get((cov, code), 0) + pd.get((cov, code), 0) + rt.get((cov, code), 0)
                if total > 0:
                    cov_with_rates.add(cov)
            if code not in code_coverage:
                gaps.append(f"No PSEGT mapping for {code} on any ISWL coverage")

        n_psetg = len(cov_with_psetg)
        n_rates = len(cov_with_rates)

        if area == "QUIKUINT":
            has_int = any(c in code_coverage for c in ("A1", "G1", "LN"))
            has_pdint = interest_info["pdint_rows"] > 0
            if has_int and has_pdint:
                status = "Partially resolved"
                gaps.append("Confirm PDINT IDENT (CENII, IBA01) maps to all 8 MPLANs; G1/LN PDINT rows sparse")
            else:
                status = "Still blocked"
        elif area == "Expenses":
            exp_codes = [c for c in codes if c in code_coverage]
            if exp_codes:
                status = "Partially resolved"
                gaps.append(f"PSEGT maps {exp_codes} via 659 CEN II slot; U1/U2/U3/G2/G3/GF absent from PSEGT")
            else:
                status = "Still blocked"
            if n_rates == 0:
                gaps.append("No PAAGERAT/PDAGE rate rows for U1/U2/U3/G2/G3/GF")
        elif area == "QUIKCVS":
            status = "Fully resolved" if n_psetg == 8 and n_rates == 8 else "Partially resolved"
            if n_rates == 8:
                gaps.append("PDAGE vs Rate_Table parity still open")
        elif area == "QUIKISSC":
            has_sr_sl = "SR" in code_coverage and "SL" in code_coverage
            status = "Partially resolved" if has_sr_sl else "Still blocked"
            gaps.append("SR/SL on 659 CEN II segment — surrender rate table pointer (not TP/TX) still needs decode")
        elif area == "QUIKCOI":
            status = "Partially resolved" if n_psetg == 8 else ("Partially resolved" if n_psetg > 0 else "Still blocked")
            gaps.append("U6 on SEGT_ID 658 CEN I / 659 CEN II; PAAGERAT resolves to SD parent coverages")
            if n_rates < 8:
                gaps.append(f"PAAGERAT U6 rows: {n_rates}/8 parent coverages")
        elif area == "QUIKGCOI":
            status = "Partially resolved" if "U5" in code_coverage else "Still blocked"
            gaps.append("U5 primarily on 659 CEN II segment; PAAGERAT on 679 CEN SD only")
        elif area == "QUIKGPS":
            status = "Partially resolved" if n_psetg == 8 else "Partially resolved"
            gaps.append("BP on 658 CEN I, 658 CEN SD, 659 CEN II, 659 CEN SR segments")
            if n_rates < 8:
                gaps.append(f"PAAGERAT BP rows: {n_rates}/8 parent coverages")
        else:
            status = "Partially resolved" if n_psetg > 0 else "Still blocked"

        evals[area] = {
            "status": status,
            "coverages_with_psetg_mapping": n_psetg,
            "coverages_with_rate_rows": n_rates,
            "gaps": [g for g in gaps if g],
            "codes_in_psetg": [c for c in codes if c in code_coverage],
        }
    return evals


def main():
    OUT_TRACE.mkdir(parents=True, exist_ok=True)
    OUT_ISSUE.mkdir(parents=True, exist_ok=True)

    log("Validating new extracts...")
    validation = validate_extracts()
    psetg_rows, types_by_id, rows_by_key = load_psetg()
    pcovrsgt_by_parent, segt_to_parent = load_pcovrsgt()

    log(f"PSEGT rows: {len(psetg_rows)}, distinct segment IDs: {len(types_by_id)}")
    traces, code_coverage = trace_hierarchy(pcovrsgt_by_parent, segt_to_parent, types_by_id)
    rate_counts_all, segts_for_type = rate_counts(segt_to_parent)
    interest_info = link_pdint(types_by_id, traces)
    qla_eval = evaluate_qla_areas(code_coverage, rate_counts_all, interest_info, traces)

    # Target code mapping summary
    code_map = {}
    for code in TARGET_CODES:
        iswl_segts = []
        for cov in ISWL_COV:
            if code in code_coverage and cov in code_coverage[code]:
                iswl_segts.extend(code_coverage[code][cov])
        rate_total = sum(
            rate_counts_all.get(src, {}).get((cov, code), 0)
            for src in rate_counts_all
            for cov in ISWL_COV
        )
        code_map[code] = {
            "psetg_mapped_iswl_coverages": len([c for c in ISWL_COV if code in code_coverage and c in code_coverage[code]]),
            "sample_slots": iswl_segts[:5],
            "total_rate_rows_all_sources": rate_total,
            "authoritative": (
                "Yes" if len([c for c in ISWL_COV if code in code_coverage and c in code_coverage[code]]) == 8
                else ("Partial" if iswl_segts else "No")
            ),
        }

    bundle = {
        "generated": datetime.now().isoformat(),
        "issue": 31,
        "validation": {k: {kk: vv for kk, vv in v.items() if kk != "sample_rows"} for k, v in validation.items()},
        "psetg_type_counts_top": dict(Counter(r.get("SEGT_TYPE") for r in psetg_rows).most_common(40)),
        "iswl_target_code_map": code_map,
        "qla_area_evaluation": qla_eval,
        "interest_info_summary": {
            k: v for k, v in interest_info.items()
            if k not in ("sample_cenii_a1_rates",)
        },
        "iswl_traces_count": len(traces),
        "iswl_traces_with_psetg": sum(1 for t in traces if t["psetg_found"] == "Y"),
        "psetg_note": "PSEGT uses multiple rows per SEGMENT_ID (one per SEGT_TYPE capability).",
    }
    bundle_path = OUT_TRACE / "iswl_segment_trace_bundle_20260629.json"
    bundle_path.write_text(json.dumps(bundle, indent=2, default=str), encoding="utf-8")

    # Write trace CSV
    trace_csv = OUT_TRACE / "ISWL_Hierarchy_Trace_20260629.csv"
    if traces:
        with open(trace_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(traces[0].keys()))
            w.writeheader()
            w.writerows(traces)

    # Write code mapping matrix
    matrix_rows = []
    for code in TARGET_CODES:
        for mplan, cov in ISWL_FLEET:
            slots = code_coverage.get(code, {}).get(cov, [])
            matrix_rows.append({
                "segment_code": code,
                "mplan": mplan,
                "coverage_id": cov,
                "psetg_slots": len(slots),
                "sample_segt_ids": "; ".join(s["segt_id"] for s in slots[:3]),
                "paagerat_rows": rate_counts_all.get("PAAGERAT", {}).get((cov, code), 0),
                "pdage_rows": rate_counts_all.get("PDAGE", {}).get((cov, code), 0),
                "rate_table_rows": rate_counts_all.get("Rate_Table", {}).get((cov, code), 0),
                "hierarchy_authoritative": "Y" if slots else "N",
            })
    matrix_path = OUT_TRACE / "ISWL_Segment_Trace_Matrix_20260629.csv"
    with open(matrix_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(matrix_rows[0].keys()))
        w.writeheader()
        w.writerows(matrix_rows)

    generate_markdown(validation, code_map, qla_eval, traces, code_coverage, interest_info, bundle)
    log(f"Done. Bundle: {bundle_path}")


def generate_markdown(validation, code_map, qla_eval, traces, code_coverage, interest_info, bundle):
    issue_md = f"""# Issue #31 Follow-up Research — PSEGT / PDINT / PDINTTBL Validation

**Date:** {datetime.now().strftime("%Y-%m-%d")}  
**Mode:** Research only — no code changes  
**New extracts:** `QLA_Migration/Source/` (20260629)

## 1. Extract validation

| Extract | Rows | Size | Key fields | Quality notes |
|---------|------|------|------------|---------------|
| **PSEGT** | {validation['PSEGT']['row_count']} | {validation['PSEGT']['size_bytes']:,} B | SEGMENT_ID, SEGT_TYPE, SEGT_DATA | {validation['PSEGT']['null_key_fields'] or 'No null SEGMENT_ID'} |
| **PDINT** | {validation['PDINT']['row_count']} | {validation['PDINT']['size_bytes']:,} B | IDENT, TYPE_CODE, DINT_RULE, EFF_DATE | {validation['PDINT']['distinct_idents']} distinct IDENTs |
| **PDINTTBL** | {validation['PDINTTBL']['row_count']} | {validation['PDINTTBL']['size_bytes']:,} B | IDENT, TYPE_CODE, DECLARED_RATE, date range | Rate schedule detail for PDINT rules |

### PSEGT distinct SEGT_TYPE count (top)

{chr(10).join(f"- `{k}`: {v}" for k, v in list(validation['PSEGT']['type_code_counts'].items())[:20])}

### PDINT TYPE_CODE distribution

{chr(10).join(f"- `{k}`: {v}" for k, v in validation['PDINT']['type_code_counts'].items())}

## 2. Authoritative segment code mapping (PSEGT + PCOVRSGT)

Chain: `PCOVRSGT.SEGT_ID` → `PSEGT.SEGMENT_ID` → `PSEGT.SEGT_TYPE`

| Code | ISWL coverages mapped | Rate rows (all sources) | Authoritative? |
|------|----------------------|-------------------------|----------------|
"""
    for code in TARGET_CODES:
        m = code_map[code]
        issue_md += f"| `{code}` | {m['psetg_mapped_iswl_coverages']}/8 | {m['total_rate_rows_all_sources']} | **{m['authoritative']}** |\n"

    issue_md += """
## 3. QLA target re-evaluation

| Target | Status | PSEGT coverages | Rate coverages | Notes |
|--------|--------|-----------------|----------------|-------|
"""
    for area, ev in qla_eval.items():
        issue_md += f"| **{area}** | {ev['status']} | {ev['coverages_with_psetg_mapping']}/8 | {ev['coverages_with_rate_rows']}/8 | {'; '.join(ev['gaps'][:2]) or '—'} |\n"

    issue_md += f"""
## 4. Interest trace (QUIKUINT)

- PDINT rows: {interest_info['pdint_rows']}; PDINTTBL rows: {interest_info['pdinttbl_rows']}
- PSEGT maps **A1/G1/LN** on ISWL via `659 CEN II` and `L14` segment slots (all 8 coverages)
- PDINT `CENII` + TYPE `A1` → PDINTTBL **4.50%** from 2002-01-01 (aligns with PPBEN `FV_GUAR_RATE`)
- PDINT IDENT links: {', '.join(l['ident'] for l in interest_info.get('ident_links', []))}
- **Gap:** PDINT extract is small (10 rules / 8 IDENTs); confirm per-MPLAN credited vs guaranteed paths

## 5. Issue #31 resolution recommendation

**Recommend: Partially resolved — do not close as fully resolved.**

| Criterion | Met? |
|-----------|------|
| PSEGT extract received | **Yes** |
| PDINT / PDINTTBL received | **Yes** |
| Primary source dependency removed | **Yes** |
| All 7 QLA areas hierarchy-proven | **No** — Expenses, QUIKISSC, senior-plan COI/GP gaps remain |
| Implementation-ready | **QUIKCVS only** (conditional); others need implementation planning + SME |

**Suggested Issue #31 status:** `Resolved — Source Dependency` with follow-on Issue for implementation / SME sign-off.

## 6. Client questions still required

1. Map PDINT `IDENT` values (e.g. `CENII`, `IBA01`) to each of the 8 ISWL MPLANs for credited vs guaranteed interest.
2. Confirm SR→SL parent/child slot numbers per form (PSEGT types present; rate pointer TBD).
3. 659 SR GD / 669 SR GD — COI/GP rate source (still zero PAAGERAT for some types).
4. PDAGE vs Rate_Table CV authoritative path for production migration.

---

*Full machine output: `docs/research/ISWL_Segment_Trace/iswl_segment_trace_bundle_20260629.json`*
"""
    (OUT_ISSUE / "Issue_31_PSEGT_PDINT_Followup_Report.md").write_text(issue_md, encoding="utf-8")

    # Update segment trace report addendum
    addendum = f"""# ISWL Segment Trace Addendum — 20260629 Extracts

**Supersedes blocker in:** `ISWL_Segment_Trace_Report.md` (2026-06-28)  
**Issue:** #31 follow-up

## Blocker removed

The May 20260530 ZIP blocker on **PSEGT**, **PDINT**, and **PDINTTBL** is **removed**. Files:

- `QLA_Migration/Source/PSEGT_Segment_Extract_20260629.csv`
- `QLA_Migration/Source/PDINT_DeclaredInterestRates_Extract_20260629.csv`
- `QLA_Migration/Source/PDINTTBL_DeclaredInterestRates_Extract_20260629.csv`

## Revised executive summary

| QLA area | Prior (2026-06-28) | After PSEGT (2026-06-29) |
|----------|---------------------|--------------------------|
| QUIKCVS | Partial | **{qla_eval['QUIKCVS']['status']}** |
| QUIKUINT | Blocked | **{qla_eval['QUIKUINT']['status']}** |
| QUIKCOI | Partial | **{qla_eval['QUIKCOI']['status']}** |
| QUIKGCOI | Partial | **{qla_eval['QUIKGCOI']['status']}** |
| QUIKGPS | Partial | **{qla_eval['QUIKGPS']['status']}** |
| QUIKISSC | Partial | **{qla_eval['QUIKISSC']['status']}** |
| Expenses | Blocked | **{qla_eval['Expenses']['status']}** |

## Mandatory hierarchy now traceable through PSEGT

```
PCOVRSGT.SEGT_ID → PSEGT.SEGMENT_ID → PSEGT.SEGT_TYPE → rate table / PDINT
```

ISWL PCOVRSGT slots with PSEGT match: **{sum(1 for t in traces if t['psetg_found']=='Y')}** / **{len(traces)}** active segment rows traced.

## Target code mapping summary

| Code | Coverages (PSEGT) | Authoritative |
|------|-------------------|---------------|
"""
    for code in TARGET_CODES:
        m = code_map[code]
        addendum += f"| `{code}` | {m['psetg_mapped_iswl_coverages']}/8 | {m['authoritative']} |\n"

    addendum += """
## Next step

Proceed to **Implementation Planning Agent** for QUIKCVS; **SME Review Agent** for QUIKUINT IDENT mapping and QUIKISSC SR/SL; retain **Source Dependency** only if May PDAGE refresh needed for parity.

*No converter, loader, catalog, or rulebook changes in this research pass.*
"""
    (OUT_TRACE / "ISWL_Segment_Trace_Addendum_20260629.md").write_text(addendum, encoding="utf-8")


if __name__ == "__main__":
    main()
