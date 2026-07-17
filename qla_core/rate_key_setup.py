"""
QLAdmin V5 rate-key (QuikPlxx) setup — derive the rate-key rows that connect an
authoritative PLAN (+ segmentation + EFFDATE) to a family's factor set.

Key rows are the DISTINCT segmentation tuple present in a family's factor grid.
Reserve / cash-value families (QuikPlTv shared by NP, QuikPlCv) additionally carry
actuarial-basis assumption fields. Those assumptions are EXTERNALIZED and business/
actuarially maintained — they are loaded from an AssumptionProvider and left as blank
configurable placeholders when not yet supplied. Nothing actuarial is invented here.
"""
import collections

from qla_core import rate_dbf_schema as S


class AssumptionProvider:
    """
    Supplies per-plan rate-key assumptions. Backed by an externalized mapping
    (e.g. plan_rate_key_assumption_mapping_template.csv once completed by actuarial).

    mapping: {(PLAN, KEY_TABLE): {FIELD: value}}  — partial allowed.
    Missing fields resolve to "" (blank placeholder), never a fabricated default.
    """

    def __init__(self, mapping=None):
        self.mapping = mapping or {}

    @classmethod
    def from_rows(cls, rows):
        """Build from iterable of dict rows with PLAN + assumption columns (+ optional KEY_TABLE)."""
        mapping = {}
        for r in rows:
            plan = (r.get("PLAN") or "").strip()
            if not plan:
                continue
            kt = (r.get("KEY_TABLE") or "").strip()
            targets = [kt] if kt else ["QuikPlCv", "QuikPlTv"]
            for key_table in targets:
                slot = mapping.setdefault((plan, key_table), {})
                for fld in S.assumption_field_names(key_table):
                    v = r.get(fld)
                    if v not in (None, "", "N/A"):
                        slot[fld] = str(v).strip()
        return cls(mapping)

    def get(self, plan, key_table, field, gender=None, uwclass=None):
        # gender/uwclass accepted for interface parity with segmentation-aware
        # providers (e.g. CSOAssumptionProvider); the static mapping is plan-level.
        return self.mapping.get((plan, key_table), {}).get(field, "")

    def missing_fields(self, plan, key_table):
        present = self.mapping.get((plan, key_table), {})
        return [f for f in S.assumption_field_names(key_table) if not present.get(f)]


class CSOAssumptionProvider:
    """
    AssumptionProvider-compatible adapter backed by the CSO Mortality Crosswalk.

    Supplies the four CV assumption fields the crosswalk is authoritative for
    (MORT / ETIMORT / NFOINT / INTMETHCV), gender/UW-class aware where the key row
    carries that segmentation. All other assumption fields (e.g. QuikPlTv reserve
    fields RSVINT / RSVMETH / INTMETHTV / STOREMEANS / CALCMIDS) stay blank/deferred.
    """

    CROSSWALK_FIELDS = ("MORT", "ETIMORT", "NFOINT", "INTMETHCV")

    def __init__(self, resolver):
        self.resolver = resolver

    def get(self, plan, key_table, field, gender=None, uwclass=None):
        if field not in self.CROSSWALK_FIELDS:
            return ""
        if field not in S.assumption_field_names(key_table):
            return ""
        return self.resolver.resolve(plan, gender=gender, uwclass=uwclass).get(field, "")

    def missing_fields(self, plan, key_table):
        res = self.resolver.resolve(plan)
        out = []
        for f in S.assumption_field_names(key_table):
            if f in self.CROSSWALK_FIELDS and res.get(f):
                continue
            out.append(f)
        return out


