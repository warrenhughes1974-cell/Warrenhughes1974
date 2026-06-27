"""
Issue 21M — QUIKMEMO / Policy Notes / ENS research (read-only).

Scans for LifePRO PNOTE/PENSE extracts, profiles columns and row counts,
and builds a trace sample for Issue #21 policies.

Usage:
  python QLA_Migration/_research_issue21m_quikmemo.py
  python QLA_Migration/_research_issue21m_quikmemo.py --write-csv
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "1.0"
BASE = Path(__file__).resolve().parents[3]
SRC = BASE / "QLA_Migration" / "Source"
OUT = BASE / "Issue_Log_Items" / "Issue_21M"
CW = BASE / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"

PNOTE_PATTERNS = [
    r"^PNOTE[_ ]PolicyNotes[_ ]Extract.*\.csv$",
    r"^PNOTE\.csv$",
]
PENSE_PATTERNS = [
    r"^PENSE[_ ]ENSData[_ ]Extract.*\.csv$",
    r"^PENSE\.csv$",
]

TRACE_POLICIES = [
    "010391876C",
    "010391895C",
    "010448806C",
    "010713704C",
    "010718309C",
    "010765930C",
    "010818663C",
]

# Client annotation (010713704C QLAdmin packet): Excel column letters only — headers TBD
PNOTE_NOTE_COLS_ANNOTATED = ["H", "I", "J", "K", "L"]
PENSE_NOTE_COLS_ANNOTATED = ["N", "O", "P", "Q"]


def _col_letter_index(letter: str) -> int:
    letter = letter.strip().upper()
    n = 0
    for ch in letter:
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n - 1


def _find_source(patterns: list[str]) -> Path | None:
    if not SRC.is_dir():
        return None
    matches: list[Path] = []
    for p in SRC.iterdir():
        if not p.is_file():
            continue
        name = p.name
        for pat in patterns:
            if re.match(pat, name, re.I):
                matches.append(p)
                break
    if not matches:
        return None
    return max(matches, key=lambda x: x.stat().st_mtime)


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", low_memory=False, on_bad_lines="skip").fillna("")
    df.columns = [str(c).replace("\ufeff", "").strip().upper() for c in df.columns]
    return df


def _load_crosswalk() -> dict[str, str]:
    cw = pd.read_csv(CW, dtype=str, header=None, names=["LP", "QLA"])
    cw["LP"] = cw["LP"].str.strip()
    cw["QLA"] = cw["QLA"].str.strip()
    return dict(zip(cw["LP"], cw["QLA"]))


def _policy_col(df: pd.DataFrame) -> str | None:
    for c in ("POLICY_NUMBER", "POLICY_NUM", "MPOLICY", "POLICY"):
        if c in df.columns:
            return c
    return df.columns[0] if len(df.columns) else None


def _resolve_annotated_cols(df: pd.DataFrame, letters: list[str]) -> list[str]:
    resolved = []
    for letter in letters:
        idx = _col_letter_index(letter)
        if idx < len(df.columns):
            resolved.append(df.columns[idx])
    return resolved


def _non_empty_rows(df: pd.DataFrame, text_cols: list[str]) -> pd.Series:
    if not text_cols:
        return pd.Series([False] * len(df))
    mask = pd.Series([False] * len(df))
    for c in text_cols:
        if c in df.columns:
            mask |= df[c].astype(str).str.strip().ne("")
    return mask


def analyze() -> dict:
    pnote_path = _find_source(PNOTE_PATTERNS)
    pense_path = _find_source(PENSE_PATTERNS)
    cw_map = _load_crosswalk()

    result = {
        "pnote_path": str(pnote_path) if pnote_path else None,
        "pense_path": str(pense_path) if pense_path else None,
        "pnote_rows": 0,
        "pense_rows": 0,
        "pnote_policies": 0,
        "pense_policies": 0,
        "pnote_cols": [],
        "pense_cols": [],
        "pnote_note_cols_resolved": [],
        "pense_note_cols_resolved": [],
        "trace": [],
        "ppolc_policies": 0,
    }

    ppolc = _find_source([r"^PPOLC[_ ]PolicyMaster[_ ]Extract.*\.csv$", r"^quikmstr\.csv$"])
    if ppolc:
        pm = _read_csv(ppolc)
        pc = _policy_col(pm)
        if pc:
            result["ppolc_policies"] = int(pm[pc].astype(str).str.strip().ne("").sum())

    for label, path, letters in (
        ("pnote", pnote_path, PNOTE_NOTE_COLS_ANNOTATED),
        ("pense", pense_path, PENSE_NOTE_COLS_ANNOTATED),
    ):
        if not path:
            continue
        df = _read_csv(path)
        result[f"{label}_rows"] = len(df)
        result[f"{label}_cols"] = list(df.columns)
        note_cols = _resolve_annotated_cols(df, letters)
        result[f"{label}_note_cols_resolved"] = note_cols
        pol_col = _policy_col(df)
        if pol_col:
            populated = df[_non_empty_rows(df, note_cols)]
            result[f"{label}_policies"] = int(populated[pol_col].astype(str).str.strip().ne("").nunique())

    # Trace sample (5 policies)
    trace_targets = TRACE_POLICIES[:5]
    for qla in trace_targets:
        lp = next((k for k, v in cw_map.items() if v.strip() == qla), None)
        entry = {
            "QLA": qla,
            "LifePRO_LP": lp or "",
            "PNOTE_rows": 0,
            "PENSE_rows": 0,
            "PNOTE_sample": "",
            "PENSE_sample": "",
            "status": "NO_SOURCE_FILES",
        }
        if pnote_path:
            df = _read_csv(pnote_path)
            pol_col = _policy_col(df)
            note_cols = result["pnote_note_cols_resolved"]
            if lp and pol_col:
                sub = df[df[pol_col].astype(str).str.strip() == lp]
                entry["PNOTE_rows"] = len(sub)
                if len(sub) and note_cols:
                    parts = []
                    for _, r in sub.head(3).iterrows():
                        parts.append(" | ".join(str(r.get(c, "")).strip() for c in note_cols if str(r.get(c, "")).strip()))
                    entry["PNOTE_sample"] = " // ".join(parts)[:500]
                    entry["status"] = "PNOTE_FOUND" if parts else "PNOTE_EMPTY"
        if pense_path:
            df = _read_csv(pense_path)
            pol_col = _policy_col(df)
            note_cols = result["pense_note_cols_resolved"]
            if lp and pol_col:
                sub = df[df[pol_col].astype(str).str.strip() == lp]
                entry["PENSE_rows"] = len(sub)
                if len(sub) and note_cols:
                    parts = []
                    for _, r in sub.head(3).iterrows():
                        parts.append(" | ".join(str(r.get(c, "")).strip() for c in note_cols if str(r.get(c, "")).strip()))
                    entry["PENSE_sample"] = " // ".join(parts)[:500]
                    if entry["status"] == "NO_SOURCE_FILES":
                        entry["status"] = "PENSE_FOUND" if parts else "PENSE_EMPTY"
                    elif parts:
                        entry["status"] = "BOTH_FOUND"
        result["trace"].append(entry)

    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-csv", action="store_true", help="Write trace CSV to Issue_21M folder")
    args = ap.parse_args()

    print("=" * 72)
    print(f"Issue 21M QUIKMEMO Research (script v{SCRIPT_VERSION})")
    print(f"Source folder: {SRC}")
    print("=" * 72)

    r = analyze()
    print(f"\nPPOLC policy count (proxy upper bound): {r['ppolc_policies']}")
    print(f"\nPNOTE file: {r['pnote_path'] or 'NOT FOUND'}")
    print(f"  rows={r['pnote_rows']} policies_with_note_cols={r['pnote_policies']}")
    if r["pnote_note_cols_resolved"]:
        print(f"  annotated cols H-L resolved: {r['pnote_note_cols_resolved']}")
    print(f"\nPENSE file: {r['pense_path'] or 'NOT FOUND'}")
    print(f"  rows={r['pense_rows']} policies_with_ens_cols={r['pense_policies']}")
    if r["pense_note_cols_resolved"]:
        print(f"  annotated cols N-Q resolved: {r['pense_note_cols_resolved']}")

    print("\n--- Trace sample (5 Issue #21 policies) ---")
    trace_df = pd.DataFrame(r["trace"])
    print(trace_df.to_string(index=False))

    if args.write_csv:
        OUT.mkdir(parents=True, exist_ok=True)
        out_path = OUT / "issue21m_trace_sample.csv"
        trace_df.to_csv(out_path, index=False)
        print(f"\nWrote: {out_path}")

    if not r["pnote_path"] and not r["pense_path"]:
        print("\nRESULT: BLOCKED — PNOTE/PENSE extracts not in Source/. Request LifePRO re-extract.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
