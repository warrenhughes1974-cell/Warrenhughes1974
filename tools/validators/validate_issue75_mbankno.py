"""Issue #75 / #45 always-on smoke: PAC Bank Acct (quikmstr.MBANKNO).

FAIL blocks release / full-batch post-check. Do not ship blank PAC Bank Acct.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.issue75_mbankno_smoke import (  # noqa: E402
    LOOKUP_NAME,
    evaluate_quikmstr,
    find_aba_lookup,
)

OUT = ROOT / "QLA_Migration" / "Output" / "quikmstr.csv"
SOURCE = ROOT / "QLA_Migration" / "Source"


def main() -> int:
    errors: list[str] = []
    lookup = find_aba_lookup(SOURCE)
    if lookup is None:
        errors.append(
            f"Missing {LOOKUP_NAME} under {SOURCE} "
            f"(root or LifePRO_Extracts_*). Without it every PAC Bank Acct blanks."
        )
    else:
        print(f"ABA lookup: {lookup}")

    ok, out_errs, stats = evaluate_quikmstr(OUT)
    errors.extend(out_errs)
    print("Issue #75 Bank Acct smoke")
    print(
        f"rows={stats['rows']} pac={stats['pac']} filled={stats['pac_filled']} "
        f"blank={stats['pac_blank']} invalid={stats['pac_invalid']}"
    )
    for pol, mb in sorted((stats.get("traces") or {}).items()):
        print(f"  {pol}={mb}")
    if errors:
        print("FAIL")
        for e in errors:
            print(f"  {e}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
