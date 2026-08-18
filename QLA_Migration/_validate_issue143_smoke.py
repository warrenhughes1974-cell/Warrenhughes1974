"""Thin wrapper — Issue #143 release smoke lives under tools/validators/."""

from __future__ import annotations

import runpy
from pathlib import Path

_TARGET = Path(__file__).resolve().parents[1] / "tools" / "validators" / "validate_issue143_smoke.py"
runpy.run_path(str(_TARGET), run_name="__main__")
