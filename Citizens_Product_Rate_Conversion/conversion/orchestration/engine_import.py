"""Enterprise Engine import boundary — no sys.path fallback (CIT-ENGINE-001)."""
from __future__ import annotations

from importlib import import_module
from typing import Any

from configuration import CitizensConfig, load_config


class EnginePackageRequiredError(ImportError):
    """Raised when the pinned Enterprise Engine package is not installed."""


def _require_engine_config(config: CitizensConfig | None = None) -> CitizensConfig:
    cfg = config or load_config()
    if cfg.engine.allow_unpinned_engine:
        raise EnginePackageRequiredError("allow_unpinned_engine must remain false")
    return cfg


def import_engine_module(module_suffix: str, config: CitizensConfig | None = None) -> Any:
    """
    Import qla_core.<module_suffix> via standard package metadata only.

    No sys.path manipulation or monorepo fallback.
    """
    cfg = _require_engine_config(config)
    import_name = cfg.engine.import_name
    full_name = f"{import_name}.{module_suffix}"
    try:
        return import_module(full_name)
    except ImportError as exc:
        raise EnginePackageRequiredError(
            f"Enterprise Engine package '{import_name}' is required but not installed. "
            f"Attempted import: {full_name}. "
            f"Engine status: {cfg.engine.status}. "
            "Install the pinned Enterprise Conversion Engine package before running conversion. "
            "See docs/architecture/ENTERPRISE_ENGINE_API_CONTRACT.md and "
            "reports/development/CIT-ENGINE-001_Package_Discovery_Report.md."
        ) from exc


def rate_dbf_schema(config: CitizensConfig | None = None):
    return import_engine_module("rate_dbf_schema", config)


def rate_factor_loader(config: CitizensConfig | None = None):
    return import_engine_module("rate_factor_loader", config)


def rate_key_setup(config: CitizensConfig | None = None):
    return import_engine_module("rate_key_setup", config)


def rate_member_setup(config: CitizensConfig | None = None):
    return import_engine_module("rate_member_setup", config)


def rate_dbf_writer(config: CitizensConfig | None = None):
    return import_engine_module("rate_dbf_writer", config)
