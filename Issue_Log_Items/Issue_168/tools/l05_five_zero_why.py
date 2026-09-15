"""Why the five L05 zeros are $0 on this morning's Q: QuikValf."""
from __future__ import annotations

import collections
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "docs", "Valuation", "analysis"))
import quikvalf_dbf as QV  # noqa: E402
from dbfread import DBF

VALF = r"Q:\CSO\CSO_Test_6_30_2026\QuikValf.dbf"
NPS = r"Q:\CSO\CSO_Test_6_30_2026\QuikNps.dbf"
WANT = {
    "9011096290C",
    "9011096291C",
    "9011097650C",
    "9011097702C",
    "9011100498C",
}


def main() -> int:
    strips = collections.defaultdict(dict)
    for rec in DBF(NPS, load=True, char_decode_errors="replace"):
        if str(rec.get("PLAN") or "").strip() != "5L0510":
            continue
        try:
            age = int(rec.get("AGE") or 0)
            page = int(str(rec.get("CNTL") or "0").strip() or 0)
        except ValueError:
            continue
        key = (age, str(rec.get("GENDER") or "").strip(), str(rec.get("UWCLASS") or "").strip())
        for i in range(10):
            raw = rec.get(f"NP{i}")
            try:
                strips[key][page * 10 + i] = float(raw or 0)
            except (TypeError, ValueError):
                pass

    valf = QV.load(VALF)
    print(f"{'POLICY':<14}{'AGE':>4}{'DUR':>4}{'SX':>3}{'CLS':>4}{'UNITS':>8}{'MTABNET':>10}{'MRESERVE':>10}  NP span  NP[dur]  NP[dur-1]")
    for row in valf.valued:
        pol = QV.policy_of(row)
        if pol not in WANT and QV.plan_code(row) != "5L0510":
            continue
        if QV.plan_code(row) != "5L0510":
            continue
        age = int(row.get("MAGE") or 0)
        dur = int(row.get("MDUR") or 0)
        sex = QV.text(row, "MSEX")
        cls = QV.text(row, "MCLASS")
        strip = strips.get((age, sex, cls), {})
        nz = sorted(d for d, v in strip.items() if v)
        span = f"{nz[0]}-{nz[-1]}" if nz else "none"
        flag = "  << ZERO" if pol in WANT else "  match"
        print(
            f"{pol:<14}{age:>4}{dur:>4}{sex:>3}{cls:>4}{QV.money(row,'MUNIT'):>8.2f}"
            f"{QV.money(row,'MTABNET'):>10.2f}{QV.money(row,'MRESERVE'):>10.2f}  "
            f"{span:<8} {strip.get(dur)}  {strip.get(dur-1)}{flag}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
