"""Print QLA_VALUATION_DATE for the active QLA_Migration/Source package (stdout)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qla_core.valuation_date import apply_valuation_date_env  # noqa: E402

SOURCE = ROOT / "QLA_Migration" / "Source"


def main() -> int:
    try:
        vd, src = apply_valuation_date_env(SOURCE)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(vd)
    if len(sys.argv) > 1 and sys.argv[1] == "--verbose":
        print(f"# {src}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
