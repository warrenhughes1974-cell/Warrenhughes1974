from __future__ import annotations

import json
import sys
from pathlib import Path

from configuration import load_config


def _checker():
    root = Path(__file__).resolve().parents[3]
    orch = root / "conversion" / "orchestration"
    if str(orch) not in sys.path:
        sys.path.insert(0, str(orch))
    engine_tools = root / "tools" / "engine"
    if str(engine_tools) not in sys.path:
        sys.path.insert(0, str(engine_tools))
    import check_engine_compatibility as checker  # noqa: WPS433
    return checker


def test_compatibility_checker_blocked_status(citizens_project) -> None:
    checker = _checker()
    cfg = load_config(project_root=citizens_project)
    result = checker.run_check(cfg)
    assert result["blocked"] is True
    assert result["compatible"] is False
    assert result["engine_status"] == "PACKAGING_REQUIRED"
    assert "PACKAGING_REQUIRED" in json.dumps(result)


def test_compatibility_checker_no_output_write_to_draft(citizens_project) -> None:
    draft = citizens_project / "output" / "csv" / "draft_pre_migration"
    draft.mkdir(parents=True)
    before = list(draft.glob("*.csv"))
    checker = _checker()
    checker.run_check(load_config(project_root=citizens_project))
    after = list(draft.glob("*.csv"))
    assert before == after
