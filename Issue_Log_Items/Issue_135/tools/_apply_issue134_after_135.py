#!/usr/bin/env python3
"""One-shot: apply #134 PNOTE-B overlay to current Output after #135 expansion.

Also relocates three non-table Output artifacts to Logs/Reports.
Does not re-run #135 expansion. Money fields are asserted unchanged.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from qla_core.issue134_claim_memo_overlay import (  # noqa: E402
    apply_issue134_claim_memos,
    write_issue134_orphan_audit,
)
from qla_core.lifepro_source_resolver import resolve_quikmemo_sources  # noqa: E402

OUT = ROOT / "QLA_Migration" / "Output"
TV = OUT / "Test_Validation"
ARCH = ROOT / "QLA_Migration" / "Archive"
LOGS = ROOT / "QLA_Migration" / "Logs"
REPORTS = ROOT / "QLA_Migration" / "Reports"
EVID = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
MARKER = "CSO_CONTROLLED_NO_PACTG_HISTORY"


def _move_keep(src: Path, dest_dir: Path, ts: str) -> tuple[str, str]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if dest.exists():
        shutil.copy2(dest, dest_dir / f"{src.stem}_pre_{ts}{src.suffix}")
    shutil.move(str(src), str(dest))
    return str(src), str(dest)


def main() -> int:
    clms_path = OUT / "quikclms.csv"
    clmp_path = OUT / "quikclmp.csv"
    if not clms_path.is_file() or not clmp_path.is_file():
        print("FAIL: missing quikclms/quikclmp")
        return 2

    clms = pd.read_csv(clms_path, dtype=str).fillna("")
    clmp = pd.read_csv(clmp_path, dtype=str).fillna("")
    pnote, _, _, _ = resolve_quikmemo_sources(str(ROOT / "QLA_Migration" / "Source"))
    if not pnote:
        print("FAIL: missing PNOTE")
        return 2

    money_cols = [c for c in ("MPAID", "MFACE", "NETDB", "MINTAMT") if c in clms.columns]
    money_before = {c: clms[c].astype(str).tolist() for c in money_cols}
    marker_before = int(clms["MEMOTEXT"].astype(str).str.contains(MARKER, regex=False).sum())

    clms_after, orphan_df, stats = apply_issue134_claim_memos(clms, pnote)
    marker_after = int(clms_after["MEMOTEXT"].astype(str).str.contains(MARKER, regex=False).sum())
    money_changed = {
        c: sum(a != b for a, b in zip(money_before[c], clms_after[c].astype(str).tolist()))
        for c in money_cols
    }

    if marker_before != 308 or marker_after != 308:
        print(f"FAIL: marker count before={marker_before} after={marker_after} expected 308")
        return 1
    if any(money_changed.values()):
        print(f"FAIL: money fields changed {money_changed}")
        return 1
    if int(stats.get("rows_updated", 0) or 0) != 142:
        print(f"FAIL: expected 142 rows_updated, got {stats}")
        return 1

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ARCH.mkdir(parents=True, exist_ok=True)
    shutil.copy2(clms_path, ARCH / f"quikclms_pre_issue135_134overlay_{ts}.csv")
    tmp = clms_path.with_suffix(".csv.tmp")
    clms_after.to_csv(tmp, index=False, encoding="utf-8")
    tmp.replace(clms_path)

    TV.mkdir(parents=True, exist_ok=True)
    shutil.copy2(clms_path, TV / "quikclms.csv")
    shutil.copy2(clmp_path, TV / "quikclmp.csv")

    audit = ""
    if not orphan_df.empty:
        audit = write_issue134_orphan_audit(orphan_df, str(REPORTS))

    moves = []
    for name, dest_dir in (
        ("Migration_Audit_Log.txt", LOGS),
        ("cso_mortality_crosswalk_qa.csv", REPORTS),
        ("variation_code_audit.csv", REPORTS),
    ):
        src = OUT / name
        if src.is_file():
            moves.append(_move_keep(src, dest_dir, ts))

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine": "v58.57",
        "overlay": "issue134_after_issue135",
        "stats": stats,
        "marker_before": marker_before,
        "marker_after": marker_after,
        "money_changed": money_changed,
        "clms_rows": int(len(clms_after)),
        "clmp_rows": int(len(clmp)),
        "orphan_audit": audit,
        "moved_artifacts": [{"from": a, "to": b} for a, b in moves],
        "test_validation_published": ["quikclms.csv", "quikclmp.csv"],
    }
    EVID.mkdir(parents=True, exist_ok=True)
    out_json = EVID / "issue135_134_overlay_apply_summary.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("Issue #134-after-#135 overlay apply")
    print(f"  rows_updated={stats.get('rows_updated')} policies={stats.get('policies_updated')}")
    print(f"  marker={marker_after} money_changed={money_changed}")
    print(f"  moved={moves}")
    print(f"  summary={out_json}")
    leftover = sorted(
        p.name for p in OUT.iterdir() if p.is_file() and not p.name.lower().startswith("quik")
    )
    print(f"  Output non-quik leftovers={leftover}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
