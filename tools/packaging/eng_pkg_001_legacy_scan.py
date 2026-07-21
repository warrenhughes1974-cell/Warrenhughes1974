"""Scan qla_core for legacy path references."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QLA = ROOT / "qla_core"
OUT = ROOT / "reports" / "packaging" / "ENG-PKG-001_Legacy_Reference_Report.csv"

PATTERNS = [
    "sys.path.insert",
    "sys.path.append",
    "CFIC_Rates",
    "Citizens",
    "QLA_Migration",
    "C:\\Users",
    "plan_analysis",
    "CSO",
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(QLA.rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT).as_posix()
        for pat in PATTERNS:
            count = text.count(pat)
            if count:
                rows.append({
                    "file": rel,
                    "reference": pat,
                    "count": count,
                    "removable": "N" if pat in ("QLA_Migration", "plan_analysis", "CSO") else "Y",
                    "notes": "Path resolver default — runtime only, not packaged client data" if pat in ("QLA_Migration", "plan_analysis") else "",
                })
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file", "reference", "count", "removable", "notes"])
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
