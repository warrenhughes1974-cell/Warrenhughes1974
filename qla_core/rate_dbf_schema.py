"""
QLAdmin V5 rate DBF schema — single source of truth for rate factor / rate-key table
structure, segmentation crosswalks, duration paging, and the CHAR(7) factor formatter.

CONFIRMED from physical DBF descriptors (docs/plan_conversion_reference):
  Factor tables (QuikGps/QuikCvs/QuikDbs/QuikDvs/QuikNps/QuikTvs) field order:
    PLAN(C6) AGE(C2) CNTL(C2) <PFX0..PFX9>(C7) GENDER(C1) UWCLASS(C2) BAND(C2)
    ISSCNTRY(C4) ISSUEST(C2) EFFDATE(D8)
  Rate-key tables: PLAN(C6) GENDER(C1) UWCLASS(C2) BAND(C2) ISSCNTRY(C4) ISSUEST(C2) EFFDATE(D8)
    QuikPlCv adds: MORT(C2) ETIMORT(C2) NFOINT(C1) INTMETHCV(C1)
    QuikPlTv adds: MORT(C2) RSVINT(C1) RSVMETH(C1) INTMETHTV(C1) STOREMEANS(L1) CALCMIDS(L1)
    (QuikPlTv is shared by NP per business decision)

Factor field capacity (CONFIRMED): factor columns are Character(7) — a literal 7-char
text string (descriptor decimals=0; the decimal point is a literal character). QLAdmin
stores the textual decimal, so capacity is "any decimal string that fits 7 chars"
(integer magnitude up to 9,999,999), NOT a hard 9999.99 numeric ceiling. Values above
9999.99 are storable when the textual form fits 7 chars (e.g. 26418.10 -> "26418.1").
"""

# ---- family routing (business-confirmed) ----
TYPE_TO_TABLE = {"CV": "QuikCvs", "DB": "QuikDbs", "NP": "QuikNps",
                 "DV": "QuikDvs", "RV": "QuikTvs", "PR": "QuikGps",
                 "NF": "QuikNff"}
FAMILY = {"QuikGps": "GROSS_PREMIUM", "QuikCvs": "CASH_VALUE", "QuikDbs": "DEATH_BENEFIT",
          "QuikDvs": "DIVIDEND", "QuikNps": "NET_PREMIUM", "QuikTvs": "TERMINAL_RESERVE",
          "QuikNff": "NONFORFEITURE_FACTOR",
          "QuikCoi": "CURRENT_COI", "QuikGcoi": "GUARANTEED_COI"}
PREFIX = {"QuikGps": "GP", "QuikCvs": "CV", "QuikDbs": "DB",
          "QuikDvs": "DV", "QuikNps": "NP", "QuikTvs": "TV",
          "QuikNff": "NFF", "QuikCoi": "QX", "QuikGcoi": "QX"}
KEY_TABLE = {"QuikGps": "QuikPlGp", "QuikCvs": "QuikPlCv", "QuikDbs": "QuikPlDb",
             "QuikDvs": "QuikPlDv", "QuikNps": "QuikPlTv", "QuikTvs": "QuikPlTv"}
# QuikCoi / QuikGcoi are standalone QLAdmin factor tables (Help §7.73 / §7.93).
# They do NOT have QuikPlxx rate-key companion tables — do not emit QuikPlCoi / QuikPlGcoi.
COI_FACTOR_TABLES = frozenset({"QuikCoi", "QuikGcoi"})
EXCLUDED_TYPE_CODES = frozenset({"NN", "PN", "TP", "TX", "UF", "SL"})

