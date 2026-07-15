"""Issue #73 validator — delegates to tools/validators/validate_issue73_misscntry.py."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[3] / "tools" / "validators" / "validate_issue73_misscntry.py"

if __name__ == "__main__":
    sys.argv[0] = str(TARGET)
    runpy.run_path(str(TARGET), run_name="__main__")
