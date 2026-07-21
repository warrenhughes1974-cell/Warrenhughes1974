"""Stage 4D installed engine integration tests."""
from __future__ import annotations

import importlib
import sys
from importlib import metadata
from pathlib import Path

import pytest

ORCH = Path(__file__).resolve().parents[3] / "conversion" / "orchestration"
if str(ORCH) not in sys.path:
    sys.path.insert(0, str(ORCH))

from configuration import ConfigurationError, assert_conversion_allowed, load_config  # noqa: E402


@pytest.mark.skipif(
    "qla-enterprise-conversion-engine" not in {d.metadata["Name"] for d in metadata.distributions()},
    reason="Engine package not installed in current environment",
)
def test_installed_engine_metadata_matches_config():
    cfg = load_config()
    assert cfg.engine.status == "PINNED"
    assert cfg.engine.distribution_name == "qla-enterprise-conversion-engine"
    assert cfg.engine.exact_version == "0.1.0"
    assert metadata.version("qla-enterprise-conversion-engine") == "0.1.0"
    import qla_core
    assert qla_core.__version__ == "0.1.0"
    assert qla_core.API_COMPATIBILITY_VERSION == 1


def test_active_orchestration_imports_no_conversion():
    import cfic_reserve_build  # noqa: F401
    import cfic_rate_publish  # noqa: F401
    import build_cfic_assumption_template  # noqa: F401


def test_conversion_gate_blocks_execution():
    with pytest.raises(ConfigurationError):
        assert_conversion_allowed(load_config())


def test_compatibility_checker_passes_when_installed():
    if "qla-enterprise-conversion-engine" not in {d.metadata["Name"] for d in metadata.distributions()}:
        pytest.skip("engine not installed")
    engine_tools = Path(__file__).resolve().parents[3] / "tools" / "engine"
    if str(engine_tools) not in sys.path:
        sys.path.insert(0, str(engine_tools))
    import check_engine_compatibility as checker  # noqa: WPS433
    result = checker.run_check(load_config())
    assert result["compatible"] is True
    assert result["blocked"] is False
