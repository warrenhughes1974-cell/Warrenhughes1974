"""
Issue 21M / 21M-FU QUIKMEMO validation.

Validates quikmemo.csv emitted from PNOTE + PENSE dual-source merge,
merged to one row per MEMOKEY (Issue 21M-FU).
Confirms unrelated table row counts unchanged and Issue #25/#26 preservation.

Usage:
  python QLA_Migration/_validate_issue21m_quikmemo.py
  python QLA_Migration/_validate_issue21m_quikmemo.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import dbf
import pandas as pd

SCRIPT_VERSION = "2.0"
ENGINE_VERSION = "v57.34"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
UAT_DBF_DIR = DEFAULT_OUTPUT / "quikmemo_uat_dbf"
SRC = PROJECT_ROOT / "QLA_Migration" / "Source"
CW = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"

PNOTE_FILE = "PNOTE_PolicyNotes_Extract_20260530.csv"
PENSE_FILE = "PENSE_ENSData_Extract_20260530.csv"

MEMO_SEGMENT_SEPARATOR = "\n---\n"

# Issue 21M-FU expected counts (post-merge grain)
EXPECTED = {
    "emitted_rows": 4380,
    "segment_rows": 29279,
    "segment_pnote": 6003,
    "segment_pense": 23276,
    "skipped_blank_pnote": 30,
    "duplicate_memokey_groups": 0,
    "max_rows_per_memokey": 1,
}

INTEGRITY_SAMPLE_POLICIES = [
    ("010718309C", "single_pnote"),
    ("010448806C", "single_pense"),
    ("010713704C", "mixed_pnote_pense"),
    ("010785099C", "largest_merged"),
    ("010335038C", "original_uat_example"),
]

TRACE_POLICIES = [
    "010391876C", "010391895C", "010448806C", "010713704C", "010718309C",
    "010765930C", "010818663C", "010785099C", "010887927C", "010310404C",
    "010335038C",
]

ROW_COUNT_TABLES = [
    "quikmstr.csv", "quikridr.csv", "quikprmh.csv", "quikplan.csv",
    "quikclid.csv", "quikclnt.csv", "quikactg.csv", "quikclms.csv", "quikclmp.csv",
]

REGRESSION_BASELINE = {
    "quikmstr.csv": 5083,
    "quikridr.csv": 7002,
    "quikprmh.csv": 205577,
    "quikplan.csv": 141,
    "quikclid.csv": 46753,
    "quikclnt.csv": 13846,
}


def _read(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def _read_source(path: Path) -> pd.DataFrame:
    df = _read(path)
    if len(df) and df.iloc[0].astype(str).str.contains("---").any():
        df = df.iloc[1:].reset_index(drop=True)
    return df


def _count_segments(memotext: str) -> tuple[int, int, int]:
    """Return (total_segments, pnote_segments, pense_segments)."""
    if not memotext:
        return 0, 0, 0
    parts = memotext.split(MEMO_SEGMENT_SEPARATOR)
    pnote = sum(1 for p in parts if p.startswith("[PNOTE]"))
    pense = sum(1 for p in parts if p.startswith("[ENS]"))
    return len(parts), pnote, pense


def _segment_dates(memotext: str) -> list[str]:
    parts = memotext.split(MEMO_SEGMENT_SEPARATOR) if memotext else []
    dates = []
    for part in parts:
        m = re.search(r"Date:\s*(\S+)", part)
        dates.append(m.group(1) if m else "")
    return dates


def validate(output_dir: Path, before_dir: Path | None) -> int:
    print("=" * 72)
    print(f"ISSUE 21M-FU QUIKMEMO VALIDATION (script v{SCRIPT_VERSION}, engine {ENGINE_VERSION})")
    print(f"Output: {output_dir}")
    print("=" * 72)

    errors: list[str] = []
    warnings: list[str] = []

    memo_path = output_dir / "quikmemo.csv"
    pnote_path = SRC / PNOTE_FILE
    pense_path = SRC / PENSE_FILE
    dbf_path = UAT_DBF_DIR / "quikmemo.dbf"

    for p in (memo_path, pnote_path, pense_path, CW):
        if not p.is_file():
            errors.append(f"Missing required file: {p}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1

    memo = _read(memo_path)
    pnote = _read_source(pnote_path)
    pense = _read_source(pense_path)

    # --- Schema ---
    if list(memo.columns) != ["MEMOKEY", "MEMOTEXT"]:
        errors.append(f"quikmemo columns wrong: {list(memo.columns)}")

    # --- Population counts (21M-FU merged grain) ---
    print("\n--- Population ---")
    print(f"  quikmemo rows: {len(memo)} (expected {EXPECTED['emitted_rows']})")
    if len(memo) != EXPECTED["emitted_rows"]:
        errors.append(f"Row count {len(memo)} != expected {EXPECTED['emitted_rows']}")

    unique_keys = memo["MEMOKEY"].str.strip().nunique()
    print(f"  unique MEMOKEY: {unique_keys} (expected {EXPECTED['emitted_rows']})")
    if unique_keys != EXPECTED["emitted_rows"]:
        errors.append(f"Unique MEMOKEY {unique_keys} != row count {len(memo)}")

    dup_groups = memo.groupby(memo["MEMOKEY"].str.strip()).size()
    dup_count = int((dup_groups > 1).sum())
    max_per_key = int(dup_groups.max()) if len(dup_groups) else 0
    print(f"  duplicate MEMOKEY groups: {dup_count} (expected {EXPECTED['duplicate_memokey_groups']})")
    print(f"  max rows per MEMOKEY: {max_per_key} (expected {EXPECTED['max_rows_per_memokey']})")
    if dup_count != EXPECTED["duplicate_memokey_groups"]:
        errors.append(f"Duplicate MEMOKEY groups {dup_count} != 0")
    if max_per_key != EXPECTED["max_rows_per_memokey"]:
        errors.append(f"Max rows per MEMOKEY {max_per_key} != 1")

    blank_keys = memo[memo["MEMOKEY"].str.strip().eq("")]
    if len(blank_keys):
        errors.append(f"{len(blank_keys)} blank MEMOKEY rows")

    seg_totals = memo["MEMOTEXT"].apply(_count_segments)
    total_segments = int(seg_totals.apply(lambda x: x[0]).sum())
    total_pnote_seg = int(seg_totals.apply(lambda x: x[1]).sum())
    total_pense_seg = int(seg_totals.apply(lambda x: x[2]).sum())
    print(f"  merged segments total: {total_segments} (expected {EXPECTED['segment_rows']})")
    print(f"  [PNOTE] segments: {total_pnote_seg} (expected {EXPECTED['segment_pnote']})")
    print(f"  [ENS] segments: {total_pense_seg} (expected {EXPECTED['segment_pense']})")
    if total_segments != EXPECTED["segment_rows"]:
        errors.append(f"Segment count {total_segments} != {EXPECTED['segment_rows']}")
    if total_pnote_seg != EXPECTED["segment_pnote"]:
        errors.append(f"PNOTE segments {total_pnote_seg} != {EXPECTED['segment_pnote']}")
    if total_pense_seg != EXPECTED["segment_pense"]:
        errors.append(f"PENSE segments {total_pense_seg} != {EXPECTED['segment_pense']}")

    # --- MEMOKEY formatting (Issue #25) ---
    print("\n--- MEMOKEY (Issue #25) ---")
    bad_width = memo[~memo["MEMOKEY"].str.len().eq(10)]
    if len(bad_width):
        errors.append(f"{len(bad_width)} MEMOKEY values not width 10")
    else:
        print("  PASS: all MEMOKEY width = 10")

    if (memo["MEMOKEY"] != memo["MEMOKEY"].str.rstrip()).any():
        warnings.append("Some MEMOKEY values have trailing spaces beyond pad (expected for left-pad)")

    leading_space = memo[memo["MEMOKEY"].str.match(r"^\s+\S")]
    print(f"  Left-padded MEMOKEY rows: {len(leading_space)}")

    mstr_path = output_dir / "quikmstr.csv"
    if mstr_path.is_file():
        mstr = _read(mstr_path)
        mpol = mstr["MPOLICY"] if "MPOLICY" in mstr.columns else mstr.iloc[:, 0]
        orphan = set(memo["MEMOKEY"].str.strip()) - set(mpol.astype(str).str.strip())
        if orphan:
            errors.append(f"{len(orphan)} MEMOKEY not in quikmstr.MPOLICY")
        else:
            print("  PASS: all MEMOKEY in quikmstr.MPOLICY")

    # --- Memo integrity samples (21M-FU) ---
    print("\n--- Memo integrity samples ---")
    integrity_rows = []
    for qla, label in INTEGRITY_SAMPLE_POLICIES:
        subset = memo[memo["MEMOKEY"].str.strip() == qla]
        if not len(subset):
            errors.append(f"Integrity sample policy missing: {qla} ({label})")
            continue
        row = subset.iloc[0]
        text = row["MEMOTEXT"]
        segs, pn, pe = _count_segments(text)
        sep_count = text.count(MEMO_SEGMENT_SEPARATOR.strip()) if MEMO_SEGMENT_SEPARATOR.strip() else 0
        expected_seps = max(0, segs - 1)
        dates = _segment_dates(text)
        order_ok = dates == sorted(dates, reverse=True) if len(dates) > 1 else True
        integrity_rows.append({
            "policy": qla, "label": label, "rows": len(subset),
            "segments": segs, "pnote_seg": pn, "pense_seg": pe,
            "separator_count": expected_seps, "ordering_ok": order_ok,
            "memotext_len": len(text),
        })
        print(f"  {qla} ({label}): rows={len(subset)} segs={segs} seps={expected_seps} order={'OK' if order_ok else 'FAIL'}")
        if len(subset) != 1:
            errors.append(f"{qla}: expected 1 row, got {len(subset)}")
        if segs > 1 and text.count("---") < expected_seps:
            errors.append(f"{qla}: separator count mismatch")
        if not order_ok:
            errors.append(f"{qla}: segment dates not descending")

    integrity_out = output_dir / "_issue21m_fu_integrity_samples.csv"
    pd.DataFrame(integrity_rows).to_csv(integrity_out, index=False)
    print(f"  Integrity report: {integrity_out}")

    # --- Trace policies ---
    print("\n--- Trace policies ---")
    cw = pd.read_csv(CW, dtype=str, header=None, names=["LP", "QLA"])
    lp_to_qla = dict(zip(cw["LP"].str.strip(), cw["QLA"].str.strip()))

    trace_rows = []
    for qla in TRACE_POLICIES:
        cnt = int((memo["MEMOKEY"].str.strip() == qla).sum())
        subset = memo[memo["MEMOKEY"].str.strip() == qla]
        segs = _count_segments(subset.iloc[0]["MEMOTEXT"])[0] if len(subset) else 0
        pn_cnt = int((pnote["POLICY_NUMBER"].astype(str).str.strip().map(lp_to_qla) == qla).sum())
        pe_cnt = int(
            pense[
                (pense["ENS_KEY_TYPE"].astype(str).str.strip().str.upper() == "P")
                & (pense["POLICY_NUMBER"].astype(str).str.strip().map(lp_to_qla).eq(qla))
            ].shape[0]
        )
        src_total = pn_cnt + pe_cnt
        trace_rows.append({
            "QLA": qla, "QUIKMEMO_rows": cnt, "segments": segs,
            "PNOTE_src": pn_cnt, "PENSE_src": pe_cnt, "src_total": src_total,
        })
        print(f"  {qla}: rows={cnt} segs={segs} (PNOTE src={pn_cnt}, PENSE src={pe_cnt})")

    trace_df = pd.DataFrame(trace_rows)
    trace_out = output_dir / "_issue21m_trace_report.csv"
    trace_df.to_csv(trace_out, index=False)

    # --- DBF / DBT ---
    print("\n--- DBF / DBT ---")
    if not dbf_path.is_file():
        errors.append(f"Missing DBF: {dbf_path}")
    else:
        sidecars = [
            p for p in (
                dbf_path.with_suffix(".dbt"),
                dbf_path.with_suffix(".fpt"),
                Path(str(dbf_path) + "t"),
            ) if p.is_file()
        ]
        print(f"  DBF: {dbf_path} ({dbf_path.stat().st_size} bytes)")
        for sc in sidecars:
            print(f"  Sidecar: {sc.name} ({sc.stat().st_size} bytes)")
        if not sidecars:
            errors.append("No DBT/FPT sidecar co-located with quikmemo.dbf")
        try:
            table = dbf.Table(str(dbf_path))
            table.open()
            dbf_rows = len(table)
            dbf_keys = [str(r.memokey).strip() for r in table]
            dbf_dup = int((pd.Series(dbf_keys).value_counts() > 1).sum())
            empty_memos = sum(1 for r in table if not (r.memotext or "").strip())
            largest = max((len(r.memotext or ""), str(r.memokey).strip()) for r in table)
            table.close()
            print(f"  DBF rows: {dbf_rows} (expected {EXPECTED['emitted_rows']})")
            print(f"  DBF duplicate keys: {dbf_dup}")
            print(f"  Empty MEMOTEXT: {empty_memos}")
            print(f"  Largest MEMOTEXT: {largest[0]} chars (policy {largest[1]})")
            if dbf_rows != EXPECTED["emitted_rows"]:
                errors.append(f"DBF rows {dbf_rows} != {EXPECTED['emitted_rows']}")
            if dbf_dup:
                errors.append(f"DBF duplicate MEMOKEY groups: {dbf_dup}")
            if empty_memos:
                errors.append(f"{empty_memos} empty MEMOTEXT in DBF")
        except Exception as exc:
            errors.append(f"DBF open/read failed: {exc}")

    # --- Regression: unrelated row counts ---
    print("\n--- Regression row counts ---")
    for name, baseline in REGRESSION_BASELINE.items():
        after_p = output_dir / name
        if not after_p.is_file():
            warnings.append(f"Missing regression table: {name}")
            continue
        count = len(_read(after_p))
        ok = count == baseline
        print(f"  {name}: {count} (baseline {baseline}) [{'OK' if ok else 'CHANGED'}]")
        if not ok:
            errors.append(f"{name} row count {count} != baseline {baseline}")

    if before_dir and before_dir.is_dir():
        for name in ROW_COUNT_TABLES:
            before_p = before_dir / name
            after_p = output_dir / name
            if before_p.is_file() and after_p.is_file():
                b, a = len(_read(before_p)), len(_read(after_p))
                if name == "quikmemo.csv":
                    continue
                if b != a:
                    errors.append(f"{name} changed {b} -> {a} vs before snapshot")

    # --- Issue #26 ---
    print("\n--- Issue #26 preservation ---")
    ridr_path = output_dir / "quikridr.csv"
    issue26_pass = False
    if ridr_path.is_file():
        ridr = _read(ridr_path)
        if "MPREM" in ridr.columns:
            mprem_pop = int(ridr["MPREM"].astype(str).str.strip().ne("").sum())
            print(f"  quikridr rows: {len(ridr)}")
            print(f"  MPREM populated: {mprem_pop}")
            if len(ridr) == REGRESSION_BASELINE["quikridr.csv"]:
                issue26_pass = True
                print("  Issue #26: PASS (quikridr unchanged, MPREM present)")
            else:
                errors.append("quikridr row count changed — Issue #26 regression")
        else:
            errors.append("MPREM column missing from quikridr")
    else:
        errors.append("quikridr.csv missing")

    print("\n--- Issue #25 preservation ---")
    issue25_pass = len(bad_width) == 0
    if mstr_path.is_file():
        mstr = _read(mstr_path)
        mpol_bad = int(mstr["MPOLICY"].astype(str).str.len().ne(10).sum()) if "MPOLICY" in mstr.columns else -1
        print(f"  MPOLICY width violations: {mpol_bad}")
        issue25_pass = issue25_pass and mpol_bad == 0
    print(f"  Issue #25: {'PASS' if issue25_pass else 'FAIL'}")

    print("\n" + "=" * 72)
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  - {w}")
    if errors:
        print("RESULT: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("RESULT: PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--before-dir", type=Path, default=None)
    args = ap.parse_args()
    return validate(args.output_dir, args.before_dir)


if __name__ == "__main__":
    sys.exit(main())
