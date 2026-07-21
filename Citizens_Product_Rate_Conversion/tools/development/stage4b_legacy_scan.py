"""Scan active technical assets for legacy references (Stage 4B)."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "manifests" / "technical_asset_manifest.csv"
OUT = ROOT / "reports" / "development" / "Stage4B_Legacy_Reference_Comparison.csv"

PATTERNS = [
    "C:\\Users",
    "Warrenhughes1974",
    "CFIC_Rates",
    "QLA_Migration",
    "CSO",
    "sys.path.insert",
    "sys.path.append",
    "qla_core",
]


def count_refs(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    return sum(text.count(p) for p in PATTERNS)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    with MANIFEST.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rel = (row.get("CURRENT_RELATIVE_PATH") or row.get("relative_path") or row.get("path") or "").replace("\\", "/")
            status = row.get("CURRENT_LIFECYCLE_STATUS", row.get("status", "UNKNOWN"))
            if not rel:
                continue
            path = ROOT / rel
            if not path.is_file():
                continue
            post = count_refs(path)
            pre = post  # post-change scan; historical docs retain audit references
            active = "ACTIVE" if status.lower() == "active" else "HISTORICAL"
            resolved = "Y" if active == "ACTIVE" and post == 0 else "PARTIAL" if active == "ACTIVE" else "N/A"
            remaining = ""
            if active == "ACTIVE" and post > 0:
                text = path.read_text(encoding="utf-8", errors="replace")
                hits = [p for p in PATTERNS if p in text]
                remaining = ";".join(hits)
                resolved = "PARTIAL" if "qla_core" in remaining and "sys.path" not in remaining else "NO"
            rows.append({
                "file": rel,
                "reference": "combined_patterns",
                "prechange_count": "",
                "postchange_count": post,
                "active_or_historical": active,
                "resolved": resolved,
                "remaining_reason": remaining or "none",
                "future_issue": "" if resolved in ("Y", "N/A") else "CIT-ENGINE-002",
            })

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            w.writeheader()
            w.writerows(rows)
    print(f"Wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
