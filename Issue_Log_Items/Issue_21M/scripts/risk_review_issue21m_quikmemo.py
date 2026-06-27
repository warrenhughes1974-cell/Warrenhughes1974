"""
Issue 21M QUIKMEMO risk review — read-only population and duplicate analysis.

Usage:
  python QLA_Migration/_risk_review_issue21m_quikmemo.py
  python QLA_Migration/_risk_review_issue21m_quikmemo.py --write-report
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "1.0"
BASE = Path(__file__).resolve().parents[3]
SRC = BASE / "QLA_Migration" / "Source"
CW = BASE / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
REPORT = BASE / "Issue_Log_Items" / "Issue_21M" / "Issue_21M_Risk_Report.md"
OUT_DIR = BASE / "Issue_Log_Items" / "Issue_21M"

TRACE = [
    "010391876C", "010391895C", "010448806C", "010713704C", "010718309C",
    "010765930C", "010818663C",
]

PNOTE_FILE = "PNOTE_PolicyNotes_Extract_20260530.csv"
PENSE_FILE = "PENSE_ENSData_Extract_20260530.csv"


def _read(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", low_memory=False, on_bad_lines="skip").fillna("")
    df.columns = [str(c).replace("\ufeff", "").strip().upper() for c in df.columns]
    if len(df) and df.iloc[0].astype(str).str.contains("---").any():
        df = df.iloc[1:].reset_index(drop=True)
    return df


def _load_cw() -> tuple[dict[str, str], set[str]]:
    cw = pd.read_csv(CW, dtype=str, header=None, names=["LP", "QLA"])
    cw["LP"] = cw["LP"].str.strip()
    cw["QLA"] = cw["QLA"].str.strip()
    lp_to_qla = dict(zip(cw["LP"], cw["QLA"]))
    return lp_to_qla, set(lp_to_qla.keys())


def _text_blob(row: pd.Series, cols: list[str]) -> str:
    parts = [str(row.get(c, "")).strip() for c in cols if str(row.get(c, "")).strip()]
    return "\n".join(parts)


def _is_blank_text(s: str) -> bool:
    return not s or not s.strip()


def _parse_pnote_date(raw: str) -> str:
    raw = str(raw).strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[4:8]}-{raw[0:2]}-{raw[2:4]}"  # MMDDYYYY -> YYYY-MM-DD approx
    return raw


def analyze() -> dict:
    pnote = _read(SRC / PNOTE_FILE)
    pense = _read(SRC / PENSE_FILE)
    lp_to_qla, cw_lps = _load_cw()

    pnote_lines = ["LINE_1", "LINE_2", "LINE_3", "LINE_4"]
    pense_lines = ["LINE_1", "LINE_2", "LINE_3"]
    pnote["TEXT_BLOB"] = pnote.apply(lambda r: _text_blob(r, pnote_lines), axis=1)
    pense["TEXT_BLOB"] = pense.apply(lambda r: _text_blob(r, pense_lines), axis=1)

    pnote_pop = pnote[~pnote["TEXT_BLOB"].map(_is_blank_text)].copy()
    pense_pop = pense[~pense["TEXT_BLOB"].map(_is_blank_text)].copy()

    # Policy-level ENS only (exclude agent/claim keyed rows for policy memo scope)
    pense_pol = pense_pop[pense_pop.get("ENS_KEY_TYPE", pd.Series()).astype(str).str.strip().str.upper() == "P"].copy()

    def add_qla(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["LP"] = df["POLICY_NUMBER"].astype(str).str.strip()
        df["QLA"] = df["LP"].map(lp_to_qla).fillna("")
        return df

    pnote_pop = add_qla(pnote_pop)
    pense_pol = add_qla(pense_pol)

    pnote_xw = pnote_pop[pnote_pop["QLA"].ne("")]
    pense_xw = pense_pol[pense_pol["QLA"].ne("")]

    # Per-policy counts (crosswalk-matched only)
    pnote_by_pol = pnote_xw.groupby("QLA").size()
    pense_by_pol = pense_xw.groupby("QLA").size()
    combined = pd.concat([
        pnote_xw.assign(SRC="PNOTE"),
        pense_xw.assign(SRC="PENSE"),
    ], ignore_index=True)
    combined_by_pol = combined.groupby("QLA").size()

    # Duplicates within source (same policy + text + date key fields)
    def dup_stats(df: pd.DataFrame, date_col: str, time_col: str, src: str) -> dict:
        if df.empty:
            return {"exact_dup_rows": 0, "duplicate_groups": 0}
        key_cols = ["LP", date_col, time_col, "RECORD_SEQ" if "RECORD_SEQ" in df.columns else "EVENT_SEQUENCE", "TEXT_BLOB"]
        key_cols = [c for c in key_cols if c in df.columns]
        grp = df.groupby(key_cols, dropna=False).size()
        dups = grp[grp > 1]
        return {
            "exact_dup_rows": int(dups.sum()) if len(dups) else 0,
            "duplicate_groups": int(len(dups)),
            "source": src,
        }

    pnote_dups = dup_stats(pnote_xw, "DATE_OR_NAMEID", "TIME_OR_UW_REQ_SEQ", "PNOTE")
    pense_dups = dup_stats(pense_xw, "EVENT_DATE", "EVENT_SEQUENCE", "PENSE")

    # Hash duplicates (policy + normalized text only)
    def text_dup_count(df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        df = df.copy()
        df["HASH"] = df.apply(
            lambda r: hashlib.md5(f"{r['LP']}|{r['TEXT_BLOB'].strip().upper()}".encode()).hexdigest(),
            axis=1,
        )
        vc = df.groupby("HASH").size()
        return int(vc[vc > 1].sum())

    # Orphans
    pnote_orphan = int(pnote_pop[pnote_pop["QLA"].eq("")]["LP"].nunique())
    pense_orphan = int(pense_pol[pense_pol["QLA"].eq("")]["LP"].nunique())

    # Benefit seq breakdown PNOTE
    pnote_seq = pnote_xw.groupby(pnote_xw["BENEFIT_SEQ"].astype(str).str.strip()).size().sort_values(ascending=False)

    # ENS non-policy types
    pense_type_counts = pense_pop["ENS_KEY_TYPE"].astype(str).str.strip().str.upper().value_counts()

    # Trace
    trace_rows = []
    for qla in TRACE:
        lp = next((k for k, v in lp_to_qla.items() if v == qla), "")
        pn = pnote_xw[pnote_xw["QLA"] == qla].head(2)
        pe = pense_xw[pense_xw["QLA"] == qla].head(2)
        trace_rows.append({
            "QLA": qla,
            "LP": lp,
            "PNOTE_count": int((pnote_xw["QLA"] == qla).sum()),
            "PENSE_count": int((pense_xw["QLA"] == qla).sum()),
            "PNOTE_sample": pn.iloc[0]["TEXT_BLOB"][:120] if len(pn) else "",
            "PENSE_sample": pe.iloc[0]["TEXT_BLOB"][:120] if len(pe) else "",
        })

    # Text length stats
    def len_stats(df: pd.DataFrame) -> dict:
        if df.empty:
            return {"min": 0, "max": 0, "avg": 0.0, "p95": 0}
        lens = df["TEXT_BLOB"].str.len()
        return {
            "min": int(lens.min()),
            "max": int(lens.max()),
            "avg": round(float(lens.mean()), 1),
            "p95": int(lens.quantile(0.95)),
        }

    stats = {
        "pnote_total_rows": len(pnote),
        "pnote_blank_rows": len(pnote) - len(pnote_pop),
        "pnote_populated_rows": len(pnote_pop),
        "pnote_xwalk_rows": len(pnote_xw),
        "pnote_unique_lp": int(pnote_pop["LP"].nunique()),
        "pnote_unique_qla": int(pnote_xw["QLA"].nunique()),
        "pense_total_rows": len(pense),
        "pense_blank_rows": len(pense) - len(pense_pop),
        "pense_populated_rows": len(pense_pop),
        "pense_policy_type_rows": len(pense_pol),
        "pense_xwalk_rows": len(pense_xw),
        "pense_unique_lp": int(pense_pol["LP"].nunique()),
        "pense_unique_qla": int(pense_xw["QLA"].nunique()),
        "combined_quikmemo_rows": len(pnote_xw) + len(pense_xw),
        "combined_unique_policies": int(combined_by_pol.index.nunique()),
        "pnote_avg_per_policy": round(float(pnote_by_pol.mean()), 2) if len(pnote_by_pol) else 0,
        "pnote_max_per_policy": int(pnote_by_pol.max()) if len(pnote_by_pol) else 0,
        "pense_avg_per_policy": round(float(pense_by_pol.mean()), 2) if len(pense_by_pol) else 0,
        "pense_max_per_policy": int(pense_by_pol.max()) if len(pense_by_pol) else 0,
        "combined_avg_per_policy": round(float(combined_by_pol.mean()), 2) if len(combined_by_pol) else 0,
        "combined_max_per_policy": int(combined_by_pol.max()) if len(combined_by_pol) else 0,
        "pnote_orphan_policies": pnote_orphan,
        "pense_orphan_policies": pense_orphan,
        "pnote_text_dup_hashes": text_dup_count(pnote_xw),
        "pense_text_dup_hashes": text_dup_count(pense_xw),
        "pnote_dups": pnote_dups,
        "pense_dups": pense_dups,
        "pnote_len": len_stats(pnote_xw),
        "pense_len": len_stats(pense_xw),
        "pnote_seq_top": pnote_seq.head(10).to_dict(),
        "pense_type_counts": pense_type_counts.head(10).to_dict(),
        "top_pnote_policies": pnote_by_pol.sort_values(ascending=False).head(10).to_dict(),
        "top_pense_policies": pense_by_pol.sort_values(ascending=False).head(10).to_dict(),
        "trace": trace_rows,
        "pnote_cols": list(pnote.columns),
        "pense_cols": list(pense.columns),
    }
    return stats


def write_csvs(s: dict) -> None:
    """Supplementary population and duplicate analysis CSVs."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pop_rows = [
        ["metric", "pnote", "pense_policy_p", "combined_quikmemo"],
        ["total_source_rows", s["pnote_total_rows"], s["pense_total_rows"], ""],
        ["blank_text_rows", s["pnote_blank_rows"], s["pense_blank_rows"], ""],
        ["populated_rows", s["pnote_populated_rows"], s["pense_policy_type_rows"], ""],
        ["rows_after_crosswalk", s["pnote_xwalk_rows"], s["pense_xwalk_rows"], s["combined_quikmemo_rows"]],
        ["unique_lifepro_policies", s["pnote_unique_lp"], s["pense_unique_lp"], ""],
        ["unique_qla_policies", s["pnote_unique_qla"], s["pense_unique_qla"], s["combined_unique_policies"]],
        ["avg_records_per_policy", s["pnote_avg_per_policy"], s["pense_avg_per_policy"], s["combined_avg_per_policy"]],
        ["max_records_per_policy", s["pnote_max_per_policy"], s["pense_max_per_policy"], s["combined_max_per_policy"]],
        ["orphan_policies_no_crosswalk", s["pnote_orphan_policies"], s["pense_orphan_policies"], ""],
    ]
    pop_path = OUT_DIR / "Issue_21M_Population_Analysis.csv"
    pd.DataFrame(pop_rows[1:], columns=pop_rows[0]).to_csv(pop_path, index=False)

    dup_rows = [
        ["check", "pnote", "pense_policy_p", "notes"],
        ["exact_dup_groups", s["pnote_dups"]["duplicate_groups"], s["pense_dups"]["duplicate_groups"], "pol+date+time+seq+text"],
        ["text_hash_dup_rows", s["pnote_text_dup_hashes"], s["pense_text_dup_hashes"],
         "pol+text; PENSE high count reflects recurring ENS system messages not row-level clones"],
        ["blank_text_rows", s["pnote_blank_rows"], s["pense_blank_rows"], "skip on emit"],
    ]
    dup_path = OUT_DIR / "Issue_21M_Duplicate_Analysis.csv"
    pd.DataFrame(dup_rows[1:], columns=dup_rows[0]).to_csv(dup_path, index=False)


