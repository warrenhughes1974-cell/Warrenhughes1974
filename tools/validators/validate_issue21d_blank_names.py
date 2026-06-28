"""
Issue #21D Track B1 — blank-name / quikclnt referential integrity validation.

Usage:
  python tools/validators/validate_issue21d_blank_names.py
  python tools/validators/validate_issue21d_blank_names.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
DEFAULT_SOURCE = PROJECT_ROOT / "QLA_Migration" / "Source"
POPULATION_CSV = PROJECT_ROOT / "Issue_Log_Items" / "Issue_21" / "Issue_21D" / "Issue_21D_Blank_Name_Population.csv"

# Legitimately cancelled in RNA (CANCEL_DATE=20050615) — not emitted by design.
ALLOWED_MISSING_CLIENT_IDS = frozenset({"598766"})

# B1-target policies (quikclnt missing row fix).
B1_TARGET_POLICIES = frozenset({
    "010766896C", "011080481C", "010464869C", "010464870C",
    "010872417C", "011047402C", "011047403C",
})


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def _client_name(clnt: pd.DataFrame, client_id: str) -> str:
    cid = str(client_id).strip()
    if not cid:
        return ""
    row = clnt[clnt["MCLIENTID"].astype(str).str.strip() == cid]
    if row.empty:
        return f"(MISSING CLIENT {cid})"
    r = row.iloc[0]
    parts = [str(r.get("MLNAME", "")).strip(), str(r.get("MFNAME", "")).strip()]
    parts = [p for p in parts if p]
    return ", ".join(parts) if parts else f"(client {cid} blank name)"


def validate(output_dir: Path, source_dir: Path) -> int:
    mstr_path = output_dir / "quikmstr.csv"
    clnt_path = output_dir / "quikclnt.csv"
    clid_path = output_dir / "quikclid.csv"
    missing = [p.name for p in (mstr_path, clnt_path, clid_path) if not p.is_file()]
    if missing:
        print(f"FAIL — missing output files: {', '.join(missing)}")
        return 1

    mstr = _read_csv(mstr_path)
    clnt = _read_csv(clnt_path)
    clid = _read_csv(clid_path)
    errors: list[str] = []

    print("=" * 72)
    print(f"ISSUE #21D TRACK B1 — BLANK NAME VALIDATION (script v{SCRIPT_VERSION})")
    print(f"Output: {output_dir}")
    print("=" * 72)

    clnt_ids = set(clnt["MCLIENTID"].astype(str).str.strip()) - {"", "-----------"}

    # RNA NAME_IDs referenced by quikclid must exist in quikclnt.
    ref_ids = set(clid["MCLIENTID"].astype(str).str.strip()) - {"", "-----------"}
    missing_from_clnt = sorted(ref_ids - clnt_ids - ALLOWED_MISSING_CLIENT_IDS)
    print(f"\nquikclid-referenced MCLIENTIDs: {len(ref_ids)}")
    print(f"Missing from quikclnt: {len(missing_from_clnt)}")
    if missing_from_clnt:
        errors.append(f"{len(missing_from_clnt)} quikclid IDs missing from quikclnt")
        for mid in missing_from_clnt[:10]:
            print(f"  missing: {mid}")

    dupes = clnt[clnt.duplicated(subset=["MCLIENTID"], keep=False)]
    if len(dupes):
        errors.append(f"{len(dupes)} duplicate MCLIENTID rows in quikclnt")

    i_flags = mstr[mstr["MPRIMID"].astype(str).str.strip().str.upper() == "I"]
    if len(i_flags):
        errors.append(f'{len(i_flags)} quikmstr row(s) have MPRIMID="I"')
    else:
        print("\nGLOBAL: PASS — no MPRIMID='I' values")

    blank_count = 0
    b1_resolved = 0
    if POPULATION_CSV.is_file():
        pop = _read_csv(POPULATION_CSV)
        for _, prow in pop.iterrows():
            pol = str(prow.get("MPOLICY", "")).strip()
            if not pol:
                continue
            pol_rows = mstr[mstr["MPOLICY"].astype(str).str.strip() == pol]
            if pol_rows.empty:
                continue
            row = pol_rows.iloc[0]
            prim = str(row.get("MPRIMID", "")).strip()
            ownr = str(row.get("MOWNRID", "")).strip()
            prim_name = _client_name(clnt, prim)
            ownr_name = _client_name(clnt, ownr)
            insured_blank = not prim or "MISSING CLIENT" in prim_name
            owner_blank = not ownr or "MISSING CLIENT" in ownr_name
            if insured_blank and owner_blank:
                blank_count += 1
            elif pol in B1_TARGET_POLICIES:
                if not insured_blank or not owner_blank:
                    b1_resolved += 1

    print(f"\nBlank-name population (both roles blank): {blank_count} (baseline target: 18 after B1)")
    print(f"B1-target policies with partial/full name resolution: {b1_resolved}/{len(B1_TARGET_POLICIES)}")

    for pol in sorted(B1_TARGET_POLICIES):
        pol_rows = mstr[mstr["MPOLICY"].astype(str).str.strip() == pol]
        if pol_rows.empty:
            errors.append(f"{pol}: not in quikmstr")
            continue
        row = pol_rows.iloc[0]
        prim = str(row.get("MPRIMID", "")).strip()
        ownr = str(row.get("MOWNRID", "")).strip()
        prim_name = _client_name(clnt, prim)
        ownr_name = _client_name(clnt, ownr)
        ok = "MISSING CLIENT" not in prim_name and prim_name.strip() != ""
        print(f"\n{pol}: MPRIMID={prim or '(blank)'} -> {prim_name} {'OK' if ok else 'FAIL'}")
        if prim and prim not in clnt_ids:
            errors.append(f"{pol}: MPRIMID {prim} not in quikclnt")
        if not ok and prim:
            errors.append(f"{pol}: insured name not resolved")

    print("\n" + "=" * 72)
    if errors:
        print(f"RESULT: FAIL ({len(errors)} issue(s))")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("RESULT: PASS — B1 referential integrity and target policies OK")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Validate Issue #21D Track B1 blank names")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    sys.exit(validate(args.output_dir.resolve(), args.source_dir.resolve()))


if __name__ == "__main__":
    main()
