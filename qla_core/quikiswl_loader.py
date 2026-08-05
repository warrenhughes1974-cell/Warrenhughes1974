"""
Issue #124 — QuikIswl month-0 seed rows for existing ISWL policies.

Builds one QuikIswl seed per base ISWL coverage (MPHASE=1, ISWL MPLAN allowlist):
  MPOLICY, MLOB=I, MLASTANNV=issue date, MMONTH=0, MDB=MUNIT*1000,
  remaining numerics 0.00, dates/logical blank.

Source of truth for keys/units/dates: converted quikridr + quikmstr Output.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from qla_core.cso_mortality_crosswalk import ISWL_MPLAN_ALLOWLIST

QUIKISWL_FIELDS = [
    "MPOLICY",
    "MLOB",
    "MLASTANNV",
    "MMONTH",
    "MACCTBAL",
    "MSURRCHG",
    "MCASHVAL",
    "MGTDCSV",
    "MLOANBAL",
    "MPREMIUMS",
    "MINT",
    "MEXP",
    "MDB",
    "MNAR",
    "MCOI",
    "MSPRCOI",
    "MCTRCOI",
    "MWPRCOI",
    "MADBCOI",
    "MGIOCOI",
    "MSURR",
    "MSUMPREM",
    "MSUSPENSE",
    "MUNALLOC",
    "MPROCDATE",
    "MPRNTSTMT",
]

ZERO_MONEY_FIELDS = [
    "MACCTBAL",
    "MSURRCHG",
    "MCASHVAL",
    "MGTDCSV",
    "MLOANBAL",
    "MPREMIUMS",
    "MINT",
    "MEXP",
    "MNAR",
    "MCOI",
    "MSPRCOI",
    "MCTRCOI",
    "MWPRCOI",
    "MADBCOI",
    "MGIOCOI",
    "MSURR",
    "MSUMPREM",
    "MSUSPENSE",
    "MUNALLOC",
]

OUTPUT_FILENAME = "QuikIswl.csv"


def _s(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _parse_unit(v: object) -> float | None:
    t = _s(v)
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _fmt_money(v: float) -> str:
    return f"{v:.2f}"


def _norm_date(v: object) -> str:
    d = "".join(ch for ch in _s(v) if ch.isdigit())
    return d[:8] if len(d) >= 8 else ""


@dataclass
class QuikIswlEmitResult:
    rows: list[dict] = field(default_factory=list)
    skipped_missing_issue: list[dict] = field(default_factory=list)
    skipped_bad_unit: list[dict] = field(default_factory=list)
    skipped_orphan_mstr: list[dict] = field(default_factory=list)
    by_plan: dict[str, int] = field(default_factory=dict)


def build_quikiswl_seed_rows(
    mstr_path: Path,
    ridr_path: Path,
    *,
    allowlist: frozenset[str] | set[str] = ISWL_MPLAN_ALLOWLIST,
) -> QuikIswlEmitResult:
    """Build month-0 QuikIswl seed rows from converted Output tables."""
    result = QuikIswlEmitResult()
    mstr: dict[str, dict[str, str]] = {}
    with mstr_path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.DictReader(f):
            pol = _s(row.get("MPOLICY"))
            if pol:
                mstr[pol] = {
                    "MISSDT": _norm_date(row.get("MISSDT")),
                    "MSTATUS": _s(row.get("MSTATUS")),
                }

    by_plan: dict[str, int] = {}
    with ridr_path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.DictReader(f):
            plan = _s(row.get("MPLAN"))
            phase = _s(row.get("MPHASE"))
            if plan not in allowlist or phase != "1":
                continue
            pol = _s(row.get("MPOLICY"))
            if not pol:
                continue
            ms = mstr.get(pol)
            if ms is None:
                result.skipped_orphan_mstr.append(
                    {"MPOLICY": pol, "MPLAN": plan, "reason": "no_quikmstr"}
                )
                continue
            issue = ms.get("MISSDT", "")
            if not issue:
                result.skipped_missing_issue.append(
                    {"MPOLICY": pol, "MPLAN": plan, "reason": "blank_MISSDT"}
                )
                continue
            unit = _parse_unit(row.get("MUNIT"))
            if unit is None:
                result.skipped_bad_unit.append(
                    {
                        "MPOLICY": pol,
                        "MPLAN": plan,
                        "MUNIT": _s(row.get("MUNIT")),
                        "reason": "bad_MUNIT",
                    }
                )
                continue

            out = {f: "" for f in QUIKISWL_FIELDS}
            out["MPOLICY"] = pol
            out["MLOB"] = "I"
            out["MLASTANNV"] = issue
            out["MMONTH"] = "0"
            out["MDB"] = _fmt_money(unit * 1000.0)
            for fld in ZERO_MONEY_FIELDS:
                out[fld] = "0.00"
            result.rows.append(out)
            by_plan[plan] = by_plan.get(plan, 0) + 1

    result.by_plan = dict(sorted(by_plan.items()))
    result.rows.sort(key=lambda r: (r["MPOLICY"], r["MLASTANNV"]))
    return result


def write_quikiswl_csv(rows: list[dict], out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=QUIKISWL_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def emit_quikiswl_seeds(output_dir: Path | str) -> dict:
    """
    Build and write QuikIswl.csv under output_dir.
    Returns a JSON-serializable summary dict.
    """
    out = Path(output_dir)
    mstr_path = out / "quikmstr.csv"
    ridr_path = out / "quikridr.csv"
    if not mstr_path.is_file() or not ridr_path.is_file():
        return {
            "status": "FAILED",
            "error": "missing quikmstr.csv or quikridr.csv",
            "output_dir": str(out),
        }
    built = build_quikiswl_seed_rows(mstr_path, ridr_path)
    path = out / OUTPUT_FILENAME
    n = write_quikiswl_csv(built.rows, path)
    return {
        "status": "SUCCESS",
        "issue": 124,
        "output": str(path),
        "rows": n,
        "by_plan": built.by_plan,
        "skipped_missing_issue": len(built.skipped_missing_issue),
        "skipped_bad_unit": len(built.skipped_bad_unit),
        "skipped_orphan_mstr": len(built.skipped_orphan_mstr),
    }
