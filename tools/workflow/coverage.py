"""Versioned issue-to-smoke coverage map.

Reuses SMOKE_JOBS from validate_release_closed_issues.py when that module exists.
Protected baseline membership cannot be hidden by deleting a registry row.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MAP_PATH = Path(__file__).resolve().parent / "coverage_map.json"
PROTECTED_BASELINE = ("25", "26", "143", "WF1")

_ISSUE_RE = re.compile(r"#?\s*([0-9]+[A-Za-z]?|[A-Z]+\d*|WF\d+)", re.I)


def load_coverage_map(path: Path | None = None) -> dict[str, Any]:
    target = path or MAP_PATH
    data = json.loads(target.read_text(encoding="utf-8"))
    if "version" not in data or "issues" not in data:
        raise ValueError("coverage map missing version or issues")
    return data


def _issue_key(raw: str) -> str:
    text = str(raw or "").strip()
    if text.upper().startswith("WF"):
        return text.upper()
    m = _ISSUE_RE.search(text)
    return (m.group(1) if m else text).lstrip("#")


def load_smoke_job_labels(root: Path | None = None) -> list[str]:
    """Return SMOKE_JOBS labels when the release validator is importable."""
    repo = root or ROOT
    module_path = repo / "tools" / "validators" / "validate_release_closed_issues.py"
    if not module_path.is_file():
        return []
    import importlib.util

    spec = importlib.util.spec_from_file_location("validate_release_closed_issues", module_path)
    if spec is None or spec.loader is None:
        return []
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    jobs = getattr(mod, "SMOKE_JOBS", None)
    if not jobs:
        return []
    return [str(label) for label, _argv, _req in jobs]


def mapped_smoke_ids(issue_id: str, coverage: dict[str, Any] | None = None) -> list[str]:
    data = coverage or load_coverage_map()
    key = _issue_key(issue_id)
    row = (data.get("issues") or {}).get(key) or (data.get("issues") or {}).get(issue_id)
    if not row:
        return []
    return [str(s) for s in row.get("smoke_ids") or []]


def issue_row(issue_id: str, coverage: dict[str, Any] | None = None) -> dict[str, Any] | None:
    data = coverage or load_coverage_map()
    key = _issue_key(issue_id)
    return (data.get("issues") or {}).get(key) or (data.get("issues") or {}).get(issue_id)


def protected_ids(coverage: dict[str, Any] | None = None) -> list[str]:
    data = coverage or load_coverage_map()
    listed = [str(x) for x in data.get("protected_baseline") or []]
    merged = list(dict.fromkeys([*PROTECTED_BASELINE, *listed]))
    return merged


def smoke_ids_in_registry(labels: list[str], smoke_id: str) -> bool:
    want = smoke_id.strip().lower()
    for label in labels:
        if label.strip().lower() == want or want in label.strip().lower():
            return True
    return False
