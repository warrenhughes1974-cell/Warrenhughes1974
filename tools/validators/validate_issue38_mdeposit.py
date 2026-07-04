"""
Issue #38 — quikdvdp MDEPOSIT / MINTYTD / MINTDATE validation.

Compares quikdvdp output to PPBENTYP ACCUM_DIVIDENDS (MDEPOSIT authority)
and optional PACTG 641 enrichment expectations.

Usage:
  python tools/validators/validate_issue38_mdeposit.py
  python tools/validators/validate_issue38_mdeposit.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from qla_core.cso_mortality_crosswalk import is_iswl_mplan

SCRIPT_VERSION = "1.0"
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
DEFAULT_SOURCE = PROJECT_ROOT / "QLA_Migration" / "Source"
CROSSWALK = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
PPBENTYP = DEFAULT_SOURCE / "PPBENTYP_BenefitType_Extract_20260530.csv"

TRACE_POLICIES = (
    "010378830C",
    "010380808C",
    "010435671C",
    "010713704C",
)
EXPECTED_NONZERO_MDEPOSIT = 59
EXPECTED_ROW_COUNT = 5083
ISWL_CONTROL = "010713704C"
ISWL_MDEPINT = "4.50"
NON_ISWL_MDEPINT = "4.00"
TOLERANCE = 0.01


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def _money(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "").str.strip(), errors="coerce"
    ).fillna(0)


def _rate(v) -> str:
    try:
        return f"{float(str(v).strip()):.2f}"
    except (TypeError, ValueError):
        return str(v).strip()


def _load_expected_mdeposit() -> dict[str, float]:
    pp = _read_csv(PPBENTYP)
    pp = pp[pp["BENEFIT_SEQ"].astype(str).str.strip().isin(["1", "01"])].copy()
    cw = _read_csv(CROSSWALK)
    cw_map = dict(
        zip(cw["OLD_VALUE"].astype(str).str.strip(), cw["NEW_VALUE"].astype(str).str.strip())
    )
    pp["LPOL"] = pp["POLICY_NUMBER"].astype(str).str.strip()
    pp["MPOLICY"] = pp["LPOL"].map(cw_map).fillna(pp["LPOL"])
    pp["ACC"] = _money(pp["ACCUM_DIVIDENDS"])
    return pp.set_index("MPOLICY")["ACC"].to_dict()


def _build_641_cache() -> dict[str, dict]:
    from qla_core.lifepro_source_resolver import resolve_table_source

    pactg_path, _ = resolve_table_source(str(DEFAULT_SOURCE), "quikprmh")
    if not pactg_path:
        return {}

    cw = _read_csv(CROSSWALK)
    cw_map = dict(
        zip(cw["OLD_VALUE"].astype(str).str.strip(), cw["NEW_VALUE"].astype(str).str.strip())
    )
    tx = _read_csv(Path(pactg_path))
    current_year = str(datetime.now().year)
    cache: dict[str, dict] = {}

    for _, row in tx.iterrows():
        raw = str(row.get("POLICY_NUMBER", row.get("POLN", ""))).strip()
        if not raw:
            continue
        pol = cw_map.get(raw, raw)
        cc = str(row.get("CREDIT_CODE", "")).strip()
        dc = str(row.get("DEBIT_CODE", "")).strip()
        trcd = str(row.get("TRCD", "")).strip()
        if not trcd:
            if cc in ("641", "0641"):
                trcd = cc
            elif dc in ("641", "0641"):
                trcd = dc
        if trcd not in ("641", "0641"):
            continue
        amt = float(_money(pd.Series([row.get("TRANS_AMOUNT", 0)])).iloc[0])
        dt = str(row.get("EFFECTIVE_DATE", "")).strip()
        if pol not in cache:
            cache[pol] = {"MINTYTD": 0.0, "MINTDATE": ""}
        if current_year in dt:
            cache[pol]["MINTYTD"] += amt
        if dt > cache[pol]["MINTDATE"]:
            cache[pol]["MINTDATE"] = dt
    return cache


def validate(output_dir: Path) -> int:
    dvdp_path = output_dir / "quikdvdp.csv"
    ridr_path = output_dir / "quikridr.csv"
    missing = [p.name for p in (dvdp_path, ridr_path) if not p.is_file()]
    if missing:
        print(f"FAIL — missing: {', '.join(missing)}")
        return 1

    if not PPBENTYP.is_file():
        print(f"FAIL — missing source: {PPBENTYP}")
        return 1

    dvdp = _read_csv(dvdp_path)
    ridr = _read_csv(ridr_path)
    expected = _load_expected_mdeposit()
    cache_641 = _build_641_cache()
    errors: list[str] = []

    print("=" * 72)
    print(f"ISSUE #38 — QUIKDVDP MDEPOSIT VALIDATION (script v{SCRIPT_VERSION})")
    print(f"Output: {output_dir}")
    print("=" * 72)

    if len(dvdp) != EXPECTED_ROW_COUNT:
        errors.append(f"Row count {len(dvdp)} != expected {EXPECTED_ROW_COUNT}")

    mdep = _money(dvdp["MDEPOSIT"])
    nonzero = int((mdep > 0).sum())
    if nonzero != EXPECTED_NONZERO_MDEPOSIT:
        errors.append(f"MDEPOSIT > 0 count {nonzero} != expected {EXPECTED_NONZERO_MDEPOSIT}")

    mismatches = 0
    for _, row in dvdp.iterrows():
        pol = str(row["MPOLICY"]).strip()
        exp = expected.get(pol, 0.0)
        got = float(_money(pd.Series([row["MDEPOSIT"]])).iloc[0])
        if abs(got - exp) > TOLERANCE:
            mismatches += 1
            if mismatches <= 5:
                errors.append(f"MDEPOSIT mismatch {pol}: got {got:.2f} expected {exp:.2f}")
    if mismatches > 5:
        errors.append(f"... and {mismatches - 5} more MDEPOSIT mismatches")

    base1 = ridr[ridr["MPHASE"].astype(str).str.strip().isin(["1", ""])]
    mplan_by_pol = {}
    for _, row in base1.iterrows():
        pol = str(row.get("MPOLICY", "")).strip()
        if pol and pol not in mplan_by_pol:
            mplan_by_pol[pol] = str(row.get("MPLAN", "")).strip()

    for pol in TRACE_POLICIES:
        rows = dvdp[dvdp["MPOLICY"].astype(str).str.strip() == pol]
        if rows.empty:
            errors.append(f"Trace policy missing: {pol}")
            continue
        r = rows.iloc[0]
        exp_mdep = expected.get(pol, 0.0)
        got_mdep = float(_money(pd.Series([r["MDEPOSIT"]])).iloc[0])
        print(
            f"TRACE {pol}: MDEPOSIT={got_mdep:.2f} (expected {exp_mdep:.2f}) "
            f"MINTYTD={_rate(r['MINTYTD'])} MINTDATE={str(r.get('MINTDATE','')).strip()} "
            f"MDEPINT={_rate(r['MDEPINT'])}"
        )
        if abs(got_mdep - exp_mdep) > TOLERANCE:
            errors.append(f"Trace MDEPOSIT fail {pol}")
        if pol == ISWL_CONTROL:
            if _rate(r["MDEPINT"]) != ISWL_MDEPINT:
                errors.append(f"ISWL control MDEPINT {pol}: got {_rate(r['MDEPINT'])}")
            if got_mdep > TOLERANCE:
                errors.append(f"ISWL control should have zero MDEPOSIT: {pol}")
        elif pol != ISWL_CONTROL and exp_mdep > 0 and got_mdep <= 0:
            errors.append(f"Trace policy should have MDEPOSIT > 0: {pol}")

    ytd_mismatch = 0
    for _, row in dvdp.iterrows():
        pol = str(row["MPOLICY"]).strip()
        c = cache_641.get(pol)
        if not c:
            continue
        got_ytd = float(_money(pd.Series([row["MINTYTD"]])).iloc[0])
        if abs(got_ytd - c["MINTYTD"]) > TOLERANCE:
            ytd_mismatch += 1
    if ytd_mismatch:
        errors.append(f"MINTYTD mismatches vs PACTG 641 cache: {ytd_mismatch}")

    print(f"\nMDEPOSIT > 0: {nonzero} / {EXPECTED_NONZERO_MDEPOSIT}")
    print(f"641 cache policies: {len(cache_641)}")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\nFAIL")
        for e in errors[:20]:
            print(f"  - {e}")
        return 1

    print("\nPASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #38 quikdvdp MDEPOSIT validator")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    return validate(args.output_dir.resolve())


if __name__ == "__main__":
    sys.exit(main())
