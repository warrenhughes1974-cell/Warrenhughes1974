"""One-time remapper: apply Issue #167 anniversary MLASTANN to Output/quikridr.csv.

ETI/RPU phase 1 (quikmstr.MSTATUS 44/45) is left on the Issue #76 paid-to value.
Path of record after this cut is app.py _compute_quikridr_mlastann.
"""

from __future__ import annotations

import argparse
import csv
import shutil
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = ROOT / "QLA_Migration" / "Output"
EVID = Path(__file__).resolve().parents[1] / "evidence"


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _ymd(v: object) -> str:
    digits = "".join(c for c in _n(v) if c.isdigit())
    return digits[:8] if len(digits) >= 8 else ""


def _as_date(ymd: str) -> date | None:
    if len(ymd) != 8:
        return None
    try:
        return date(int(ymd[:4]), int(ymd[4:6]), int(ymd[6:8]))
    except ValueError:
        return None


def _ann_mlastann(issue_ymd: str, val: date) -> str:
    issue = _as_date(issue_ymd)
    if not issue or issue > val:
        return ""
    dur = val.year - issue.year - ((val.month, val.day) < (issue.month, issue.day))
    return str(dur) if dur >= 0 else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--valuation-date", default="20260831")
    args = ap.parse_args()

    val = _as_date("".join(c for c in args.valuation_date if c.isdigit()))
    if not val:
        print("FAIL: bad valuation date")
        return 1

    ridr_path = args.output_dir / "quikridr.csv"
    mstr_path = args.output_dir / "quikmstr.csv"
    EVID.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    shutil.copy2(ridr_path, EVID / f"quikridr_pre_issue167_{stamp}.csv")

    with mstr_path.open(newline="", encoding="utf-8", errors="replace") as f:
        mstr = {_n(r.get("MPOLICY")): _n(r.get("MSTATUS")) for r in csv.DictReader(f)}

    with ridr_path.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        rows = list(reader)

    changed = 0
    skipped_nfo = 0
    for r in rows:
        pol = _n(r.get("MPOLICY"))
        if _n(r.get("MPHASE")) == "1" and mstr.get(pol) in ("44", "45"):
            skipped_nfo += 1
            continue
        new = _ann_mlastann(_ymd(r.get("MEFFDATE")), val)
        if _n(r.get("MLASTANN")) != new:
            r["MLASTANN"] = new
            changed += 1

    tmp = ridr_path.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(ridr_path)
    print(f"remapped {changed} MLASTANN; skipped {skipped_nfo} ETI/RPU phase-1; val={val:%Y%m%d}")
    print(f"wrote {ridr_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
