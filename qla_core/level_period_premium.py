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

For these plans the attained-age rate is the LifePRO band 1 row at that age
(the original band, before ``map_band`` collapses 1/2/3 to QLAdmin band 00).
Duplicate band-1 rows keep the first row in the file. If band 1 is absent, the
lowest band number present is used and a warning is logged. Every other plan
still uses the PAAGERAT first-row collision rule. A lookup age with no source
rate is left blank.

``QLA_TL10_LEVEL_PERIOD_PR=0/false/no/off`` restores the attained-age slot axis
and leaves VARGP alone.

``QLA_PR_SEGMENT_SLOT_OWNERSHIP=0`` combined with this feature is unsupported.
Slot ownership is what gives one premium segment to every plan that carries it
at SEQ 1. Turning that off while level-period expansion is on sends the shared
segment to a single parent, so the other plan never receives a grid.
"""
from __future__ import annotations

import csv
import json
import logging
import os

logger = logging.getLogger(__name__)

from qla_core import rate_dbf_schema as S

# LifePRO band kept for these plans. QLAdmin BAND stays 00 (Issue #71).
PREFERRED_SOURCE_BAND = 1

LEVEL_PERIOD_ENV = "QLA_TL10_LEVEL_PERIOD_PR"
CONFIG_KEY = "paagerat_pr_level_period"
VARGP_LEVEL_PERIOD = "2"

# In-code defaults. The rate-loader config carries the same map.
DEFAULT_RENEWAL_PERIODS = {
    "5L0110": 10,
    "5L0510": 10,
    "5L075Y": 5,
}

# Staged plan setup wins. Output/quikplan.csv is a previous conversion and must
# not change the issue-age ceiling of the grid being built.
_QUIKPLAN_CANDIDATES = (
    ("plan_governance", "staged", "quikplan_staged.csv"),
    ("plan_governance", "staged", "quikplan.csv"),
    ("QLA_Migration", "Output", "quikplan.csv"),
)

_DEFAULT_PERIODS = None
_GPS_CACHE = {"stamp": None, "plans": frozenset()}


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
        logger.warning(
            "%s is %s, not a map; no level-period plans",
            CONFIG_KEY, type(raw).__name__,
        )
        return out
    for plan, years in raw.items():
        name = str(plan).strip()
        if not name or name.startswith("_"):
            continue
        try:
            period = int(years)
        except (TypeError, ValueError):
            logger.warning("%s %s=%r is not an integer; skipped", CONFIG_KEY, name, years)
            continue
        if period <= 0:
            logger.warning("%s %s=%r is not a positive period; skipped", CONFIG_KEY, name, years)
            continue
        out[name] = period
    return out


def _periods_from_cfg(cfg) -> dict[str, int]:
    """A present key replaces the defaults, including an explicit empty map."""
    if not isinstance(cfg, dict) or CONFIG_KEY not in cfg:
        return dict(DEFAULT_RENEWAL_PERIODS)
    return _as_periods(cfg.get(CONFIG_KEY))


def renewal_periods(cfg: dict | None = None) -> dict[str, int]:
    """Per-plan renewal period.

    A missing config key uses the in-code defaults. A present key replaces them,
    and an empty map turns the feature off. The no-argument lookup is cached so
    a quikplan refresh does not re-read the config once per row. Unparseable
    entries are skipped with a warning and do not restore the defaults.
    """
    global _DEFAULT_PERIODS
    if cfg is None:
        if _DEFAULT_PERIODS is None:
            _DEFAULT_PERIODS = _periods_from_cfg(load_pipeline_config())
        return dict(_DEFAULT_PERIODS)
    return _periods_from_cfg(cfg)


def _parse_age(raw) -> int | None:
    text = ("" if raw is None else str(raw)).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _quikgps_csv(root: str) -> str | None:
    directory = os.path.join(root, "QLA_Migration", "Output", "rates")
    if not os.path.isdir(directory):
        return None
    for name in os.listdir(directory):
        if name.lower() == "quikgps.csv":
            return os.path.join(directory, name)
    return None


def _scan_quikgps(path: str) -> frozenset:
    """Plans with a non-zero QuikGps cell. Zeros do not count as a rate on file."""
    found = set()
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as handle:
        for row in csv.DictReader(handle):
            plan = (row.get("PLAN") or "").strip()
            if not plan or plan in found:
                continue
            for index in range(S.N_DURATION_COLS):
                text = (row.get(f"GP{index}") or "").strip()
                if not text:
                    continue
                try:
                    value = float(text)
                except ValueError:
                    continue
                if value != 0:
                    found.add(plan)
                    break
    return frozenset(found)


def plans_with_quikgps(root: str | None = None) -> set[str]:
    """Plans that currently have a real QuikGps grid. Cached on file stamp."""
    base = root or repo_root()
    path = _quikgps_csv(base)
    if path and os.path.isfile(path):
        stat = os.stat(path)
        stamp = (path, stat.st_mtime_ns, stat.st_size)
    else:
        stamp = (path, None, None)
    if _GPS_CACHE["stamp"] == stamp:
        return set(_GPS_CACHE["plans"])
    plans = _scan_quikgps(path) if path and os.path.isfile(path) else frozenset()
    _GPS_CACHE["stamp"] = stamp
    _GPS_CACHE["plans"] = plans
    return set(plans)


def load_hiage(root: str | None, plans) -> dict[str, int]:
    """PLAN -> quikplan HIAGE. Staged quikplan wins over Output/quikplan.csv."""
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


def _source_band_number(row: dict) -> int | None:
    """Original LifePRO band. ``source_band_raw`` is the value before map_band."""
    raw = str(row.get("source_band_raw") or "").strip()
    if raw.isdigit():
        return int(raw)
    return None


def _choose_source_row(candidates: list[dict]) -> tuple[dict, bool]:
    """Band 1, else the lowest band number. First file row wins inside a band.

    Returns ``(row, fell_back)``. ``fell_back`` is true when band 1 was absent.
    """
    preferred = [
        row for row in candidates
        if _source_band_number(row) == PREFERRED_SOURCE_BAND
    ]
    if preferred:
        return preferred[0], False
    numbered = [
        (number, row) for row in candidates
        if (number := _source_band_number(row)) is not None
    ]
    if numbered:
        lowest = min(number for number, _row in numbered)
        for number, row in numbered:
            if number == lowest:
                return row, True
    return candidates[0], True


def _collapse_attained(rows: list[dict]) -> dict[tuple, dict[int, dict]]:
    """One source row per attained age for an allow-listed plan.

    Selection is LifePRO band 1, independent of file order across bands.
    Duplicate rows of that band keep the first. QLAdmin BAND on the row is
    unchanged (00). This does not call ``build_factor_grid``, so the PAAGERAT
    first-row collision rule stays in force for every other plan.
    """
    if not rows:
        return {}
    buckets: dict[tuple, dict[int, list]] = {}
    for row in rows:
        attained = _row_attained_age(row)
        group = (
            row.get("plan"), row.get("gender"), row.get("uwclass"), row.get("band"),
            row.get("isscntry"), row.get("issuest"), row.get("effdate"),
        )
        buckets.setdefault(group, {}).setdefault(attained, []).append(row)

    grouped: dict[tuple, dict[int, dict]] = {}
    warned = set()
    for group, by_age in buckets.items():
        plan, gender, uwclass = group[0], group[1], group[2]
        rates: dict[int, dict] = {}
        for attained, candidates in by_age.items():
            chosen, fell_back = _choose_source_row(candidates)
            rates[attained] = chosen
            if not fell_back:
                continue
            mark = (plan, gender, uwclass, attained)
            if mark in warned:
                continue
            warned.add(mark)
            logger.warning(
                "No LifePRO band 1 for plan %s sex %s class %s age %s; using band %s",
                plan, gender, uwclass, attained, _source_band_number(chosen),
            )
        grouped[group] = rates
    return grouped


def _cell_row(src: dict, issue_age: int, index: int) -> dict:
    out = dict(src)
    cntl, col = S.duration_to_cntl_col(index)
    out["age"] = f"{issue_age:02d}"
    out["original_age"] = out["age"]
    out["age_capped"] = False
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
    warned_hiage = set()
    for group in sorted(collapsed):
        rates = collapsed[group]
        if not rates:
            continue
        plan = group[0]
        period = period_of[plan]
        low = min(rates)
        high_src = max(rates)
        cap = _parse_age(hiage_by_plan.get(plan))
        if cap is None or cap <= 0 or cap < low:
            top_issue = high_src
            if plan not in warned_hiage:
                warned_hiage.add(plan)
                logger.warning(
                    "HIAGE %s for %s is missing or below the lowest rated age %s; "
                    "using highest source age %s",
                    "missing" if cap is None else cap, plan, low, high_src,
                )
        else:
            top_issue = min(cap, high_src)
        for issue_age in range(low, top_issue + 1):
            index = 0
            while index <= S.MAX_AGE and (issue_age + index) <= high_src:
                lookup = issue_age + period * (index // period)
                src = rates.get(lookup)
                if src is not None:
                    yield _cell_row(src, issue_age, index)
                index += 1


def pin_level_period_vargp(rows, touched=None, plans_on_file=None):
    """Force VARGP 2 on level-period plans that have a real QuikGps grid.

    A plan with no gross-premium rows keeps its current VARGP (4 when the table
    is not on file). No other field moves.

    ``plans_on_file`` is the set of plans the caller already observed. ``None``
    reads QuikGps once (cached on the file stamp). An empty set pins nothing.

    Returns ``(rows, touched)``. A disabled kill switch returns the rows unchanged.
    """
    out_touched = dict(touched or {})
    if not level_period_enabled():
        return [dict(row) for row in rows], out_touched
    plans = set(renewal_periods())
    if plans_on_file is None:
        on_file = plans_with_quikgps()
    else:
        on_file = {str(plan).strip() for plan in plans_on_file}
    eligible = plans & on_file
    out = []
    for row in rows:
        copied = dict(row)
        plan = (copied.get("PLAN") or "").strip()
        if plan in eligible and (copied.get("VARGP") or "").strip() != VARGP_LEVEL_PERIOD:
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


def pin_level_period_vargp_frame(df, plans_on_file=None):
    """Set VARGP to 2 on rows that have a real QuikGps grid. Other columns stay."""
    if df is None or getattr(df, "empty", True):
        return df
    columns = getattr(df, "columns", [])
    if "PLAN" not in columns or "VARGP" not in columns:
        return df
    if not level_period_enabled():
        return df
    plans = set(renewal_periods())
    if plans_on_file is None:
        on_file = plans_with_quikgps()
    else:
        on_file = {str(plan).strip() for plan in plans_on_file}
    eligible = plans & on_file
    for idx in df.index:
        plan = str(df.at[idx, "PLAN"] or "").strip()
        if plan in eligible and str(df.at[idx, "VARGP"] or "").strip() != VARGP_LEVEL_PERIOD:
            df.at[idx, "VARGP"] = VARGP_LEVEL_PERIOD
    return df
