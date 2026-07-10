"""Tests for chk_schema."""

import pandas as pd

from data_governance.constants.schema_manifests import SCHEMA_MANIFESTS
from data_governance.rules.chk_schema import check_schema


def test_fmt007_column_order():
    cols = list(SCHEMA_MANIFESTS["quikclid"])
    cols[0], cols[1] = cols[1], cols[0]
    data = {"quikclid.csv": pd.DataFrame(columns=cols)}
    findings = check_schema(data)
    assert any(f.rule_id == "FMT-007" for f in findings)


def test_fmt008_extra_and_missing():
    cols = list(SCHEMA_MANIFESTS["quikclid"]) + ["EXTRA_COL"]
    cols = cols[1:]  # drop first required
    data = {"quikclid.csv": pd.DataFrame(columns=cols)}
    findings = check_schema(data)
    assert any(f.rule_id == "FMT-008" and "EXTRA_COL" in f.reason for f in findings)
    assert any(f.rule_id == "FMT-008" and "missing" in f.reason.lower() for f in findings)


def test_gov012_version_mismatch():
    data = {"_context": {"app_table_version": "9.9.9"}}
    findings = check_schema(data)
    assert any(f.rule_id == "GOV-012" for f in findings)
