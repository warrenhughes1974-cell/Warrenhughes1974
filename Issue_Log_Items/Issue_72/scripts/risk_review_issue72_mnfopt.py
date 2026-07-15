"""Read-only Issue #72 risk simulation: force MNFOPT from MSTATUS 44/45."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "QLA_Migration" / "Output" / "quikmstr.csv"
EV = Path(__file__).resolve().parents[1] / "evidence"


def n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def main() -> None:
    rows = list(csv.DictReader(OUT.open(newline="", encoding="utf-8", errors="replace")))
    deltas: list[tuple[str, str, str, str]] = []
    for r in rows:
        st, nfo, pol = n(r.get("MSTATUS")), n(r.get("MNFOPT")), n(r.get("MPOLICY"))
        new = nfo
        if st == "44":
            new = "2"
        elif st == "45":
            new = "3"
        if new != nfo:
            deltas.append((pol, st, nfo, new))

    EV.mkdir(parents=True, exist_ok=True)
    path = EV / "issue72_risk_mnfopt_deltas.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["MPOLICY", "MSTATUS", "MNFOPT_BEFORE", "MNFOPT_AFTER"])
        w.writerows(deltas)

    print(f"rows={len(rows)} deltas={len(deltas)}")
    print("transitions", Counter((a, b, c) for _, a, b, c in deltas))
    print("wrote", path)


if __name__ == "__main__":
    main()
