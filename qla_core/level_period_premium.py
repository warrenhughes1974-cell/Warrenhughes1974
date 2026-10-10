"""Level renewal-period gross premium for an allow-listed set of plans.

LifePRO holds the base premium per unit level inside each renewal period and
re-rates at the renewal date to the source attained-age rate for the new period.
QuikGps for those plans is the issue-age by policy-year grid QLAdmin calls
"varies by issue age and year" (VARGP 2):

    value(issue age a, policy-year index k) = attained-age rate at
        a + R * (k // R)

R is that plan's renewal period. It comes from ``paagerat_pr_level_period`` in
the rate-loader config, or from ``DEFAULT_RENEWAL_PERIODS`` when the key is
absent. It is never inferred from the plan name.

The attained-age rate is the cell ``build_factor_grid`` would have stored for
that age on the slot axis (segment tier, then first row; band-collapse priority
on any non-PAAGERAT cell). A lookup age with no source rate is left blank.

``QLA_TL10_LEVEL_PERIOD_PR=0/false/no/off`` restores the attained-age slot axis
and leaves VARGP alone.
"""
from __future__ import annotations

import csv
import json
import os

from qla_core import rate_dbf_schema as S
from qla_core.rate_factor_loader import build_factor_grid

LEVEL_PERIOD_ENV = "QLA_TL10_LEVEL_PERIOD_PR"
CONFIG_KEY = "paagerat_pr_level_period"
VARGP_LEVEL_PERIOD = "2"

# In-code defaults. The rate-loader config carries the same map.
DEFAULT_RENEWAL_PERIODS = {
    "5L0110": 10,
    "5L0510": 10,
    "5L075Y": 5,
}

_QUIKPLAN_CANDIDATES = (
    ("QLA_Migration", "Output", "quikplan.csv"),
    ("plan_governance", "staged", "quikplan_staged.csv"),
    ("plan_governance", "staged", "quikplan.csv"),
)


def repo_root() -> str:
    return os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


