"""Shared pytest fixtures for Citizens configuration tests."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

MARKER = ".citizens-project-root"
CITIZENS_YAML = """\
client_code: CITIZENS
project_name: Citizens Product and Rate Conversion
project_version: "0.4.0-stage4b"
configuration_version: "1.0.0"
environment: local
"""
ENGINE_YAML = """\
distribution_name: null
import_name: qla_core
exact_version: null
api_compatibility_version: null
source_type: SOURCE_ONLY_NOT_PACKAGED
source_location: null
package_sha256: null
engine_commit: null
strict_version_check: true
allow_unpinned_engine: false
required_modules:
  - rate_dbf_schema
  - rate_factor_loader
  - rate_key_setup
  - rate_member_setup
  - rate_dbf_writer
required_symbols: []
status: PACKAGING_REQUIRED
notes: test fixture
"""
SOURCE_YAML = """\
source_original_root: source/original
source_supplemental_root: source/supplemental
source_actuarial_root: source/actuarial
source_product_documents_root: source/product_documents
source_extracts_root: source/extracts
source_inventory_root: source/inventory
archive_root: archive
quarantine_root: quarantine
working_mappings_root: mappings/working
approved_mappings_root: mappings/approved
manifests_root: manifests
reserve_dbf: source/original/dbf/cifi0007.DBF
plans_dbf: source/original/dbf/cifi0004.dbf
plan_crosswalk: mappings/working/plans/Citizens_Plan_Crosswalk.xlsx
rate_requirements_catalog: mappings/working/rate_types/Citizens_Plan_Rate_Requirements_Catalog.xlsx
rate_key_assumptions: mappings/working/business_inputs/cfic_rate_key_assumptions.csv
reserve_staging_root: staging/normalized_rates/reserve/staging
plans_staging: staging/normalized_plans/staging/plans_master.csv
"""
OUTPUT_YAML = """\
staging_root: staging
normalized_plans_root: staging/normalized_plans
normalized_rates_root: staging/normalized_rates
rejected_rows_root: staging/rejected_rows
intermediate_root: staging/intermediate
validation_root: validation
reports_root: reports
output_root: output
draft_rates_root: output/csv/draft_pre_migration
release_rates_root: output/rates
release_packages_root: output/release_packages
run_workspace_root: staging/intermediate/runs
log_root: reports/runs/logs
"""
RUNTIME_YAML = """\
dry_run: true
validation_only: true
write_output: false
allow_source_write: false
fail_on_rejected_row: true
fail_on_duplicate_key: true
fail_on_missing_mapping: true
fail_on_missing_rate_source: true
fail_on_unknown_source_authority: true
require_approved_mapping: true
require_authoritative_source: true
preserve_intermediate_files: true
overwrite_existing_output: false
run_id: null
selected_plan_codes: []
selected_rate_types: []
enabled_modules: []
"""
LOGGING_YAML = """\
level: INFO
format: "%(message)s"
console: true
file_enabled: false
file_path: reports/runs/logs/citizens.log
"""


def _write_yaml(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _copy_schemas(target_config: Path, source_config: Path) -> None:
    src_schemas = source_config / "schemas"
    dst_schemas = target_config / "schemas"
    if dst_schemas.exists():
        shutil.rmtree(dst_schemas)
    shutil.copytree(src_schemas, dst_schemas)


@pytest.fixture
def citizens_project(tmp_path: Path) -> Path:
    root = tmp_path / "citizens"
    root.mkdir()
    (root / MARKER).write_text("project: test\nclient_code: CITIZENS\nmarker_version: 1\n", encoding="utf-8")
    cfg = root / "config"
    _write_yaml(cfg / "citizens.yaml", CITIZENS_YAML)
    _write_yaml(cfg / "engine_version.yaml", ENGINE_YAML)
    _write_yaml(cfg / "source_locations.yaml", SOURCE_YAML)
    _write_yaml(cfg / "output_locations.yaml", OUTPUT_YAML)
    _write_yaml(cfg / "runtime.yaml", RUNTIME_YAML)
    _write_yaml(cfg / "logging.yaml", LOGGING_YAML)
    for env in ("local", "validation", "production"):
        _write_yaml(cfg / "environments" / f"{env}.yaml", f"environment: {env}\n")
    real_config = Path(__file__).resolve().parents[1] / "config"
    _copy_schemas(cfg, real_config)
    (root / "mappings" / "approved").mkdir(parents=True)
    (root / "source" / "original").mkdir(parents=True)
    return root


@pytest.fixture
def nested_cwd(citizens_project: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    nested = citizens_project / "deep" / "nested" / "work"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    return citizens_project
