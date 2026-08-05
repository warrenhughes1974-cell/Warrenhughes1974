"""
Issue #124 — read-only research: QuikIswl month-0 seed population.

Does NOT emit QuikIswl.csv or modify production Output.
Candidate grain: quikridr MPHASE=1 rows whose MPLAN is in ISWL_MPLAN_ALLOWLIST,
joined to quikmstr.MISSDT for issue date; MDB = MUNIT * 1000.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "QLA_Migration" / "Output"
EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_124" / "evidence"

try:
    from qla_core.cso_mortality_crosswalk import ISWL_MPLAN_ALLOWLIST
except Exception:  # pragma: no cover — fallback if import path differs
    ISWL_MPLAN_ALLOWLIST = frozenset(
        {"1658C1", "1658CS", "1659C2", "1659CR", "1659CS", "1659SR", "1669SR", "1679CS"}
    )


def _s(v: object) -> str:
    return (str(v) if v is not None else "").strip()


def _f(v: object) -> float | None:
    t = _s(v)
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    mstr_path = OUT / "quikmstr.csv"
    ridr_path = OUT / "quikridr.csv"
    iswl_path = OUT / "QuikIswl.csv"
    if not iswl_path.exists():
        iswl_path = OUT / "quikiswl.csv"

    mstr: dict[str, dict[str, str]] = {}
    with mstr_path.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            pol = _s(row.get("MPOLICY"))
            if pol:
                mstr[pol] = {
                    "MISSDT": _s(row.get("MISSDT")),
                    "MSTATUS": _s(row.get("MSTATUS")),
                }

    rows: list[dict] = []
    by_plan = Counter()
    by_status = Counter()
    missing_issue = 0
    bad_unit = 0

    with ridr_path.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            plan = _s(row.get("MPLAN"))
            phase = _s(row.get("MPHASE"))
            if plan not in ISWL_MPLAN_ALLOWLIST or phase != "1":
                continue
            pol = _s(row.get("MPOLICY"))
            unit = _f(row.get("MUNIT"))
            ms = mstr.get(pol, {})
            issue = ms.get("MISSDT", "")
            status = ms.get("MSTATUS", "")
            by_plan[plan] += 1
            by_status[status] += 1
            if not issue:
                missing_issue += 1
            if unit is None:
                bad_unit += 1
                mdb = ""
            else:
                mdb = f"{unit * 1000.0:.2f}"
            rows.append(
                {
                    "MPOLICY": pol,
                    "MPLAN": plan,
                    "MSTATUS": status,
                    "MPHSTAT": _s(row.get("MPHSTAT")),
                    "MISSDT": issue,
                    "MEFFDATE": _s(row.get("MEFFDATE")),
                    "MUNIT": _s(row.get("MUNIT")),
                    "MDB_PROPOSED": mdb,
                    "MLOB": "I",
                    "MLASTANNV": issue,
                    "MMONTH_PROPOSED": "0",
                }
            )

    existing_iswl = iswl_path.exists()
    existing_rows = 0
    if existing_iswl:
        with iswl_path.open(newline="", encoding="utf-8", errors="replace") as f:
            existing_rows = sum(1 for _ in csv.DictReader(f))

    sample_path = EVIDENCE / "issue124_quikiswl_seed_candidates_sample.csv"
    with sample_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["MPOLICY"])
        w.writeheader()
        w.writerows(rows[:50])

    summary = {
        "candidate_policies": len(rows),
        "by_plan": dict(sorted(by_plan.items())),
        "by_mstatus": dict(sorted(by_status.items())),
        "missing_missdt": missing_issue,
        "bad_munit": bad_unit,
        "existing_quikiswl_file": str(iswl_path) if existing_iswl else None,
        "existing_quikiswl_rows": existing_rows,
        "proposed_mapping": {
            "MPOLICY": "quikridr/quikmstr MPOLICY (format_qladmin_mpolicy)",
            "MLOB": "literal I",
            "MLASTANNV": "quikmstr.MISSDT (ISSUE_DATE)",
            "MDB": "quikridr.MUNIT * 1000",
            "MMONTH": "0 (month-0 seed assumption)",
            "other_numerics": "0.00 (assumption)",
        },
        "sample_csv": str(sample_path.relative_to(ROOT)),
    }
    summary_path = EVIDENCE / "issue124_quikiswl_seed_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
