"""Issue #45 Validation Agent — Output-level checks after v57.77 batch."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

MIG = Path(__file__).resolve().parent
ROOT = MIG.parent
EV = ROOT / "Issue_Log_Items" / "Issue_45" / "evidence"
BEFORE = EV / "before_batch_v57.77"
OUT = MIG / "Output" / "quikmstr.csv"
EXC = MIG / "Reports" / "bank_draft_account_exceptions.csv"

TRACE = ("010157076C", "010161748C", "010348734C")
NEITHER_MP = ()  # resolve via SOURCE_POLICY 9015000043


def mask(mb: str) -> str:
    mb = str(mb or "").strip()
    if not mb or "/" not in mb:
        return mb or "(blank)"
    a, c = mb.split("/", 1)
    ad, cd = re.sub(r"\D", "", a), re.sub(r"\D", "", c)
    a4 = ad[-4:] if len(ad) >= 4 else "????"
    c4 = cd[-4:] if len(cd) >= 4 else "????"
    return f"*****{a4}/****{c4}"


def main() -> int:
    errors: list[str] = []
    print("=== Issue #45 Output Validation ===")

    if not OUT.is_file():
        print(f"FAIL: missing {OUT}")
        return 1
    if not EXC.is_file():
        print(f"FAIL: missing {EXC}")
        return 1
    if not (BEFORE / "quikmstr.csv").is_file():
        print(f"FAIL: missing before snapshot {BEFORE}")
        return 1

    qm = pd.read_csv(OUT, dtype=str).fillna("")
    bq = pd.read_csv(BEFORE / "quikmstr.csv", dtype=str).fillna("")
    exc = pd.read_csv(EXC, dtype=str).fillna("")
    qm.columns = [c.strip().upper() for c in qm.columns]
    bq.columns = [c.strip().upper() for c in bq.columns]
    exc.columns = [c.strip().upper() for c in exc.columns]

    print(f"quikmstr rows: {len(qm)} (before {len(bq)})")
    print(f"exception rows: {len(exc)}")
    print(f"exception cols: {list(exc.columns)}")
    if "EXCEPTION_REASON" in exc.columns:
        print("reasons:", exc["EXCEPTION_REASON"].value_counts().to_dict())

    # 1) Trace policies filled
    for mp in TRACE:
        row = qm[qm["MPOLICY"].astype(str).str.strip() == mp]
        if row.empty:
            errors.append(f"Trace {mp} missing from quikmstr")
            continue
        r = row.iloc[0]
        mb = str(r["MBANKNO"]).strip()
        bf = str(r["MBILLFRM"]).strip()
        print(f"Trace {mp}: MBILLFRM={bf} MBANKNO={mask(mb)}")
        if bf != "2":
            errors.append(f"Trace {mp}: MBILLFRM expected 2 got {bf}")
        if not mb or "/" not in mb:
            errors.append(f"Trace {mp}: MBANKNO still blank")

    # 2) Exception count dropped
    if len(exc) > 30:
        errors.append(f"Exception count too high: {len(exc)} (expected ~15-24)")
    if len(exc) < 1:
        # 13 neither + some MISSING_ROUTING expected; warn if zero unless truly perfect
        print("NOTE: zero exceptions (unexpected but possible)")

    # 3) Neither-source still exception
    if "SOURCE_POLICY" in exc.columns:
        if not (exc["SOURCE_POLICY"].astype(str).str.strip() == "9015000043").any():
            errors.append("9015000043 should remain in exceptions (neither source)")

    # 4) PAC filled vs blank
    pac = qm[qm["MBILLFRM"].astype(str).str.strip() == "2"]
    filled = pac[pac["MBANKNO"].astype(str).str.strip() != ""]
    blank = pac[pac["MBANKNO"].astype(str).str.strip() == ""]
    print(f"PAC rows: {len(pac)} filled={len(filled)} blank={len(blank)}")
    if len(filled) < 2000:
        errors.append(f"PAC filled MBANKNO too low: {len(filled)}")

    # 5) Previously banked PPACH sample unchanged
    sample_path = BEFORE / "ppach_banked_sample_before.csv"
    if sample_path.is_file():
        bb = pd.read_csv(sample_path, dtype=str).fillna("")
        qb = qm.set_index(qm["MPOLICY"].astype(str).str.strip())
        changed = 0
        checked = 0
        mmode_chg = 0
        macct_chg = 0
        for _, r in bb.iterrows():
            mp = str(r["MPOLICY"]).strip()
            if mp not in qb.index:
                continue
            checked += 1
            after = qb.loc[mp]
            if isinstance(after, pd.DataFrame):
                after = after.iloc[0]
            if str(r["MBANKNO"]).strip() != str(after["MBANKNO"]).strip():
                changed += 1
                if changed <= 3:
                    print("PPACH CHANGED", mp, mask(r["MBANKNO"]), "->", mask(after["MBANKNO"]))
            if "MMODEPREM" in bb.columns and str(r.get("MMODEPREM", "")).strip() != str(after.get("MMODEPREM", "")).strip():
                mmode_chg += 1
            if "MACCTNO" in bb.columns and str(r.get("MACCTNO", "")).strip() != str(after.get("MACCTNO", "")).strip():
                macct_chg += 1
        print(f"PPACH sample: checked={checked} MBANKNO_changed={changed} MMODEPREM_chg={mmode_chg} MACCTNO_chg={macct_chg}")
        if changed:
            errors.append(f"PPACH-banked MBANKNO changed on {changed}/{checked} sample rows")
        if mmode_chg:
            errors.append(f"MMODEPREM changed on {mmode_chg} sample rows")
        if macct_chg:
            errors.append(f"MACCTNO changed on {macct_chg} sample rows")

    # 6) Previously blank candidates: many now filled; all still MBILLFRM=2
    prev_blank = set(
        bq[
            (bq["MBILLFRM"].astype(str).str.strip() == "2")
            & (bq["MBANKNO"].astype(str).str.strip() == "")
        ]["MPOLICY"]
        .astype(str)
        .str.strip()
    )
    qb = qm.set_index(qm["MPOLICY"].astype(str).str.strip())
    still2 = 0
    now_filled = 0
    for mp in prev_blank:
        if mp not in qb.index:
            continue
        after = qb.loc[mp]
        if isinstance(after, pd.DataFrame):
            after = after.iloc[0]
        if str(after["MBILLFRM"]).strip() == "2":
            still2 += 1
        if str(after["MBANKNO"]).strip():
            now_filled += 1
    print(f"prev blank={len(prev_blank)} still MBILLFRM=2={still2} now filled={now_filled}")
    if now_filled < 700:
        errors.append(f"rescued fills too low: {now_filled}")
    if still2 < len(prev_blank) * 0.99:
        errors.append("MBILLFRM drift on previously blank bank-draft policies")

    # 7) New exception columns present
    for col in ("PPPAC_ACCOUNT", "ABA_SOURCE", "BANK_SOURCE", "EXCEPTION_REASON"):
        if col not in exc.columns:
            errors.append(f"exception CSV missing column {col}")

    # Row count stability
    if abs(len(qm) - len(bq)) > 5:
        errors.append(f"quikmstr row count drift: before {len(bq)} after {len(qm)}")

    # Write evidence
    EV.mkdir(parents=True, exist_ok=True)
    rows = []
    for mp in TRACE:
        row = qm[qm["MPOLICY"].astype(str).str.strip() == mp]
        if row.empty:
            continue
        r = row.iloc[0]
        rows.append(
            {
                "MPOLICY": mp,
                "MBILLFRM": r["MBILLFRM"],
                "MBANKNO_MASKED": mask(r["MBANKNO"]),
            }
        )
    pd.DataFrame(rows).to_csv(EV / "issue45_validation_trace_masked.csv", index=False)
    exc.to_csv(EV / "issue45_exceptions_after.csv", index=False)

    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
