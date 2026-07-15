"""Read-only risk simulation for Issue #73 — MISSCNTRY USA → 0000.

Does not modify production mapping or Output.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QUIKMSTR = ROOT / "QLA_Migration" / "Output" / "quikmstr.csv"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence"


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with QUIKMSTR.open(newline="", encoding="utf-8", errors="replace") as f:
        rows = list(csv.DictReader(f))

    counts = Counter((r.get("MISSCNTRY") or "").strip() for r in rows)
    would_change = sum(1 for r in rows if (r.get("MISSCNTRY") or "").strip() != "0000")

    summary = EVIDENCE / "issue73_risk_impact_summary.csv"
    with summary.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "count"])
        w.writerow(["quikmstr_rows", len(rows)])
        for k, v in sorted(counts.items()):
            w.writerow([f"MISSCNTRY_{k or 'BLANK'}", v])
        w.writerow(["would_change_to_0000", would_change])
        w.writerow(["already_0000", len(rows) - would_change])

    sample = EVIDENCE / "issue73_risk_misscntry_simulation.csv"
    with sample.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "MPOLICY",
            "MISSCNTRY_before",
            "MISSCNTRY_after",
            "MISSUEST",
            "MRESSTATE",
            "would_change",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows[:20]:
            before = (r.get("MISSCNTRY") or "").strip()
            w.writerow(
                {
                    "MPOLICY": r.get("MPOLICY"),
                    "MISSCNTRY_before": before,
                    "MISSCNTRY_after": "0000",
                    "MISSUEST": r.get("MISSUEST"),
                    "MRESSTATE": r.get("MRESSTATE"),
                    "would_change": "Y" if before != "0000" else "N",
                }
            )

    print(f"rows={len(rows)} would_change={would_change} counts={dict(counts)}")
    print(f"wrote {summary}")
    print(f"wrote {sample}")


if __name__ == "__main__":
    main()
