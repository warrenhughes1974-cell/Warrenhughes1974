#!/usr/bin/env python3
"""Issue #135 — restore verified TV claims package to Output and archive targets."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "QLA_Migration" / "Output"
TV = OUT / "Test_Validation"
ARCH = ROOT / "QLA_Migration" / "Archive"
STAGING = ROOT / "QLA_Migration" / "Staging" / "claims_uat_dbf"
EVID = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
QDEST = Path(r"Q:\CSO\CSO_Test_6_30_2026")
EXPECTED_CLMP_SHA = "5dd6d9da57134da17a81382c58e8cdb2fd3f161a8c99475d780104b778bff0fc"


def rowcount(p: Path) -> int:
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return sum(1 for _ in csv.DictReader(f))


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print("TS", ts)

    src_clms = TV / "quikclms.csv"
    src_clmp = TV / "quikclmp.csv"
    dst_clms = OUT / "quikclms.csv"
    dst_clmp = OUT / "quikclmp.csv"

    tv_clms_n = rowcount(src_clms)
    tv_clmp_n = rowcount(src_clmp)
    tv_clmp_sha = sha256(src_clmp)
    print("TV", tv_clms_n, tv_clmp_n, "clmp_sha", tv_clmp_sha)

    if tv_clms_n != 6044 or tv_clmp_n != 5495 or tv_clmp_sha != EXPECTED_CLMP_SHA:
        print("FAIL: TV package not verified final 6044/5495")
        return 2

    before = {
        "out_clms": rowcount(dst_clms),
        "out_clmp": rowcount(dst_clmp),
        "out_clms_sha": sha256(dst_clms),
        "out_clmp_sha": sha256(dst_clmp),
        "tv_clms": tv_clms_n,
        "tv_clmp": tv_clmp_n,
        "tv_clms_sha": sha256(src_clms),
        "tv_clmp_sha": tv_clmp_sha,
    }
    print("BEFORE", before)

    ARCH.mkdir(parents=True, exist_ok=True)
    bak_clms = ARCH / f"quikclms_pre_issue135_deploy_{ts}.csv"
    bak_clmp = ARCH / f"quikclmp_pre_issue135_deploy_{ts}.csv"
    shutil.copy2(dst_clms, bak_clms)
    shutil.copy2(dst_clmp, bak_clmp)
    print("archived Output CSVs", bak_clms.name, bak_clmp.name)

    tmp_clms = dst_clms.with_suffix(".csv.promote_tmp")
    tmp_clmp = dst_clmp.with_suffix(".csv.promote_tmp")
    shutil.copy2(src_clms, tmp_clms)
    shutil.copy2(src_clmp, tmp_clmp)
    tmp_clms.replace(dst_clms)
    tmp_clmp.replace(dst_clmp)

    shutil.copy2(dst_clms, src_clms)
    shutil.copy2(dst_clmp, src_clmp)

    after = {
        "out_clms": rowcount(dst_clms),
        "out_clmp": rowcount(dst_clmp),
        "tv_clms": rowcount(src_clms),
        "tv_clmp": rowcount(src_clmp),
        "out_clms_sha": sha256(dst_clms),
        "out_clmp_sha": sha256(dst_clmp),
        "out_eq_tv_clms": sha256(dst_clms) == sha256(src_clms),
        "out_eq_tv_clmp": sha256(dst_clmp) == sha256(src_clmp),
        "out_clmp_matches_expected_post_sha": sha256(dst_clmp) == EXPECTED_CLMP_SHA,
    }
    print("AFTER", after)
    if not (
        after["out_clms"] == 6044
        and after["out_clmp"] == 5495
        and after["out_eq_tv_clms"]
        and after["out_eq_tv_clmp"]
        and after["out_clmp_matches_expected_post_sha"]
    ):
        print("FAIL: promote verification failed")
        return 3

    stage_arch = ARCH / f"claims_uat_dbf_pre_issue135_deploy_{ts}"
    stage_arch.mkdir(parents=True, exist_ok=True)
    staging_archived = []
    if STAGING.is_dir():
        for p in STAGING.iterdir():
            if p.is_file():
                shutil.copy2(p, stage_arch / p.name)
                staging_archived.append(p.name)
    print("archived staging files", len(staging_archived), "->", stage_arch)

    q_arch = None
    q_archived = []
    if QDEST.is_dir():
        q_arch = ARCH / f"Q_CSO_Test_6_30_2026_pre_issue135_deploy_{ts}"
        q_arch.mkdir(parents=True, exist_ok=True)
        for name in ("QUIKCLMS.DBF", "QUIKCLMS.DBT", "QUIKCLMP.DBF"):
            src = QDEST / name
            if src.is_file():
                shutil.copy2(src, q_arch / name)
                q_archived.append(name)
    print("archived Q files", q_archived, "->", q_arch)

    summary = {
        "generated_at": ts,
        "action": "restore_verified_tv_package_to_output_for_deploy",
        "engine": "v58.60",
        "before": before,
        "after": after,
        "archive_output_clms": str(bak_clms),
        "archive_output_clmp": str(bak_clmp),
        "archive_staging_dir": str(stage_arch),
        "staging_archived_files": staging_archived,
        "archive_q_dir": str(q_arch) if q_arch else None,
        "q_archived_files": q_archived,
        "source": "Output/Test_Validation verified 6044/5495 (post zero-payee SHA)",
        "promotion_ok": True,
    }
    out_json = EVID / "issue135_deploy_restore_summary.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("PROMOTION_OK wrote", out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
