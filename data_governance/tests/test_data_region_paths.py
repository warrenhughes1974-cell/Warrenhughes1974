"""Tests for path-based data-region framework behavior."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from data_governance.data_access.region_path import (
    DataRegionPathError,
    validate_data_region_path,
)
from data_governance.data_access.table_resolver import TableResolver
from data_governance.execution.runner import run_data_governance


def test_valid_data_region_path_accepted(tmp_path):
    resolved = validate_data_region_path(str(tmp_path))
    assert os.path.isdir(resolved)
    assert Path(resolved) == tmp_path.resolve()


def test_nonexistent_path_clear_error():
    with pytest.raises(DataRegionPathError, match="does not exist"):
        validate_data_region_path(r"Z:\this\path\does\not\exist_dg_test")


def test_path_without_read_permission_clear_error(tmp_path, monkeypatch):
    def _no_access(path, mode):
        return False

    monkeypatch.setattr(os, "access", _no_access)
    with pytest.raises(DataRegionPathError, match="No read permission"):
        validate_data_region_path(str(tmp_path))


def test_table_filenames_resolved_case_insensitive(tmp_path):
    # Mixed-case filename on disk
    (tmp_path / "QuikComp.DBF").write_bytes(b"")  # placeholder; resolver only checks name
    (tmp_path / "quikagts.dbf").write_bytes(b"")
    (tmp_path / "QUIKMSTR.dbf").write_bytes(b"")
    resolver = TableResolver(str(tmp_path))
    assert resolver.resolve("QuikComp") is not None
    assert resolver.resolve("QuikComp").filename.lower() == "quikcomp.dbf"
    assert resolver.resolve("QuikAgts").filename.lower() == "quikagts.dbf"
    assert resolver.resolve("QuikMstr").filename.lower() == "quikmstr.dbf"


def test_selected_input_path_in_run_summary(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikAgts": [{"MAGENT": "1", "MAGTNAME": "A", "MCOMP": "A"}],
        "QuikMstr": [{"MPOLICY": "123456789A"}],
        "QuikActg": [{"MCOMP": "A", "MPLAN": "PLAN01"}],
    }
    result = run_data_governance(
        input_path=str(tmp_path),
        output_path=str(tmp_path / "gov_out"),
        write_reports=True,
        preloaded_tables=tables,
    )
    summary = result.to_run_summary()
    assert summary["data_region_path"] == str(tmp_path)
    assert result.data_dir == str(tmp_path)
    report = open(result.report_md_path, encoding="utf-8").read()
    assert str(tmp_path) in report
    assert result.source_opened_read_only is True
    assert result.source_files_modified is False


def test_source_files_not_modified(tmp_path):
    dbf = tmp_path / "QUIKCOMP.DBF"
    # Minimal valid-enough empty file marker; we use preloaded data for the rule
    content = b"SOURCE_MARKER_UNCHANGED"
    dbf.write_bytes(content)
    before = dbf.read_bytes()
    tables = {"QuikComp": [{"MCOMP": "A"}]}
    run_data_governance(
        input_path=str(tmp_path),
        output_path=str(tmp_path / "out"),
        rule_id="DG-QUIKCOMP-001",
        write_reports=False,
        preloaded_tables=tables,
    )
    assert dbf.read_bytes() == before
    assert dbf.read_bytes() == content
    # mtime may change on some FS when opened; content is the authority
    assert dbf.stat().st_size == len(content)


def test_output_only_in_selected_location(tmp_path):
    region = tmp_path / "region"
    out_base = tmp_path / "governance_out"
    region.mkdir()
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikAgts": [{"MAGENT": "1", "MAGTNAME": "A", "MCOMP": "A"}],
        "QuikMstr": [{"MPOLICY": "123456789A"}],
        "QuikActg": [{"MCOMP": "A", "MPLAN": "PLAN01"}],
    }
    result = run_data_governance(
        input_path=str(region),
        output_path=str(out_base),
        write_reports=True,
        preloaded_tables=tables,
    )
    assert str(result.output_dir).startswith(str(out_base))
    assert result.run_id in result.output_dir
    # No governance report files written into the source region
    region_files = {p.name for p in region.iterdir()}
    assert "data_governance_findings.csv" not in region_files
    assert "data_governance_results.csv" not in region_files
    assert "1_What_Was_Checked.html" not in region_files
    assert "2_Items_Needing_Attention.csv" not in region_files


def test_two_region_runs_produce_separate_folders(tmp_path):
    r1 = tmp_path / "region_a"
    r2 = tmp_path / "region_b"
    out = tmp_path / "out"
    r1.mkdir()
    r2.mkdir()
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikAgts": [{"MAGENT": "1", "MAGTNAME": "A", "MCOMP": "A"}],
        "QuikMstr": [{"MPOLICY": "123456789A"}],
        "QuikActg": [{"MCOMP": "A", "MPLAN": "PLAN01"}],
    }
    result1 = run_data_governance(
        input_path=str(r1),
        output_path=str(out),
        write_reports=True,
        preloaded_tables=tables,
    )
    result2 = run_data_governance(
        input_path=str(r2),
        output_path=str(out),
        write_reports=True,
        preloaded_tables=tables,
    )
    assert result1.output_dir != result2.output_dir
    assert result1.run_id != result2.run_id
    assert os.path.isdir(result1.output_dir)
    assert os.path.isdir(result2.output_dir)
    assert result1.data_dir == str(r1)
    assert result2.data_dir == str(r2)


def test_missing_table_affects_only_dependent_rules(tmp_path):
    # Only QuikComp present; tables required by other rules missing
    tables = {"QuikComp": [{"MCOMP": "A"}]}
    result = run_data_governance(
        input_path=str(tmp_path),
        output_path=str(tmp_path / "out"),
        write_reports=False,
        preloaded_tables=tables,
    )
    by_id = {r.rule_id: r for r in result.rule_results}
    assert by_id["DG-QUIKCOMP-001"].status == "PASS"
    assert by_id["DG-QUIKCOMP-002"].status == "ERROR"
    assert by_id["DG-QUIKCOMP-003"].status == "ERROR"
    assert by_id["DG-QUIKMSTR-001"].status == "ERROR"
    assert by_id["DG-QUIKACTG-001"].status == "ERROR"
    assert by_id["DG-QUIKACTG-002"].status == "ERROR"
    assert by_id["DG-QUIKLIST-001"].status == "ERROR"
    assert by_id["DG-QUIKLIST-002"].status == "ERROR"
    assert by_id["DG-QUIKDATE-001"].status == "ERROR"


def test_unrelated_rules_continue_when_one_table_missing(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikMstr": [{"MPOLICY": "123456789A"}],
        # QuikAgts intentionally absent
    }
    result = run_data_governance(
        input_path=str(tmp_path),
        output_path=str(tmp_path / "out"),
        write_reports=False,
        preloaded_tables=tables,
    )
    by_id = {r.rule_id: r for r in result.rule_results}
    assert by_id["DG-QUIKCOMP-002"].status == "ERROR"
    assert by_id["DG-QUIKCOMP-001"].status == "PASS"
    assert by_id["DG-QUIKCOMP-003"].status == "PASS"
    assert by_id["DG-QUIKMSTR-001"].status == "PASS"
    assert by_id["DG-QUIKACTG-001"].status == "ERROR"
    assert by_id["DG-QUIKACTG-002"].status == "ERROR"
    assert by_id["DG-QUIKLIST-001"].status == "ERROR"
    assert by_id["DG-QUIKLIST-002"].status == "ERROR"
    assert by_id["DG-QUIKDATE-001"].status == "ERROR"
