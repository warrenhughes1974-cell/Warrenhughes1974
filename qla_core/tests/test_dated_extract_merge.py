"""Smoke tests: dated extract discover + filename newest wins."""
from __future__ import annotations

import csv
import os
from pathlib import Path

from qla_core.dated_extract_merge import (
    discover_dated_extracts,
    filename_extract_date,
    merge_dated_extracts,
    ensure_merged_family,
)


def test_filename_extract_date():
    assert filename_extract_date("PAAGERAT_AttainedAge_Rates_Extract_20260714.csv") == "20260714"
    assert filename_extract_date("PDAGE_AgeDuration_Rates_Extract_20260630.csv") == "20260630"
    assert filename_extract_date("no_date.csv") is None


def test_discover_sorts_by_filename_date(tmp_path: Path):
    for d in ("20260630", "20260714", "20260713"):
        p = tmp_path / f"PAAGERAT_AttainedAge_Rates_Extract_{d}.csv"
        p.write_text("COVERAGE_ID,TYPE_CODE\nA,PR\n", encoding="latin1")
    found = discover_dated_extracts(str(tmp_path), "PAAGERAT")
    assert [d for d, _ in found] == ["20260630", "20260713", "20260714"]


def test_newest_filename_wins_and_keeps_older_unique(tmp_path: Path):
    older = tmp_path / "PAAGERAT_AttainedAge_Rates_Extract_20260630.csv"
    newer = tmp_path / "PAAGERAT_AttainedAge_Rates_Extract_20260714.csv"
    # older: key A value OLD; key B value ONLY_OLD
    older.write_text(
        "COVERAGE_ID,TYPE_CODE,SEX,BAND,UWCLS,RECORD_SEQ,SEQ,VALUE_INFO\n"
        "COV1,PR,M,1,1,1,10,OLD\n"
        "COV2,PR,M,1,1,1,10,ONLY_OLD\n",
        encoding="latin1",
    )
    # newer: key A value NEW (wins); no COV2
    # Also touch disk mtime so older file is "newer" on disk — filename still wins
    newer.write_text(
        "COVERAGE_ID,TYPE_CODE,SEX,BAND,UWCLS,RECORD_SEQ,SEQ,VALUE_INFO\n"
        "COV1,PR,M,1,1,1,10,NEW\n",
        encoding="latin1",
    )
    os.utime(older, None)  # bump older mtime after newer written

    staging = tmp_path / "merged.csv"
    files = discover_dated_extracts(str(tmp_path), "PAAGERAT")
    summary = merge_dated_extracts(
        files,
        ("COVERAGE_ID", "TYPE_CODE", "SEX", "BAND", "UWCLS", "RECORD_SEQ", "SEQ"),
        str(staging),
    )
    assert summary["newest_date"] == "20260714"
    assert summary["rows"] == 2

    by_cov = {}
    with staging.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            by_cov[row["COVERAGE_ID"]] = row["VALUE_INFO"]
    assert by_cov["COV1"] == "NEW"
    assert by_cov["COV2"] == "ONLY_OLD"


def test_ensure_merged_family_single_file(tmp_path: Path):
    p = tmp_path / "PAAGE_AttainedAge_Rates_Extract_20260714.csv"
    p.write_text(
        "COVERAGE_ID,TYPE_CODE,SEX,BAND,UWCLS,RECORD_SEQ\n"
        "C1,PR,M,1,1,1\n",
        encoding="latin1",
    )
    staging = tmp_path / "stg"
    staging.mkdir()
    path, summary = ensure_merged_family(str(tmp_path), str(staging), "PAAGE")
    assert path == str(p.resolve()) or os.path.normpath(path) == os.path.normpath(str(p))
    assert summary.get("single_file") is True
