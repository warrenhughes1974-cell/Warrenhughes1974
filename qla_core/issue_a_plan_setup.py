"""Issue A — internal QuikPlan post-process (Robert CSO review).

Surgical fixes that do not require SME sign-off:
  A6  — clear orphan *VARY* flags when no rate keys exist for that family
  A8a/b/e — A-prefix annuity riders: PAR=0, VARDB=0, PLANVALOPT=N, all *VARY*=N
  A9b — prefix-9 supplemental plans: PAR=0
"""
from __future__ import annotations

import csv
import os
from collections import defaultdict

import pandas as pd

from qla_core.normalize_utils import normalize
from qla_core.quikplan_rate_variation_flags import VARY_FIELD_NAMES

KEY_FAM = {
    "GP": "QuikPlGp",
    "DB": "QuikPlDb",
    "CV": "QuikPlCv",
    "TV": "QuikPlTv",
    "DV": "QuikPlDv",
}
VARY_SUFFIXES = ("GP", "DB", "CV", "TV", "DV")
VARY_DIMS = ("GDVARY", "UWVARY", "BDVARY", "STVARY")


def default_rates_dir(repo_root: str) -> str:
    return os.path.normpath(os.path.join(repo_root, "QLA_Migration", "Output", "rates"))


def load_rate_key_counts(repo_root: str, rates_dir: str | None = None) -> dict[str, dict[str, int]]:
    """Return {plan: {GP: n, DB: n, ...}} from emitted QuikPl*.csv (if present)."""
    rates_dir = rates_dir or default_rates_dir(repo_root)
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {fam: 0 for fam in KEY_FAM})
    if not os.path.isdir(rates_dir):
        return {}
    for fam, table in KEY_FAM.items():
        path = os.path.join(rates_dir, f"{table}.csv")
        if not os.path.isfile(path):
            continue
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    plan = normalize(row.get("PLAN", ""))
                    if plan:
                        counts[plan][fam] += 1
        except OSError:
            continue
    return dict(counts)


def _vary_fields_for_family(family: str) -> list[str]:
    return [f"{dim}{family}" for dim in VARY_DIMS if f"{dim}{family}" in VARY_FIELD_NAMES]


def _clear_family_vary_flags(df: pd.DataFrame, idx, family: str) -> int:
    n = 0
    for field in _vary_fields_for_family(family):
        if field not in df.columns:
            continue
        if str(df.at[idx, field] or "").strip().upper() not in ("", "N", "F", "0", "FALSE"):
            df.at[idx, field] = "N"
            n += 1
    return n


def apply_issue_a_plan_setup(
    df: pd.DataFrame,
    repo_root: str | None = None,
    rates_dir: str | None = None,
    log=None,
) -> pd.DataFrame:
    """Apply Issue A quikplan corrections after rate enrichment and #21J modal overlay."""
    if df is None or df.empty or "PLAN" not in df.columns:
        return df

    repo_root = repo_root or os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    key_counts = load_rate_key_counts(repo_root, rates_dir=rates_dir)

    stats = {
        "a6_orphan_flags_cleared": 0,
        "a8_par_vardb": 0,
        "a8e_pvo_defaults": 0,
        "a9b_par_cleared": 0,
    }

    for idx in df.index:
        plan = normalize(df.at[idx, "PLAN"])
        if not plan:
            continue

        # A9b — supplemental prefix 9: non-participating
        if plan.startswith("9") and "PAR" in df.columns:
            if str(df.at[idx, "PAR"] or "").strip() != "0":
                df.at[idx, "PAR"] = "0"
                stats["a9b_par_cleared"] += 1

        # A8a/b/e — A-prefix annuity deposit riders
        if plan.startswith("A"):
            changed = False
            if "PAR" in df.columns and str(df.at[idx, "PAR"] or "").strip() != "0":
                df.at[idx, "PAR"] = "0"
                changed = True
            if "VARDB" in df.columns and str(df.at[idx, "VARDB"] or "").strip() != "0":
                df.at[idx, "VARDB"] = "0"
                changed = True
            if changed:
                stats["a8_par_vardb"] += 1
            if "PLANVALOPT" in df.columns and str(df.at[idx, "PLANVALOPT"] or "").strip().upper() == "Y":
                df.at[idx, "PLANVALOPT"] = "N"
                stats["a8e_pvo_defaults"] += 1
            for field in VARY_FIELD_NAMES:
                if field not in df.columns:
                    continue
                if str(df.at[idx, field] or "").strip().upper() not in ("", "N", "F", "0", "FALSE"):
                    df.at[idx, field] = "N"
                    stats["a8e_pvo_defaults"] += 1

        # A6 — orphan category flags with no backing keys
        fam_counts = key_counts.get(plan, {})
        for fam in VARY_SUFFIXES:
            if fam_counts.get(fam, 0) > 0:
                continue
            stats["a6_orphan_flags_cleared"] += _clear_family_vary_flags(df, idx, fam)

    try:
        df.attrs["issue_a_plan_setup_stats"] = stats
    except Exception:
        pass

    if log and any(stats.values()):
        log(
            "Issue A plan setup: "
            f"A6 orphan flags cleared={stats['a6_orphan_flags_cleared']} "
            f"A8 PAR/VARDB plans={stats['a8_par_vardb']} "
            f"A8e PVO cells={stats['a8e_pvo_defaults']} "
            f"A9b PAR cleared={stats['a9b_par_cleared']}"
        )
    return df