# ---- segmentation crosswalks (business-confirmed) ----
SEX_MAP = {"F": "F", "M": "M", "J": "J"}
BAND_MAP = {"1": "01", "2": "02", "3": "03"}
# Issue #118 — form-aware UW map (Underwriting Classes by Form + Eric L14).
# Legacy flat UWCLASS_MAP kept for reference/tests; runtime uses map_uwclass(..., plan/coverage).
UWCLASS_MAP = {"0": "00", "N": "NS", "S": "SM", "P": "PR", "B": "ST"}
# L10 smoker/blend family — LifePRO S = Smoker, B = Blended
L10_COVERAGE_PREFIXES = ("L10",)
L10_COVERAGE_IDS = frozenset({
    "L10 LP95", "L10 LP95SR", "L10 PRE97", "L10 PREUNI", "L10 CDT", "L10 SDT",
    "L10 OLD", "L10 SR OLD",
})
# Must cover every "L10*" coverage in the Policy Form Crosswalk. QLAdmin plan codes do not
# carry the family name consistently (910SWP, 9CDTWP), so the set is enumerated and guarded
# by validate_issue118_uwclass.py rather than pattern-matched.
L10_PLANS = frozenset({
    "1L1095", "1L10OD", "1L10PR", "1L10SO", "1L10SR",
    "5CDT10", "7SDT10", "9ADB10", "9OLDWP", "9WPL10", "910RWP",
    "9GPO10", "9JPO10", "910SWP", "9CDTWP",
})
L14_COVERAGE_IDS = frozenset({"L14"})
L14_PLANS = frozenset({"1L14SC"})
# Approved QLAdmin UW domain after #118 (NS retired from QuikUwpo / new emits)
QLA_UWCLASS_DOMAIN = frozenset({"00", "ST", "PR", "SM", "BL", "NT", "PQ"})
# Backward-compatible alias used by older rider pass-through checks
QLA_RIDER_UWCLASS_PASS = QLA_UWCLASS_DOMAIN

FACTOR_FIELD_LEN = 7
COI_FACTOR_FIELD_LEN = 10  # QuikCoi/QuikGcoi QX0–QX9 per QLAdmin Help §7.73 / §7.93
NFF_FACTOR_FIELD_LEN = 10  # QuikNff NFF0-NFF9 per QLAdmin Help §7.158
FACTOR_FIELD_LEN_BY_TABLE = {
    "QuikCoi": COI_FACTOR_FIELD_LEN,
    "QuikGcoi": COI_FACTOR_FIELD_LEN,
    "QuikNff": NFF_FACTOR_FIELD_LEN,
}
N_DURATION_COLS = 10
DEFAULT_DECIMALS = 2  # LifePRO source precision / QLAdmin convention
MAX_AGE = 99          # QLAdmin AGE field is C2; ages above this are capped (business rule)
STANDARD_EFFDATE = "19000101"  # authoritative single rate generation (no effective-date variants)


def factor_field_len(table):
    """CHAR width for factor columns (GP/CV/QX/etc.) on a given table."""
    return FACTOR_FIELD_LEN_BY_TABLE.get(table, FACTOR_FIELD_LEN)


def factor_table_fields(table):
    """Confirmed ordered (name, type, length, decimals) for a factor table."""
    pfx = PREFIX[table]
    flen = factor_field_len(table)
    fields = [("PLAN", "C", 6, 0), ("AGE", "C", 2, 0), ("CNTL", "C", 2, 0)]
    fields += [(f"{pfx}{i}", "C", flen, 0) for i in range(N_DURATION_COLS)]
    fields += [("GENDER", "C", 1, 0), ("UWCLASS", "C", 2, 0), ("BAND", "C", 2, 0),
               ("ISSCNTRY", "C", 4, 0), ("ISSUEST", "C", 2, 0), ("EFFDATE", "D", 8, 0)]
    return fields


_KEY_BASE = [("PLAN", "C", 6, 0), ("GENDER", "C", 1, 0), ("UWCLASS", "C", 2, 0),
             ("BAND", "C", 2, 0), ("ISSCNTRY", "C", 4, 0), ("ISSUEST", "C", 2, 0),
             ("EFFDATE", "D", 8, 0)]
_KEY_ASSUMPTIONS = {
    "QuikPlCv": [("MORT", "C", 2, 0), ("ETIMORT", "C", 2, 0), ("NFOINT", "C", 1, 0),
                 ("INTMETHCV", "C", 1, 0)],
    "QuikPlTv": [("MORT", "C", 2, 0), ("RSVINT", "C", 1, 0), ("RSVMETH", "C", 1, 0),
                 ("INTMETHTV", "C", 1, 0), ("STOREMEANS", "L", 1, 0), ("CALCMIDS", "L", 1, 0)],
}


