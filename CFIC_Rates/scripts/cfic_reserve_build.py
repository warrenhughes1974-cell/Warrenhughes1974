"""Build in-memory CFIC reserve rate structures (QuikCvs/Tvs/Nps + keys + members)."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CFIC_ROOT = REPO_ROOT / "CFIC_Rates"
SCRIPTS_ISSUE03 = CFIC_ROOT / "Issue_Log" / "CFIC_Issue_03" / "scripts"

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SCRIPTS_ISSUE03))

from cfic_paths import ASSUMPTIONS_CSV, STAGING_RESERVE  # noqa: E402
from qla_core import rate_dbf_schema as S  # noqa: E402
from qla_core import rate_factor_loader as L  # noqa: E402
from qla_core import rate_key_setup as K  # noqa: E402
from qla_core import rate_member_setup as MB  # noqa: E402

VALUE_MAP = {
    "cash_value": "QuikCvs",
    "term_rsv": "QuikTvs",
    "pup_ins": "QuikNps",
}

KEY_FIELDS = ("PLAN", "GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE")


def load_staging_plan(plan: str) -> list[dict[str, str]]:
    path = STAGING_RESERVE / plan.upper() / "reserve_grid.csv"
    if not path.exists():
        raise FileNotFoundError(f"No staging for {plan}: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_staging_plans(plans: list[str] | None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if plans:
        for plan in plans:
            rows.extend(load_staging_plan(plan))
        return rows
    for plan_dir in sorted(STAGING_RESERVE.iterdir()):
        if plan_dir.is_dir():
            path = plan_dir / "reserve_grid.csv"
            if path.exists():
                with path.open(newline="", encoding="utf-8") as f:
                    rows.extend(csv.DictReader(f))
    return rows


def transform_staging(rows: list[dict[str, str]], config: L.LoaderConfig):
    lineno = 0
    for row in rows:
        ql_plan = row["ql_plan"].strip()[:6].ljust(6)
        gender = row["gender"].strip() or "0"
        uwclass = row["uwclass"].strip() or "00"
        band = row["band"].strip() or "00"
        try:
            iss_age = int(row["issue_age"])
            pol_year = int(row["policy_year"])
        except ValueError:
            continue

        original_age = str(iss_age)
        emit_age = min(iss_age, S.MAX_AGE)
        age_capped = emit_age != iss_age
        age2 = str(emit_age).zfill(2)

        try:
            ql_dur = S.source_duration_to_ql(pol_year)
        except ValueError:
            continue
        if ql_dur < 0:
            continue
        cntl, col = S.duration_to_cntl_col(ql_dur)

        for col_name, table in VALUE_MAP.items():
            raw = (row.get(col_name) or "").strip()
            if not raw:
                continue
            try:
                value = float(raw)
            except ValueError:
                continue
            lineno += 1
            yield {
                "status": "IN_SCOPE",
                "table": table,
                "plan": ql_plan,
                "age": age2,
                "cntl": cntl,
                "col": col,
                "gender": gender,
                "uwclass": uwclass,
                "band": band,
                "isscntry": config.isscntry,
                "issuest": config.issuest,
                "effdate": config.effdate,
                "source_duration": str(pol_year),
                "ql_duration": ql_dur,
                "value": value,
                "raw_value": raw,
                "lineno": lineno,
                "original_age": original_age,
                "age_capped": age_capped,
                "cfic_plan": row["cfic_plan"],
            }


def load_assumptions(path: Path) -> K.AssumptionProvider:
    if not path.exists():
        return K.AssumptionProvider()
    with path.open(newline="", encoding="utf-8") as f:
        return K.AssumptionProvider.from_rows(list(csv.DictReader(f)))


def _dedupe_keys(rows: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    out = []
    for row in rows:
        key = tuple(row.get(f) for f in KEY_FIELDS)
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def build_reserve_package(
    plans: list[str] | None,
    assumptions_path: Path = ASSUMPTIONS_CSV,
) -> dict:
    """
    Returns dict with factor_rows, key_rows, member_rows, meta.
    Raises on empty staging or no transformable cells.
    """
    staging_rows = load_staging_plans(plans)
    if not staging_rows:
        raise RuntimeError("No staging rows loaded")

    config = L.LoaderConfig(isscntry="0000", issuest="00")
    assumptions = load_assumptions(assumptions_path)
    transformed = list(transform_staging(staging_rows, config))
    if not transformed:
        raise RuntimeError("No transformable rate cells")

    grids, collisions, _cap_collisions = L.build_factor_grid(iter(transformed), config)

    collision_rows = [
        {
            "table": table,
            "plan": key[0].strip(),
            "age": key[1],
            "cntl": key[2],
            "col": col,
            "gender": key[3],
            "uwclass": key[4],
            "band": key[5],
            "prior_lineno": prior_lineno,
            "lineno": lineno,
        }
        for table, key, col, prior_lineno, lineno in collisions
    ]

    factor_tables = ["QuikCvs", "QuikTvs", "QuikNps"]
    factor_rows: dict[str, list[dict]] = {}
    key_rows: dict[str, list[dict]] = {}
    dep_notes: list[dict] = []
    fmt_issue_count = 0

    for table in factor_tables:
        grid = grids.get(table, {})
        if not grid:
            continue
        rows, fmt_issues = L.grid_to_factor_rows(table, grid, config)
        factor_rows[table] = rows
        fmt_issue_count += len(fmt_issues)
        kt, krows, dep = K.build_key_rows(table, grid, assumptions)
        key_rows[kt] = key_rows.get(kt, []) + krows
        dep_notes.extend(dep)

    for kt in ("QuikPlCv", "QuikPlTv"):
        if kt in key_rows:
            key_rows[kt] = _dedupe_keys(key_rows[kt])

    member_rows, placeholders = MB.build_member_rows(grids, effdate=config.effdate)

    cfic_plans = sorted({r["cfic_plan"] for r in staging_rows})
    return {
        "factor_rows": factor_rows,
        "key_rows": key_rows,
        "member_rows": member_rows,
        "meta": {
            "cfic_plans": cfic_plans,
            "collisions": len(collisions),
            "collision_rows": collision_rows,
            "fmt_issues": fmt_issue_count,
            "dep_notes": dep_notes,
            "member_placeholders": dict(placeholders),
        },
    }
