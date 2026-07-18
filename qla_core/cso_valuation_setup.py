"""
CSO Valuation Setup loader (Issue #80).

Authority: plan_analysis/source_data/rates/CSO_Valuation_Setup.csv
(derived from docs/Valuation_Setup.xlsx + QLAdmin Help code map).

Blank cells mean the assumption does not apply — emit blank; never fall back to
CSO_Mortiality_Crosswalk for plans listed in this file.
"""
from __future__ import annotations

import csv
import os

from qla_core import rate_dbf_schema as S

DEFAULT_VALUATION_SETUP_RELPATH = os.path.join(
    "plan_analysis", "source_data", "rates", "CSO_Valuation_Setup.csv",
)

CV_FIELDS = ("MORT", "ETIMORT", "NFOINT", "INTMETHCV")
TV_FIELDS = ("MORT", "RSVINT", "RSVMETH", "INTMETHTV", "STOREMEANS", "CALCMIDS")
QUIKPLAN_FIELDS = ("NFOINT", "INTMETHCV")


def default_valuation_setup_path(repo_root: str) -> str:
    return os.path.normpath(os.path.join(repo_root, DEFAULT_VALUATION_SETUP_RELPATH))


def _clean(v) -> str:
    if v is None:
        return ""
    return str(v).strip()


class ValuationSetupResolver:
    """Plan-level Valuation_Setup assumptions keyed by QLA PLAN."""

    def __init__(self, by_plan: dict[str, dict], source_path: str = ""):
        self._by_plan = by_plan
        self.source_path = source_path

    @classmethod
    def from_rows(cls, rows, source_path: str = "") -> "ValuationSetupResolver":
        by_plan = {}
        for r in rows:
            plan = _clean(r.get("qla_plan"))
            if not plan:
                continue
            by_plan[plan] = {k: _clean(v) for k, v in r.items()}
        return cls(by_plan, source_path)

    @property
    def plans_loaded(self) -> int:
        return len(self._by_plan)

    @property
    def plan_codes(self) -> frozenset[str]:
        return frozenset(self._by_plan)

    def has_plan(self, ql_plan_code) -> bool:
        return _clean(ql_plan_code) in self._by_plan

    def _row(self, ql_plan_code) -> dict:
        return self._by_plan.get(_clean(ql_plan_code), {})

    def field_value(self, ql_plan_code, key_table: str, field: str) -> str:
        row = self._row(ql_plan_code)
        if not row:
            return ""
        prefix = "QuikPlCv" if key_table == "QuikPlCv" else "QuikPlTv"
        return _clean(row.get(f"{prefix}_{field}"))

    def quikplan_value(self, ql_plan_code, field: str) -> str:
        row = self._row(ql_plan_code)
        if not row:
            return ""
        return _clean(row.get(f"QuikPlCv_{field}"))


def load_valuation_setup(path: str) -> ValuationSetupResolver:
    if not path or not os.path.isfile(path):
        return ValuationSetupResolver({}, source_path=path or "")
    with open(path, encoding="utf-8-sig", newline="") as f:
        return ValuationSetupResolver.from_rows(list(csv.DictReader(f)), source_path=path)


class ValuationSetupAssumptionProvider:
    """Plan-level assumptions for QuikPlCv / QuikPlTv key tables."""

    def __init__(self, resolver: ValuationSetupResolver):
        self.resolver = resolver

    def has_plan(self, plan) -> bool:
        return self.resolver.has_plan(plan)

    def get(self, plan, key_table, field, gender=None, uwclass=None):
        if not self.resolver.has_plan(plan):
            return ""
        if field not in S.assumption_field_names(key_table):
            return ""
        return self.resolver.field_value(plan, key_table, field)

    def missing_fields(self, plan, key_table):
        if self.resolver.has_plan(plan):
            return []
        return list(S.assumption_field_names(key_table))


class CompositeAssumptionProvider:
    """Valuation_Setup wins for listed plans; fallback for all others."""

    def __init__(self, primary: ValuationSetupAssumptionProvider, fallback=None):
        self.primary = primary
        self.fallback = fallback

    def get(self, plan, key_table, field, gender=None, uwclass=None):
        if self.primary.has_plan(plan):
            return self.primary.get(plan, key_table, field, gender=gender, uwclass=uwclass)
        if self.fallback is not None:
            return self.fallback.get(plan, key_table, field, gender=gender, uwclass=uwclass)
        return ""

    def missing_fields(self, plan, key_table):
        if self.primary.has_plan(plan):
            return []
        if self.fallback is not None:
            return self.fallback.missing_fields(plan, key_table)
        return list(S.assumption_field_names(key_table))


def apply_quikplan_valuation_setup(df, resolver: ValuationSetupResolver, log=None):
    """
    Overwrite quikplan NFOINT / INTMETHCV from Valuation_Setup for in-scope plans.
    Blank authority values clear existing cells (assumption does not apply).
    """
    def _log(msg):
        if log:
            log(msg)

    fields = [f for f in QUIKPLAN_FIELDS if f in df.columns]
    if "PLAN" not in df.columns or not fields:
        return {"applied": False, "reason": "PLAN/NFOINT/INTMETHCV columns absent"}

    updated = 0
    overwrites = 0
    diffs = []
    for idx in df.index:
        plan = _clean(df.at[idx, "PLAN"])
        if not plan or not resolver.has_plan(plan):
            continue
        for fld in fields:
            new_val = resolver.quikplan_value(plan, fld)
            old_val = _clean(df.at[idx, fld])
            if new_val != old_val:
                if old_val != "":
                    overwrites += 1
                df.at[idx, fld] = new_val
                updated += 1
                diffs.append({"PLAN": plan, "FIELD": fld, "OLD": old_val, "NEW": new_val})

    qa = {
        "applied": True,
        "source_path": resolver.source_path,
        "plans_loaded": resolver.plans_loaded,
        "fields_applied": fields,
        "cells_updated": updated,
        "cells_overwritten": overwrites,
        "diffs": diffs,
    }
    _log(
        f"CSO Valuation Setup (quikplan): loaded={resolver.plans_loaded} "
        f"cells_updated={updated} overwrites={overwrites}"
    )
    return qa


def apply_quikplan_cv_assumptions_excluding_plans(df, resolver, exclude_plans, log=None):
    """Run legacy CSO crosswalk apply skipping plans already on Valuation_Setup."""
    exclude = frozenset(_clean(p) for p in (exclude_plans or []))
    if "PLAN" not in df.columns:
        return {"applied": False, "skipped_all": True}

    class _Filtered:
        def resolve(self, plan, gender=None, uwclass=None):
            if _clean(plan) in exclude:
                return {"matched": False}
            return resolver.resolve(plan, gender=gender, uwclass=uwclass)

        @property
        def plans_loaded(self):
            return resolver.plans_loaded

        def qa_summary(self):
            return resolver.qa_summary()

    from qla_core.cso_mortality_crosswalk import apply_quikplan_cv_assumptions

    return apply_quikplan_cv_assumptions(df, _Filtered(), log=log)
