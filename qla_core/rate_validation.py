"""
QLAdmin V5 rate emit validation — implements the R4 validation matrix as gated checks.

Severities:
  BLOCKER  must pass before emit.
  WARNING  reported, does not block (e.g. deferred actuarial assumptions, precision reduction).

Per business clarification (R5): missing actuarial assumptions are WARNINGS (deferred), not
blockers; loader construction proceeds. Factor capacity uses the confirmed CHAR(7) text rule
(magnitude preserved, precision reduced only if needed) — values are blocked only if they
cannot fit 7 chars even as an integer.
"""
import collections

from qla_core import rate_dbf_schema as S

GENDER_DOMAIN = {"F", "M", "J", "0"}
UWCLASS_DOMAIN = {"00", "NS", "SM", "PR", "ST"}
BAND_DOMAIN = {"00", "01", "02", "03"}
TYPE_FAMILY = {"PR": "GROSS_PREMIUM", "BP": "GROSS_PREMIUM", "U6": "CURRENT_COI", "U5": "GUARANTEED_COI",
               "CV": "CASH_VALUE", "DB": "DEATH_BENEFIT",
               "DV": "DIVIDEND", "NP": "NET_PREMIUM", "RV": "TERMINAL_RESERVE"}

# ISWL Phase 2 — billable premium MPLANs (PAAGERAT BP authority)
ISWL_BP_MPLANS = frozenset({"1658CS", "1659CS", "1669SR", "1679CS"})
# ISWL Phase 3 — current COI MPLANs (PAAGERAT U6)
ISWL_COI_MPLANS = frozenset({"1658CS", "1679CS"})
# ISWL Phase 4 — guaranteed COI MPLANs (PAAGERAT U5)
ISWL_GCOI_MPLANS = frozenset({"1679CS"})


def _issue(issues, vid, severity, table, detail, **kw):
    rec = {"id": vid, "severity": severity, "table": table, "detail": detail}
    rec.update(kw)
    issues.append(rec)


def _valid_effdate(s):
    s = (s or "").strip()
    if len(s) != 8 or not s.isdigit():
        return False
    y, m, d = int(s[:4]), int(s[4:6]), int(s[6:8])
    return 1 <= m <= 12 and 1 <= d <= 31  # YYYYMMDD shape check


