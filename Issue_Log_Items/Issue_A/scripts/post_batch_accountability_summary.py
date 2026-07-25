"""Summarize accountability report after a full batch (read-only)."""
from __future__ import annotations

import glob
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
matches = sorted(
    glob.glob(str(REPO / "Issue_Log_Items" / "Issue_Log_Data_Accountability_*.json")),
    key=os.path.getmtime,
)
path = matches[-1]
data = json.loads(Path(path).read_text(encoding="utf-8"))
rows = data.get("results") or []

print(f"report: {path}")
print(f"counts: {data.get('counts')}")
print()
print("=== KEY ISSUES ===")
want = [
    "#2", "#75", "#99", "#105", "#108", "#110", "#111", "#114",
    "#21F", "#38", "#54", "#55", "#60", "#72", "#76", "#25",
]
for label in want:
    hits = [r for r in rows if str(r.get("id", "")).startswith(label)]
    if not hits:
        print(f"{label}: (not registered)")
        continue
    for r in hits:
        detail = str(r.get("detail", ""))[:140]
        print(f"{r['id']}: {r['status']} — {detail}")

print()
print("=== ALL GAPS ===")
for r in rows:
    if r.get("status") == "GAP":
        print(f"{r['id']}: {str(r.get('detail', ''))[:180]}")

print()
print("=== IN_DATA ===")
print(", ".join(sorted({r["id"] for r in rows if r.get("status") == "IN_DATA"})))
