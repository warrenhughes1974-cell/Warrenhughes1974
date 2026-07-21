from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import pytest

from configuration import CitizensConfig, EngineConfig, RuntimeConfig, PathRegistry, PathEntry
from engine_import import EnginePackageRequiredError, import_engine_module


def _engine_config(**overrides) -> CitizensConfig:
    engine = EngineConfig(
        distribution_name=overrides.get("distribution_name"),
        import_name="qla_core",
        exact_version=overrides.get("exact_version"),
        api_compatibility_version=None,
        source_type=None,
        source_location=None,
        package_sha256=None,
        engine_commit=None,
        strict_version_check=True,
        allow_unpinned_engine=False,
        required_modules=("rate_dbf_schema",),
        required_symbols={},
        status=overrides.get("status", "PACKAGING_REQUIRED"),
        notes=None,
    )
    runtime = RuntimeConfig(
        dry_run=True,
        validation_only=True,
        write_output=False,
        allow_source_write=False,
        fail_on_rejected_row=True,
        fail_on_duplicate_key=True,
        fail_on_missing_mapping=True,
        fail_on_missing_rate_source=True,
        fail_on_unknown_source_authority=True,
        require_approved_mapping=True,
        require_authoritative_source=True,
        preserve_intermediate_files=True,
        overwrite_existing_output=False,
        run_id=None,
        selected_plan_codes=(),
        selected_rate_types=(),
        enabled_modules=(),
    )
    return CitizensConfig(
        client_code="CITIZENS",
        project_name="test",
        project_version="0",
        configuration_version="1",
        environment="local",
        project_root=Path("."),
        config_dir=Path("config"),
        engine=engine,
        runtime=runtime,
        paths=PathRegistry(project_root=Path(".")),
        logging={},
        raw={},
    )


def test_missing_engine_package_raises() -> None:
    cfg = _engine_config()
    with pytest.raises(EnginePackageRequiredError, match="not installed"):
        import_engine_module("this_module_does_not_exist_stage4d", cfg)


def test_mock_engine_module_import(citizens_project) -> None:
    mod = ModuleType("qla_core.rate_dbf_schema")
    mod.MAX_AGE = 99
    sys.modules["qla_core"] = ModuleType("qla_core")
    sys.modules["qla_core.rate_dbf_schema"] = mod
    cfg = _engine_config(status="PINNED", distribution_name="qla-core", exact_version="1.0.0")
    imported = import_engine_module("rate_dbf_schema", cfg)
    assert imported.MAX_AGE == 99
    sys.modules.pop("qla_core.rate_dbf_schema", None)
    sys.modules.pop("qla_core", None)


def test_unpinned_engine_rejected() -> None:
    engine = EngineConfig(
        distribution_name=None,
        import_name="qla_core",
        exact_version=None,
        api_compatibility_version=None,
        source_type=None,
        source_location=None,
        package_sha256=None,
        engine_commit=None,
        strict_version_check=True,
        allow_unpinned_engine=True,
        required_modules=("rate_dbf_schema",),
        required_symbols={},
        status="UNKNOWN",
        notes=None,
    )
    cfg = _engine_config()
    object.__setattr__(cfg, "engine", engine)
    with pytest.raises(EnginePackageRequiredError, match="allow_unpinned_engine"):
        import_engine_module("rate_dbf_schema", cfg)
