"""
QLAdmin V5 plan member / dimension tables (QuikPlGd, QuikPlUw, QuikPlBd, QuikPlSt, QuikPlNb).

These declare, per PLAN, the segmentation MEMBERS the plan uses (gender / UW class / band /
state-country lists) plus a new-business window. Member CODE lists are derived directly from the
validated rate-key segmentation tuples (union across all families for each plan) — nothing is
invented. Code DESCRIPTIONS use standard conventional labels. Actuarial/business numeric fields
that are not present in the rate extract are emitted as AUDITED placeholders, never fabricated:
  * QuikPlBd.BDLOWVAL  -> 0.0 placeholder (band breakpoint amount; business input)
  * QuikPlSt.MLOANINT  -> blank placeholder (loan interest; business input)
  * QuikPlNb.TERMDATE  -> blank (open-ended availability)
EFFDATE is the authoritative STANDARD_EFFDATE.
"""
import collections

from qla_core import rate_dbf_schema as S


def _plan_members(grids):
    """Per plan, the union of segmentation members across all factor grids."""
    g = collections.defaultdict(lambda: {"gender": set(), "uw": set(), "band": set(), "st": set()})
    for table, grid in grids.items():
        for (plan, age, cntl, gender, uwclass, band, isscntry, issuest, effdate) in grid.keys():
            m = g[plan]
            m["gender"].add(gender)
            m["uw"].add(uwclass)
            m["band"].add(band)
            m["st"].add((isscntry, issuest))
    return g


def build_member_rows(grids, effdate=None):
    """
    Returns (member_rows, placeholders) where:
      member_rows: {table_name: [ordered dict rows]}
      placeholders: counts of audited placeholder fields emitted (business input pending).
    """
    effdate = effdate or S.STANDARD_EFFDATE
    members = _plan_members(grids)
    out = {t: [] for t in S.MEMBER_TABLES}
    ph = collections.Counter()

    for plan in sorted(members):
        m = members[plan]
        for code in sorted(m["gender"]):
            out["QuikPlGd"].append({"PLAN": plan, "GDCODE": code,
                                    "GDDESCR": S.GENDER_LABEL.get(code, code)})
        for code in sorted(m["uw"]):
            out["QuikPlUw"].append({"PLAN": plan, "UWCODE": code,
                                    "UWDESCR": S.UWCLASS_LABEL.get(code, code)})
        for code in sorted(m["band"]):
            out["QuikPlBd"].append({"PLAN": plan, "BDCODE": code,
                                    "BDDESCR": S.BAND_LABEL.get(code, code),
                                    "BDLOWVAL": 0.0})  # audited placeholder
            ph["BDLOWVAL"] += 1
        for (isscntry, issuest) in sorted(m["st"]):
            out["QuikPlSt"].append({"PLAN": plan, "ISSCNTRY": isscntry,
                                    "CNTRYTXT": S.DEFAULT_CNTRY_TXT, "ISSUEST": issuest,
                                    "STATETXT": S.DEFAULT_STATE_TXT, "MLOANINT": "",
                                    "MLOANINTX": ""})  # MLOANINT blank placeholder
            ph["MLOANINT"] += 1
            out["QuikPlNb"].append({"PLAN": plan, "ISSCNTRY": isscntry, "ISSUEST": issuest,
                                    "EFFDATE": effdate, "TERMDATE": ""})  # open-ended
            ph["TERMDATE"] += 1
    return out, ph
