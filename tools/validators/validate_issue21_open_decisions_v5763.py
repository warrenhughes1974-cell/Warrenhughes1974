"""Post-batch validation for Issue #21 open decisions (v57.63)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output"
REPORTS = ROOT / "QLA_Migration" / "Reports"


def main() -> int:
    print("=" * 72)
    print("ISSUE #21 OPEN-DECISION VALIDATION (v57.63 post-batch)")
    print("=" * 72)
    errors: list[str] = []

    # --- 21D ---
    dv = pd.read_csv(OUT / "quikdvdp.csv", dtype=str, encoding="latin1").fillna("")
    n450 = int((dv["MDEPINT"].astype(str).str.strip() == "4.50").sum())
    n400 = int((dv["MDEPINT"].astype(str).str.strip() == "4.00").sum())
    print(f"\n[21D] MDEPINT: 4.50={n450}  4.00={n400}")
    if n450 < 2000:
        errors.append(f"21D: expected ~2268 ISWL at 4.50, got {n450}")
    else:
        print("  PASS")

    # --- 21E ---
    ridr = pd.read_csv(OUT / "quikridr.csv", dtype=str, encoding="latin1").fillna("")
    ridr.columns = [c.strip().upper() for c in ridr.columns]
    phase = ridr["MPHASE"].astype(str).str.strip().str.lstrip("0").replace("", "0")
    phase1 = ridr[phase == "1"]
    mcv0 = pd.to_numeric(phase1["MCV0"], errors="coerce").fillna(0.0)
    nz = int((mcv0 != 0).sum())
    print(f"\n[21E] phase-1 MCV0 nonzero: {nz} of {len(phase1)}")
    for pol, expect in [("010713704C", 45551.94), ("010818663C", 12475.03)]:
        rows = ridr[
            (ridr["MPOLICY"].astype(str).str.strip() == pol) & (phase == "1")
        ]
        if rows.empty:
            errors.append(f"21E: {pol} phase-1 missing")
            print(f"  FAIL: {pol} not found")
            continue
        val = float(str(rows.iloc[0]["MCV0"]).strip() or 0)
        ok = abs(val - expect) < 0.02
        status = "PASS" if ok else "FAIL"
        print(f"  {pol} MCV0={val} expect={expect} -> {status}")
        if not ok:
            errors.append(f"21E: {pol} MCV0={val} expected {expect}")
    if nz < 1800:
        errors.append(f"21E: expected ~1830 UL MCV0, got {nz}")
    else:
        print(f"  PASS: {nz} UL fund balances loaded")

    trad = ridr[
        (ridr["MPOLICY"].astype(str).str.strip() == "010448806C") & (phase == "1")
    ]
    if not trad.empty:
        tval = str(trad.iloc[0]["MCV0"]).strip()
        print(f"  traditional sample 010448806C MCV0={tval!r}")

    # --- 21F ---
    ph = pd.read_csv(OUT / "quikprmh.csv", dtype=str, encoding="latin1", usecols=["DATEPAID"]).fillna("")
    dates = ph["DATEPAID"].astype(str).str.strip()
    dates = dates[dates.str.len() >= 8]
    print(f"\n[21F] quikprmh rows={len(ph)} DATEPAID min={dates.min()} max={dates.max()}")
    if str(dates.min()) >= "20170101":
        print("  PASS: floor at/after 2017-01-01")
    else:
        print(f"  NOTE: floor earlier than 2017: {dates.min()}")

    # --- 21G ---
    gpath = REPORTS / "issue21g_premium_basis_totals.csv"
    print(f"\n[21G] report exists={gpath.is_file()}")
    if not gpath.is_file():
        errors.append("21G: staged report missing")
    else:
        g = pd.read_csv(gpath, dtype=str).fillna("")
        print(f"  rows={len(g)} books={g['BOOK'].value_counts().to_dict()}")
        for key, label in [("713704", "010713704C"), ("448806", "010448806C")]:
            hit = g[
                g["MPOLICY"].astype(str).str.contains(key, na=False)
                | g["SOURCE_POLICY"].astype(str).str.contains(key, na=False)
            ]
            if len(hit):
                r = hit.iloc[0]
                print(
                    f"  {label}: BOOK={r['BOOK']} PREM={r['PREMIUMS_PAID']} "
                    f"BASIS={r['TAX_BASIS']} STATUS={r['STATUS']}"
                )
            else:
                print(f"  {label}: not found")
        if len(g) < 4000:
            errors.append(f"21G: expected ~4886 rows, got {len(g)}")
        else:
            print(f"  PASS: {len(g)} staged totals")

    # --- 21I ---
    benf = pd.read_csv(OUT / "quikbenf.csv", dtype=str, encoding="latin1").fillna("")
    print(f"\n[21I] rows={len(benf)}")
    print("  MTYPE:", benf["MTYPE"].value_counts().to_dict())
    print("  MRELATION:", benf["MRELATION"].value_counts().head(3).to_dict())
    benf["s"] = pd.to_numeric(benf["MSPLIT"], errors="coerce").fillna(0)
    ok_splits = True
    for t in ["P", "C"]:
        sub = benf[benf["MTYPE"] == t]
        tot = sub.groupby("MPOLICY")["s"].sum()
        bad = int((abs(tot - 100) >= 0.01).sum())
        print(f"  MTYPE={t} policies={len(tot)} sum!=100: {bad}")
        if bad:
            ok_splits = False
            errors.append(f"21I: {bad} {t} groups not summing to 100")
    if ok_splits and set(benf["MRELATION"].astype(str).str.strip().unique()) == {"1000"}:
        print("  PASS: splits reconcile; MRELATION=1000 intentional")
    elif ok_splits:
        print("  PASS: splits reconcile")

    # --- Issue 36 still present ---
    mstr = pd.read_csv(OUT / "quikmstr.csv", dtype=str, encoding="latin1").fillna("")
    print("\n[36] modal factors on quikmstr:")
    for c in ["MSEMI", "MQTRL", "MMTHD", "MMTHB"]:
        populated = int((mstr[c].astype(str).str.strip() != "").sum())
        print(f"  {c}: {populated}/{len(mstr)}")
        if populated < 5000:
            errors.append(f"36: {c} under-populated ({populated})")

    print("\n" + "=" * 72)
    if errors:
        print(f"RESULT: FAIL ({len(errors)} issues)")
        for e in errors:
            print(" -", e)
        return 1
    print("RESULT: PASS — all Issue #21 open-decision checks OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
