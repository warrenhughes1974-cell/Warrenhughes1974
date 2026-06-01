"""
CSO Mortality Crosswalk loader / resolver (isolated enhancement).

Business-delivered crosswalk that supplies QLAdmin-ready cash value assumption codes
per QL Plan Code:

    MORT       (Mortality Table / Table for Guaranteed Values)
    ETIMORT    (ETI Mortality Table)
    NFOINT     (NFO Interest)
    INTMETHCV  (Cash Value Interest Method)

Source file (delivered spelling preserved):
    plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv

Design contract:
  * READ-ONLY against the CSV; never mutates the source.
  * No business mortality codes are invented or hardcoded here — every value comes
    from the CSV.
  * Resolution priority: most-specific gender+UW-class column, then the plan default.
  * Blank values stay blank (e.g. ETI table blank, computed-method NFO interest blank);
    a blank specific value falls back to the default but never fabricates a code.
  * QL Plan Code not present -> returns blanks with matched=False (caller logs + skips);
    conversion is never failed by a missing or blank row.

This module is consumed by BOTH:
  * app.py quikplan conversion  -> NFOINT / INTMETHCV (the CV fields in QUIKPLAN_SCHEMA)
  * rate-key setup (QuikPlCv / QuikPlTv) -> MORT / ETIMORT / NFOINT / INTMETHCV
"""
from __future__ import annotations

import csv
import os

# Fields this crosswalk is authoritative for.
CV_ASSUMPTION_FIELDS = ("MORT", "ETIMORT", "NFOINT", "INTMETHCV")

# QLAdmin segmentation value -> crosswalk column token.
_GENDER_KEY = {"M": "m", "F": "f", "J": "j"}
_UWCLASS_KEY = {"00": "00", "NS": "ns", "SM": "sm"}

_PLAN_COL = "qla_plan_code"
_MORT_DEFAULT_COL = "mort_code_default"
_ETI_DEFAULT_COL = "eti_code_default"
_NFO_COL = "nfo_interest_code"
_INTMETHCV_COL = "qla_intmethcv_code"
_REVIEW_FLAG_COL = "review_flag"
_NOTES_COL = "conversion_notes"

# Delivered filename intentionally uses the "Mortiality" spelling.
DEFAULT_CROSSWALK_RELPATH = os.path.join(
    "plan_analysis", "source_data", "rates", "CSO_Mortiality_Crosswalk.csv",
)


def default_crosswalk_path(repo_root: str) -> str:
    return os.path.normpath(os.path.join(repo_root, DEFAULT_CROSSWALK_RELPATH))


def _clean(v) -> str:
    """Strip surrounding whitespace only — preserve leading zeros / coded values."""
    if v is None:
        return ""
    return str(v).strip()


class CSOMortalityResolver:
    """Keyed by QL Plan Code; returns QLAdmin-ready CV assumption codes."""

    def __init__(self, rows_by_plan: dict, source_path: str = ""):
        self._by_plan = rows_by_plan
        self.source_path = source_path
        # QA tracking (deduped by plan).
        self._matched_plans: set[str] = set()
        self._missing_plans: set[str] = set()
        self._default_used_plans: set[str] = set()
        self._review_flag_plans: set[str] = set()

    # ---- construction ----
    @classmethod
    def from_rows(cls, rows, source_path: str = "") -> "CSOMortalityResolver":
        by_plan = {}
        for r in rows:
            plan = _clean(r.get(_PLAN_COL))
            if not plan:
                continue
            by_plan[plan] = {k: _clean(v) for k, v in r.items()}
        return cls(by_plan, source_path)

    # ---- core resolution ----
    def resolve(self, ql_plan_code, gender=None, uwclass=None) -> dict:
        """
        Return QLAdmin-ready CV assumption codes for a QL Plan Code.

        gender/uwclass are optional. When supplied and a matching gender+UW-class
        column exists, the most specific value is used; otherwise the plan default
        is used. Missing plan -> blanks with matched=False.
        """
        plan = _clean(ql_plan_code)
        row = self._by_plan.get(plan)
        if row is None:
            if plan:
                self._missing_plans.add(plan)
            return {
                "PLAN": plan, "MORT": "", "ETIMORT": "", "NFOINT": "", "INTMETHCV": "",
                "matched": False, "used_default": False,
                "review_flag": "", "conversion_notes": "",
            }

        self._matched_plans.add(plan)
        g = _GENDER_KEY.get(_clean(gender).upper())
        u = _UWCLASS_KEY.get(_clean(uwclass).upper())

        mort, mort_def = self._specific_or_default(row, "mort_code", g, u, _MORT_DEFAULT_COL)
        eti, eti_def = self._specific_or_default(row, "eti_code", g, u, _ETI_DEFAULT_COL)
        nfo = _clean(row.get(_NFO_COL))
        intmethcv = _clean(row.get(_INTMETHCV_COL))
        review = _clean(row.get(_REVIEW_FLAG_COL))
        notes = _clean(row.get(_NOTES_COL))

        used_default = mort_def or eti_def
        if used_default:
            self._default_used_plans.add(plan)
        if review:
            self._review_flag_plans.add(plan)

        return {
            "PLAN": plan, "MORT": mort, "ETIMORT": eti, "NFOINT": nfo, "INTMETHCV": intmethcv,
            "matched": True, "used_default": used_default,
            "review_flag": review, "conversion_notes": notes,
        }

    @staticmethod
    def _specific_or_default(row, prefix, g, u, default_col):
        """Return (value, used_default). Specific gender+UW wins; blank falls back."""
        if g and u:
            specific = _clean(row.get(f"{prefix}_{g}_{u}"))
            if specific:
                return specific, False
        return _clean(row.get(default_col)), True

    # ---- QA summary ----
    @property
    def plans_loaded(self) -> int:
        return len(self._by_plan)

    def qa_summary(self) -> dict:
        return {
            "source_path": self.source_path,
            "plans_loaded": self.plans_loaded,
            "plans_matched": len(self._matched_plans),
            "plans_missing": len(self._missing_plans),
            "plans_using_default": len(self._default_used_plans),
            "plans_with_review_flag": len(self._review_flag_plans),
            "missing_plan_codes": sorted(self._missing_plans),
            "review_flag_plan_codes": sorted(self._review_flag_plans),
        }


