"""Read-only compare of authorized #124 reseed vs pre-reseed smoke MDB snapshot."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output"
EVID = Path(__file__).resolve().parent / "evidence"
SMOKE = EVID / "issue143_smoke_summary.json"


def fnum(v):
    s = str(v or "").replace(",", "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def main():
    pre = {r["mpolicy"]: r for r in json.loads(SMOKE.read_text(encoding="utf-8"))["issue124_mdb_mismatches"]}
    ridr_unit = {}
    with (OUT / "quikridr.csv").open(newline="", encoding="latin1", errors="replace") as fh:
        for row in csv.DictReader(fh):
            if str(row.get("MPHASE") or "").strip() != "1":
                continue
            ridr_unit[str(row.get("MPOLICY") or "").strip()] = fnum(row.get("MUNIT"))

    iswl = {}
    with (OUT / "QuikIswl.csv").open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        for row in csv.DictReader(fh):
            iswl[str(row.get("MPOLICY") or "").strip()] = fnum(row.get("MDB"))

    twenty_three = []
    for pol, rec in sorted(pre.items()):
        stored = iswl.get(pol)
        unit = ridr_unit.get(pol)
        expected = rec["expected"]
        twenty_three.append(
            {
                "mpolicy": pol,
                "pre_mdb": rec["stored"],
                "post_mdb": stored,
                "expected_mdb": expected,
                "munit": unit,
                "matches_munit_x_1000": stored is not None and abs(stored - expected) <= 0.011,
            }
        )

    unrelated_mismatch = []
    for pol, stored in iswl.items():
        if pol in pre:
            continue
        unit = ridr_unit.get(pol)
        if unit is None or stored is None:
            unrelated_mismatch.append({"mpolicy": pol, "reason": "missing_unit_or_mdb"})
            continue
        if abs(stored - unit * 1000.0) > 0.011:
            unrelated_mismatch.append(
                {"mpolicy": pol, "mdb": stored, "expected": round(unit * 1000.0, 2)}
            )

    gold = next(r for r in twenty_three if r["mpolicy"] == "9010757606C")
    summary = {
        "quikiswl_rows": len(iswl),
        "affected_23_ok": all(r["matches_munit_x_1000"] for r in twenty_three),
        "gold": gold,
        "unrelated_mdb_ne_current_munit": unrelated_mismatch,
        "changed_23": twenty_three,
    }
    outp = EVID / "issue143_reseed_compare.json"
    outp.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in summary if k != "changed_23"}, indent=2))
    print("wrote", outp)
    return 0 if summary["affected_23_ok"] and not unrelated_mismatch else 1


if __name__ == "__main__":
    raise SystemExit(main())
