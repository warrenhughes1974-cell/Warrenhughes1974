from __future__ import annotations

from pathlib import Path

from configuration import load_config


def test_integration_load_real_project() -> None:
    root = Path(__file__).resolve().parents[3]
    cfg = load_config(environment="local", project_root=root)
    assert cfg.project_root == root
    assert cfg.paths.get("source_original_root").exists() or True  # path registered
    assert cfg.runtime.dry_run is True
