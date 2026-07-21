"""
QLAdmin V5 plan member / dimension tables (QuikPlGd, QuikPlUw, QuikPlBd, QuikPlSt, QuikPlNb).

These declare, per PLAN, the segmentation MEMBERS the plan uses (gender / UW class / band /
state-country lists) plus a new-business window. Member CODE lists are derived directly from the
validated rate-key segmentation tuples (union across all families for each plan) — nothing is
invented. Code DESCRIPTIONS use standard conventional labels. Actuarial/business numeric fields
that are not present in the rate extract are emitted as AUDITED placeholders, never fabricated:
  * QuikPlBd.BDLOWVAL  -> 0.0 placeholder (band breakpoint amount; business input)
  * QuikPlSt.MLOANINT  -> 0.00 default (Issue #77; EX_Rate_Tables convention)
  * QuikPlNb.TERMDATE  -> blank (open-ended availability)
EFFDATE is the authoritative STANDARD_EFFDATE.
"""
import collections

from qla_core import rate_dbf_schema as S

# Issue #77 — match docs/EX_Rate_Tables QuikPlSt convention when loan rate not sourced
DEFAULT_MLOANINT = 0.00


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
                                    "STATETXT": S.DEFAULT_STATE_TXT,
                                    "MLOANINT": DEFAULT_MLOANINT,
                                    "MLOANINTX": ""})
            ph["MLOANINT"] += 1
            out["QuikPlNb"].append({"PLAN": plan, "ISSCNTRY": isscntry, "ISSUEST": issuest,
                                    "EFFDATE": effdate, "TERMDATE": ""})  # open-ended
            ph["TERMDATE"] += 1
    return out, ph


# Issue #77 / EX guide — NOT APPLICABLE codes (omit when real codes already exist)
_NA_GENDER = "0"
_NA_UW = "00"
_NA_BAND = "00"


def prune_default_members_when_real_exist(member_rows):
    """
    Drop Gender 0 / UW 00 / Band 00 member rows when the plan already has real codes.
    Matches EX_Rate_Tables (almost never both). Returns count removed.
    """
    removed = 0
    gd_rows = member_rows.get("QuikPlGd") or []
    by_plan_g = collections.defaultdict(set)
    for r in gd_rows:
        by_plan_g[r.get("PLAN")].add((r.get("GDCODE") or "").strip())
    new_gd = []
    for r in gd_rows:
        plan, code = r.get("PLAN"), (r.get("GDCODE") or "").strip()
        real = {c for c in by_plan_g.get(plan, ()) if c and c != _NA_GENDER}
        if code == _NA_GENDER and real:
            removed += 1
            continue
        new_gd.append(r)
    member_rows["QuikPlGd"] = new_gd

    uw_rows = member_rows.get("QuikPlUw") or []
    by_plan_u = collections.defaultdict(set)
    for r in uw_rows:
        by_plan_u[r.get("PLAN")].add((r.get("UWCODE") or "").strip())
    new_uw = []
    for r in uw_rows:
        plan, code = r.get("PLAN"), (r.get("UWCODE") or "").strip()
        real = {c for c in by_plan_u.get(plan, ()) if c and c != _NA_UW}
        if code == _NA_UW and real:
            removed += 1
            continue
        new_uw.append(r)
    member_rows["QuikPlUw"] = new_uw

    bd_rows = member_rows.get("QuikPlBd") or []
    by_plan_b = collections.defaultdict(set)
    for r in bd_rows:
        by_plan_b[r.get("PLAN")].add((r.get("BDCODE") or "").strip())
    new_bd = []
    for r in bd_rows:
        plan, code = r.get("PLAN"), (r.get("BDCODE") or "").strip()
        real = {c for c in by_plan_b.get(plan, ()) if c and c != _NA_BAND}
        if code == _NA_BAND and real:
            removed += 1
            continue
        new_bd.append(r)
    member_rows["QuikPlBd"] = new_bd
    return removed