def key_table_fields(key_table):
    """Confirmed ordered (name, type, length, decimals) for a QuikPlxx key table."""
    return list(_KEY_BASE) + list(_KEY_ASSUMPTIONS.get(key_table, []))


# ---- member / dimension tables (confirmed layouts) ----
_MEMBER_TABLE_FIELDS = {
    "QuikPlGd": [("PLAN", "C", 6, 0), ("GDCODE", "C", 1, 0), ("GDDESCR", "C", 20, 0)],
    "QuikPlUw": [("PLAN", "C", 6, 0), ("UWCODE", "C", 2, 0), ("UWDESCR", "C", 20, 0)],
    "QuikPlBd": [("PLAN", "C", 6, 0), ("BDCODE", "C", 2, 0), ("BDDESCR", "C", 20, 0),
                 ("BDLOWVAL", "N", 10, 3)],
    "QuikPlSt": [("PLAN", "C", 6, 0), ("ISSCNTRY", "C", 4, 0), ("CNTRYTXT", "C", 25, 0),
                 ("ISSUEST", "C", 2, 0), ("STATETXT", "C", 20, 0), ("MLOANINT", "N", 5, 2),
                 ("MLOANINTX", "C", 1, 0)],
    "QuikPlNb": [("PLAN", "C", 6, 0), ("ISSCNTRY", "C", 4, 0), ("ISSUEST", "C", 2, 0),
                 ("EFFDATE", "D", 8, 0), ("TERMDATE", "D", 8, 0)],
    "QuikUint": [("MPLAN", "C", 6, 0), ("MEFFDATE", "D", 8, 0),
                 ("MGTDRATE", "N", 8, 4), ("MCURRATE", "N", 8, 4)],
    "QuikAint": [("MPLAN", "C", 6, 0), ("MEFFDATE", "D", 8, 0),
                 ("MINTRATE", "N", 7, 4), ("MINTRATE1", "N", 7, 4)],
    "QuikIssc": [("PLAN", "C", 6, 0), ("AGE", "N", 3, 0), ("GENDER", "C", 1, 0),
                 ("UWCLASS", "C", 2, 0), ("BAND", "C", 2, 0), ("ISSCNTRY", "C", 4, 0),
                 ("ISSUEST", "C", 2, 0)]
                 + [(f"SCHG{i:02d}", "N", 8, 4) for i in range(1, 21)],
}
MEMBER_TABLES = list(_MEMBER_TABLE_FIELDS.keys())

# Standard member-code descriptions (conventional labels; not actuarial/business values).
# Issue #118: 00 = Standard (LifePRO class 0); NT/PQ truncated to C(20).
GENDER_LABEL = {"0": "NOT APPLICABLE", "M": "MALE", "F": "FEMALE", "J": "JOINT"}
UWCLASS_LABEL = {
    "00": "STANDARD",
    "ST": "STANDARD",
    "PR": "PREFERRED",
    "SM": "STANDARD SMOKER",
    "BL": "BLENDED",
    "NT": "STANDARD NON-TOBACCO",  # 20
    "PQ": "PREFERRED NON-TOBAC",   # 18
}
BAND_LABEL = {"00": "NOT APPLICABLE", "01": "BAND 1", "02": "BAND 2", "03": "BAND 3"}
DEFAULT_CNTRY_TXT = "ALL (OTHER)"
DEFAULT_STATE_TXT = "ALL (OTHER)"


def member_table_fields(name):
    return list(_MEMBER_TABLE_FIELDS[name])


def quikuint_fields():
    """QuikUint UL interest rates — QLAdmin Help §7.223."""
    return list(_MEMBER_TABLE_FIELDS["QuikUint"])


def quikaint_fields():
    """QuikAint annuity interest rates — QLAdmin Help §7.31."""
    return list(_MEMBER_TABLE_FIELDS["QuikAint"])


