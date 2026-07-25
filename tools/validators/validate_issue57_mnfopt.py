"""
Issue #57 — quikmstr MNFOPT (NFO option) validation — Option B.

Validates:
  - Master_Value_Translation NF_3/NF_4/NF_5 and preserved NF_1/NF_2/NF_9
  - Sync_Rulebook_quikmstr: PAID_UP_TYPE must NOT map to MNFOPT
  - Eric trace policies (ETI/RPU/APL)
  - Issue #21A regression: 010391876C MNFOPT=2; codes 1/2 -> APL
  - MNFOPT domain 0-3; quikmstr row count

Usage:
  python tools/validators/validate_issue57_mnfopt.py
  python tools/validators/validate_issue57_mnfopt.py --output-dir QLA_Migration/Output
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
RULEBOOK = PROJECT_ROOT / "QLA_Migration" / "Configs" / "Sync_Rulebook_quikmstr.csv"
PPBENTYP = DEFAULT_SOURCE / "PPBENTYP_BenefitType_Extract_20260630.csv"
CROSSWALK = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"

SCRIPT_VERSION = "1.1"
EXPECTED_ROW_COUNT = 5083

REQUIRED_TRANS = {
    "NF_1": "1",
    "NF_2": "1",
    "NF_3": "1",
    "NF_4": "2",
    "NF_5": "3",
    "NF_9": "0",
    "NFO_3": "1",
    "NFO_4": "2",
    "NFO_5": "3",
}

ERIC_TRACES = {
    "010367131C": "2",
    "010148272C": "2",
    "010143726C": "2",
    "010392763C": "3",
    "011221309C": "1",
}

REGRESSION_21A = {
    "010391876C": "2",  # enrich-on-zero guard: non-zero must not be overwritten
}


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def _strip_val(s: object) -> str:
    return str(s).strip().replace(".0", "")


def _canon(v: object) -> str:
    """Policy identity that matches across the Issue #2 key change (v58.29).

    Traces below are recorded in the pre-#2 10-char form; MPOLICY is now 11 characters.
    Dropping a trailing C and a single leading 9 makes both forms comparable.
    """
    s = _strip_val(v).upper()
    if s.endswith("C"):
        s = s[:-1]
    if s.startswith("9"):
        s = s[1:]
    return s


def _load_trans() -> dict[str, str]:
    trans: dict[str, str] = {}
    with TRANSLATION.open(encoding="latin1") as f:
        for row in csv.DictReader(f):
            k = row.get("Source_Code", row.get("SOURCE_CODE", "")).strip()
            if not k and row:
                k = list(row.values())[0].strip()
            v = row.get("QLA_Result", row.get("QLA_RESULT", "")).strip()
            if not v and len(row) >= 2:
                v = list(row.values())[1].strip()
            if k:
                trans[k] = v
    return trans


def _rulebook_has_paid_up_mnfopt() -> bool:
    with RULEBOOK.open(encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            sf = (row.get("Source_Field") or "").strip().upper()
            tf = (row.get("Target_Field") or "").strip().upper()
            if sf == "PAID_UP_TYPE" and tf == "MNFOPT":
                return True
    return False


def _resolve_source_nfo(row: pd.Series) -> str:
    """Issue 21A cache: BF row BF_NON_FORFEITURE else NON_FORFEITURE (seq 1)."""
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


def validate(output_dir: Path) -> int:
    errors: list[str] = []
    quikmstr_path = output_dir / "quikmstr.csv"

    trans = _load_trans()
    for key, want in REQUIRED_TRANS.items():
        got = trans.get(key)
        if got != want:
            errors.append(f"Translation {key}: expected {want}, got {got!r}")

    if _rulebook_has_paid_up_mnfopt():
        errors.append("Rulebook still maps PAID_UP_TYPE -> MNFOPT (Issue #57 Option B)")

    if not quikmstr_path.exists():
        errors.append(f"Missing quikmstr output: {quikmstr_path} (rerun batch conversion)")

    if errors and not quikmstr_path.exists():
        print(f"Issue #57 MNFOPT validator v{SCRIPT_VERSION}")
        print("FAIL (prerequisites)")
        for e in errors:
            print(f"  - {e}")
        return 1

    qm = _read_csv(quikmstr_path)
    if len(qm) != EXPECTED_ROW_COUNT:
        errors.append(f"quikmstr row count: got {len(qm)}, expected {EXPECTED_ROW_COUNT}")

    qm["_CANON"] = qm["MPOLICY"].map(_canon)
    mnfopt = qm.set_index("_CANON")["MNFOPT"].astype(str).str.strip().str.replace(".0", "", regex=False)
    invalid = mnfopt[~mnfopt.isin(["0", "1", "2", "3", ""])]
    if len(invalid):
        errors.append(f"MNFOPT outside 0-3: {len(invalid)} policies (e.g. {invalid.index[0]}={invalid.iloc[0]})")

    print(f"Issue #57 MNFOPT validator v{SCRIPT_VERSION}")
    print(f"Output: {quikmstr_path}")
    print(f"quikmstr rows: {len(qm)}")

    for mp, want in {**ERIC_TRACES, **REGRESSION_21A}.items():
        got = _strip_val(mnfopt.get(_canon(mp), "")) or "0"
        label = "ERIC" if mp in ERIC_TRACES else "21A"
        print(f"TRACE {label} {mp}: MNFOPT={got} expected={want}")
        if got != want:
            errors.append(f"Trace {mp}: MNFOPT={got}, expected {want}")

    # Spot-check: code 5 with PAID_UP_TYPE=PU must not stay 0 (Eric RPU)
    if PPBENTYP.exists():
        ppb = _read_csv(PPBENTYP)
        ppb = ppb[ppb["BENEFIT_SEQ"].astype(str).str.strip().isin(["1", "01"])].copy()
        # Match on canonical identity rather than the crosswalk: Master_Crosswalk.csv still
        # holds pre-Issue-#2 New_Value keys, so a cw lookup here silently matches nothing.
        for _, r in ppb.iterrows():
            lp = _strip_val(r.get("POLICY_NUMBER", ""))
            if _canon(lp) != _canon("010392763C"):
                continue
            raw = _resolve_source_nfo(r)
            sim = _translate_nfo(raw, trans)
            print(f"SOURCE 010392763C: LP_NFO={raw} translate-> {sim}")
            if sim != "3":
                errors.append(f"010392763C source sim: expected 3, got {sim}")

    print(f"\nErrors: {len(errors)}")
    if errors:
        print("FAIL - rerun batch conversion after Issue #57 rulebook/translation changes")
        for e in errors[:25]:
            print(f"  - {e}")
        return 1

    print("PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #57 quikmstr MNFOPT validator")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    return validate(args.output_dir.resolve())


if __name__ == "__main__":
    sys.exit(main())
