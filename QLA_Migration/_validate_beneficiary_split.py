"""
Beneficiary equal-split validation (Issue 21I post-conversion QA).

Script version: 1.0

Usage:
  python QLA_Migration/_validate_beneficiary_split.py
  python QLA_Migration/_validate_beneficiary_split.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
EXPECTED_COLUMNS = ["MPOLICY", "MBENFID", "MTYPE", "MRELATION", "MSPLIT"]

GOLDEN_POLICIES = {
    "010391876C": {
        "row_count": 2,
        "mbenfids": {"696178", "599508"},
        "mtype": "P",
        "split_each": "50.00",
    },
    "010818663C": {
        "row_count": 1,
        "mbenfids": {"602078"},
        "mtype": "P",
        "split_each": "100.00",
    },
    "010914384C": {
        "dual_role_mbenfid": "708812",
        "mtypes": {"P", "C"},
    },
}


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def _split_sum(rows: pd.DataFrame) -> float:
    return sum(float(str(v).strip() or 0) for v in rows["MSPLIT"])


def validate(output_dir: Path) -> int:
    benf_path = output_dir / "quikbenf.csv"
    clnt_path = output_dir / "quikclnt.csv"
    errors = []

    if not benf_path.is_file():
        print(f"FAIL — missing {benf_path}")
        return 1

    benf = _read_csv(benf_path)
    cols = [c.strip().upper() for c in benf.columns]
    if cols != EXPECTED_COLUMNS:
        errors.append(f"schema mismatch: expected {EXPECTED_COLUMNS}, got {cols}")

    print("=" * 72)
    print(f"BENEFICIARY SPLIT VALIDATION (Issue 21I, script v{SCRIPT_VERSION})")
    print(f"Output: {output_dir}")
    print("=" * 72)

    dup = benf.groupby(["MPOLICY", "MBENFID", "MTYPE"]).size()
    dup_keys = dup[dup > 1]
    if len(dup_keys):
        errors.append(f"{len(dup_keys)} duplicate (MPOLICY, MBENFID, MTYPE) keys remain")
        print(f"\nGLOBAL: FAIL — {len(dup_keys)} duplicate keys")
    else:
        print("\nGLOBAL: PASS — no duplicate (MPOLICY, MBENFID, MTYPE) keys")

    bad_groups = []
    for (pol, mtype), grp in benf.groupby(["MPOLICY", "MTYPE"]):
        if not str(mtype).strip():
            continue
        total = _split_sum(grp)
        if abs(total - 100.0) > 0.001:
            bad_groups.append((pol, mtype, total, len(grp)))
    if bad_groups:
        errors.append(f"{len(bad_groups)} (MPOLICY, MTYPE) groups do not sum to 100.00")
        print(f"GLOBAL: FAIL — {len(bad_groups)} groups with MSPLIT sum != 100.00")
        for item in bad_groups[:10]:
            print(f"  POL={item[0]} MTYPE={item[1]} sum={item[2]:.2f} rows={item[3]}")
    else:
        print("GLOBAL: PASS — all (MPOLICY, MTYPE) groups sum to 100.00")

    if clnt_path.is_file():
        clnt = _read_csv(clnt_path)
        clnt_ids = set(clnt["MCLIENTID"].astype(str).str.strip())
        missing = benf[~benf["MBENFID"].astype(str).str.strip().isin(clnt_ids)]
        if len(missing):
            errors.append(f"{len(missing)} MBENFID values missing from quikclnt")
            print(f"GLOBAL: FAIL — {len(missing)} MBENFID not in quikclnt")
        else:
            print("GLOBAL: PASS — all MBENFID values exist in quikclnt")
    else:
        print("GLOBAL: SKIP — quikclnt.csv not found for referential check")

    for policy, expect in GOLDEN_POLICIES.items():
        rows = benf[benf["MPOLICY"].astype(str).str.strip() == policy]
        print(f"\n{policy}:")
        if rows.empty:
            errors.append(f"{policy}: not in quikbenf")
            print("  NOT FOUND")
            continue
        for _, r in rows.iterrows():
            print(
                f"  MBENFID={r['MBENFID'].strip()} MTYPE={r['MTYPE'].strip()} "
                f"MSPLIT={r['MSPLIT'].strip()}"
            )

        if "row_count" in expect:
            if len(rows) != expect["row_count"]:
                errors.append(f"{policy}: expected {expect['row_count']} rows, got {len(rows)}")
            ids = set(rows["MBENFID"].astype(str).str.strip())
            if ids != expect["mbenfids"]:
                errors.append(f"{policy}: expected MBENFID {expect['mbenfids']}, got {ids}")
            if not all(rows["MTYPE"].astype(str).str.strip() == expect["mtype"]):
                errors.append(f"{policy}: expected MTYPE={expect['mtype']}")
            if not all(rows["MSPLIT"].astype(str).str.strip() == expect["split_each"]):
                errors.append(f"{policy}: expected MSPLIT={expect['split_each']} each")

        if "dual_role_mbenfid" in expect:
            cid = expect["dual_role_mbenfid"]
            dual = rows[rows["MBENFID"].astype(str).str.strip() == cid]
            types = set(dual["MTYPE"].astype(str).str.strip())
            if types != expect["mtypes"]:
                errors.append(f"{policy}: expected {cid} in MTYPE {expect['mtypes']}, got {types}")
            for mtype in expect["mtypes"]:
                sub = rows[rows["MTYPE"].astype(str).str.strip() == mtype]
                total = _split_sum(sub)
                if abs(total - 100.0) > 0.001:
                    errors.append(f"{policy}: MTYPE={mtype} sum={total:.2f}")

    print("\n" + "=" * 72)
    if errors:
        print(f"RESULT: FAIL ({len(errors)} issue(s))")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("RESULT: PASS — beneficiary split checks OK")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Validate Issue 21I quikbenf equal splits")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    sys.exit(validate(args.output_dir.resolve()))


if __name__ == "__main__":
    main()
