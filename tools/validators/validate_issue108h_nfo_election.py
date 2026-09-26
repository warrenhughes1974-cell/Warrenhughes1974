"""Issue #108H — NFO election is not forced to match ETI/RPU status.

Robert De Sarro, email 2026-07-25: the election does not have to match policy
status 44 or 45. The conversion loads the LifePRO election and leaves it.
A blank stays 0. A stored election that differs from the status stays as stored.
Disagreements are listed for review. They are not corrected.

Fail-closed: a later quikmstr rebatch that forces MNFOPT from MSTATUS (the old
Issue #72 behavior) fails this smoke.

Usage:
  python tools/validators/validate_issue108h_nfo_election.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output" / "quikmstr.csv"
DEFAULT_REPORT = (
    PROJECT_ROOT / "QLA_Migration" / "Reports" / "nfo_election_status_mismatch.csv"
)
SCRIPT_VERSION = "1.0"

# Source election, not the status-derived value (44->2, 45->3).
GOLDS = {
    "9014059C": ("45", "0"),
    "9010374099C": ("44", "1"),
    "9010381516C": ("45", "2"),
}
STATUS_ELECTION = {"44": "2", "45": "3"}


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _canon(v: object) -> str:
    s = _n(v).upper()
    if s.endswith("C"):
        s = s[:-1]
    if s.startswith("9"):
        s = s[1:]
    return s


def _load(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    errors: list[str] = []
    if not DEFAULT_OUTPUT.exists():
        print(f"FAIL: missing {DEFAULT_OUTPUT}")
        return 1
    if not DEFAULT_REPORT.exists():
        print(f"FAIL: missing {DEFAULT_REPORT}")
        return 1

    rows = _load(DEFAULT_OUTPUT)
    by_pol = {_canon(r.get("MPOLICY")): r for r in rows}
    reported = {_canon(r.get("MPOLICY")): r for r in _load(DEFAULT_REPORT)}

    disagreements = 0
    for r in rows:
        st = _n(r.get("MSTATUS"))
        want = STATUS_ELECTION.get(st)
        if want is None:
            continue
        if _n(r.get("MNFOPT")) != want:
            disagreements += 1
    if disagreements == 0:
        errors.append(
            "every ETI/RPU policy has the status-derived election "
            "(44->2, 45->3); the Issue #72 force is back"
        )

    for pol, (exp_st, exp_nfo) in GOLDS.items():
        row = by_pol.get(_canon(pol))
        if not row:
            errors.append(f"missing gold {pol}")
            continue
        got_st = _n(row.get("MSTATUS"))
        got_nfo = _n(row.get("MNFOPT"))
        if got_st != exp_st or got_nfo != exp_nfo:
            errors.append(
                f"{pol}: expected status {exp_st} election {exp_nfo}, "
                f"got {got_st}/{got_nfo}"
            )
            continue
        rep = reported.get(_canon(pol))
        if not rep:
            errors.append(f"{pol}: source election kept but absent from the review report")
            continue
        if _n(rep.get("MSTATUS")) != exp_st or _n(rep.get("MNFOPT_EMITTED")) != exp_nfo:
            errors.append(
                f"{pol}: report says {_n(rep.get('MSTATUS'))}/"
                f"{_n(rep.get('MNFOPT_EMITTED'))}, output has {got_st}/{got_nfo}"
            )

    print(f"validate_issue108h_nfo_election v{SCRIPT_VERSION}")
    print(f"  election/status disagreements left as stored: {disagreements}")
    print(f"  golds={len(GOLDS)}")
    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