def validate(grids, factor_rows_by_table, fmt_issues, key_rows_by_table,
             dependency_notes, authoritative_plans, config):
    """Run all applicable gates. Returns (issues, summary Counter)."""
    issues = []
    summary = collections.Counter()
    auth = set(authoritative_plans or [])

    # ---- factor-row gates ----
    for table, rows in factor_rows_by_table.items():
        pfx = S.PREFIX[table]
        seen_keys = set()
        for row in rows:
            plan = row["PLAN"]
            key = (plan, row["AGE"], row["CNTL"], row["GENDER"], row["UWCLASS"],
                   row["BAND"], row["ISSCNTRY"], row["ISSUEST"], row["EFFDATE"])
            # V01 PLAN in authoritative catalog
            if auth and plan not in auth:
                _issue(issues, "V01", "BLOCKER", table, f"PLAN {plan} not in authoritative catalog")
            # V02 PLAN no spaces / nonblank
            if (not plan) or (" " in plan):
                _issue(issues, "V02", "BLOCKER", table, f"PLAN '{plan}' blank or contains space")
            # V03 no duplicate factor keys
            if key in seen_keys:
                _issue(issues, "V03", "BLOCKER", table, f"duplicate factor key {key}")
            seen_keys.add(key)
            # V08 valid AGE
            if not (row["AGE"].isdigit() and 0 <= int(row["AGE"]) <= 99):
                _issue(issues, "V08", "BLOCKER", table, f"invalid AGE '{row['AGE']}' key={key}")
            # V09 valid CNTL
            if not (row["CNTL"].isdigit() and int(row["CNTL"]) >= 0):
                _issue(issues, "V09", "BLOCKER", table, f"invalid CNTL '{row['CNTL']}' key={key}")
            # V11 segmentation present
            if any(row[f] in (None, "") for f in ("GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST")):
                _issue(issues, "V11", "BLOCKER", table, f"missing segmentation dimension key={key}")
            # V12 crosswalk domains
            if row["GENDER"] not in GENDER_DOMAIN:
                _issue(issues, "V12", "BLOCKER", table, f"GENDER '{row['GENDER']}' out of domain key={key}")
            if row["UWCLASS"] not in UWCLASS_DOMAIN:
                _issue(issues, "V12", "BLOCKER", table, f"UWCLASS '{row['UWCLASS']}' out of domain key={key}")
            if row["BAND"] not in BAND_DOMAIN:
                _issue(issues, "V12", "BLOCKER", table, f"BAND '{row['BAND']}' out of domain key={key}")
            # V07 EFFDATE must be the authoritative standard generation
            if row["EFFDATE"] != S.STANDARD_EFFDATE:
                _issue(issues, "V07", "BLOCKER", table,
                       f"EFFDATE '{row['EFFDATE']}' != {S.STANDARD_EFFDATE} key={key}")

    # ---- V10 factor fits target field (from formatter) ----
    for fi in fmt_issues:
        if fi["issue"] == "DOES_NOT_FIT":
            _issue(issues, "V10", "BLOCKER", fi["table"],
                   f"value {fi['value']} field {fi['field']} cannot fit CHAR(7)", lineno=fi.get("lineno"))
        elif fi["issue"] == "PRECISION_REDUCED":
            _issue(issues, "V10", "WARNING", fi["table"],
                   f"value {fi['value']} stored as '{fi['text']}' (decimal precision reduced to fit CHAR(7))",
                   lineno=fi.get("lineno"))

    # ---- key-table gates ----
    factor_keys_by_keytable = collections.defaultdict(set)
    for table, grid in grids.items():
        if table not in S.KEY_TABLE:
            continue
        kt = S.KEY_TABLE[table]
        for (plan, age, cntl, g, u, b, c, st, eff) in grid.keys():
            factor_keys_by_keytable[kt].add((plan, g, u, b, c, st, eff))

    for kt, rows in key_rows_by_table.items():
        seen = set()
        keyset = set()
        for row in rows:
            seg = (row["PLAN"], row["GENDER"], row["UWCLASS"], row["BAND"],
                   row["ISSCNTRY"], row["ISSUEST"], row["EFFDATE"])
            keyset.add(seg)
            # V07 EFFDATE must be the authoritative standard generation (key rows)
            if row["EFFDATE"] != S.STANDARD_EFFDATE:
                _issue(issues, "V07", "BLOCKER", kt,
                       f"key EFFDATE '{row['EFFDATE']}' != {S.STANDARD_EFFDATE} {seg}")
            # V04 no duplicate key rows
            if seg in seen:
                _issue(issues, "V04", "BLOCKER", kt, f"duplicate rate-key row {seg}")
            seen.add(seg)
            # V06 key resolves at least one factor row
            if seg not in factor_keys_by_keytable[kt]:
                _issue(issues, "V06", "WARNING", kt, f"rate key {seg} has no factor rows")
        # V05 every factor row has a parent key row
        for seg in factor_keys_by_keytable[kt]:
            if seg not in keyset:
                _issue(issues, "V05", "BLOCKER", kt, f"orphan factor segmentation {seg} has no rate key")

    # ---- V15 assumptions deferred (WARNING per business clarification #2) ----
    for dep in dependency_notes:
        _issue(issues, "V15", "WARNING", dep["key_table"],
               f"assumptions deferred for PLAN {dep['plan']}: {','.join(dep['missing'])}")

    for rec in issues:
        summary[(rec["id"], rec["severity"])] += 1
    return issues, summary


def age_cap_warnings(cap_counter):
    """
    Build AGE_CAPPED_TO_99 warnings from a counter keyed
    (PLAN, TYPE_CODE, ORIGINAL_AGE, EMITTED_AGE) -> ROW_COUNT.
    Controlled, audited transformation: never a blocker.
    """
    out = []
    for (plan, type_code, original_age, emitted_age), count in sorted(cap_counter.items()):
        out.append({
            "id": "AGE_CAPPED_TO_99", "severity": "WARNING",
            "table": TYPE_FAMILY.get(type_code, type_code),
            "detail": f"PLAN {plan} {type_code}: AGE {original_age} capped to {emitted_age} ({count} rows)",
            "plan": plan, "type_code": type_code,
            "original_age": original_age, "emitted_age": emitted_age, "row_count": count,
        })
    return out


def blockers(issues):
    return [i for i in issues if i["severity"] == "BLOCKER"]
