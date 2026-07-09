"""
Issue #21A — quikmstr MNFOPT (NFO option) validation.

Validates:
  - Master_Value_Translation NF_1/NF_2/NF_9 entries
  - PPBENTYP BF_NON_FORFEITURE cache resolution (source simulation)
  - Trace policy MNFOPT in quikmstr output
  - MNFOPT domain 0–3; quikmstr row count; no overwrite regression on 010391876C

Usage:
  python tools/validators/validate_issue21a_mnfopt.py
  python tools/validators/validate_issue21a_mnfopt.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
DEFAULT_SOURCE = PROJECT_ROOT / "QLA_Migration" / "Source"
TRANSLATION = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Value_Translation.csv"
PPBENTYP = DEFAULT_SOURCE / "PPBENTYP_BenefitType_Extract_20260530.csv"
CROSSWALK = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
TRACE_CSV = (
    PROJECT_ROOT / "Issue_Log_Items" / "Issue_21" / "Issue_21A" / "Issue_21A_Trace_Samples.csv"
)

SCRIPT_VERSION = "1.0"
EXPECTED_ROW_COUNT = 5083
NO_OVERWRITE_CONTROL = "010391876C"
REQUIRED_TRANS = {"NF_1": "1", "NF_2": "1", "NF_9": "0"}


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def _strip_val(s: object) -> str:
    return str(s).strip().replace(".0", "")


def _load_trans() -> dict[str, str]:
    trans: dict[str, str] = {}
    with TRANSLATION.open(encoding="latin1") as f:
        for row in csv.DictReader(f):
            k = row.get("Source_Code", row.get("SOURCE_CODE", "")).strip()
            v = row.get("QLA_Result", row.get("QLA_RESULT", "")).strip()
            if k:
                trans[k] = v
    return trans


def _resolve_source_nfo(row: pd.Series) -> str:
    """Issue 21A cache: BF row BF_NON_FORFEITURE else NON_FORFEITURE."""
    tc = _strip_val(row.get("TYPE_CODE", ""))
    bnf = _strip_val(row.get("BF_NON_FORFEITURE", ""))
    nf = _strip_val(row.get("NON_FORFEITURE", ""))

    def _usable(v: str) -> bool:
        if not v or v.lower() in ("nan", "none", "null"):
            return False
        if v in ("-----------------", "--------------"):
            return False
        return bool(v.replace("-", "").strip())

    if tc == "BF" and _usable(bnf):
        return bnf
    if _usable(nf):
        return nf
    return ""


def _translate_nfo(raw: str, trans: dict[str, str]) -> str:
    if not raw:
        return "0"
    key = f"NF_{raw.upper()}"
    if key in trans:
        return trans[key]
    if raw.isdigit():
        return trans.get(key, raw)
    return trans.get(key, "0")


def _build_expected_mnfopt(ppb: pd.DataFrame, cw_map: dict[str, str], trans: dict[str, str]) -> dict[str, str]:
    """Expected MNFOPT when enrich-on-zero applies (rulebook 0/blank only)."""
    expected: dict[str, str] = {}
    for _, r in ppb.iterrows():
        lp = _strip_val(r.get("POLICY_NUMBER", ""))
        mp = cw_map.get(lp, lp)
        raw = _resolve_source_nfo(r)
        val = _translate_nfo(raw, trans)
        if not val.isdigit():
            val = "0"
        expected[mp] = val
    return expected


def validate(output_dir: Path) -> int:
    errors: list[str] = []
    quikmstr_path = output_dir / "quikmstr.csv"

    trans = _load_trans()
    for key, want in REQUIRED_TRANS.items():
        got = trans.get(key)
        if got != want:
            errors.append(f"Translation {key}: expected {want}, got {got!r}")

    if not PPBENTYP.exists():
        errors.append(f"Missing PPBENTYP source: {PPBENTYP}")
    if not quikmstr_path.exists():
        errors.append(f"Missing quikmstr output: {quikmstr_path} (rerun batch conversion)")

    if errors and not quikmstr_path.exists():
        print(f"Issue #21A validator v{SCRIPT_VERSION}")
        print("FAIL (prerequisites)")
        for e in errors:
            print(f"  - {e}")
        return 1

    ppb = _read_csv(PPBENTYP)
    ppb = ppb[ppb["BENEFIT_SEQ"].astype(str).str.strip().isin(["1", "01"])].copy()

    cw = _read_csv(CROSSWALK)
    old_col = "OLD_VALUE" if "OLD_VALUE" in cw.columns else "Old_Value"
    new_col = "NEW_VALUE" if "NEW_VALUE" in cw.columns else "New_Value"
    cw_map = dict(zip(cw[old_col].astype(str).str.strip(), cw[new_col].astype(str).str.strip()))

    qm = _read_csv(quikmstr_path)
    if len(qm) != EXPECTED_ROW_COUNT:
        errors.append(f"quikmstr row count: got {len(qm)}, expected {EXPECTED_ROW_COUNT}")

    mnfopt = qm.set_index("MPOLICY")["MNFOPT"].astype(str).str.strip().str.replace(".0", "", regex=False)
    invalid = mnfopt[~mnfopt.isin(["0", "1", "2", "3", ""])]
    if len(invalid):
        errors.append(f"MNFOPT outside 0–3: {len(invalid)} policies (e.g. {invalid.index[0]}={invalid.iloc[0]})")

    ctrl = qm[qm["MPOLICY"].astype(str).str.strip() == NO_OVERWRITE_CONTROL]
    if ctrl.empty:
        errors.append(f"Control policy missing: {NO_OVERWRITE_CONTROL}")
    elif _strip_val(ctrl.iloc[0]["MNFOPT"]) != "2":
        errors.append(
            f"Regression: {NO_OVERWRITE_CONTROL} MNFOPT must stay 2 (enrich guard), "
            f"got {_strip_val(ctrl.iloc[0]['MNFOPT'])}"
        )

    expected_from_source = _build_expected_mnfopt(ppb, cw_map, trans)

    trace_rows = []
    if TRACE_CSV.exists():
        with TRACE_CSV.open(encoding="utf-8") as f:
            trace_rows = list(csv.DictReader(f))

    print(f"Issue #21A MNFOPT validator v{SCRIPT_VERSION}")
    print(f"Output: {quikmstr_path}")
    print(f"quikmstr rows: {len(qm)}")

    for tr in trace_rows:
        mp = tr["MPOLICY"].strip()
        approved = tr["APPROVED_MNFOPT"].strip()
        current_out = _strip_val(mnfopt.get(mp, "")) or "0"
        sim = expected_from_source.get(mp, "0")
        print(
            f"TRACE {mp}: MNFOPT={current_out} approved={approved} "
            f"source_sim={sim} track={tr.get('FIX_TRACK', '')}"
        )
        if current_out != approved:
            errors.append(f"Trace {mp}: MNFOPT={current_out}, expected {approved}")

    # Source code 9 must not passthrough as 9
    code9 = 0
    for _, r in ppb.iterrows():
        lp = _strip_val(r.get("POLICY_NUMBER", ""))
        mp = cw_map.get(lp, lp)
        raw = _resolve_source_nfo(r)
        if raw == "9":
            code9 += 1
            translated = _translate_nfo(raw, trans)
            if translated != "0":
                errors.append(f"NF_9 safety: policy {mp} translates to {translated}, expected 0")

    print(f"Source code 9 policies (NF_9->0): {code9}")

    print(f"\nErrors: {len(errors)}")
    if errors:
        print("FAIL - rerun batch conversion with v57.47+ if trace policies still at baseline")
        for e in errors[:25]:
            print(f"  - {e}")
        return 1

    print("PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #21A quikmstr MNFOPT validator")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    return validate(args.output_dir.resolve())


if __name__ == "__main__":
    sys.exit(main())