def quikissc_fields():
    """QuikIssc surrender charge schedules — QLAdmin Help §7.144."""
    return list(_MEMBER_TABLE_FIELDS["QuikIssc"])


# Issue A A10 — QuikUwpo master UW-class dropdown (Help §7.230). Not plan-keyed.
_QUIKUWPO_FIELDS = [
    ("UWCODE", "C", 2, 0),
    ("UWDESCR", "C", 20, 0),
]


def quikuwpo_fields():
    """QuikUwpo underwriting class codes — QLAdmin Help §7.230."""
    return list(_QUIKUWPO_FIELDS)


def assumption_field_names(key_table):
    return [f[0] for f in _KEY_ASSUMPTIONS.get(key_table, [])]


def dbf_spec(fields):
    """Render field list into a `dbf` library spec string (used by the writer, R5+)."""
    parts = []
    for name, t, length, dec in fields:
        if t == "C":
            parts.append(f"{name} C({length})")
        elif t == "N":
            parts.append(f"{name} N({length},{dec})")
        elif t == "D":
            parts.append(f"{name} D")
        elif t == "L":
            parts.append(f"{name} L")
        else:
            parts.append(f"{name} C({length})")
    return "; ".join(parts)


# ---- segmentation transforms ----
def map_sex(raw):
    return SEX_MAP.get((raw or "").strip(), None)


