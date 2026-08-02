#!/usr/bin/env python3
"""Issue #135 — promote Test_Validation quikclms/quikclmp to Output root (rollback-safe)."""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "QLA_Migration" / "Output"
TV = OUT / "Test_Validation"
ARCH = ROOT / "QLA_Migration" / "Archive"
REPORTS = ROOT / "QLA_Migration" / "Reports"
EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def rowcount(p: Path) -> int:
    import csv

    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return sum(1 for _ in csv.DictReader(f))


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ARCH.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    src_clms = TV / "quikclms.csv"
    src_clmp = TV / "quikclmp.csv"
    dst_clms = OUT / "quikclms.csv"
    dst_clmp = OUT / "quikclmp.csv"
    if not src_clms.is_file() or not src_clmp.is_file():
        print("FAIL: missing Test_Validation sources")
        return 2

    before = {
        "out_clms": rowcount(dst_clms),
        "out_clmp": rowcount(dst_clmp),
        "tv_clms": rowcount(src_clms),
        "tv_clmp": rowcount(src_clmp),
        "out_clms_md5": md5(dst_clms),
        "out_clmp_md5": md5(dst_clmp),
        "tv_clms_md5": md5(src_clms),
        "tv_clmp_md5": md5(src_clmp),
    }
    print("BEFORE", before)

    # Expect intended package
    if before["tv_clms"] != 6044 or before["tv_clmp"] != 5497:
        print("FAIL: TV is not the intended 6044/5497 package")
        return 3

    bak_clms = ARCH / f"quikclms_pre_issue135_reconcile_{ts}.csv"
    bak_clmp = ARCH / f"quikclmp_pre_issue135_reconcile_{ts}.csv"
    shutil.copy2(dst_clms, bak_clms)
    shutil.copy2(dst_clmp, bak_clmp)
    print("archived", bak_clms.name, bak_clmp.name)

    # Atomic-ish promote
    tmp_clms = dst_clms.with_suffix(".csv.promote_tmp")
    tmp_clmp = dst_clmp.with_suffix(".csv.promote_tmp")
    shutil.copy2(src_clms, tmp_clms)
    shutil.copy2(src_clmp, tmp_clmp)
    tmp_clms.replace(dst_clms)
    tmp_clmp.replace(dst_clmp)

    # Keep Test_Validation synchronized (byte-identical)
    shutil.copy2(dst_clms, src_clms)
    shutil.copy2(dst_clmp, src_clmp)

    # Move non-table claims_* artifacts out of Output root
    moved = []
    for name in [
        "claims_cross_table_validation_report.csv",
        "claims_cross_table_validation_summary.txt",
        "claims_emit_enhancement_validation.csv",
        "claims_emit_enhancement_validation_summary.txt",
        "claims_review_hold_manifest.csv",
    ]:
        src = OUT / name
        if src.is_file():
            dest = REPORTS / name
            if dest.exists():
                dest = REPORTS / f"{src.stem}_reconcile_{ts}{src.suffix}"
            shutil.move(str(src), str(dest))
            moved.append({"from": str(src), "to": str(dest)})

    after = {
        "out_clms": rowcount(dst_clms),
        "out_clmp": rowcount(dst_clmp),
        "tv_clms": rowcount(src_clms),
        "tv_clmp": rowcount(src_clmp),
        "out_eq_tv_clms": md5(dst_clms) == md5(src_clms),
        "out_eq_tv_clmp": md5(dst_clmp) == md5(src_clmp),
        "out_matches_pre_tv_md5_clms": md5(dst_clms) == before["tv_clms_md5"],
        "out_matches_pre_tv_md5_clmp": md5(dst_clmp) == before["tv_clmp_md5"],
    }
    print("AFTER", after)

    summary = {
        "generated_at": ts,
        "action": "promote_test_validation_to_output",
        "before": before,
        "after": after,
        "archive_clms": str(bak_clms),
        "archive_clmp": str(bak_clmp),
        "moved_artifacts": moved,
        "promotion_ok": (
            after["out_clms"] == 6044
            and after["out_clmp"] == 5497
            and after["out_eq_tv_clms"]
            and after["out_eq_tv_clmp"]
        ),
    }
    out_json = EVIDENCE / "issue135_reconcile_promote_summary.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("summary", out_json)
    print("PROMOTION_OK" if summary["promotion_ok"] else "PROMOTION_FAIL")
    return 0 if summary["promotion_ok"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