def level_period_enabled() -> bool:
    """Kill switch: QLA_TL10_LEVEL_PERIOD_PR=0 restores the prior slot-axis layout."""
    raw = (os.environ.get(LEVEL_PERIOD_ENV) or "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def load_pipeline_config(root: str | None = None) -> dict:
    path = os.path.join(
        root or repo_root(),
        "plan_analysis",
        "phase_r5_rate_loader",
        "rate_loader_config.json",
    )
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _as_periods(raw) -> dict[str, int]:
    out: dict[str, int] = {}
    if not isinstance(raw, dict):
        return out
    for plan, years in raw.items():
        name = str(plan).strip()
        if not name or name.startswith("_"):
            continue
        try:
            period = int(years)
        except (TypeError, ValueError):
            continue
        if period > 0:
            out[name] = period
    return out


def renewal_periods(cfg: dict | None = None) -> dict[str, int]:
    """Per-plan renewal period. Config wins; otherwise the in-code defaults."""
    if cfg is None:
        cfg = load_pipeline_config()
    parsed = _as_periods((cfg or {}).get(CONFIG_KEY))
    if parsed:
        return parsed
    return dict(DEFAULT_RENEWAL_PERIODS)


def _parse_age(raw) -> int | None:
    text = ("" if raw is None else str(raw)).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def load_hiage(root: str | None, plans) -> dict[str, int]:
    """PLAN -> quikplan HIAGE. Output quikplan wins over the staged plan file."""
    wanted = {str(p).strip() for p in plans if str(p).strip()}
    found: dict[str, int] = {}
    base = root or repo_root()
    for parts in _QUIKPLAN_CANDIDATES:
        if not wanted - set(found):
            break
        path = os.path.join(base, *parts)
        if not os.path.isfile(path):
            continue
        with open(path, newline="", encoding="utf-8-sig", errors="replace") as handle:
            for row in csv.DictReader(handle):
                plan = (row.get("PLAN") or "").strip()
                if plan not in wanted or plan in found:
                    continue
                age = _parse_age(row.get("HIAGE"))
                if age is None:
                    continue
                found[plan] = age
    return found


def _row_attained_age(row: dict) -> int:
    if row.get("attained_age_slot"):
        return int(row["ql_duration"])
    return int(str(row["age"]))


def _collapse_attained(rows: list[dict]) -> dict[tuple, dict[int, dict]]:
    """One winning source row per attained age, using the factor-grid rules.

    ``build_factor_grid`` is the same function that writes today's slot-axis
    cell, so the first renewal block matches the table the plan carries now.
    """
    if not rows:
        return {}
    grids, _collisions, _caps = build_factor_grid(iter(rows), None)
    by_lineno: dict = {}
    for row in rows:
        by_lineno.setdefault(row.get("lineno"), []).append(row)

    grouped: dict[tuple, dict[int, dict]] = {}
    for key, cells in (grids.get("QuikGps") or {}).items():
        plan, age, cntl, gender, uwclass, band, isscntry, issuest, effdate = key
        group = (plan, gender, uwclass, band, isscntry, issuest, effdate)
        rates = grouped.setdefault(group, {})
        for col, cell in cells.items():
            value, _raw, lineno = cell[0], cell[1], cell[2]
            matches = [
                row for row in by_lineno.get(lineno, [])
                if abs(float(row["value"]) - float(value)) < 1e-9
            ]
            if not matches:
                continue
            src = matches[0]
            if src.get("attained_age_slot"):
                attained = (int(cntl) if str(cntl).isdigit() else 0) * S.N_DURATION_COLS + int(col)
            else:
                attained = int(age)
            rates[attained] = src
    return grouped


def _cell_row(src: dict, issue_age: int, index: int) -> dict:
    out = dict(src)
    cntl, col = S.duration_to_cntl_col(index)
    out["age"] = f"{issue_age:02d}"
    out["cntl"] = cntl
    out["col"] = col
    out["ql_duration"] = index
    out["attained_age_slot"] = False
    out["value"] = src["value"]
    out["raw_value"] = src.get("raw_value")
    return out


def reshape_pr_stream(source_rows, periods: dict, hiage_by_plan: dict | None = None):
    """Replace allow-listed slot-axis rows with an issue-age by policy-year grid.

    Every other row is yielded unchanged. Allow-listed rows set
    ``attained_age_slot`` False so they are not added to the slot-axis plan set.
    """
    period_of = _as_periods(periods)
    if not period_of:
        yield from source_rows
        return

    if hiage_by_plan is None:
        hiage_by_plan = load_hiage(repo_root(), period_of)
    else:
        hiage_by_plan = {
            str(plan).strip(): int(age)
            for plan, age in hiage_by_plan.items()
            if _parse_age(age) is not None
        }

    buffered = []
    for row in source_rows:
        if row.get("status") == "IN_SCOPE" and row.get("plan") in period_of:
            buffered.append(row)
        else:
            yield row

    collapsed = _collapse_attained(buffered)
    for group in sorted(collapsed):
        rates = collapsed[group]
        if not rates:
            continue
        plan = group[0]
        period = period_of[plan]
        low = min(rates)
        high_src = max(rates)
        hiage = hiage_by_plan.get(plan)
        top_issue = high_src if hiage is None else min(int(hiage), high_src)
        if top_issue < low:
            continue
        for issue_age in range(low, top_issue + 1):
            index = 0
            while index <= S.MAX_AGE and (issue_age + index) <= high_src:
                lookup = issue_age + period * (index // period)
                src = rates.get(lookup)
                if src is not None:
                    yield _cell_row(src, issue_age, index)
                index += 1


def pin_level_period_vargp(rows, touched=None):
    """Force VARGP 2 on the level-period plans. No other field moves.

    Returns ``(rows, touched)``. A disabled kill switch returns the rows unchanged.
    """
    out_touched = dict(touched or {})
    if not level_period_enabled():
        return [dict(row) for row in rows], out_touched
    plans = set(renewal_periods())
    out = []
    for row in rows:
        copied = dict(row)
        plan = (copied.get("PLAN") or "").strip()
        if plan in plans and (copied.get("VARGP") or "").strip() != VARGP_LEVEL_PERIOD:
            copied["VARGP"] = VARGP_LEVEL_PERIOD
            already = plan in out_touched
            base = dict(out_touched.get(plan) or {"PLAN": plan})
            base["VARGP"] = VARGP_LEVEL_PERIOD
            if not already:
                base["UPDATE_REASON"] = (
                    "Level renewal-period gross premium; VARGP 2 (issue age and year)"
                )
            out_touched[plan] = base
        out.append(copied)
    return out, out_touched


def pin_level_period_vargp_row(row: dict) -> dict:
    rows, _touched = pin_level_period_vargp([row], {})
    return rows[0]


def pin_level_period_vargp_frame(df):
    """Set VARGP to 2 on a quikplan frame. Other columns stay as they are."""
    if df is None or getattr(df, "empty", True):
        return df
    columns = getattr(df, "columns", [])
    if "PLAN" not in columns or "VARGP" not in columns:
        return df
    if not level_period_enabled():
        return df
    plans = set(renewal_periods())
    for idx in df.index:
        plan = str(df.at[idx, "PLAN"] or "").strip()
        if plan in plans and str(df.at[idx, "VARGP"] or "").strip() != VARGP_LEVEL_PERIOD:
            df.at[idx, "VARGP"] = VARGP_LEVEL_PERIOD
    return df
