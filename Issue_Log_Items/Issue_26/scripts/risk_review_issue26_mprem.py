"""
Issue #26 MPREM mapping risk review — read-only before/after simulation.

Usage:
  python QLA_Migration/_risk_review_issue26_mprem.py
  python QLA_Migration/_risk_review_issue26_mprem.py --write-report
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "1.0"
BASE = Path(__file__).resolve().parents[3]
SRC = BASE / "QLA_Migration" / "Source"
OUT = BASE / "QLA_Migration" / "Output"
CW = BASE / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
REPORT = BASE / "Issue_Log_Items" / "Issue_26" / "Issue_26_MPREM_Risk_Review_Report.md"

TRACE = ["010310404C", "010331768C", "010367131C"]


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.strip().replace("", pd.NA), errors="coerce")


def _fmt_money(v) -> str:
    if pd.isna(v):
        return ""
    return f"{float(v):.2f}"


def load_joined() -> pd.DataFrame:
    ppben = pd.read_csv(SRC / "PPBEN_PolicyBenefit_Extract_20260530.csv", dtype=str, encoding="latin1", low_memory=False)
    ppben.columns = [c.strip().upper() for c in ppben.columns]
    ppben["POLICY_NUMBER"] = ppben["POLICY_NUMBER"].astype(str).str.strip()
    ppben["BENEFIT_SEQ"] = ppben["BENEFIT_SEQ"].astype(str).str.strip().str.replace(".0", "", regex=False)
    ppben["MPHASE"] = ppben["BENEFIT_SEQ"].str.lstrip("0").replace("", "0")

    ridr = pd.read_csv(OUT / "quikridr.csv", dtype=str, encoding="latin1")
    ridr.columns = [c.strip().upper() for c in ridr.columns]
    ridr["MPHASE"] = ridr["MPHASE"].astype(str).str.strip()

    cw = pd.read_csv(CW, dtype=str, header=None, names=["LP", "QLA"])
    cw["LP"] = cw["LP"].str.strip()
    cw["QLA"] = cw["QLA"].str.strip()

    ppben = ppben.merge(cw, left_on="POLICY_NUMBER", right_on="LP", how="left")
    merged = ppben.merge(
        ridr,
        left_on=["QLA", "MPHASE"],
        right_on=["MPOLICY", "MPHASE"],
        how="inner",
        suffixes=("_SRC", "_OUT"),
    )
    for c in ["ANN_PREM_PER_UNIT", "MODE_PREMIUM", "VALUE_PER_UNIT", "NUMBER_OF_UNITS", "BENEFIT_FEE", "MPREM", "MVPU", "MUNIT"]:
        if c in merged.columns:
            merged[c] = _num(merged[c])
    return merged


def simulate_proposed(merged: pd.DataFrame, fallback_mode: str) -> pd.Series:
    ann = merged["ANN_PREM_PER_UNIT"]
    mode = merged["MODE_PREMIUM"]
    if fallback_mode == "blank":
        return ann.where(ann.notna() & (ann != 0), other=pd.NA)
    if fallback_mode == "mode_prem":
        return ann.where(ann.notna() & (ann != 0), other=mode)
    if fallback_mode == "mode_per_unit":
        units = merged["NUMBER_OF_UNITS"]
        derived = mode / units
        return ann.where(ann.notna() & (ann != 0), other=derived)
    raise ValueError(fallback_mode)


def analyze(fallback_mode: str = "mode_prem") -> dict:
    m = load_joined()
    current = m["MPREM"]
    proposed = simulate_proposed(m, fallback_mode)
    delta = (proposed - current).abs()
    changed = delta.fillna(0) > 0.01

    ann = m["ANN_PREM_PER_UNIT"]
    ann_pop = ann.notna() & (ann != 0)
    ann_blank = ~ann_pop

    stats = {
        "total_quikridr_rows_joined": len(m),
        "ann_ppu_populated": int(ann_pop.sum()),
        "ann_ppu_blank_zero": int(ann_blank.sum()),
        "ann_equals_mode": int(((ann - m["MODE_PREMIUM"]).abs() < 0.01).sum()),
        "ann_differs_mode": int(((ann - m["MODE_PREMIUM"]).abs() >= 0.01).sum()),
        "rows_would_change": int(changed.sum()),
        "rows_unchanged": int((~changed).sum()),
        "fallback_mode": fallback_mode,
    }

    m = m.copy()
    m["MPREM_CURRENT"] = current
    m["MPREM_PROPOSED"] = proposed
    m["MPREM_DELTA"] = proposed - current
    m["MPREM_DELTA_ABS"] = delta
    m["ANN_BLANK"] = ann_blank

    top25 = (
        m[changed]
        .sort_values("MPREM_DELTA_ABS", ascending=False)
        .head(25)[
            [
                "QLA", "MPHASE", "MPLAN", "MPHSTAT", "BENEFIT_TYPE", "BENEFIT_SEQ",
                "ANN_PREM_PER_UNIT", "MODE_PREMIUM", "MPREM_CURRENT", "MPREM_PROPOSED", "MPREM_DELTA",
                "NUMBER_OF_UNITS", "BENEFIT_FEE",
            ]
        ]
    )

    by_type = (
        m.groupby("BENEFIT_TYPE")
        .agg(
            rows=("MPREM", "count"),
            ann_pop=("ANN_PREM_PER_UNIT", lambda s: (s.notna() & (s != 0)).sum()),
            ann_blank=("ANN_PREM_PER_UNIT", lambda s: (~s.notna() | (s == 0)).sum()),
            would_change=("MPREM_DELTA_ABS", lambda s: (s.fillna(0) > 0.01).sum()),
        )
        .sort_values("would_change", ascending=False)
    )

    m["COVERAGE_CLASS"] = m["BENEFIT_SEQ"].map(lambda x: "base_seq1" if str(x).strip() == "1" else "rider_supplemental")
    by_coverage = (
        m.groupby("COVERAGE_CLASS")
        .agg(
            rows=("MPREM", "count"),
            ann_pop=("ANN_PREM_PER_UNIT", lambda s: (s.notna() & (s != 0)).sum()),
            ann_blank=("ANN_PREM_PER_UNIT", lambda s: (~s.notna() | (s == 0)).sum()),
            would_change=("MPREM_DELTA_ABS", lambda s: (s.fillna(0) > 0.01).sum()),
        )
    )

    by_plan = (
        m.groupby("MPLAN", dropna=False)
        .agg(rows=("MPREM", "count"), would_change=("MPREM_DELTA_ABS", lambda s: (s.fillna(0) > 0.01).sum()))
        .sort_values("would_change", ascending=False)
        .head(20)
    )

    by_seq = (
        m.groupby("BENEFIT_SEQ")
        .agg(
            rows=("MPREM", "count"),
            ann_pop=("ANN_PREM_PER_UNIT", lambda s: (s.notna() & (s != 0)).sum()),
            ann_blank=("ANN_PREM_PER_UNIT", lambda s: (~s.notna() | (s == 0)).sum()),
            would_change=("MPREM_DELTA_ABS", lambda s: (s.fillna(0) > 0.01).sum()),
        )
        .sort_index()
    )

    by_status = (
        m.groupby("MPHSTAT")
        .agg(rows=("MPREM", "count"), would_change=("MPREM_DELTA_ABS", lambda s: (s.fillna(0) > 0.01).sum()))
        .sort_values("would_change", ascending=False)
        .head(15)
    )

    by_plan = by_plan.reset_index()
    by_seq = by_seq.reset_index()
    by_status = by_status.reset_index()

    blank_rows = m[ann_blank].copy()
    blank_with_mode = blank_rows[blank_rows["MODE_PREMIUM"].notna() & (blank_rows["MODE_PREMIUM"] != 0)]

    # quikmstr MMODPREM unchanged check
    mstr = pd.read_csv(OUT / "quikmstr.csv", dtype=str, encoding="latin1")
    mstr.columns = [c.strip().upper() for c in mstr.columns]
    cw_map = pd.read_csv(CW, dtype=str, header=None, names=["LP", "QLA"])
    cw_map["LP"] = cw_map["LP"].str.strip()
    cw_map["QLA"] = cw_map["QLA"].str.strip()
    ppolc = pd.read_csv(SRC / "PPOLC_PolicyMaster_Extract_20260530.csv", dtype=str, encoding="latin1")
    ppolc.columns = [c.strip().upper() for c in ppolc.columns]
    ppolc["POLICY_NUMBER"] = ppolc["POLICY_NUMBER"].astype(str).str.strip()
    ppolc = ppolc.merge(cw_map, left_on="POLICY_NUMBER", right_on="LP", how="left")
    mstr_chk = mstr.merge(ppolc[["QLA", "MODE_PREMIUM"]], left_on="MPOLICY", right_on="QLA", how="inner")
    mstr_chk["MMODEPREM"] = _num(mstr_chk["MMODEPREM"])
    mstr_chk["MODE_PREMIUM"] = _num(mstr_chk["MODE_PREMIUM"])
    mmodprem_match = int(((mstr_chk["MMODEPREM"] - mstr_chk["MODE_PREMIUM"]).abs() < 0.01).sum())

    # Compare fallback options
    fb_compare = {}
    fb_blank_regression = int(
        (ann_blank & current.notna() & (current.abs() > 0.01)).sum()
    )
    for fb in ("blank", "mode_prem", "mode_per_unit"):
        prop = simulate_proposed(m, fb)
        if fb == "blank":
            ch = (prop.isna() & current.notna() & (current.abs() > 0.01)) | (
                ann_pop & ((prop - current).abs() > 0.01)
            )
        else:
            ch = (prop - current).abs().fillna(0) > 0.01
        fb_compare[fb] = int(ch.sum())

    trace = m[m["QLA"].isin(TRACE) & (m["MPHASE"].astype(str) == "1")][
        ["QLA", "ANN_PREM_PER_UNIT", "MODE_PREMIUM", "MPREM_CURRENT", "MPREM_PROPOSED"]
    ]

    return {
        "stats": stats,
        "top25": top25,
        "by_plan": by_plan,
        "by_seq": by_seq,
        "by_status": by_status,
        "by_type": by_type.reset_index(),
        "by_coverage": by_coverage.reset_index(),
        "blank_rows": blank_rows,
        "blank_with_mode_count": len(blank_with_mode),
        "mmodprem_match": mmodprem_match,
        "mmodprem_total": len(mstr_chk),
        "fb_compare": fb_compare,
        "fb_blank_regression": fb_blank_regression,
        "trace": trace,
        "merged": m,
    }


def _df_to_md(df: pd.DataFrame, max_rows: int | None = None) -> str:
    view = df.head(max_rows) if max_rows else df
    if view.empty:
        return "(none)"
    cols = list(view.columns)
    lines = [
        "| " + " | ".join(str(c) for c in cols) + " |",
        "| " + " | ".join("---" for _ in cols) + " |",
    ]
    for _, row in view.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if isinstance(v, float) and pd.notna(v):
                cells.append(f"{v:.2f}" if abs(v) < 1e6 else f"{v:.4g}")
            else:
                cells.append(str(v) if pd.notna(v) else "")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_report(result: dict) -> None:
    s = result["stats"]
    lines = [
        "# Issue #26 — MPREM Mapping Risk Review Report",
        "",
        f"**Generated by:** `_risk_review_issue26_mprem.py` v{SCRIPT_VERSION}",
        f"**Fallback simulated:** `{s['fallback_mode']}`",
        "**Status:** Risk analysis only — no code changes",
        "",
        "## Go / No-Go Recommendation",
        "",
        "**GO for Development** with **conditional fallback** — see §5.",
        "",
        "Rationale: QLAdmin defines `MPREM` as annual premium per unit. Current mapping is semantically wrong for 83%+ of populated-rate rows. Modal premium remains on `quikmstr.MMODPREM` (unchanged). Primary risk is **2,994 benefit rows with blank `ANN_PREM_PER_UNIT`** — must use explicit fallback, not blind swap.",
        "",
        "## 1. Current vs Proposed Mapping",
        "",
        "| Field | Current source | Proposed source | Change? |",
        "|-------|----------------|-----------------|---------|",
        "| quikridr.MPREM | PPBEN.MODE_PREMIUM | PPBEN.ANN_PREM_PER_UNIT (+ fallback) | **Yes** |",
        "| quikridr.MVPU | PPBEN.VALUE_PER_UNIT | unchanged | No |",
        "| quikridr.MUNIT | PPBEN.NUMBER_OF_UNITS | unchanged | No |",
        "| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | unchanged | No |",
        "| quikmstr.MMODE | PPOLC.BILLING_MODE | unchanged | No |",
        "| quikprmh.PREMIUM | PPBEN/MODE_PREMIUM | unchanged | No |",
        "",
        "## 2. Premium Fields That Must Remain Unchanged",
        "",
        "| Target | Source (rulebook) | Touched by Issue #26? |",
        "|--------|-------------------|----------------------|",
        "| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | **No** |",
        "| quikmstr.MMODE | PPOLC.BILLING_MODE | **No** |",
        "| quikridr.MVPU | PPBEN.VALUE_PER_UNIT | **No** |",
        "| quikridr.MUNIT | PPBEN.NUMBER_OF_UNITS | **No** |",
        "| quikridr fee slots (MANNLFEE, MSEMIFEE, …) | defaults / unmapped | **No** |",
        "| quikprmh.PREMIUM / MLIFE | MODE_PREMIUM | **No** |",
        "| quikplan modal factors | quikplan catalog | **No** |",
        "",
        "## 3. Repo References to quikridr.MPREM",
        "",
        "| Location | Role |",
        "|----------|------|",
        "| `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` | **Only population path** (`MODE_PREMIUM` → `MPREM`) |",
        "| `app.py` / `QLA_Migration/app.py` | Generic rulebook loop — no MPREM-specific transform |",
        "| `validation_config/schema_manifest.json` | Schema column list only |",
        "| `qla_core/non_product_row_governance.py` | Uses MPREM as product-row indicator (non-zero check) |",
        "| Issue #26 research scripts | Read-only analysis |",
        "",
        "No validation rule, claims path, or premium-history job **reads or recalculates** `quikridr.MPREM`.",
        "",
        "## 4. Population Analysis",
        "",
        f"| Metric | Count |",
        f"|--------|------:|",
        f"| Total quikridr rows (joined to PPBEN) | {s['total_quikridr_rows_joined']} |",
        f"| ANN_PREM_PER_UNIT populated (non-zero) | {s['ann_ppu_populated']} |",
        f"| ANN_PREM_PER_UNIT blank/zero | {s['ann_ppu_blank_zero']} |",
        f"| ANN_PREM_PER_UNIT == MODE_PREMIUM | {s['ann_equals_mode']} |",
        f"| ANN_PREM_PER_UNIT != MODE_PREMIUM | {s['ann_differs_mode']} |",
        f"| Rows that would change MPREM (fallback `{s['fallback_mode']}`) | {s['rows_would_change']} |",
        f"| Rows unchanged | {s['rows_unchanged']} |",
        "",
        "### By benefit sequence (BENEFIT_SEQ)",
        "",
        _df_to_md(result["by_seq"]),
        "",
        "### Base vs rider/supplemental (seq 1 vs seq > 1)",
        "",
        _df_to_md(result["by_coverage"]),
        "",
        "### By benefit type",
        "",
        _df_to_md(result["by_type"].head(15)),
        "",
        "### Top plans by row change count",
        "",
        _df_to_md(result["by_plan"].head(15)),
        "",
        "### By phase status (MPHSTAT)",
        "",
        _df_to_md(result["by_status"]),
        "",
        "## 5. Fallback Recommendation",
        "",
        "| Fallback option | Rows changed vs current | Assessment |",
        "|-----------------|------------------------:|------------|",
    ]
    for fb, cnt in result["fb_compare"].items():
        note = "recommended" if fb == "mode_prem" else ("high regression" if fb == "blank" else "not recommended")
        lines.append(f"| `{fb}` | {cnt} | {note} |")

    lines.extend([
        "",
        f"**`blank` fallback regression detail:** {result['fb_blank_regression']} blank-ANN rows currently carry non-zero MPREM and would be cleared.",
        "",
        "**Recommended fallback: `mode_prem` when ANN_PREM_PER_UNIT is blank/zero**",
        "",
        f"- On blank rows (`n={s['ann_ppu_blank_zero']}`), retain current `MODE_PREMIUM` value in MPREM.",
        "- Avoids introducing new zeros/blanks on rows that currently carry a numeric MPREM.",
        "- **Caveat:** On blank rows, retained value is still semantically modal premium, not annual rate — same ambiguity as today, but **no regression** vs current QLAdmin behavior for those rows.",
        "",
        "**Alternative `mode_per_unit` (MODE_PREMIUM ÷ units):** Not recommended as default — can produce nonsensical rates on rider rows and fee-loaded modals.",
        "",
        "**Alternative `blank`:** Would zero/blank MPREM on 2,994+ rows — **high regression risk** for policies currently displaying modal values.",
        "",
        f"Blank ANN rows with non-zero MODE_PREMIUM: **{result['blank_with_mode_count']}** (would stay unchanged under `mode_prem` fallback).",
        "",
        "## 6. Trace Policies (phase 1)",
        "",
        _df_to_md(result["trace"]),
        "",
        "## 7. Top 25 Largest MPREM Changes (proposed vs current)",
        "",
        _df_to_md(result["top25"]),
        "",
        "**Edge case:** `010718276C` phase 4 (SU) has negative `MODE_PREMIUM` (-87.70) but populated `ANN_PREM_PER_UNIT` (1641.30). Proposed mapping correctly uses ANN_PPU; verify rider/supplemental UAT.",
        "",
        "## 8. MMODPREM & Premium History — Untouched",
        "",
        f"| Check | Result |",
        f"|-------|--------|",
        f"| quikmstr.MMODEPREM matches PPOLC MODE_PREMIUM | {result['mmodprem_match']} / {result['mmodprem_total']} |",
        f"| Proposed change touches quikmstr | **No** |",
        f"| Proposed change touches quikprmh | **No** |",
        f"| Proposed change touches modal factors / quikplan | **No** |",
        "",
        "## 9. Material Calculation Impact",
        "",
        "Policies where **populated** ANN_PPU differs from current MPREM: **{}** rows — these are **intentional corrections** (Issue #26 fix), not accidental drift.".format(s["ann_differs_mode"]),
        "",
        "Policies where ANN_PPU is blank and fallback retains MODE_PREMIUM: **no change** vs today.",
        "",
        "Policies where ANN_PPU == MODE_PREMIUM: **{}** rows — **no numeric change**.".format(s["ann_equals_mode"]),
        "",
        "## 10. Recommended Development Agent Task",
        "",
        "1. Update `Sync_Rulebook_quikridr.csv`: `ANN_PREM_PER_UNIT` → `MPREM` (remove `MODE_PREMIUM` → `MPREM`).",
        "2. Add engine-level fallback in `app.py` (minimal): if normalized `ANN_PREM_PER_UNIT` blank/zero after source read, use `MODE_PREMIUM` for MPREM emit only.",
        "3. Do **not** change quikmstr, quikprmh, MVPU, MUNIT, fee fields.",
        "4. Add `_validate_issue26_mprem.py` — assert populated ANN_PPU == emitted MPREM; log fallback usage count.",
        "5. Version bump; full batch + trace policy UAT.",
        "",
        "## 11. Regression Testing Checklist",
        "",
        "- [ ] 010310404C / 010331768C / 010367131C phase-1 MPREM = 13.20 / 10.96 / 9.12",
        "- [ ] quikmstr.MMODPREM unchanged for trace policies",
        "- [ ] quikprmh PREMIUM/MLIFE unchanged",
        "- [ ] MVPU still 1000.00 (typical) on trace policies",
        "- [ ] Fallback row count logged; spot-check 10 blank-ANN policies",
        "- [ ] Phase 2+ rider rows: verify MPREM behavior",
        "- [ ] non_product_row_governance still passes (MPREM indicator rows)",
        "- [ ] Client Coverage Prem/Unit + Policy Modal Premium both correct",
        "",
        "## Appendix A — Blank ANN_PREM_PER_UNIT (full list)",
        "",
        f"**{s['ann_ppu_blank_zero']} rows** — see `Issue_Log_Items/Issue_26/issue26_blank_ann_ppu_all.csv`.",
        "",
        "Sample (first 100): `Issue_Log_Items/Issue_26/issue26_blank_ann_ppu_sample.csv`.",
        "",
    ])

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    sample_path = REPORT.parent / "issue26_blank_ann_ppu_sample.csv"
    full_path = REPORT.parent / "issue26_blank_ann_ppu_all.csv"
    blank = result["blank_rows"]
    cols = ["QLA", "MPHASE", "MPLAN", "MPHSTAT", "BENEFIT_TYPE", "BENEFIT_SEQ", "MODE_PREMIUM", "ANN_PREM_PER_UNIT", "MPREM_CURRENT"]
    blank[cols].head(100).to_csv(sample_path, index=False)
    blank[cols].to_csv(full_path, index=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-report", action="store_true")
    ap.add_argument("--fallback", default="mode_prem", choices=["blank", "mode_prem", "mode_per_unit"])
    args = ap.parse_args()

    result = analyze(args.fallback)
    s = result["stats"]
    print("=== Issue #26 MPREM Risk Review ===")
    for k, v in s.items():
        print(f"  {k}: {v}")
    print("\nFallback comparison (rows changed):")
    for k, v in result["fb_compare"].items():
        print(f"  {k}: {v}")
    print(f"\nMMODPREM match: {result['mmodprem_match']}/{result['mmodprem_total']}")
    print("\nTrace policies (phase 1):")
    print(result["trace"].to_string(index=False))
    print("\nTop 5 MPREM changes:")
    print(result["top25"].head(5)[["QLA", "MPHASE", "MPREM_CURRENT", "MPREM_PROPOSED", "MPREM_DELTA"]].to_string(index=False))

    if args.write_report:
        write_report(result)
        print(f"\nReport written: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