def ensure_members_for_keys(member_rows, key_rows, effdate=None):
    """
    Issue #77: ensure member codes exist for every segmentation used on key rows
    (including default key stubs). Does not add NOT APPLICABLE codes when real
    codes already exist for that plan. Returns count of member rows added.
    """
    effdate = effdate or S.STANDARD_EFFDATE
    prune_default_members_when_real_exist(member_rows)
    added = 0
    gd = {(r.get("PLAN"), r.get("GDCODE")) for r in member_rows.get("QuikPlGd", [])}
    uw = {(r.get("PLAN"), r.get("UWCODE")) for r in member_rows.get("QuikPlUw", [])}
    bd = {(r.get("PLAN"), r.get("BDCODE")) for r in member_rows.get("QuikPlBd", [])}
    st = {(r.get("PLAN"), r.get("ISSCNTRY"), r.get("ISSUEST")) for r in member_rows.get("QuikPlSt", [])}
    nb = {(r.get("PLAN"), r.get("ISSCNTRY"), r.get("ISSUEST")) for r in member_rows.get("QuikPlNb", [])}

    member_rows.setdefault("QuikPlGd", [])
    member_rows.setdefault("QuikPlUw", [])
    member_rows.setdefault("QuikPlBd", [])
    member_rows.setdefault("QuikPlSt", [])
    member_rows.setdefault("QuikPlNb", [])

    plan_real_g = collections.defaultdict(set)
    plan_real_u = collections.defaultdict(set)
    plan_real_b = collections.defaultdict(set)
    for p, code in gd:
        if code and code != _NA_GENDER:
            plan_real_g[p].add(code)
    for p, code in uw:
        if code and code != _NA_UW:
            plan_real_u[p].add(code)
    for p, code in bd:
        if code and code != _NA_BAND:
            plan_real_b[p].add(code)

    for rows in (key_rows or {}).values():
        for r in rows:
            plan = (r.get("PLAN") or "").strip()
            if not plan:
                continue
            gender = (r.get("GENDER") or "").strip()
            uwclass = (r.get("UWCLASS") or "").strip()
            band = (r.get("BAND") or "").strip()
            isscntry = (r.get("ISSCNTRY") or "").strip() or "0000"
            issuest = (r.get("ISSUEST") or "").strip() or "00"
            if gender and (plan, gender) not in gd:
                if gender == _NA_GENDER and plan_real_g[plan]:
                    continue
                member_rows["QuikPlGd"].append({
                    "PLAN": plan, "GDCODE": gender,
                    "GDDESCR": S.GENDER_LABEL.get(gender, gender),
                })
                gd.add((plan, gender))
                if gender != _NA_GENDER:
                    plan_real_g[plan].add(gender)
                added += 1
            if uwclass and (plan, uwclass) not in uw:
                if uwclass == _NA_UW and plan_real_u[plan]:
                    continue
                member_rows["QuikPlUw"].append({
                    "PLAN": plan, "UWCODE": uwclass,
                    "UWDESCR": S.UWCLASS_LABEL.get(uwclass, uwclass),
                })
                uw.add((plan, uwclass))
                if uwclass != _NA_UW:
                    plan_real_u[plan].add(uwclass)
                added += 1
            if band and (plan, band) not in bd:
                if band == _NA_BAND and plan_real_b[plan]:
                    continue
                member_rows["QuikPlBd"].append({
                    "PLAN": plan, "BDCODE": band,
                    "BDDESCR": S.BAND_LABEL.get(band, band),
                    "BDLOWVAL": 0.0,
                })
                bd.add((plan, band))
                if band != _NA_BAND:
                    plan_real_b[plan].add(band)
                added += 1
            if (plan, isscntry, issuest) not in st:
                member_rows["QuikPlSt"].append({
                    "PLAN": plan, "ISSCNTRY": isscntry,
                    "CNTRYTXT": S.DEFAULT_CNTRY_TXT, "ISSUEST": issuest,
                    "STATETXT": S.DEFAULT_STATE_TXT,
                    "MLOANINT": DEFAULT_MLOANINT, "MLOANINTX": "",
                })
                st.add((plan, isscntry, issuest))
                added += 1
            if (plan, isscntry, issuest) not in nb:
                member_rows["QuikPlNb"].append({
                    "PLAN": plan, "ISSCNTRY": isscntry, "ISSUEST": issuest,
                    "EFFDATE": effdate, "TERMDATE": "",
                })
                nb.add((plan, isscntry, issuest))
                added += 1
    # Final prune in case key walk re-introduced NA beside real codes
    removed = prune_default_members_when_real_exist(member_rows)
    return added - removed if removed else added


def build_quikuwpo_rows(member_rows, key_rows=None):
    """Issue A A10 — distinct UWCODE master for QuikUwpo (one row per code, always include 00)."""
    codes = {"00"}
    for row in member_rows.get("QuikPlUw") or []:
        code = (row.get("UWCODE") or "").strip()
        if code:
            codes.add(code)
    if key_rows:
        for rows in key_rows.values():
            for row in rows or []:
                code = (row.get("UWCLASS") or "").strip()
                if code:
                    codes.add(code)
    out = []
    for code in sorted(codes):
        descr = S.UWCLASS_LABEL.get(code, code)
        out.append({"UWCODE": code, "UWDESCR": (descr or code)[:20]})
    return out
