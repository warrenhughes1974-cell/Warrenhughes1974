"""Issue 21F — Regression (G6) read-only checks for v57.73."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from qla_core.issue21f_premium_adjustment import (  # noqa: E402
    CONV_ADJ_MSOURCE,
    CONV_ADJ_USER_ID,
    is_conversion_adjustment_row,
)

OUT = ROOT / "QLA_Migration" / "Output"
ARC = ROOT / "QLA_Migration" / "Archive" / "quikprmh_pre_21f_v57.72.csv"
SCHEMA = [
    "MPOLICY", "DATEPAID", "RENEWAL", "PREMIUM", "MLIFE", "MTERM", "MSUPP",
    "MANN", "MHEALTH", "XS", "MPAIDTO", "POSTDATE", "MPOSTDATE", "MSOURCE",
    "MBATCH", "USER_ID", "MBILLFRM", "MMODEPD",
]
# Prior documented Output counts from first Regression (pre-v57.73)
EXPECTED_OTHER = {
    "quikmstr": 5083,
    "quikridr": 6934,
    "quikplan": 141,
    "quikclid": 34449,
    "quikclnt": 13597,
    "quikbenf": 5916,
}


def main() -> int:
    findings: list[str] = []

    def fail(msg: str) -> None:
        findings.append(msg)
        print(f"FAIL: {msg}")

    print("=== ROW COUNTS ===")
    counts: dict[str, int] = {}
    for t in list(EXPECTED_OTHER) + ["quikprmh"]:
        p = OUT / f"{t}.csv"
        n = sum(1 for _ in open(p, encoding="latin1", errors="replace")) - 1
        counts[t] = n
        print(f"{t}: {n}")

    prmh = pd.read_csv(OUT / "quikprmh.csv", dtype=str, encoding="latin1").fillna("")
    before = pd.read_csv(ARC, dtype=str, encoding="latin1").fillna("")
    print(f"before archive: {len(before)}")

    if list(prmh.columns) != SCHEMA:
        fail(f"schema drift: {list(prmh.columns)}")
    else:
        print("SCHEMA OK")

    adj_mask = prmh.apply(lambda r: is_conversion_adjustment_row(r.to_dict()), axis=1)
    adj = prmh[adj_mask].copy()
    hist = prmh[~adj_mask].copy()
    print(f"adj={len(adj)} hist={len(hist)}")

    bmask = before.apply(lambda r: is_conversion_adjustment_row(r.to_dict()), axis=1)
    bhist = before[~bmask].copy()
    print(f"before_hist={len(bhist)} before_adj={int(bmask.sum())}")

    if len(bhist) != len(hist):
        fail(f"hist count {len(bhist)} -> {len(hist)}")
    elif not bhist.reset_index(drop=True).equals(hist.reset_index(drop=True)):
        fail("hist content changed")
    else:
        print("HIST unchanged PASS")

    if len(prmh) != len(bhist) + len(adj):
        fail(f"row math {len(prmh)} != {len(bhist)}+{len(adj)}")
    else:
        print(f"ROW_MATH PASS {len(bhist)}+{len(adj)}={len(prmh)}")

    if (hist["MSOURCE"].astype(str).str.strip().str.upper() == CONV_ADJ_MSOURCE).any():
        fail("hist MSOURCE pollution")
    if (hist["USER_ID"].astype(str).str.strip().str.upper() == CONV_ADJ_USER_ID).any():
        fail("hist USER_ID pollution")
    else:
        print("HIST pollution PASS")

    short_adj = int((adj["MPOLICY"].astype(str).map(len) < 10).sum())
    short_hist = int((hist["MPOLICY"].astype(str).map(len) < 10).sum())
    print(f"#25 adj_len<10={short_adj} hist_len<10={short_hist}")
    if short_adj:
        fail(f"#25 {short_adj} adj MPOLICY unpadded")
    else:
        print("#25 PASS")

    ridr_cols = list(pd.read_csv(OUT / "quikridr.csv", nrows=0, encoding="latin1").columns)
    if "MPREM" not in ridr_cols:
        fail("#26 MPREM missing")
    else:
        print(f"#26 MPREM column PASS (MMODPREM={'MMODPREM' in ridr_cols})")

    adj["PREM_F"] = pd.to_numeric(adj["PREMIUM"], errors="coerce")
    prem_sum = float(adj["PREM_F"].sum())
    print(f"CONV_ADJ sum={prem_sum:.2f} count={len(adj)}")
    dates = hist["DATEPAID"].astype(str).str.strip()
    dates = dates[dates.str.len() >= 8]
    print(f"hist DATEPAID min={dates.min()} max={dates.max()}")

    for t, exp in EXPECTED_OTHER.items():
        if counts.get(t) != exp:
            fail(f"{t} count {counts.get(t)} != prior {exp}")
        else:
            print(f"{t} stable PASS")

    print("\n=== VERDICT ===")
    if findings:
        print("FAIL")
        for f in findings:
            print(f" - {f}")
        return 1
    print("PASS")
    print(f"COUNTS={counts}")
    print(f"ADJ_COUNT={len(adj)} ADJ_SUM={prem_sum:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
