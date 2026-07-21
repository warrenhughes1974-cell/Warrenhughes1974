"""Citizens path constants derived from centralized configuration (CIT-ARCH-001)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from configuration import CitizensConfig, load_config

# QLAdmin load-package table names (format policy — not business mapping)
LOAD_PACKAGE_TABLES = frozenset({
    "QuikCvs", "QuikTvs", "QuikNps",
    "QuikPlCv", "QuikPlTv",
    "QuikMbrs", "QuikMbrCv", "QuikMbrTv",
})


@lru_cache(maxsize=4)
def get_config(environment: str | None = None) -> CitizensConfig:
    return load_config(environment=environment)


def clear_config_cache() -> None:
    get_config.cache_clear()


def _bind_paths(cfg: CitizensConfig) -> dict[str, Path]:
    p = cfg.paths
    root = cfg.project_root
    return {
        "PROJECT_ROOT": root,
        "OUTPUT_RATES": p.get("draft_rates_root"),
        "LEGACY_OUTPUT_RATES": p.get("release_rates_root"),
        "REPORTS": p.get("reports_root") / "audit",
        "VALIDATION": p.get("validation_root") / "rate_validation",
        "STAGING_RESERVE": p.get("reserve_staging_root"),
        "ASSUMPTIONS_CSV": p.get("rate_key_assumptions"),
        "RESERVE_DBF": p.get("reserve_dbf"),
        "PLANS_DBF": p.get("plans_dbf"),
        "CROSSWALK": p.get("plan_crosswalk"),
        "PLANS_STAGING": p.get("plans_staging"),
        "ISSUE03_SCRIPTS": root / "archive/legacy_cfic_rates/issues/CFIC_Issue_03/scripts",
    }


def refresh_path_constants(environment: str | None = None) -> None:
    """Rebind module-level path constants (used by tests)."""
    global PROJECT_ROOT, OUTPUT_RATES, LEGACY_OUTPUT_RATES, REPORTS, VALIDATION
    global STAGING_RESERVE, ASSUMPTIONS_CSV, RESERVE_DBF, PLANS_DBF, CROSSWALK
    global PLANS_STAGING, ISSUE03_SCRIPTS, EXTRACT_SCRIPT, EXTRACT_PLANS_SCRIPT
    global VALIDATE_SCRIPT, BUILD_ASSUMPTIONS_SCRIPT

    bound = _bind_paths(get_config(environment))
    PROJECT_ROOT = bound["PROJECT_ROOT"]
    OUTPUT_RATES = bound["OUTPUT_RATES"]
    LEGACY_OUTPUT_RATES = bound["LEGACY_OUTPUT_RATES"]
    REPORTS = bound["REPORTS"]
    VALIDATION = bound["VALIDATION"]
    STAGING_RESERVE = bound["STAGING_RESERVE"]
    ASSUMPTIONS_CSV = bound["ASSUMPTIONS_CSV"]
    RESERVE_DBF = bound["RESERVE_DBF"]
    PLANS_DBF = bound["PLANS_DBF"]
    CROSSWALK = bound["CROSSWALK"]
    PLANS_STAGING = bound["PLANS_STAGING"]
    ISSUE03_SCRIPTS = bound["ISSUE03_SCRIPTS"]
    EXTRACT_SCRIPT = ISSUE03_SCRIPTS / "extract_cfic_reserve_dbf.py"
    EXTRACT_PLANS_SCRIPT = ISSUE03_SCRIPTS / "extract_cfic_plans_dbf.py"
    VALIDATE_SCRIPT = ISSUE03_SCRIPTS / "validate_cfic_issue03_p7mn_pilot.py"
    BUILD_ASSUMPTIONS_SCRIPT = bound["PROJECT_ROOT"] / "conversion/orchestration/build_cfic_assumption_template.py"


# Default bindings at import (local environment)
refresh_path_constants()