def map_band(raw):
    """Map LifePRO band to QLAdmin BAND.

    Issue #71: fleet standard is 00 (NOT APPLICABLE), matching quikridr MBAND=00.
    LifePRO bands 1/2/3 (and padded 01/02/03) all collapse to 00 at emit.
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    if raw in BAND_MAP or raw in ("00", "01", "02", "03"):
        return "00"
    return None


def band_collapse_priority(raw):
    """Prefer former band 01 when multi-band rows collapse (Issue #71 SD-71-5). Lower wins."""
    raw = (raw or "").strip()
    if raw in ("1", "01"):
        return 1
    if raw in ("2", "02"):
        return 2
    if raw in ("3", "03"):
        return 3
    if raw in ("0", "00"):
        return 0
    return 99


def _is_l10_context(plan=None, coverage_id=None):
    """True when product is L10 smoker/blend family (S=Smoker, B=Blended)."""
    plan = (plan or "").strip().upper()
    cov = (coverage_id or "").strip().upper()
    if plan in {p.upper() for p in L10_PLANS}:
        return True
    if cov in {c.upper() for c in L10_COVERAGE_IDS}:
        return True
    if plan in {c.upper() for c in L10_COVERAGE_IDS}:
        return True
    if cov.startswith(L10_COVERAGE_PREFIXES) or plan.startswith(L10_COVERAGE_PREFIXES):
        return True
    return False


def _is_l14_context(plan=None, coverage_id=None):
    plan = (plan or "").strip().upper()
    cov = (coverage_id or "").strip().upper()
    if plan in {p.upper() for p in L14_PLANS} or cov in {p.upper() for p in L14_PLANS}:
        return True
    if cov in {c.upper() for c in L14_COVERAGE_IDS} or plan in {c.upper() for c in L14_COVERAGE_IDS}:
        return True
    return False


def map_uwclass(raw, plan=None, coverage_id=None):
    """Map LifePRO UW letter → QLAdmin UWCLASS (Issue #118 form-aware).

    Returns None only when the letter cannot be mapped (caller treats as BAD_VALUE).
    """
    v = (raw or "").strip()
    if not v or set(v) <= {"-"}:
        return "00"
    if v in QLA_UWCLASS_DOMAIN:
        return v
    l14 = _is_l14_context(plan, coverage_id)
    l10 = _is_l10_context(plan, coverage_id)
    if v == "0":
        return "00"
    if v == "P":
        return "PR"
    if v == "B":
        return "BL"
    if v == "S":
        return "SM" if l10 else "ST"
    if l14:
        return {"N": "NT", "T": "ST", "Q": "PQ", "R": "PR"}.get(v)
    # Non-L14 residual letters (Risk Option A — retire NS; no orphans)
    if v in ("N", "Q", "T", "R", "M"):
        return "00"
    return None


def map_rider_uwclass(raw, plan=None, coverage_id=None):
    """Map LifePRO UNDERWRITING_CLASS → quikridr MUWCLASS (rate-key codes).

    Issue #118: form/plan-aware; never apply bare status map (S→55/P→41/N→T/T→56).
    Blank → 00 (Standard). Always returns an approved domain code when possible.
    """
    v = (raw or "").strip()
    if not v or set(v) <= {"-"}:
        return "00"
    if v in QLA_UWCLASS_DOMAIN:
        return v
    mapped = map_uwclass(v, plan=plan, coverage_id=coverage_id)
    if mapped:
        return mapped
    # Last resort: do not emit orphan LifePRO letters
    return "00"


def duration_to_cntl_col(ql_duration):
    """0-based QL duration -> (CNTL 2-char page, column index 0..9)."""
    return str(ql_duration // 10).zfill(2), ql_duration % 10


# Issue #140: QLAdmin Help 7.94 / 7.82 define the factor columns as the year axis
# (column n holds slot n + CNTL*10) and AGE as the issue-age key. An attained-age
# grid has no issue-age axis, so AGE stays 00 and the age itself is the slot that
# quikplan VARGP / VARDB = 3 ("Vary by Attained Age") tells QLAdmin to read.
ATTAINED_AGE_KEY = "00"


def attained_age_to_age_cntl_col(attained_age):
    """Attained age -> (AGE key, CNTL 2-char page, column index 0..9)."""
    cntl, col = duration_to_cntl_col(attained_age)
    return ATTAINED_AGE_KEY, cntl, col


def source_duration_to_ql(source_duration):
    """LifePRO 1-based -> QLAdmin 0-based. Returns int or raises ValueError."""
    return int(source_duration) - 1


def rv_source_duration_to_ql(source_duration):
    """Issue #106: RV LifePRO Dur labels match QuikTvs Dur (identity, not source-1)."""
    return int(source_duration)


def duration_to_ql_for_type(type_code, source_duration):
    """Route duration indexing by TYPE_CODE.

    RV = #106 identity. DV = identity as of 2026-08-13 (Warren approval, Eric
    'Rates of Identified Issues - 8.13.26' evidence: LifePRO pays the dividend
    for anniversary year N from native Dur N — e.g. 670 GL85-8 M/3 18.52@56,
    960 PO M/26 22.61@58 — and every extract DV subslice's duration labels were
    proven equal to PDAGE native years, so identity is exact). Other non-CV
    types remain source-1.
    """
    if (type_code or "").strip() in ("RV", "DV"):
        return rv_source_duration_to_ql(source_duration)
    return source_duration_to_ql(source_duration)


def format_factor(value, max_len=FACTOR_FIELD_LEN, source_decimals=DEFAULT_DECIMALS):
    """
    Format a numeric factor into the CHAR(7) text field WITHOUT scaling or truncating
    magnitude. Preserves the most decimal precision that fits `max_len` chars, reproducing
    QLAdmin's leading-zero-less convention (0.88 -> ".88", 0.0 -> ".00").

    Returns (text, fits, precision_reduced):
      fits             False only if magnitude needs > max_len chars even as an integer.
      precision_reduced True if fewer decimals than source_decimals were needed to fit
                        AND that lost real precision (i.e. magnitude preserved, <0.5 unit
                        rounding at the reduced decimal place).
    """
    if value is None:
        return "", True, False
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "", False, False

    def render(dec):
        s = f"{v:.{dec}f}"
        if s.startswith("0."):
            s = s[1:]
        elif s.startswith("-0."):
            s = "-" + s[2:]
        return s

    for dec in range(source_decimals, -1, -1):
        s = render(dec)
        if len(s) <= max_len:
            reduced = dec < source_decimals and round(v, dec) != round(v, source_decimals)
            return s, True, reduced
    # cannot fit even as integer -> true overflow (magnitude too large for the field)
    return render(0), False, True
