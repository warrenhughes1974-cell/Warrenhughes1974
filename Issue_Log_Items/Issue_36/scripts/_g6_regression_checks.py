#!/usr/bin/env python3
"""Issue #36 G6 regression evidence (read-only)."""
from __future__ import annotations

import csv
import os
import re
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(REPO, "QLA_Migration", "Output")
sys.path.insert(0, REPO)

from qla_core.normalize_utils import format_qladmin_mpolicy

QUIK_TABLES = [
    "quikmstr",
    "quikridr",
    "quikplan",
    "quikclid",
    "quikclnt",
    "quikbenf",
    "quikprmh",
    "quikmemo",
    "quikdvdp",
    "quikdvpr",
    "quikagts",
    "quikactg",
]

# Expected quikmstr schema from app.py TABLE_SCHEMAS
EXPECTED_MSTR = [
    "MPOLICY", "MSTATUS", "MSTATDATE", "MISSDT", "MPAIDTO", "MBILLTO", "MNFOPT", "MDIVOPT",
    "MBILLFRM", "MBILLDAY", "MACCTNO", "MBANKNO", "MPREBILL", "MMODE", "MMODEPREM",
    "MSEMI", "MQTRL", "MMTHD", "MMTHB", "MINQUIRY", "MISSUEST", "MBFCY", "MGROUP",
    "MPRIMID", "MOWNRID", "MPAYRID", "MASGNID", "MBENPID", "MBENCID", "MAPPDATE",
    "MSUBMDATE", "MRELDATE", "MRELOTHER", "MORIGBILL", "MORIGMODE", "MISSCNTRY",
    "MOWNCID", "MACHCNT", "MACHNXTDT", "MRESSTATE", "MBLLDOM", "MSPCODE", "MISSCLASS",
    "MMSMBI", "MORGBLLDOM",
]

FACTOR_COLS = ("MSEMI", "MQTRL", "MMTHD", "MMTHB")


def _read(path: str) -> list[dict]:
    with open(path, newline="", encoding="latin1", errors="replace") as f:
        return list(csv.DictReader(f))


def main() -> int:
    failures: list[str] = []
    print("=== Row counts ===")
    counts = {}
    for t in QUIK_TABLES:
        path = os.path.join(OUT, f"{t}.csv")
        if not os.path.isfile(path):
            print(f"{t}: MISSING")
            continue
        rows = _read(path)
        counts[t] = len(rows)
        print(f"{t}: {len(rows)}")

    # Known stable baselines from recent issues (v57.46+ fleet)
    expected_counts = {
        "quikmstr": 5083,
        "quikplan": 141,
        "quikmemo": 5083,
    }
    for t, exp in expected_counts.items():
        if counts.get(t) != exp:
            failures.append(f"{t} count {counts.get(t)} != expected {exp}")

    mstr_path = os.path.join(OUT, "quikmstr.csv")
    mstr = _read(mstr_path)
    cols = list(mstr[0].keys()) if mstr else []
    print("\n=== quikmstr schema order ===")
    if cols != EXPECTED_MSTR:
        failures.append("quikmstr column order/schema mismatch")
        # show first diff
        for i, (a, b) in enumerate(zip(cols, EXPECTED_MSTR)):
            if a != b:
                print(f"  first diff at {i}: got {a!r} expected {b!r}")
                break
        if len(cols) != len(EXPECTED_MSTR):
            print(f"  len got {len(cols)} expected {len(EXPECTED_MSTR)}")
    else:
        print("PASS — matches TABLE_SCHEMAS quikmstr")

    print("\n=== Factor vs non-factor population ===")
    for f in FACTOR_COLS:
        blank = sum(1 for r in mstr if not (r.get(f) or "").strip())
        print(f"  {f} blank={blank}")
        if blank:
            failures.append(f"{f} unexpectedly blank {blank}")

    # Non-factor critical fields still populated
    for f in ("MPOLICY", "MSTATUS", "MMODE", "MMODEPREM", "MBILLFRM"):
        blank = sum(1 for r in mstr if not (r.get(f) or "").strip())
        print(f"  {f} blank={blank}")
        if f in ("MPOLICY", "MSTATUS") and blank:
            failures.append(f"{f} blank {blank}")

    print("\n=== #25 MPOLICY width ===")
    short = sum(1 for r in mstr if len(format_qladmin_mpolicy((r.get("MPOLICY") or "").strip()) if False else (r.get("MPOLICY") or "")) != 10)
    # Direct length on emitted value
    short = sum(1 for r in mstr if len(r.get("MPOLICY") or "") != 10)
    print(f"  short MPOLICY: {short}")
    if short:
        failures.append(f"MPOLICY short {short}")

    print("\n=== #26 MPREM / MMODEPREM ===")
    ridr_path = os.path.join(OUT, "quikridr.csv")
    if os.path.isfile(ridr_path):
        ridr = _read(ridr_path)
        mprem_blank = sum(1 for r in ridr if not (r.get("MPREM") or "").strip())
        mrid_blank = sum(1 for r in ridr if not (r.get("MRIDRID") or "").strip())
        print(f"  MPREM blank={mprem_blank}/{len(ridr)}")
        print(f"  MRIDRID blank={mrid_blank}/{len(ridr)}")
        if mprem_blank:
            failures.append(f"MPREM blank {mprem_blank}")
    mmod_blank = sum(1 for r in mstr if not (r.get("MMODEPREM") or "").strip())
    print(f"  MMODEPREM blank={mmod_blank}/{len(mstr)}")
    if mmod_blank:
        failures.append(f"MMODEPREM blank {mmod_blank}")

    print("\n=== #21J quikplan factors sample ===")
    qp_path = os.path.join(OUT, "quikplan.csv")
    if os.path.isfile(qp_path):
        qp = { (r.get("PLAN") or "").strip(): r for r in _read(qp_path) }
        for plan, semi in (("1659C2", "52.5000"), ("170858", "52.0000"), ("221END", "51.0140")):
            row = qp.get(plan)
            got = (row.get("SEMI") or "").strip() if row else "MISSING"
            ok = got == semi
            print(f"  {plan} SEMI={got} expected={semi} {'OK' if ok else 'FAIL'}")
            if not ok:
                failures.append(f"quikplan {plan} SEMI regression")

    print("\n=== APP_VERSION ===")
    for rel in ("app.py", os.path.join("QLA_Migration", "app.py")):
        text = open(os.path.join(REPO, rel), encoding="utf-8", errors="replace").read()
        m = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', text)
        ver = m.group(1) if m else "?"
        print(f"  {rel}: {ver}")
        if ver != "v57.62":
            failures.append(f"{rel} version {ver}")

    print("\n=== Code surface (expected files only) ===")
    # informational — list key symbols present
    from qla_core import modal_premium_factors as mpf
    assert hasattr(mpf, "apply_plan_modal_factors_to_quikmstr")
    assert hasattr(mpf, "apply_pac_gl85_modal_overrides")
    print("  modal_premium_factors: plan copy + PAC present")

    if failures:
        print("\nREGRESSION FAIL")
        for f in failures:
            print(" ", f)
        return 1
    print("\nREGRESSION PASS — Issue #36 G6 evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
