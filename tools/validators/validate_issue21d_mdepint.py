"""
Issue #21D Track A — quikdvdp.MDEPINT validation (ISWL 4.50% / non-ISWL 4.00%).

Usage:
  python tools/validators/validate_issue21d_mdepint.py
  python tools/validators/validate_issue21d_mdepint.py --output-dir QLA_Migration/Output
  python tools/validators/validate_issue21d_mdepint.py --baseline-dir QLA_Migration/Output/_issue21d_baseline
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from qla_core.cso_mortality_crosswalk import ISWL_MPLAN_ALLOWLIST, is_iswl_mplan

SCRIPT_VERSION = "1.0"
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
ISWL_RATE = "4.50"
NON_ISWL_RATE = "4.00"
TRACE_POLICIES = ("010713704C", "010818663C")


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def _rate(v) -> str:
    try:
        return f"{float(str(v).strip()):.2f}"
    except (TypeError, ValueError):
        return str(v).strip()


def validate(output_dir: Path, baseline_dir: Path | None) -> int:
    dvdp_path = output_dir / "quikdvdp.csv"
    ridr_path = output_dir / "quikridr.csv"
    missing = [p.name for p in (dvdp_path, ridr_path) if not p.is_file()]
    if missing:
        print(f"FAIL — missing: {', '.join(missing)}")
        return 1

    dvdp = _read_csv(dvdp_path)
    ridr = _read_csv(ridr_path)
    errors: list[str] = []

    print("=" * 72)
    print(f"ISSUE #21D TRACK A — MDEPINT VALIDATION (script v{SCRIPT_VERSION})")
    print(f"Output: {output_dir}")
    print(f"ISWL allowlist: {sorted(ISWL_MPLAN_ALLOWLIST)}")
    print("=" * 72)

    base1 = ridr[ridr["MPHASE"].astype(str).str.strip().isin(["1", ""])]
    mplan_by_pol = {}
    for _, row in base1.iterrows():
        pol = str(row.get("MPOLICY", "")).strip()
        if pol and pol not in mplan_by_pol:
            mplan_by_pol[pol] = str(row.get("MPLAN", "")).strip()

    iswl_policies: set[str] = set()
    for pol, mplan in mplan_by_pol.items():
        if is_iswl_mplan(mplan):
            iswl_policies.add(pol)

    dvdp_rates = {_rate(r) for r in dvdp["MDEPINT"].astype(str)}
    print(f"\nUnique MDEPINT values: {sorted(dvdp_rates)}")

    iswl_rows = dvdp[dvdp["MPOLICY"].astype(str).str.strip().isin(iswl_policies)]
    non_iswl_rows = dvdp[~dvdp["MPOLICY"].astype(str).str.strip().isin(iswl_policies)]

    bad_iswl = iswl_rows[iswl_rows["MDEPINT"].apply(_rate) != ISWL_RATE]
    bad_non = non_iswl_rows[non_iswl_rows["MDEPINT"].apply(_rate) != NON_ISWL_RATE]

    print(f"ISWL policies (phase-1 MPLAN allowlist): {len(iswl_policies)}")
    print(f"quikdvdp ISWL rows: {len(iswl_rows)} | non-ISWL rows: {len(non_iswl_rows)}")

    if len(iswl_rows) != len(iswl_policies):
        errors.append(
            f"ISWL row count mismatch: quikdvdp={len(iswl_rows)} vs MPLAN allowlist={len(iswl_policies)}"
        )

    if len(bad_iswl):
        errors.append(f"{len(bad_iswl)} ISWL policies have MDEPINT != {ISWL_RATE}")
        for pol in bad_iswl["MPOLICY"].head(5):
            errors.append(f"  sample ISWL fail: {pol}")

    if len(bad_non):
        errors.append(f"{len(bad_non)} non-ISWL policies have MDEPINT != {NON_ISWL_RATE}")
        for pol in bad_non["MPOLICY"].head(5):
            errors.append(f"  sample non-ISWL fail: {pol}")

    for pol in TRACE_POLICIES:
        rows = dvdp[dvdp["MPOLICY"].astype(str).str.strip() == pol]
        if rows.empty:
            print(f"\n{pol}: not in quikdvdp")
            continue
        mplan = mplan_by_pol.get(pol, "?")
        rate = _rate(rows.iloc[0]["MDEPINT"])
        expected = ISWL_RATE if is_iswl_mplan(mplan) else NON_ISWL_RATE
        ok = rate == expected
        print(f"\n{pol}: MPLAN={mplan} MDEPINT={rate} expected={expected} {'OK' if ok else 'FAIL'}")
        if not ok:
            errors.append(f"{pol}: MDEPINT {rate} expected {expected}")

    if baseline_dir and (baseline_dir / "quikdvdp.csv").is_file():
        base = _read_csv(baseline_dir / "quikdvdp.csv")
        base = base.set_index(base["MPOLICY"].astype(str).str.strip())
        cur = dvdp.set_index(dvdp["MPOLICY"].astype(str).str.strip())
        common = base.index.intersection(cur.index)
        changed_non_iswl = 0
        for pol in common:
            if pol in iswl_policies:
                continue
            if _rate(base.loc[pol, "MDEPINT"]) != _rate(cur.loc[pol, "MDEPINT"]):
                changed_non_iswl += 1
        print(f"\nBaseline diff: non-ISWL MDEPINT changes = {changed_non_iswl}")
        if changed_non_iswl:
            errors.append(f"{changed_non_iswl} non-ISWL policies changed vs baseline")

    print("\n" + "=" * 72)
    if errors:
        print(f"RESULT: FAIL ({len(errors)} issue(s))")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("RESULT: PASS — ISWL MDEPINT 4.50; non-ISWL unchanged at 4.00")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Validate Issue #21D Track A MDEPINT")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--baseline-dir", type=Path, default=None)
    args = parser.parse_args()
    sys.exit(validate(args.output_dir.resolve(), args.baseline_dir.resolve() if args.baseline_dir else None))


if __name__ == "__main__":
    main()
