"""
Deprecated legacy path module — delegates to citizens_paths (CIT-ARCH-001).

Retire in a future issue after all callers migrate to citizens_paths or configuration.load_config.
"""
from __future__ import annotations

import warnings

warnings.warn(
    "legacy_cfic_paths (cfic_paths) is deprecated; use citizens_paths or configuration.load_config",
    DeprecationWarning,
    stacklevel=2,
)

from citizens_paths import (  # noqa: F401,E402
    ASSUMPTIONS_CSV,
    BUILD_ASSUMPTIONS_SCRIPT,
    CROSSWALK,
    EXTRACT_PLANS_SCRIPT,
    EXTRACT_SCRIPT,
    ISSUE03_SCRIPTS,
    LEGACY_OUTPUT_RATES,
    LOAD_PACKAGE_TABLES,
    OUTPUT_RATES,
    PLANS_DBF,
    PLANS_STAGING,
    REPORTS,
    RESERVE_DBF,
    STAGING_RESERVE,
    VALIDATE_SCRIPT,
    VALIDATION,
)

__all__ = [
    "ASSUMPTIONS_CSV",
    "BUILD_ASSUMPTIONS_SCRIPT",
    "CROSSWALK",
    "EXTRACT_PLANS_SCRIPT",
    "EXTRACT_SCRIPT",
    "ISSUE03_SCRIPTS",
    "LEGACY_OUTPUT_RATES",
    "LOAD_PACKAGE_TABLES",
    "OUTPUT_RATES",
    "PLANS_DBF",
    "PLANS_STAGING",
    "REPORTS",
    "RESERVE_DBF",
    "STAGING_RESERVE",
    "VALIDATE_SCRIPT",
    "VALIDATION",
]
