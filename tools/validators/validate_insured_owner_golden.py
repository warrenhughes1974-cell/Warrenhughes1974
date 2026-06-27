"""
Golden-policy insured/owner validation (post-conversion QA only).

Script version: 1.1

Usage:
  python QLA_Migration/_validate_insured_owner_golden.py
  python QLA_Migration/_validate_insured_owner_golden.py --output-dir QLA_Migration/Output
  python QLA_Migration/_validate_insured_owner_golden.py --source-dir QLA_Migration/Source
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "1.1"
PPOLC_GLOB = "PPOLC_PolicyMaster_Extract_*.csv"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
DEFAULT_SOURCE = PROJECT_ROOT / "QLA_Migration" / "Source"

GOLDEN_POLICIES = {
    "010818663C": {"insured_last": "PROCTOR", "owner_last": "PROCTOR", "expected_client_id": "602078"},
    "010713704C": {"insured_last": None, "owner_last": None},
    "010391876C": {"insured_last": None, "owner_last": None},
    "010448806C": {"insured_last": None, "owner_last": None},
    "010391895C": {"insured_last": None, "owner_last": None},
    "010718309C": {"insured_last": None, "owner_last": None},
    "010765930C": {"insured_last": None, "owner_last": None},
}


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def _find_rna_extract(source_dir: Path) -> Path | None:
    matches = sorted(source_dir.glob("RelationshipNameAddress_Extract*.csv"))
    return matches[-1] if matches else None


def _find_ppolc_extract(source_dir: Path) -> Path:
    """Locate PPOLC policy master extract; prefer newest when multiple exist."""
    matches = list(source_dir.glob(PPOLC_GLOB))
    if not matches:
        raise FileNotFoundError(
            f"No PPOLC policy master extract found in: {source_dir}\n"
            f"Expected filename pattern: {PPOLC_GLOB}"
        )
    if len(matches) == 1:
        return matches[0]
    selected = max(matches, key=lambda p: p.stat().st_mtime)
    print(
        f"PPOLC source: {selected} "
        f"(selected from {len(matches)} matching files by modification time)"
    )
    return selected


def _client_name(clnt: pd.DataFrame, client_id: str) -> str:
    cid = str(client_id).strip()
    if not cid:
        return ""
    row = clnt[clnt["MCLIENTID"].astype(str).str.strip() == cid]
    if row.empty:
        return f"(client {cid} NOT IN quikclnt)"
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
        print("Run full batch first (quikclnt -> quikclid -> quikmstr).")
        return 1

    mstr = _read_csv(mstr_path)
    clnt = _read_csv(clnt_path)
    clid = _read_csv(clid_path)
    errors = []

    print("=" * 72)
    print(f"GOLDEN POLICY INSURED/OWNER VALIDATION (script v{SCRIPT_VERSION})")
    print(f"Output: {output_dir}")

    ppolc_path = _find_ppolc_extract(source_dir)
    if len(list(source_dir.glob(PPOLC_GLOB))) == 1:
        print(f"PPOLC source: {ppolc_path}")
    ppolc = _read_csv(ppolc_path)
    if "PRIMARY_PERSON" in ppolc.columns:
        i_src = (ppolc["PRIMARY_PERSON"].astype(str).str.strip().str.upper() == "I").sum()
        print(f"PPOLC PRIMARY_PERSON='I' rows: {i_src} (must not map to quikmstr.MPRIMID)")

    rna_path = _find_rna_extract(source_dir)
    print(f"RNA source: {rna_path or '(not found — name-only checks still run)'}")
    print("=" * 72)

    i_flags = mstr[mstr["MPRIMID"].astype(str).str.strip().str.upper() == "I"]
    if len(i_flags):
        errors.append(f'{len(i_flags)} quikmstr row(s) have MPRIMID="I" (PRIMARY_PERSON type flag leak)')
        print(f"\nGLOBAL: FAIL — {len(i_flags)} policies with MPRIMID='I'")
    else:
        print("\nGLOBAL: PASS — no MPRIMID='I' values")

    single_alpha = mstr[
        mstr["MPRIMID"].astype(str).str.strip().str.match(r"^[A-Za-z]$", na=False)
    ]
    if len(single_alpha):
        errors.append(f"{len(single_alpha)} quikmstr row(s) have single-letter MPRIMID (type-flag leak)")

    clnt_ids = set(clnt["MCLIENTID"].astype(str).str.strip())
    for policy, expect in GOLDEN_POLICIES.items():
        pol_rows = mstr[mstr["MPOLICY"].astype(str).str.strip() == policy]
        if pol_rows.empty:
            errors.append(f"{policy}: not found in quikmstr.csv")
            print(f"\n{policy}: NOT IN quikmstr")
            continue

        row = pol_rows.iloc[0]
        prim = str(row.get("MPRIMID", "")).strip()
        ownr = str(row.get("MOWNRID", "")).strip()
        prim_name = _client_name(clnt, prim)
        ownr_name = _client_name(clnt, ownr)

        clid_rows = clid[
            (clid["MPOLICY"].astype(str).str.strip() == policy)
            & (clid["MPHASE"].astype(str).str.strip().isin(["1", ""]))
        ]
        in_rows = clid_rows[clid_rows["MRELATION"].astype(str).str.strip().isin(["IN", "INSD"])]
        po_rows = clid_rows[clid_rows["MRELATION"].astype(str).str.strip().isin(["PO", "OWNR"])]

        print(f"\n{policy}:")
        print(f"  MPRIMID={prim or '(blank)'} -> {prim_name}")
        print(f"  MOWNRID={ownr or '(blank)'} -> {ownr_name}")
        print(f"  quikclid IN rows: {len(in_rows)} | PO rows: {len(po_rows)}")

        if not prim:
            errors.append(f"{policy}: MPRIMID is blank")
        elif prim.upper() == "I":
            errors.append(f"{policy}: MPRIMID is 'I'")
        if not ownr:
            errors.append(f"{policy}: MOWNRID is blank")
        if prim and prim not in clnt_ids:
            errors.append(f"{policy}: MPRIMID {prim} not in quikclnt")
        if ownr and ownr not in clnt_ids:
            errors.append(f"{policy}: MOWNRID {ownr} not in quikclnt")

        exp_last = expect.get("insured_last")
        if exp_last and exp_last.upper() not in prim_name.upper():
            errors.append(f"{policy}: insured expected last name {exp_last}, got {prim_name}")
        exp_own = expect.get("owner_last")
        if exp_own and exp_own.upper() not in ownr_name.upper():
            errors.append(f"{policy}: owner expected last name {exp_own}, got {ownr_name}")

        exp_cid = expect.get("expected_client_id")
        if exp_cid and prim != exp_cid:
            errors.append(f"{policy}: expected MPRIMID {exp_cid}, got {prim or '(blank)'}")

    print("\n" + "=" * 72)
    if errors:
        print(f"RESULT: FAIL ({len(errors)} issue(s))")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("RESULT: PASS — golden policy insured/owner checks OK")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Validate insured/owner on golden Issue 21 policies")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    sys.exit(validate(args.output_dir.resolve(), args.source_dir.resolve()))


if __name__ == "__main__":
    main()
