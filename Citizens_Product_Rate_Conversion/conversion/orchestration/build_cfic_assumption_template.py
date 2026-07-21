"""Build OBQ-2 assumption template rows from published rate keys."""
from __future__ import annotations

import csv
from pathlib import Path

from citizens_paths import ASSUMPTIONS_CSV, OUTPUT_RATES

KEY_CV = OUTPUT_RATES / "QuikPlCv.csv"
KEY_TV = OUTPUT_RATES / "QuikPlTv.csv"
OUT = ASSUMPTIONS_CSV

HEADER = [
    "PLAN", "KEY_TABLE", "MORT", "ETIMORT", "NFOINT", "INTMETHCV",
    "RSVINT", "RSVMETH", "INTMETHTV", "STOREMEANS", "CALCMIDS", "NOTES",
]


def read_plans(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return sorted({(r.get("PLAN") or "").strip() for r in csv.DictReader(f) if r.get("PLAN")})


def main() -> None:
    cv_plans = read_plans(KEY_CV)
    tv_plans = read_plans(KEY_TV)
    rows = []
    for plan in cv_plans:
        rows.append({
            "PLAN": plan, "KEY_TABLE": "QuikPlCv",
            "MORT": "", "ETIMORT": "", "NFOINT": "", "INTMETHCV": "",
            "RSVINT": "", "RSVMETH": "", "INTMETHTV": "", "STOREMEANS": "", "CALCMIDS": "",
            "NOTES": "OBQ-2 — fill before QLAdmin load",
        })
    for plan in tv_plans:
        rows.append({
            "PLAN": plan, "KEY_TABLE": "QuikPlTv",
            "MORT": "", "ETIMORT": "", "NFOINT": "", "INTMETHCV": "",
            "RSVINT": "", "RSVMETH": "", "INTMETHTV": "", "STOREMEANS": "", "CALCMIDS": "",
            "NOTES": "OBQ-2 — shared QuikTvs/QuikNps key",
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} assumption template rows -> {OUT}")


if __name__ == "__main__":
    main()