def build_key_rows(table, grid, assumptions=None):
    """
    Derive QuikPlxx key rows for one factor table's grid.

    Returns (key_table_name, rows, dependency_notes):
      rows               ordered dicts matching key_table_fields(key_table_name).
      dependency_notes   list of {plan, key_table, missing:[...]} where assumptions are
                         still required (informational; does NOT block loader construction).
    """
    assumptions = assumptions or AssumptionProvider()
    key_table = S.KEY_TABLE[table]
    seen = {}
    for (plan, age, cntl, gender, uwclass, band, isscntry, issuest, effdate) in grid.keys():
        seg = (plan, gender, uwclass, band, isscntry, issuest, effdate)
        seen[seg] = True

    rows = []
    dep = []
    dep_emitted = set()
    for (plan, gender, uwclass, band, isscntry, issuest, effdate) in sorted(seen):
        row = {"PLAN": plan, "GENDER": gender, "UWCLASS": uwclass, "BAND": band,
               "ISSCNTRY": isscntry, "ISSUEST": issuest, "EFFDATE": effdate}
        for fld in S.assumption_field_names(key_table):
            row[fld] = assumptions.get(plan, key_table, fld, gender=gender, uwclass=uwclass)
        rows.append(row)
        missing = assumptions.missing_fields(plan, key_table)
        if missing and (plan, key_table) not in dep_emitted:
            dep.append({"plan": plan, "key_table": key_table, "missing": missing})
            dep_emitted.add((plan, key_table))
    return key_table, rows, dep


# Issue #77 — Plan Values / rate-key families that must always have a header key
# when the plan has any loaded factor rates (default stub if that family has none).
# EX_Rate_Tables: use NOT APPLICABLE (0/00) only when no real codes exist — never
# both (e.g. do not keep Gender 0 when F/M already exist).
FAMILY_KEY_TABLES = ("QuikPlGp", "QuikPlDb", "QuikPlCv", "QuikPlTv", "QuikPlDv")
DEFAULT_KEY_GENDER = "0"
DEFAULT_KEY_UWCLASS = "00"
DEFAULT_KEY_BAND = "00"
DEFAULT_KEY_ISSCNTRY = "0000"
DEFAULT_KEY_ISSUEST = "00"


def _plan_key_dims(key_rows, plan):
    genders, uws, bands, sts = set(), set(), set(), set()
    for rows in (key_rows or {}).values():
        for r in rows:
            if (r.get("PLAN") or "") != plan:
                continue
            if r.get("GENDER"):
                genders.add((r.get("GENDER") or "").strip())
            if r.get("UWCLASS"):
                uws.add((r.get("UWCLASS") or "").strip())
            if r.get("BAND"):
                bands.add((r.get("BAND") or "").strip())
            sts.add((
                (r.get("ISSCNTRY") or "").strip() or DEFAULT_KEY_ISSCNTRY,
                (r.get("ISSUEST") or "").strip() or DEFAULT_KEY_ISSUEST,
            ))
    return genders, uws, bands, sts


def preferred_stub_segmentation(key_rows, plan):
    """
    Prefer real codes already on the plan's keys (EX pattern).
    Fall back to NOT APPLICABLE only when that dimension has no real values.
    """
    genders, uws, bands, sts = _plan_key_dims(key_rows, plan)
    real_g = sorted(g for g in genders if g and g != DEFAULT_KEY_GENDER)
    real_u = sorted(u for u in uws if u and u != DEFAULT_KEY_UWCLASS)
    real_b = sorted(b for b in bands if b and b != DEFAULT_KEY_BAND)
    isscntry, issuest = (DEFAULT_KEY_ISSCNTRY, DEFAULT_KEY_ISSUEST)
    if sts:
        isscntry, issuest = sorted(sts)[0]
    return {
        "GENDER": real_g[0] if real_g else DEFAULT_KEY_GENDER,
        "UWCLASS": real_u[0] if real_u else DEFAULT_KEY_UWCLASS,
        "BAND": real_b[0] if real_b else DEFAULT_KEY_BAND,
        "ISSCNTRY": isscntry,
        "ISSUEST": issuest,
    }


def is_na_stub_signature(row):
    """True when key matches the NOT-APPLICABLE stub shape (0/00/00/0000/00)."""
    return (
        (row.get("GENDER") or "").strip() == DEFAULT_KEY_GENDER
        and (row.get("UWCLASS") or "").strip() == DEFAULT_KEY_UWCLASS
        and (row.get("BAND") or "").strip() == DEFAULT_KEY_BAND
        and ((row.get("ISSCNTRY") or "").strip() or DEFAULT_KEY_ISSCNTRY) == DEFAULT_KEY_ISSCNTRY
        and ((row.get("ISSUEST") or "").strip() or DEFAULT_KEY_ISSUEST) == DEFAULT_KEY_ISSUEST
    )


