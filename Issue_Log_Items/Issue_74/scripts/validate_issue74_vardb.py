"""Wrapper for Issue #74 quikplan VARDB validator."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "validators"))
runpy.run_path(str(ROOT / "tools" / "validators" / "validate_issue74_vardb.py"), run_name="__main__")
