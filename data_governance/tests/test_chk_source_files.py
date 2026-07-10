"""Tests for chk_source_files."""

import os
import tempfile

from data_governance.rules.chk_source_files import check_source_files


def test_gov003_missing_source():
    with tempfile.TemporaryDirectory() as td:
        data = {"_context": {"source_dir": td, "required_source_files": ["PPBEN.csv"], "output_dir": td}}
        findings = check_source_files(data)
        assert any(f.rule_id == "GOV-003" for f in findings)


def test_gov005_missing_quikplan():
    with tempfile.TemporaryDirectory() as td:
        data = {"_context": {"source_dir": td, "required_source_files": [], "output_dir": td}}
        findings = check_source_files(data)
        assert any(f.rule_id == "GOV-005" for f in findings)


def test_gov005_present():
    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td, "quikplan.csv"), "w").write("PLAN\nABC123\n")
        data = {
            "_context": {"source_dir": td, "required_source_files": [], "output_dir": td},
            "quikplan.csv": __import__("pandas").read_csv(os.path.join(td, "quikplan.csv")),
        }
        findings = check_source_files(data)
        assert not any(f.rule_id == "GOV-005" for f in findings)