def make_default_key_row(plan, key_table, assumptions=None, effdate=None, seg=None):
    """One stub key; uses preferred real segmentation when available (Issue #77)."""
    assumptions = assumptions or AssumptionProvider()
    effdate = effdate or S.STANDARD_EFFDATE
    seg = seg or {
        "GENDER": DEFAULT_KEY_GENDER,
        "UWCLASS": DEFAULT_KEY_UWCLASS,
        "BAND": DEFAULT_KEY_BAND,
        "ISSCNTRY": DEFAULT_KEY_ISSCNTRY,
        "ISSUEST": DEFAULT_KEY_ISSUEST,
    }
    gender = seg["GENDER"]
    uwclass = seg["UWCLASS"]
    row = {
        "PLAN": plan,
        "GENDER": gender,
        "UWCLASS": uwclass,
        "BAND": seg["BAND"],
        "ISSCNTRY": seg["ISSCNTRY"],
        "ISSUEST": seg["ISSUEST"],
        "EFFDATE": effdate,
    }
    for fld in S.assumption_field_names(key_table):
        row[fld] = assumptions.get(plan, key_table, fld, gender=gender, uwclass=uwclass)
    return row


def repair_na_stubs_when_real_codes_exist(key_rows, assumptions=None):
    """
    Rewrite NOT-APPLICABLE stub keys to preferred real codes when the plan
    already has F/M (or real UW/band) on other keys. Returns rows repaired.
    """
    assumptions = assumptions or AssumptionProvider()
    repaired = 0
    plans = set()
    for rows in (key_rows or {}).values():
        for r in rows:
            if r.get("PLAN"):
                plans.add(r["PLAN"])
    for plan in plans:
        seg = preferred_stub_segmentation(key_rows, plan)
        if seg["GENDER"] == DEFAULT_KEY_GENDER and seg["UWCLASS"] == DEFAULT_KEY_UWCLASS:
            continue  # plan truly has no real gender/UW — keep NA stubs
        for kt, rows in (key_rows or {}).items():
            for r in rows:
                if (r.get("PLAN") or "") != plan:
                    continue
                if not is_na_stub_signature(r):
                    continue
                # Prefer real codes; keep NA only for dims that still have none
                r["GENDER"] = seg["GENDER"]
                r["UWCLASS"] = seg["UWCLASS"]
                r["BAND"] = seg["BAND"]
                r["ISSCNTRY"] = seg["ISSCNTRY"]
                r["ISSUEST"] = seg["ISSUEST"]
                for fld in S.assumption_field_names(kt):
                    if not (r.get(fld) or "").strip():
                        r[fld] = assumptions.get(
                            plan, kt, fld, gender=r["GENDER"], uwclass=r["UWCLASS"],
                        )
                repaired += 1
    return repaired


def ensure_default_key_stubs(key_rows, rated_plans, assumptions=None, effdate=None):
    """
    Issue #77: for every plan with loaded rates, ensure each GP/DB/CV/TV/DV key
    table has at least one row. Missing families get a single stub using preferred
    real segmentation when available (NOT APPLICABLE only if no real codes).
    Does not invent factor grid values.
    Returns list of (plan, key_table) stubs added.
    """
    assumptions = assumptions or AssumptionProvider()
    effdate = effdate or S.STANDARD_EFFDATE
    # First: align any existing NA stubs that sit beside real F/M (or UW) codes
    repair_na_stubs_when_real_codes_exist(key_rows, assumptions=assumptions)
    added = []
    for plan in sorted(p for p in rated_plans if p):
        seg = preferred_stub_segmentation(key_rows, plan)
        for kt in FAMILY_KEY_TABLES:
            rows = key_rows.setdefault(kt, [])
            if any((r.get("PLAN") or "") == plan for r in rows):
                continue
            rows.append(make_default_key_row(plan, kt, assumptions, effdate, seg=seg))
            added.append((plan, kt))
    return added


def rated_plans_from_grids(grids):
    """Plans that appear on any factor grid (loaded rates)."""
    plans = set()
    for grid in (grids or {}).values():
        for key in grid.keys():
            plan = key[0] if isinstance(key, (tuple, list)) else None
            if plan:
                plans.add(plan)
    return plans
