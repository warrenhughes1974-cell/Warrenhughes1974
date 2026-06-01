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
