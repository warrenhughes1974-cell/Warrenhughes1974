from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from configuration import ConfigurationError, assert_conversion_allowed, find_project_root, load_config


def test_project_root_from_nested_directory(nested_cwd: Path) -> None:
    nested = nested_cwd / "deep" / "nested" / "work"
    probe = nested / "probe.txt"
    probe.write_text("x", encoding="utf-8")
    root = find_project_root(probe)
    assert root == nested_cwd
    assert (root / ".citizens-project-root").is_file()


def test_project_root_independent_of_cwd(citizens_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir("/")
    root = find_project_root(citizens_project / "config" / "citizens.yaml")
    assert root == citizens_project


def test_local_environment_load(citizens_project: Path) -> None:
    cfg = load_config(environment="local", project_root=citizens_project)
    assert cfg.environment == "local"
    assert cfg.client_code == "CITIZENS"


def test_validation_environment_load(citizens_project: Path) -> None:
    env_file = citizens_project / "config/environments/validation.yaml"
    env_file.write_text(
        "environment: validation\nruntime:\n  validation_only: true\n  dry_run: true\n",
        encoding="utf-8",
    )
    cfg = load_config(environment="validation", project_root=citizens_project)
    assert cfg.environment == "validation"
    assert cfg.runtime.validation_only is True


def test_missing_environment_rejection(citizens_project: Path) -> None:
    with pytest.raises(ConfigurationError, match="Unknown environment"):
        load_config(environment="staging", project_root=citizens_project)


def test_missing_configuration_file_rejection(citizens_project: Path) -> None:
    (citizens_project / "config/runtime.yaml").unlink()
    with pytest.raises(ConfigurationError, match="Missing required configuration"):
        load_config(project_root=citizens_project)


def test_schema_validation_failure(citizens_project: Path) -> None:
    bad = {"client_code": "WRONG"}
    (citizens_project / "config/citizens.yaml").write_text(yaml.dump(bad), encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_config(project_root=citizens_project)


def test_path_traversal_rejection(citizens_project: Path) -> None:
    out = citizens_project / "config/output_locations.yaml"
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    data["reports_root"] = "../../outside"
    out.write_text(yaml.dump(data), encoding="utf-8")
    with pytest.raises(ConfigurationError, match="Path traversal"):
        load_config(project_root=citizens_project)


def test_writable_under_source_original_rejection(citizens_project: Path) -> None:
    out = citizens_project / "config/output_locations.yaml"
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    data["staging_root"] = "source/original/staging_bad"
    out.write_text(yaml.dump(data), encoding="utf-8")
    with pytest.raises(ConfigurationError, match="source/original"):
        load_config(project_root=citizens_project)


def test_writable_under_cfic_rates_rejection(citizens_project: Path) -> None:
    out = citizens_project / "config/output_locations.yaml"
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    data["output_root"] = "CFIC_Rates/output"
    out.write_text(yaml.dump(data), encoding="utf-8")
    with pytest.raises(ConfigurationError, match="cfic_rates"):
        load_config(project_root=citizens_project)


def test_writable_under_cso_rejection(citizens_project: Path) -> None:
    out = citizens_project / "config/output_locations.yaml"
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    data["validation_root"] = "cso/validation"
    out.write_text(yaml.dump(data), encoding="utf-8")
    with pytest.raises(ConfigurationError, match="cso"):
        load_config(project_root=citizens_project)


def test_source_write_rejection(citizens_project: Path) -> None:
    runtime = citizens_project / "config/runtime.yaml"
    data = yaml.safe_load(runtime.read_text(encoding="utf-8"))
    data["allow_source_write"] = True
    runtime.write_text(yaml.dump(data), encoding="utf-8")
    with pytest.raises(ConfigurationError, match="allow_source_write"):
        load_config(project_root=citizens_project)


def test_safety_defaults(citizens_project: Path) -> None:
    cfg = load_config(project_root=citizens_project)
    assert cfg.runtime.dry_run is True
    assert cfg.runtime.validation_only is True
    assert cfg.runtime.write_output is False
    assert cfg.runtime.overwrite_existing_output is False
    assert cfg.runtime.require_approved_mapping is True
    assert cfg.runtime.require_authoritative_source is True


def test_assert_conversion_blocked_by_defaults(citizens_project: Path) -> None:
    cfg = load_config(project_root=citizens_project)
    with pytest.raises(ConfigurationError, match="dry_run"):
        assert_conversion_allowed(cfg)


def test_env_var_cannot_disable_safety(citizens_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = citizens_project / "config/runtime.yaml"
    data = yaml.safe_load(runtime.read_text(encoding="utf-8"))
    data["dry_run"] = False
    data["write_output"] = True
    data["validation_only"] = False
    data["allow_source_write"] = True
    runtime.write_text(yaml.dump(data), encoding="utf-8")
    monkeypatch.setenv("CITIZENS_ENV", "local")
    with pytest.raises(ConfigurationError, match="allow_source_write"):
        load_config(project_root=citizens_project)


def test_citizens_project_root_env(citizens_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CITIZENS_PROJECT_ROOT", str(citizens_project))
    root = find_project_root()
    assert root == citizens_project


def test_citizens_project_root_blocks_invalid(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CITIZENS_PROJECT_ROOT", str(tmp_path))
    with pytest.raises(ConfigurationError):
        find_project_root()


def test_windows_path_normalization(citizens_project: Path) -> None:
    cfg = load_config(project_root=citizens_project)
    reports = cfg.paths.get("reports_root")
    assert reports.is_absolute()
    assert reports.relative_to(citizens_project)


def test_external_engine_metadata_unresolved(citizens_project: Path) -> None:
    cfg = load_config(project_root=citizens_project)
    assert cfg.engine.distribution_name is None
    assert cfg.engine.exact_version is None
    assert cfg.engine.status == "PACKAGING_REQUIRED"
    assert cfg.engine.allow_unpinned_engine is False