def load_cso_mortality_crosswalk(path: str) -> CSOMortalityResolver:
    """Load the crosswalk CSV into a reusable resolver. Missing file -> empty resolver."""
    if not path or not os.path.isfile(path):
        return CSOMortalityResolver({}, source_path=path or "")
    with open(path, encoding="utf-8-sig", newline="") as f:
        return CSOMortalityResolver.from_rows(list(csv.DictReader(f)), source_path=path)


# ---------------------------------------------------------------------------
# quikplan integration helper (NFOINT / INTMETHCV are the CV fields in QUIKPLAN_SCHEMA)
# ---------------------------------------------------------------------------
def apply_quikplan_cv_assumptions(df, resolver: CSOMortalityResolver, log=None):
    """
    Populate quikplan NFOINT / INTMETHCV from the crosswalk, in place, by PLAN.

    Rollback-safe / blank-safe rules:
      * Only NFOINT and INTMETHCV are touched (the CV assumption fields present in
        QUIKPLAN_SCHEMA). MORT/ETIMORT are not quikplan columns and are left to the
        rate-key tables.
      * A blank crosswalk value never blanks an existing populated value.
      * An overwrite of an existing populated value is logged before/after.
      * A PLAN missing from the crosswalk is logged; existing behavior is preserved.

    Returns a QA summary dict (also includes resolver-level counts).
    """
    def _log(msg):
        if log:
            log(msg)

    fields = [f for f in ("NFOINT", "INTMETHCV") if f in df.columns]
    if "PLAN" not in df.columns or not fields:
        return {"applied": False, "reason": "PLAN/NFOINT/INTMETHCV columns absent"}

    updated = 0
    overwrites = 0
    blank_preserved = 0
    diffs = []
    for idx in df.index:
        plan = _clean(df.at[idx, "PLAN"])
        if not plan:
            continue
        res = resolver.resolve(plan)
        if not res["matched"]:
            continue
        for fld in fields:
            new_val = res[fld]
            old_val = _clean(df.at[idx, fld])
            if new_val == "":
                if old_val != "":
                    blank_preserved += 1
                continue
            if new_val != old_val:
                if old_val != "":
                    overwrites += 1
                    _log(f"CSO crosswalk: PLAN {plan} {fld} '{old_val}' -> '{new_val}' (crosswalk override)")
                df.at[idx, fld] = new_val
                updated += 1
                diffs.append({"PLAN": plan, "FIELD": fld, "OLD": old_val, "NEW": new_val})

    qa = resolver.qa_summary()
    missing = qa["missing_plan_codes"]
    if missing:
        _log(f"WARNING: CSO crosswalk: {len(missing)} quikplan PLAN(s) not in "
             f"CSO_Mortiality_Crosswalk.csv (CV assumptions left as-is): {missing}")
    if qa["review_flag_plan_codes"]:
        _log(f"CSO crosswalk: {len(qa['review_flag_plan_codes'])} matched PLAN(s) carry a "
             f"review flag for QA/UAT: {qa['review_flag_plan_codes']}")

    qa.update({
        "applied": True,
        "fields_applied": fields,
        "cells_updated": updated,
        "cells_overwritten": overwrites,
        "blank_values_preserved": blank_preserved,
        "diffs": diffs,
    })
    return qa
