"""ENG-PKG-001 packaging tests — import safety and Citizens API contract."""
from __future__ import annotations

import importlib
import sys
from importlib import metadata
from pathlib import Path

import pytest

REQUIRED_MODULES = (
    "rate_dbf_schema",
    "rate_factor_loader",
    "rate_key_setup",
    "rate_member_setup",
    "rate_dbf_writer",
)

REQUIRED_SYMBOLS = {
    "rate_dbf_schema": ["MAX_AGE", "source_duration_to_ql", "duration_to_cntl_col", "KEY_TABLE"],
    "rate_factor_loader": ["LoaderConfig", "build_factor_grid", "grid_to_factor_rows"],
    "rate_key_setup": ["AssumptionProvider", "build_key_rows"],
    "rate_member_setup": ["build_member_rows"],
    "rate_dbf_writer": ["emit_all_rate_tables_csv"],
}


@pytest.fixture
def import_snapshot(tmp_path: Path):
    before_sys_path = list(sys.path)
    before_cwd = Path.cwd()
    yield tmp_path
    sys.path[:] = before_sys_path


def test_qla_core_imports(import_snapshot):
    import qla_core
    assert qla_core.__version__ == "0.1.0"
    assert qla_core.API_COMPATIBILITY_VERSION == 1


def test_required_modules_import(import_snapshot):
    for mod in REQUIRED_MODULES:
        importlib.import_module(f"qla_core.{mod}")


def test_required_symbols_exist(import_snapshot):
    for mod, symbols in REQUIRED_SYMBOLS.items():
        module = importlib.import_module(f"qla_core.{mod}")
        for sym in symbols:
            assert hasattr(module, sym), f"missing {mod}.{sym}"


@pytest.mark.skipif(
    "qla-enterprise-conversion-engine" not in {d.metadata["Name"] for d in metadata.distributions()},
    reason="Package not installed — metadata test runs after wheel install",
)
def test_package_metadata_matches_version(import_snapshot):
    import qla_core
    dist_version = metadata.version("qla-enterprise-conversion-engine")
    assert dist_version == qla_core.__version__


def test_import_no_sys_path_mutation(import_snapshot):
    before = list(sys.path)
    importlib.import_module("qla_core.rate_dbf_writer")
    assert sys.path == before


def test_import_no_file_writes(import_snapshot, tmp_path, monkeypatch):
    neutral = tmp_path / "neutral_cwd"
    neutral.mkdir()
    monkeypatch.chdir(neutral)
    before_files = set(neutral.iterdir())
    importlib.import_module("qla_core.rate_factor_loader")
    after_files = set(neutral.iterdir())
    assert before_files == after_files


def test_rate_schema_behavior_unchanged(import_snapshot):
    S = importlib.import_module("qla_core.rate_dbf_schema")
    assert S.duration_to_cntl_col(0) == ("00", 0)
    assert S.source_duration_to_ql(1) == 0
    assert S.format_factor(1.5)  # returns string, no exception


def test_factor_loader_config_defaults(import_snapshot):
    L = importlib.import_module("qla_core.rate_factor_loader")
    cfg = L.LoaderConfig()
    assert cfg.isscntry == "0000"
    assert cfg.issuest == "00"


def test_key_setup_blank_assumptions(import_snapshot):
    K = importlib.import_module("qla_core.rate_key_setup")
    provider = K.AssumptionProvider()
    assert provider.get("TESTPL", "QuikPlCv", "MORT") == ""


def test_member_setup_empty_grids(import_snapshot):
    MB = importlib.import_module("qla_core.rate_member_setup")
    rows, placeholders = MB.build_member_rows({})
    assert all(len(v) == 0 for v in rows.values())
