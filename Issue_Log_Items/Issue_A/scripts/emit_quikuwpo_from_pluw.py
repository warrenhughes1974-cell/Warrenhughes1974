"""Issue A A10 — emit QuikUwpo.csv from existing QuikPlUw (+ optional key UWCLASS)."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from qla_core.rate_dbf_writer import write_quikuwpo_csv  # noqa: E402
from qla_core.rate_member_setup import build_quikuwpo_rows  # noqa: E402

RATES = ROOT / "QLA_Migration" / "Output" / "rates"
OUT = RATES / "QuikUwpo.csv"
KEY_TABLES = ("QuikPlGp", "QuikPlDb", "QuikPlCv", "QuikPlTv", "QuikPlDv")


def main() -> int:
    pluw = RATES / "QuikPlUw.csv"
    if not pluw.is_file():
        print(f"Missing {pluw}")
        return 1

    with pluw.open(newline="", encoding="utf-8-sig") as f:
        member_rows = {"QuikPlUw": list(csv.DictReader(f))}

    key_rows = {}
    for name in KEY_TABLES:
        path = RATES / f"{name}.csv"
        if path.is_file():
            with path.open(newline="", encoding="utf-8-sig") as f:
                key_rows[name] = list(csv.DictReader(f))

    rows = build_quikuwpo_rows(member_rows, key_rows=key_rows)
    n = write_quikuwpo_csv(str(OUT), rows, overwrite=True)
    print(f"Wrote {OUT} ({n} rows)")
    for r in rows:
        print(f"  {r['UWCODE']}  {r['UWDESCR']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
