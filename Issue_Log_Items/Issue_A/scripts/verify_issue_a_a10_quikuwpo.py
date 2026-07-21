"""Issue A A10 — QuikUwpo coverage vs QuikPlUw."""
from __future__ import annotations

import csv
from pathlib import Path

RATES = Path(__file__).resolve().parents[3] / "QLA_Migration" / "Output" / "rates"


def main() -> int:
    pluw = RATES / "QuikPlUw.csv"
    uwpo = RATES / "QuikUwpo.csv"
    if not pluw.is_file():
        print(f"Missing {pluw}")
        return 1
    if not uwpo.is_file():
        print(f"Missing {uwpo} FAIL")
        return 1

    with pluw.open(newline="", encoding="utf-8-sig") as f:
        need = {(r.get("UWCODE") or "").strip() for r in csv.DictReader(f)}
        need.discard("")
    need.add("00")

    with uwpo.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    codes = [(r.get("UWCODE") or "").strip() for r in rows]
    uniq = set(codes)

    print("=== Issue A A10 QuikUwpo ===")
    print(f"QuikUwpo rows: {len(codes)}")
    for r in rows:
        print(f"  {r.get('UWCODE')}  {r.get('UWDESCR')}")
    dupes = len(codes) - len(uniq)
    missing = sorted(need - uniq)
    extra_ok = True  # extras allowed if from keys
    print(f"duplicate UWCODE: {dupes} {'PASS' if dupes == 0 else 'FAIL'}")
    print(f"missing vs QuikPlUw: {missing or 'none'} {'PASS' if not missing else 'FAIL'}")
    print(f"00 present: {'PASS' if '00' in uniq else 'FAIL'}")
    return 0 if dupes == 0 and not missing and "00" in uniq else 1


if __name__ == "__main__":
    raise SystemExit(main())
