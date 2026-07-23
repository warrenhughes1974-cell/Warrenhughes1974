"""Issue #2 regression checks — read-only. Run from repo root with sys.path."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from qla_core.normalize_utils import format_qladmin_mpolicy  # noqa: E402

OUT = ROOT / "QLA_Migration" / "Output"

# Prior full-batch baseline (Issue A run log 2026-07-21 evening)
BASE = {
    "quikmstr.csv": 5083,
    "quikridr.csv": 6934,
    "quikplan.csv": 141,
    "quikprmh.csv": 209470,
    "quikbenh.csv": 41066,
    "quikloan.csv": 356,
    "quikclms.csv": 5594,
    "quikclmp.csv": 6422,
    "quikrmst.csv": 733,
    "QuikIsrr.csv": 3657,
    "quikclid.csv": None,
    "quikclnt.csv": None,
    "quikbenf.csv": None,
    "quikmemo.csv": None,
    "quikdvdp.csv": None,
}


def nrows(name: str) -> int | None:
    p = OUT / name
    if not p.is_file():
        return None
    with open(p, "rb") as f:
        return sum(1 for _ in f) - 1


def main() -> int:
    errors: list[str] = []
    print("=== ROW COUNTS ===")
    for t, b in BASE.items():
        n = nrows(t)
        if n is None:
            print(f"{t}: MISSING")
            errors.append(f"missing {t}")
            continue
        if b is None:
            print(f"{t}: now={n}")
            continue
        delta = n - b
        # Allow small intentional emit drift on history tables
        soft = t in ("quikprmh.csv", "quikbenh.csv")
        ok = delta == 0 or (soft and abs(delta) <= 50)
        print(f"{t}: now={n} base={b} delta={delta} {'OK' if ok else 'FAIL'}")
        if not ok:
            errors.append(f"{t} delta={delta}")

    print("\n=== SCHEMA COLUMN ORDER (spot) ===")
    for t in ("quikmstr.csv", "quikridr.csv", "quikplan.csv"):
        df = pd.read_csv(OUT / t, dtype=str, nrows=0, encoding="latin-1")
        print(f"{t}: {len(df.columns)} cols; first={list(df.columns)[:6]}")

    print("\n=== Issue #99 ISWLFE (checked-in working-tree fix in this build) ===")
    qp = pd.read_csv(OUT / "quikplan.csv", dtype=str).fillna("")
    iswl = ["1658C1", "1658CS", "1659C2", "1659CS", "1659CR", "1659SR", "1669SR", "1679CS"]
    for p in iswl:
        r = qp[qp["PLAN"] == p]
        if r.empty:
            errors.append(f"ISWL plan missing {p}")
            print(p, "MISSING")
            continue
        row = r.iloc[0]
        tags = {k: row.get(k, "") for k in ("MKTG", "PRODUCT", "HLOB")}
        ok = all(v == "ISWLFE" for v in tags.values())
        print(p, tags, "OK" if ok else "FAIL")
        if not ok:
            errors.append(f"ISWLFE fail {p}")

    print("\n=== Issue #2 key contract ===")
    m = pd.read_csv(OUT / "quikmstr.csv", dtype=str)
    lens = m["MPOLICY"].astype(str).str.len().value_counts().to_dict()
    print("lens", lens)
    if lens != {11: len(m)}:
        errors.append(f"MPOLICY width not all 11: {lens}")
    if m["MPOLICY"].astype(str).str.strip().str.startswith("90").mean() < 0.99:
        errors.append("not ~all keys start with 90")
    for lp in ("9010143726", "901222DC"):
        exp = format_qladmin_mpolicy(lp)
        if (m["MPOLICY"] == exp).sum() != 1:
            errors.append(f"missing {exp!r}")

    print("\n=== Non-key spot: quikridr phase-1 for 9010143726 ===")
    r = pd.read_csv(OUT / "quikridr.csv", dtype=str).fillna("")
    key = format_qladmin_mpolicy("9010143726")
    sub = r[(r["MPOLICY"] == key) & (r["MPHASE"].astype(str).str.strip() == "1")]
    if sub.empty:
        errors.append("missing phase-1 ridr for 9010143726")
    else:
        row = sub.iloc[0]
        print({k: row.get(k) for k in ("MPOLICY", "MPLAN", "MPREM", "MUNIT", "MVPU", "MANNLFEE")})

    if "MRIDRID" in r.columns:
        blank = (r["MRIDRID"].astype(str).str.strip() == "").sum()
        print(f"blank MRIDRID: {blank}/{len(r)}")

    # #26 light check: MPREM numeric populated on phase-1 where MUNIT>0
    print("\n=== Issue #26 light (MPREM populated) ===")
    ph1 = r[r["MPHASE"].astype(str).str.strip() == "1"].copy()
    def _f(x):
        try:
            return float(str(x).strip() or "nan")
        except ValueError:
            return float("nan")
    ph1["_u"] = ph1["MUNIT"].map(_f) if "MUNIT" in ph1 else 0
    ph1["_p"] = ph1["MPREM"].map(_f) if "MPREM" in ph1 else 0
    with_units = ph1[ph1["_u"].fillna(0) > 0]
    blank_prem = with_units["_p"].isna() | (with_units["MPREM"].astype(str).str.strip() == "")
    print(f"phase1 with units: {len(with_units)}; blank MPREM among them: {blank_prem.sum()}")
    if blank_prem.sum() > len(with_units) * 0.05:
        errors.append("too many blank MPREM on unit rows")

    print("\n=== Checked-in tip presence (v58.27 artifacts in Output) ===")
    rates = OUT / "rates"
    for name in ("QuikUwpo.csv", "QuikUint.csv", "QuikIssc.csv", "QuikCvs.csv"):
        p = rates / name
        print(f"rates/{name}: {'YES' if p.is_file() else 'NO'} size={p.stat().st_size if p.is_file() else 0}")
        if not p.is_file():
            errors.append(f"missing rates/{name}")

    print("\n" + "=" * 60)
    if errors:
        for e in errors:
            print("FAIL:", e)
        print("REGRESSION: FAIL")
        return 1
    print("REGRESSION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
