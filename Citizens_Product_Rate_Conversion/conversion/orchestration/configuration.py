"""Centralized Citizens project configuration loader (CIT-ARCH-001)."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "PyYAML is required for Citizens configuration. Install with: pip install pyyaml"
    ) from exc

PROJECT_MARKER = ".citizens-project-root"
VALID_ENVIRONMENTS = frozenset({"local", "validation", "production"})
FORBIDDEN_WRITABLE_SEGMENTS = (
    "cfic_rates",
    "qla_migration",
    "cso",
    "source/original",
    "quarantine/sensitive_review",
)
BLOCKED_ROOT_NAMES = frozenset({"cfic_rates", "qla_migration", "cso"})


class ConfigurationError(Exception):
    """Raised when configuration is invalid or unsafe."""


@dataclass(frozen=True)
class EngineConfig:
    distribution_name: str | None
    import_name: str
    exact_version: str | None
    api_compatibility_version: str | None
    source_type: str | None
    source_location: str | None
    package_sha256: str | None
    engine_commit: str | None
    strict_version_check: bool
    allow_unpinned_engine: bool
    required_modules: tuple[str, ...]
    required_symbols: dict[str, tuple[str, ...]]
    status: str
    notes: str | None


@dataclass(frozen=True)
class RuntimeConfig:
    dry_run: bool
    validation_only: bool
    write_output: bool
    allow_source_write: bool
    fail_on_rejected_row: bool
    fail_on_duplicate_key: bool
    fail_on_missing_mapping: bool
    fail_on_missing_rate_source: bool
    fail_on_unknown_source_authority: bool
    require_approved_mapping: bool
    require_authoritative_source: bool
    preserve_intermediate_files: bool
    overwrite_existing_output: bool
    run_id: str | None
    selected_plan_codes: tuple[str, ...]
    selected_rate_types: tuple[str, ...]
    enabled_modules: tuple[str, ...]


@dataclass(frozen=True)
class PathEntry:
    key: str
    path: Path
    category: str
    writable: bool
    external: bool


@dataclass
class PathRegistry:
    project_root: Path
    entries: dict[str, PathEntry] = field(default_factory=dict)

    def get(self, key: str) -> Path:
        if key not in self.entries:
            raise KeyError(f"Unknown path key: {key}")
        return self.entries[key].path

    def require_writable(self, key: str) -> Path:
        entry = self.entries[key]
        if not entry.writable:
            raise ConfigurationError(f"Path '{key}' is not writable: {entry.path}")
        return entry.path

    def require_readonly(self, key: str) -> Path:
        entry = self.entries[key]
        if entry.writable:
            raise ConfigurationError(f"Path '{key}' is writable, expected read-only")
        return entry.path


@dataclass(frozen=True)
class CitizensConfig:
    client_code: str
    project_name: str
    project_version: str
    configuration_version: str
    environment: str
    project_root: Path
    config_dir: Path
    engine: EngineConfig
    runtime: RuntimeConfig
    paths: PathRegistry
    logging: dict[str, Any]
    raw: dict[str, Any]


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigurationError(f"Missing required configuration file: {path}")
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ConfigurationError(f"Configuration file must be a mapping: {path}")
    return data


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _validate_schema(data: dict[str, Any], schema_path: Path, label: str) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    _validate_object(data, schema, label)


def _validate_object(data: Any, schema: dict[str, Any], path: str) -> None:
    expected_type = schema.get("type")
    if expected_type == "object":
        if not isinstance(data, dict):
            raise ConfigurationError(f"{path}: expected object")
        required = schema.get("required", [])
        for key in required:
            if key not in data:
                raise ConfigurationError(f"{path}: missing required key '{key}'")
        props = schema.get("properties", {})
        for key, value in data.items():
            if key not in props:
                continue
            sub_schema = props[key]
            _validate_object(value, sub_schema, f"{path}.{key}")
        return

    if expected_type == "array":
        if not isinstance(data, list):
            raise ConfigurationError(f"{path}: expected array")
        item_schema = schema.get("items")
        if item_schema:
            for idx, item in enumerate(data):
                _validate_object(item, item_schema, f"{path}[{idx}]")
        return

    if expected_type == "boolean":
        if not isinstance(data, bool):
            raise ConfigurationError(f"{path}: expected boolean")
        return

    if expected_type == "string":
        if not isinstance(data, str):
            raise ConfigurationError(f"{path}: expected string")
        if "const" in schema and data != schema["const"]:
            raise ConfigurationError(f"{path}: must equal {schema['const']!r}")
        if "enum" in schema and data not in schema["enum"]:
            raise ConfigurationError(f"{path}: must be one of {schema['enum']}")
        if schema.get("minLength") and len(data) < schema["minLength"]:
            raise ConfigurationError(f"{path}: string too short")
        return

    if isinstance(expected_type, list):
        if not any(_type_matches(data, t, schema, path) for t in expected_type):
            raise ConfigurationError(f"{path}: invalid type {type(data).__name__}")
        return


def _type_matches(data: Any, expected: str, schema: dict[str, Any], path: str) -> bool:
    if expected == "null" and data is None:
        return True
    if expected == "string" and isinstance(data, str):
        if "const" in schema and data != schema["const"]:
            raise ConfigurationError(f"{path}: must equal {schema['const']!r}")
        return True
    if expected == "integer" and isinstance(data, int) and not isinstance(data, bool):
        return True
    if expected == "boolean" and isinstance(data, bool):
        return True
    return False


def find_project_root(start: Path | None = None) -> Path:
    """Locate Citizens project root via marker file; independent of cwd when start is set."""
    env_root = os.environ.get("CITIZENS_PROJECT_ROOT")
    if env_root:
        candidate = Path(env_root).resolve()
        if (candidate / PROJECT_MARKER).is_file():
            return candidate
        raise ConfigurationError(
            f"CITIZENS_PROJECT_ROOT={env_root} does not contain {PROJECT_MARKER}"
        )

    current = (start or Path(__file__).resolve()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        marker = candidate / PROJECT_MARKER
        if marker.is_file():
            return candidate
    raise ConfigurationError(
        f"Could not locate Citizens project root (missing {PROJECT_MARKER})"
    )


def _reject_blocked_root(project_root: Path) -> None:
    parts = {part.lower() for part in project_root.parts}
    if parts & BLOCKED_ROOT_NAMES:
        raise ConfigurationError(
            f"Project root resolves inside blocked location: {project_root}"
        )
    name = project_root.name.lower()
    if name in BLOCKED_ROOT_NAMES:
        raise ConfigurationError(f"Project root cannot be {name}")


def _normalize_relative(project_root: Path, rel_path: str, key: str) -> Path:
    if not rel_path or rel_path.strip() == "":
        raise ConfigurationError(f"Empty path for key '{key}'")
    if re.match(r"^[A-Za-z]:", rel_path) or rel_path.startswith("\\\\"):
        raise ConfigurationError(f"Absolute path not allowed for project key '{key}': {rel_path}")
    if rel_path.startswith("/"):
        raise ConfigurationError(f"Absolute POSIX path not allowed for key '{key}': {rel_path}")
    candidate = (project_root / rel_path).resolve()
    try:
        candidate.relative_to(project_root.resolve())
    except ValueError as exc:
        raise ConfigurationError(
            f"Path traversal blocked for '{key}': {rel_path} resolves outside project root"
        ) from exc
    return candidate


def _assert_writable_allowed(key: str, rel_path: str, project_root: Path) -> None:
    lowered = rel_path.replace("\\", "/").lower()
    for segment in FORBIDDEN_WRITABLE_SEGMENTS:
        if segment in lowered or lowered.startswith(segment):
            raise ConfigurationError(
                f"Writable path '{key}' must not be under {segment}: {rel_path}"
            )
    resolved_name = project_root.name.lower()
    if resolved_name in BLOCKED_ROOT_NAMES:
        raise ConfigurationError(f"Writable path '{key}' blocked for root {project_root}")


def _build_path_registry(
    project_root: Path,
    source_cfg: dict[str, Any],
    output_cfg: dict[str, Any],
) -> PathRegistry:
    registry = PathRegistry(project_root=project_root)
    readonly_keys = {
        "source_original_root": "source",
        "source_supplemental_root": "source",
        "source_actuarial_root": "source",
        "source_product_documents_root": "source",
        "source_extracts_root": "source",
        "source_inventory_root": "source",
        "archive_root": "archive",
        "quarantine_root": "quarantine",
        "working_mappings_root": "mappings_working",
        "approved_mappings_root": "mappings_approved",
        "manifests_root": "manifests",
        "reserve_dbf": "source_file",
        "plans_dbf": "source_file",
        "plan_crosswalk": "mapping_file",
        "rate_requirements_catalog": "mapping_file",
        "rate_key_assumptions": "mapping_file",
        "reserve_staging_root": "staging_read",
        "plans_staging": "staging_read",
    }
    writable_keys = {
        "staging_root": "staging",
        "normalized_plans_root": "staging",
        "normalized_rates_root": "staging",
        "rejected_rows_root": "staging",
        "intermediate_root": "staging",
        "validation_root": "validation",
        "reports_root": "reports",
        "output_root": "output",
        "draft_rates_root": "output_draft",
        "release_rates_root": "output_release",
        "release_packages_root": "output_release",
        "run_workspace_root": "workspace",
        "log_root": "logs",
    }
    for key, category in readonly_keys.items():
        rel = source_cfg.get(key)
        if not rel:
            continue
        path = _normalize_relative(project_root, rel, key)
        registry.entries[key] = PathEntry(key, path, category, writable=False, external=False)
    for key, category in writable_keys.items():
        rel = output_cfg.get(key)
        if not rel:
            continue
        _assert_writable_allowed(key, rel, project_root)
        path = _normalize_relative(project_root, rel, key)
        registry.entries[key] = PathEntry(key, path, category, writable=True, external=False)
    return registry


def _parse_required_symbols(raw: Any) -> dict[str, tuple[str, ...]]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return {str(k): tuple(v) for k, v in raw.items()}
    if isinstance(raw, list):
        return {}
    raise ConfigurationError("required_symbols must be a mapping of module to symbol list")


def _parse_engine(engine_cfg: dict[str, Any]) -> EngineConfig:
    api_ver = engine_cfg.get("api_compatibility_version")
    return EngineConfig(
        distribution_name=engine_cfg.get("distribution_name"),
        import_name=str(engine_cfg.get("import_name", "qla_core")),
        exact_version=engine_cfg.get("exact_version"),
        api_compatibility_version=str(api_ver) if api_ver is not None else None,
        source_type=engine_cfg.get("source_type"),
        source_location=engine_cfg.get("source_location"),
        package_sha256=engine_cfg.get("package_sha256"),
        engine_commit=engine_cfg.get("engine_commit"),
        strict_version_check=bool(engine_cfg.get("strict_version_check", True)),
        allow_unpinned_engine=bool(engine_cfg.get("allow_unpinned_engine", False)),
        required_modules=tuple(engine_cfg.get("required_modules", [])),
        required_symbols=_parse_required_symbols(engine_cfg.get("required_symbols")),
        status=str(engine_cfg.get("status", "UNKNOWN")),
        notes=engine_cfg.get("notes"),
    )


def _parse_runtime(runtime_cfg: dict[str, Any], engine_cfg: EngineConfig) -> RuntimeConfig:
    if runtime_cfg.get("allow_source_write") and not runtime_cfg.get("dry_run", True):
        if any(runtime_cfg.get(k) for k in ("write_output",)):
            pass  # validated separately
    unpinned = runtime_cfg.get("allow_unpinned_engine", engine_cfg.allow_unpinned_engine)
    if unpinned:
        raise ConfigurationError("allow_unpinned_engine must remain false")
    return RuntimeConfig(
        dry_run=bool(runtime_cfg.get("dry_run", True)),
        validation_only=bool(runtime_cfg.get("validation_only", True)),
        write_output=bool(runtime_cfg.get("write_output", False)),
        allow_source_write=bool(runtime_cfg.get("allow_source_write", False)),
        fail_on_rejected_row=bool(runtime_cfg.get("fail_on_rejected_row", True)),
        fail_on_duplicate_key=bool(runtime_cfg.get("fail_on_duplicate_key", True)),
        fail_on_missing_mapping=bool(runtime_cfg.get("fail_on_missing_mapping", True)),
        fail_on_missing_rate_source=bool(runtime_cfg.get("fail_on_missing_rate_source", True)),
        fail_on_unknown_source_authority=bool(
            runtime_cfg.get("fail_on_unknown_source_authority", True)
        ),
        require_approved_mapping=bool(runtime_cfg.get("require_approved_mapping", True)),
        require_authoritative_source=bool(
            runtime_cfg.get("require_authoritative_source", True)
        ),
        preserve_intermediate_files=bool(
            runtime_cfg.get("preserve_intermediate_files", True)
        ),
        overwrite_existing_output=bool(runtime_cfg.get("overwrite_existing_output", False)),
        run_id=runtime_cfg.get("run_id"),
        selected_plan_codes=tuple(runtime_cfg.get("selected_plan_codes", [])),
        selected_rate_types=tuple(runtime_cfg.get("selected_rate_types", [])),
        enabled_modules=tuple(runtime_cfg.get("enabled_modules", [])),
    )


def _validate_runtime_guards(config: CitizensConfig) -> None:
    rt = config.runtime
    if rt.allow_source_write:
        raise ConfigurationError("allow_source_write must remain false in Stage 4B")
    approved_dir = config.paths.get("approved_mappings_root")
    if rt.require_approved_mapping and not rt.dry_run and rt.write_output:
        if not approved_dir.exists() or not any(approved_dir.iterdir()):
            raise ConfigurationError(
                "Conversion run blocked: require_approved_mapping=true but "
                f"approved mappings absent at {approved_dir}"
            )


def load_config(
    environment: str | None = None,
    project_root: Path | None = None,
    config_dir: Path | None = None,
) -> CitizensConfig:
    """Load, merge, validate, and return Citizens configuration."""
    root = project_root or find_project_root()
    _reject_blocked_root(root)
    cfg_dir = config_dir or Path(os.environ.get("CITIZENS_CONFIG_DIR", root / "config"))
    if not cfg_dir.is_absolute():
        cfg_dir = (root / cfg_dir).resolve()
    schemas_dir = cfg_dir / "schemas"

    env = environment or os.environ.get("CITIZENS_ENV", "local")
    if env not in VALID_ENVIRONMENTS:
        raise ConfigurationError(f"Unknown environment '{env}'; expected one of {sorted(VALID_ENVIRONMENTS)}")

    citizens_cfg = _load_yaml(cfg_dir / "citizens.yaml")
    engine_cfg = _load_yaml(cfg_dir / "engine_version.yaml")
    source_cfg = _load_yaml(cfg_dir / "source_locations.yaml")
    output_cfg = _load_yaml(cfg_dir / "output_locations.yaml")
    runtime_cfg = _load_yaml(cfg_dir / "runtime.yaml")
    logging_cfg = _load_yaml(cfg_dir / "logging.yaml")
    env_path = cfg_dir / "environments" / f"{env}.yaml"
    env_override = _load_yaml(env_path)

    _validate_schema(citizens_cfg, schemas_dir / "citizens_config.schema.json", "citizens")
    _validate_schema(engine_cfg, schemas_dir / "engine_version.schema.json", "engine")
    _validate_schema(source_cfg, schemas_dir / "source_locations.schema.json", "source")
    _validate_schema(output_cfg, schemas_dir / "output_locations.schema.json", "output")
    _validate_schema(runtime_cfg, schemas_dir / "runtime.schema.json", "runtime")

    citizens_cfg["environment"] = env
    if "runtime" in env_override:
        runtime_cfg = _deep_merge(runtime_cfg, env_override["runtime"])
    if "logging" in env_override:
        logging_cfg = _deep_merge(logging_cfg, env_override["logging"])

    engine = _parse_engine(engine_cfg)
    runtime = _parse_runtime(runtime_cfg, engine)
    paths = _build_path_registry(root, source_cfg, output_cfg)

    config = CitizensConfig(
        client_code=str(citizens_cfg["client_code"]),
        project_name=str(citizens_cfg["project_name"]),
        project_version=str(citizens_cfg["project_version"]),
        configuration_version=str(citizens_cfg["configuration_version"]),
        environment=env,
        project_root=root,
        config_dir=cfg_dir,
        engine=engine,
        runtime=runtime,
        paths=paths,
        logging=logging_cfg,
        raw={
            "citizens": citizens_cfg,
            "engine": engine_cfg,
            "source": source_cfg,
            "output": output_cfg,
            "runtime": runtime_cfg,
            "logging": logging_cfg,
            "environment_override": env_override,
        },
    )
    _validate_runtime_guards(config)
    return config


def assert_conversion_allowed(config: CitizensConfig) -> None:
    """Raise when runtime safety defaults block conversion execution."""
    rt = config.runtime
    if rt.dry_run:
        raise ConfigurationError(
            "Conversion blocked: dry_run=true. Set dry_run=false only after approved mappings "
            "and authoritative source are in place."
        )
    if rt.validation_only:
        raise ConfigurationError("Conversion blocked: validation_only=true")
    if not rt.write_output:
        raise ConfigurationError("Conversion blocked: write_output=false")
    if rt.require_approved_mapping:
        approved = config.paths.get("approved_mappings_root")
        if not approved.exists() or not any(approved.iterdir()):
            raise ConfigurationError(
                f"Conversion blocked: no approved mappings under {approved}"
            )
    if rt.require_authoritative_source:
        raise ConfigurationError(
            "Conversion blocked: require_authoritative_source=true and source authority "
            "remains PROPOSED (see SOURCE_AUTHORITY.md)"
        )
    if config.engine.status not in ("PINNED", "INSTALLED_PACKAGE_CONFIRMED"):
        raise ConfigurationError(
            f"Conversion blocked: Enterprise Engine status is {config.engine.status}. "
            "Install pinned engine package first."
        )
