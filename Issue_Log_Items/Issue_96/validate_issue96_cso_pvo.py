"""Issue #96 — CSO val PVO + QuikPl* wiring for SAL MULTPL / L17 family.

Validates against full QLA_Migration/Output/ (not Test_Validation only).
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output"
RATES = OUT / "rates"

FOCUS = (
    "1SALOL",
    "1SALMI",
    "1SALML",
    "1L17SP",
    "10L171",
    "10L172",
    "117JPO",
    "17MJPO",
)
TV_COUNTS = {
    "1SALOL": 508,
    "1SALMI": 508,
    "1SALML": 508,
    "1L17SP": 38,
    "10L171": 38,
    "10L172": 38,
    "117JPO": 38,
    "17MJPO": 38,
}
PL_KEY_FIELDS = ("MORT", "ETIMORT", "NFOINT", "INTMETHCV", "RSVINT", "RSVMETH", "INTMETHTV")


def _load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _plan_rows(rows: list[dict], plan: str) -> list[dict]:
    return [r for r in rows if (r.get("PLAN") or "").strip() == plan]


def _codes(row: dict) -> tuple:
    return tuple((row.get(k) or "").strip() for k in PL_KEY_FIELDS)


def main() -> int:
    fails: list[str] = []
    qp = { (r.get("PLAN") or "").strip(): r for r in _load(OUT / "quikplan.csv") }
    tvs = _load(RATES / "QuikTvs.csv")
    pltv = _load(RATES / "QuikPlTv.csv")
    plcv = _load(RATES / "QuikPlCv.csv")
    tv_counts = Counter((r.get("PLAN") or "").strip() for r in tvs)

    for plan in FOCUS:
        row = qp.get(plan)
        if not row:
            fails.append(f"{plan}: missing from quikplan")
            continue
        if (row.get("PLANVALOPT") or "").strip() != "Y":
            fails.append(f"{plan}: PLANVALOPT expected Y got {(row.get('PLANVALOPT') or '').strip()!r}")
        if (row.get("GDVARYTV") or "").strip() != "Y":
            fails.append(f"{plan}: GDVARYTV expected Y got {(row.get('GDVARYTV') or '').strip()!r}")
        if tv_counts.get(plan, 0) != TV_COUNTS[plan]:
            fails.append(f"{plan}: QuikTvs expected {TV_COUNTS[plan]} got {tv_counts.get(plan, 0)}")
        if len(_plan_rows(pltv, plan)) < 2:
            fails.append(f"{plan}: QuikPlTv expected >=2 rows got {len(_plan_rows(pltv, plan))}")
        if plan.startswith("1SAL") and len(_plan_rows(plcv, plan)) < 2:
            fails.append(f"{plan}: QuikPlCv expected >=2 rows got {len(_plan_rows(plcv, plan))}")

    # 1SALMI Pl* codes must match 1SALOL (CSO_Valuation_Setup)
    for label, rows in (("QuikPlTv", pltv), ("QuikPlCv", plcv)):
        ol = sorted(
            ((r.get("GENDER") or "").strip(), _codes(r))
            for r in _plan_rows(rows, "1SALOL")
        )
        mi = sorted(
            ((r.get("GENDER") or "").strip(), _codes(r))
            for r in _plan_rows(rows, "1SALMI")
        )
        if ol and mi and ol != mi:
            fails.append(f"1SALMI {label} codes != 1SALOL ({mi} vs {ol})")

    # L17 children QuikTvs fingerprint == 1L17SP
    def tv_fp(plan: str):
        keys = ["AGE", "CNTL", "GENDER", "UWCLASS", "BAND", "TV0", "TV1", "TV2", "TV3", "TV4"]
        out = []
        for r in tvs:
            if (r.get("PLAN") or "").strip() != plan:
                continue
            out.append(tuple((r.get(k) or "").strip() for k in keys))
        return sorted(out)

    parent = tv_fp("1L17SP")
    for child in ("10L171", "10L172", "117JPO", "17MJPO"):
        if tv_fp(child) != parent:
            fails.append(f"{child}: QuikTvs grid != 1L17SP")

    # Issue A A8e — no A-prefix PLANVALOPT=Y
    a_y = [
        p for p, r in qp.items()
        if p.startswith("A") and (r.get("PLANVALOPT") or "").strip().upper() == "Y"
    ]
    if a_y:
        fails.append(f"A8e: annuity PLANVALOPT=Y plans={a_y}")

    if fails:
        print("FAIL - Issue #96")
        for f in fails:
            print(" ", f)
        return 1
    print("PASS - Issue #96 CSO PVO + SAL/L17 QuikPl* / QuikTvs")
    for plan in FOCUS:
        print(
            f"  {plan}: PVO=Y GDVARYTV=Y QuikTvs={tv_counts.get(plan, 0)} "
            f"PlTv={len(_plan_rows(pltv, plan))} PlCv={len(_plan_rows(plcv, plan))}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