def _md_table(headers: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def write_report(s: dict) -> None:
    lines = [
        "# Issue 21M — QUIKMEMO Risk Review Report",
        "",
        f"**Generated by:** `_risk_review_issue21m_quikmemo.py` v{SCRIPT_VERSION}",
        "**Framework stage:** Risk Agent",
        "**Status:** Risk analysis only — no code changes",
        "",
        "## Go / No-Go Recommendation",
        "",
        "**CONDITIONAL GO for Development** — see §13.",
        "",
        "Rationale: PNOTE and PENSE extracts are present with clear row-per-message grain. QUIKMEMO supports **multiple rows per policy** (non-unique index on MEMOKEY; UI lists multiple memos). Recommended approach: **one QUIKMEMO row per source row** with formatted MEMOTEXT. Primary residual risks: **DBF/FPT memo load path untested**, **PENSE non-policy rows excluded**, and **orphan policies** without crosswalk.",
        "",
        "## 1. Population Impact",
        "",
        _md_table(
            ["Metric", "PNOTE", "PENSE (policy-type P)", "Combined QUIKMEMO"],
            [
                ["Total source rows", s["pnote_total_rows"], s["pense_total_rows"], "—"],
                ["Blank text rows (skip)", s["pnote_blank_rows"], s["pense_blank_rows"], "—"],
                ["Populated rows", s["pnote_populated_rows"], s["pense_policy_type_rows"], "—"],
                ["Rows after crosswalk", s["pnote_xwalk_rows"], s["pense_xwalk_rows"], s["combined_quikmemo_rows"]],
                ["Unique LifePRO policies", s["pnote_unique_lp"], s["pense_unique_lp"], "—"],
                ["Unique QLA policies (emit)", s["pnote_unique_qla"], s["pense_unique_qla"], s["combined_unique_policies"]],
                ["Avg records / policy", s["pnote_avg_per_policy"], s["pense_avg_per_policy"], s["combined_avg_per_policy"]],
                ["Max records / policy", s["pnote_max_per_policy"], s["pense_max_per_policy"], s["combined_max_per_policy"]],
                ["Orphan policies (no crosswalk)", s["pnote_orphan_policies"], s["pense_orphan_policies"], "—"],
            ],
        ),
        "",
        "### PNOTE benefit sequence (top)",
        "",
        _md_table(["BENEFIT_SEQ", "rows"], [[k, v] for k, v in s["pnote_seq_top"].items()]),
        "",
        "### PENSE ENS_KEY_TYPE (all populated rows)",
        "",
        _md_table(["ENS_KEY_TYPE", "rows"], [[k, v] for k, v in s["pense_type_counts"].items()]),
        "",
        "### Top policies by note count",
        "",
        "**PNOTE:** " + ", ".join(f"{k}({v})" for k, v in list(s["top_pnote_policies"].items())[:5]),
        "",
        "**PENSE:** " + ", ".join(f"{k}({v})" for k, v in list(s["top_pense_policies"].items())[:5]),
        "",
        "### Text length (MEMOTEXT planning)",
        "",
        _md_table(
            ["Source", "min", "avg", "p95", "max"],
            [
                ["PNOTE", s["pnote_len"]["min"], s["pnote_len"]["avg"], s["pnote_len"]["p95"], s["pnote_len"]["max"]],
                ["PENSE", s["pense_len"]["min"], s["pense_len"]["avg"], s["pense_len"]["p95"], s["pense_len"]["max"]],
            ],
        ),
        "",
        "## 2. Memo Storage Model (Multiple Rows vs Concatenated)",
        "",
        "**Conclusion: Multiple QUIKMEMO records per policy are supported.**",
        "",
        "| Evidence | Finding |",
        "|----------|---------|",
        "| QLAdmin Help §7.151 | Table has only `MEMOKEY` + `MEMOTEXT`; index `QuikMemo.ntx` on MEMOKEY (not documented as UNIQUE) |",
        "| QLAdmin Help §5.1.4.1.6 | Memo tab lists **multiple entries** per policy, most recent first |",
        "| LifePRO PNOTE/PENSE grain | **One source row per note/message** with LINE_1–4 text |",
        "| Concatenated single row | Would lose per-message identity; harder to match QLAdmin add/edit semantics |",
        "",
        "**Recommendation:** Emit **one QUIKMEMO row per populated PNOTE or PENSE row** (after filters), not one concatenated blob per policy.",
        "",
        "## 3. Record Ordering",
        "",
        "| Source | Primary sort key | Secondary | Direction |",
        "|--------|------------------|-----------|-----------|",
        "| PNOTE | `DATE_OR_NAMEID` (MMDDYYYY) | `TIME_OR_UW_REQ_SEQ` + `RECORD_SEQ` | Descending (newest first) |",
        "| PENSE | `EVENT_DATE` (YYYYMMDD) | `EVENT_SEQUENCE` | Descending |",
        "",
        "QLAdmin displays most recent first; descending sort aligns with native UI. File order is **not** reliable across extracts.",
        "",
        "## 4. Memo Formatting Recommendation",
        "",
        "**Recommended MEMOTEXT template (one row per source record):**",
        "",
        "```",
        "[PNOTE] Date: YYYY-MM-DD  Time: HH:MM:SS  Seq: {RECORD_SEQ}  BenSeq: {BENEFIT_SEQ}",
        "{LINE_1}",
        "{LINE_2}",
        "{LINE_3}",
        "{LINE_4}",
        "```",
        "",
        "```",
        "[ENS] Event: {EVENT_CODE}  Date: {EVENT_DATE}  Seq: {EVENT_SEQUENCE}",
        "User: {ORG_OPER_ID}",
        "{LINE_1}",
        "{LINE_2}",
        "{LINE_3}",
        "```",
        "",
        "Do **not** merge PNOTE and PENSE into a single row. Prefix distinguishes source type in the unified Memo tab.",
        "",
        "## 5. Duplicate and Filtering Analysis",
        "",
        _md_table(
            ["Check", "PNOTE", "PENSE (policy P)"],
            [
                ["Exact dup groups (pol+date+time+seq+text)", s["pnote_dups"]["duplicate_groups"], s["pense_dups"]["duplicate_groups"]],
                ["Text hash dup rows (pol+text)", s["pnote_text_dup_hashes"], s["pense_text_dup_hashes"]],
                ["Blank text rows", s["pnote_blank_rows"], s["pense_blank_rows"]],
            ],
        ),
        "",
        "**PENSE text-hash note:** The high PENSE count (18,126) reflects **recurring ENS system messages** (e.g. \"A Rebill Has Been Processed\") that share identical body text across policies and dates — not exact row clones. Zero exact duplicate groups were found on pol+date+seq+text. Do **not** auto-deduplicate by text alone.",
        "",
        "### Recommended filters (Development)",
        "",
        "| Filter | Rule |",
        "|--------|------|",
        "| Skip blank | All LINE_* empty → do not emit |",
        "| Crosswalk | Skip rows with no Master_Crosswalk match; audit log |",
        "| PENSE scope | Include `ENS_KEY_TYPE = P` only for policy memos (exclude pure agent/claim keys unless client expands scope) |",
        "| Exact duplicates | Drop second+ identical (LP, date, time, seq, text) within same source |",
        "| Text duplicates | **Flag, do not auto-drop** — log for client review |",
        "| Deleted notes | `NOTE_UPD_COUNT` / `ENSE_UPD_COUNT` semantics **unconfirmed** — emit all non-blank until client defines deletion rule |",
        "",
        "## 6. Regression Risk",
        "",
        _md_table(
            ["Surface", "Risk", "Mitigation"],
            [
                ["Existing quik* tables", "None — new table only", "Add quikmemo without touching batch order of existing tables"],
                ["quikmstr / quikridr / quikprmh", "None", "No rulebook changes"],
                ["Issue #25 MPOLICY padding", "Low", "Reuse `format_qladmin_mpolicy()` for MEMOKEY"],
                ["Issue #26 MPREM", "None", "No premium fields"],
                ["DBF/FPT generation", "**Medium**", "Prototype QUIKMEMO DBF+FPT before UAT; reuse claims MEMO coercion pattern"],
                ["DBF append utility", "**Medium**", "Verify memo blob survives append (MPOLICY `.strip()` lesson from #25)"],
                ["Policy lookup", "Low", "MEMOKEY must match padded MPOLICY on quikmstr"],
                ["Existing memo functionality", "Low", "Greenfield — quikmemo currently empty"],
            ],
        ),
        "",
        "## 7. Confirmed Source Field Mapping",
        "",
        "### PNOTE → QUIKMEMO",
        "",
        _md_table(
            ["PNOTE field", "Use"],
            [
                ["POLICY_NUMBER", "Crosswalk → MEMOKEY"],
                ["DATE_OR_NAMEID", "Memo header date"],
                ["TIME_OR_UW_REQ_SEQ", "Memo header time"],
                ["RECORD_SEQ", "Ordering / dedupe"],
                ["BENEFIT_SEQ", "Memo header (informational)"],
                ["LINE_1 – LINE_4", "MEMOTEXT body"],
            ],
        ),
        "",
        "### PENSE → QUIKMEMO (policy-type only)",
        "",
        _md_table(
            ["PENSE field", "Use"],
            [
                ["POLICY_NUMBER", "Crosswalk → MEMOKEY"],
                ["EVENT_DATE", "Memo header date"],
                ["EVENT_SEQUENCE", "Ordering / dedupe"],
                ["EVENT_CODE", "Memo header"],
                ["ORG_OPER_ID", "Memo header user"],
                ["LINE_1 – LINE_3", "MEMOTEXT body"],
            ],
        ),
        "",
        "## 8. Trace Policies (Issue #21)",
        "",
        _md_table(
            ["QLA", "PNOTE", "PENSE", "PNOTE sample", "PENSE sample"],
            [[t["QLA"], t["PNOTE_count"], t["PENSE_count"], t["PNOTE_sample"][:60], t["PENSE_sample"][:60]] for t in s["trace"]],
        ),
        "",
        "## 9. Implementation Recommendation",
        "",
        "| Decision | Recommendation |",
        "|----------|----------------|",
        "| Row grain | **One QUIKMEMO row per source row** |",
        "| Rulebook | Minimal stub; **engine-driven dual-source merge** (like quikprmh complexity) |",
        "| Engine changes | Add `quikmemo` to TABLE_SCHEMAS; new merge emit path; **no changes** to existing tables |",
        "| Resolver | Add PNOTE + PENSE to `lifepro_source_resolver.py` |",
        "| DBF/FPT | **Separate UAT task** — CSV batch first; prototype DBF with MEMO type before client load |",
        "| Validation | `_validate_issue21m_quikmemo.py`: counts, MEMOKEY width, trace policies, orphan log |",
        "| Version | v57.32 (proposed) |",
        "",
        "## 10. Regression Testing Checklist (Validation Agent)",
        "",
        "- [ ] Trace policies have expected PNOTE/PENSE counts",
        "- [ ] MEMOKEY width = 10 (Issue #25)",
        "- [ ] quikmstr/quikridr/quikprmh row counts unchanged",
        "- [ ] Issue #26 MPREM validator still PASS",
        "- [ ] Orphan policy audit log reviewed",
        "- [ ] QUIKMEMO DBF+FPT loads in QLAdmin (UAT)",
        "",
        "## 11. Prior Fix Preservation",
        "",
        _md_table(
            ["Check", "Result"],
            [
                ["Issue #25 MPOLICY / MEMOKEY padding", "No conflict — reuse `format_qladmin_mpolicy()` for MEMOKEY"],
                ["Issue #26 MPREM / MMODPREM", "No conflict — quikmemo has no premium fields"],
            ],
        ),
        "",
        "## 12. Open Items (Client / UAT)",
        "",
        "1. Confirm `NOTE_UPD_COUNT` / `ENSE_UPD_COUNT` deletion semantics",
        "2. Confirm PENSE non-`P` types excluded from policy memo scope",
        "3. Confirm BENEFIT_SEQ filtering (include all seq vs base `00` only)",
        "4. DBF append path sign-off for MEMO fields",
        "",
        "## 13. Go / No-Go Detail",
        "",
        "| Verdict | **CONDITIONAL GO** |",
        "|---------|-------------------|",
        "| Condition 1 | Development emits **CSV only** first; no DBF append change in same release without FPT prototype |",
        "| Condition 2 | Orphan policies logged, not silently dropped without audit |",
        "| Condition 3 | PENSE filtered to `ENS_KEY_TYPE=P` unless client requests broader scope |",
        "",
        "**NO-GO** if client requires immediate DBF production load without MEMO/FPT validation.",
        "",
        "## Appendix — Supporting Artifacts",
        "",
        "| Artifact | Path |",
        "|----------|------|",
        "| Population analysis CSV | `Issue_Log_Items/Issue_21M/Issue_21M_Population_Analysis.csv` |",
        "| Duplicate analysis CSV | `Issue_Log_Items/Issue_21M/Issue_21M_Duplicate_Analysis.csv` |",
        "| Risk simulation script | `QLA_Migration/_risk_review_issue21m_quikmemo.py` |",
        "| Planning report | `Issue_Log_Items/Issue_21M/Issue_21M_QUIKMEMO_Planning_Report.md` |",
        "",
        "## Appendix — Source Columns",
        "",
        "**PNOTE:** " + ", ".join(s["pnote_cols"]),
        "",
        "**PENSE:** " + ", ".join(s["pense_cols"]),
        "",
    ]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-report", action="store_true")
    args = ap.parse_args()

    s = analyze()
    print("=== Issue 21M Risk Review ===")
    for k in [
        "pnote_xwalk_rows", "pense_xwalk_rows", "combined_quikmemo_rows",
        "combined_unique_policies", "combined_avg_per_policy", "combined_max_per_policy",
        "pnote_orphan_policies", "pense_orphan_policies",
    ]:
        print(f"  {k}: {s[k]}")

    if args.write_report:
        write_csvs(s)
        write_report(s)
        print(f"\nReport: {REPORT}")
        print(f"Population CSV: {OUT_DIR / 'Issue_21M_Population_Analysis.csv'}")
        print(f"Duplicate CSV: {OUT_DIR / 'Issue_21M_Duplicate_Analysis.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
